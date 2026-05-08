"""
KDP_MASTER - File Indexer Service
================================
Indexador de archivos con soporte para threading y FTS5.
"""

import os
import hashlib
import threading
import queue
from pathlib import Path
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

try:
    from app.database.db_manager import DatabaseManager
except ImportError:
    from app.database.db_manager import DatabaseManager as DatabaseManager

logger = logging.getLogger(__name__)

FILE_TYPE_MAP = {
    '.vtt': 'transcription',
    '.srt': 'transcription',
    '.mp4': 'video',
    '.mkv': 'video',
    '.avi': 'video',
    '.mov': 'video',
    '.webm': 'video',
    '.mp3': 'audio',
    '.wav': 'audio',
    '.m4a': 'audio',
    '.flac': 'audio',
    '.pdf': 'document',
    '.doc': 'document',
    '.docx': 'document',
    '.txt': 'document',
    '.png': 'image',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.gif': 'image',
    '.webp': 'image',
}

MAX_SIZE_FOR_HASH = 5 * 1024 * 1024


class FileIndexer:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.scan_queue = queue.Queue()
        self._executor = None
        self._cancelled = False
    
    def classify_file(self, file_path: str) -> str:
        """Clasifica el tipo de archivo por extensión."""
        ext = Path(file_path).suffix.lower()
        return FILE_TYPE_MAP.get(ext, 'other')
    
    def should_reindex(self, file_path: str) -> bool:
        """Determina si un archivo debe ser reindexado comparando mtime y tamaño."""
        if not os.path.exists(file_path):
            return False
        try:
            stat = os.stat(file_path)
            current_mtime = stat.st_mtime
            current_size = stat.st_size
            existing = self.db.file_index_exists(file_path)
            if not existing:
                return True
            return existing['mtime'] != current_mtime or existing['file_size'] != current_size
        except OSError:
            return False
    
    def calculate_hash(self, file_path: str) -> Optional[str]:
        """Calcula hash MD5 para archivos pequeños ( <=5MB)."""
        try:
            size = os.path.getsize(file_path)
            if size > MAX_SIZE_FOR_HASH:
                return None
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, IOError):
            return None
    
    def index_file(self, file_path: str, base_paths: List[str] = None) -> Optional[int]:
        """Indexa un solo archivo."""
        if not os.path.isfile(file_path):
            return None
        try:
            stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_type = self.classify_file(file_path)
            parent_dir = os.path.dirname(file_path)
            content_hash = self.calculate_hash(file_path) if file_type == 'transcription' else None
            metadata = {
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
            }
            file_id = self.db.file_index_upsert(
                file_path=file_path,
                file_name=file_name,
                file_type=file_type,
                file_size=stat.st_size,
                mtime=stat.st_mtime,
                content_hash=content_hash,
                parent_dir=parent_dir,
                metadata_json=str(metadata)
            )
            if file_type == 'transcription' and file_id:
                self._index_transcription_content(file_path, file_id)
            return file_id
        except Exception as e:
            logger.error(f"Error indexando {file_path}: {e}")
            return None
    
    def _index_transcription_content(self, file_path: str, file_id: int):
        """Añade contenido de transcripción a FTS5."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            self.db.transcription_add_content(file_id, content)
        except Exception as e:
            logger.warning(f"Fallo al indexar contenido FTS5 para {file_path}: {e}")
    
    def scan_directory(self, path: str, base_paths: List[str] = None) -> List[Dict]:
        """Escanea un directorio síncrono (para uso no-GUI)."""
        results = []
        if not os.path.isdir(path):
            return results
        for root, dirs, files in os.walk(path):
            for f in files:
                fpath = os.path.join(root, f)
                if self.should_reindex(fpath):
                    file_id = self.index_file(fpath, base_paths)
                    if file_id:
                        results.append({"file_path": fpath, "file_id": file_id})
        return results
    
    def init_background_scan(self, paths: List[str], ui_callback: Callable = None):
        """
        Inicia escaneo en background sin congelar UI.
        
        ui_callback(status: str, current: int, total: int, filename: str)
        status: 'scanning' | 'indexing' | 'done' | 'error'
        """
        self._cancelled = False
        self._executor = ThreadPoolExecutor(max_workers=2)
        thread = threading.Thread(
            target=self._background_worker,
            args=(paths, ui_callback),
            daemon=True
        )
        thread.start()
    
    def _background_worker(self, paths: List[str], ui_callback: Callable):
        """Worker que ejecuta el escaneo en background."""
        total_files = 0
        indexed_count = 0
        error_count = 0
        all_files = []
        
        for path in paths:
            if self._cancelled:
                break
            if not os.path.isdir(path):
                continue
            for root, dirs, files in os.walk(path):
                for f in files:
                    all_files.append(os.path.join(root, f))
        total_files = len(all_files)
        
        if ui_callback:
            ui_callback('scanning', 0, total_files, '')
        
        for i, fpath in enumerate(all_files):
            if self._cancelled:
                break
            if self.should_reindex(fpath):
                if ui_callback:
                    ui_callback('indexing', i + 1, total_files, os.path.basename(fpath))
                try:
                    file_id = self.index_file(fpath, paths)
                    if file_id:
                        indexed_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"Error indexando {fpath}: {e}")
                    error_count += 1
        
        if ui_callback:
            ui_callback('done', indexed_count, total_files, f'{indexed_count} archivos indexados')
        logger.info(f"Indexación completada: {indexed_count} indexados, {error_count} errores")
    
    def cancel_scan(self):
        """Cancela el escaneo en progreso."""
        self._cancelled = True
        if self._executor:
            self._executor.shutdown(wait=False)
    
    def search_transcriptions(self, query: str, limit: int = 50) -> List[Dict]:
        """Busca en transcripciones usando FTS5."""
        return self.db.transcription_search(query, limit)
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de la indexación."""
        return self.db.file_index_get_stats()
    
    def purge_missing(self, base_paths: List[str]) -> int:
        """Elimina entradas de archivos que ya no existen."""
        return self.db.file_index_purge_missing(base_paths)