"""
CC Schema Monitor - Módulo 13: Compresor LZ4 para Logs
=====================================================
Comprime texto histórico para ahorrar espacio en disco sin perder
capacidad de búsqueda FTS5.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import re
import gzip
import struct
import hashlib
import logging
import threading
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import lz4.frame
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False
    logger.warning("lz4 not available - using gzip fallback")

COMPRESSION_THRESHOLD_KB = 50
MAX_LOG_AGE_DAYS = 90


@dataclass
class CompressionResult:
    success: bool
    original_size: int
    compressed_size: int
    compression_ratio: float
    method: str
    file_path: str
    error: Optional[str] = None


@dataclass
class LogFileInfo:
    path: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    last_modified: datetime
    compressed_at: Optional[datetime] = None
    line_count: int = 0


class LogCompressor:
    """
    Compresor LZ4 para Logs de Transcripción
    Comprime texto histórico manteniendo capacidad de búsqueda.
    """

    def __init__(self, compression_level: int = 3, use_lz4: bool = LZ4_AVAILABLE):
        self.compression_level = compression_level
        self.use_lz4 = use_lz4 and LZ4_AVAILABLE
        self._stats = {
            'total_compressed': 0,
            'total_original_size': 0,
            'total_compressed_size': 0,
            'failed': 0
        }
        self._lock = threading.Lock()

    def compress_file(self, file_path: str, delete_original: bool = False) -> CompressionResult:
        """
        Comprime un archivo de log.

        Args:
            file_path: Ruta al archivo
            delete_original: Si eliminar archivo original después de comprimir

        Returns:
            CompressionResult con estadísticas
        """
        if not os.path.exists(file_path):
            return CompressionResult(
                success=False,
                original_size=0,
                compressed_size=0,
                compression_ratio=0.0,
                method="none",
                file_path=file_path,
                error="File not found"
            )

        try:
            original_size = os.path.getsize(file_path)

            if original_size < COMPRESSION_THRESHOLD_KB * 1024:
                return CompressionResult(
                    success=False,
                    original_size=original_size,
                    compressed_size=0,
                    compression_ratio=0.0,
                    method="skip_small",
                    file_path=file_path,
                    error="File too small to compress"
                )

            with open(file_path, 'rb') as f:
                data = f.read()

            if self.use_lz4:
                compressed = lz4.frame.compress(
                    data,
                    compression_level=self.compression_level,
                    content_checksum=True
                )
                method = "lz4"
            else:
                compressed = gzip.compress(data, compresslevel=self.compression_level)
                method = "gzip"

            compressed_size = len(compressed)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            compressed_path = file_path + '.lz4' if self.use_lz4 else file_path + '.gz'

            with open(compressed_path, 'wb') as f:
                f.write(compressed)

            with self._lock:
                self._stats['total_compressed'] += 1
                self._stats['total_original_size'] += original_size
                self._stats['total_compressed_size'] += compressed_size

            if delete_original:
                os.remove(file_path)

            return CompressionResult(
                success=True,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=ratio,
                method=method,
                file_path=compressed_path
            )

        except Exception as e:
            with self._lock:
                self._stats['failed'] += 1
            logger.error(f"Compression failed for {file_path}: {e}")
            return CompressionResult(
                success=False,
                original_size=0,
                compressed_size=0,
                compression_ratio=0.0,
                method="none",
                file_path=file_path,
                error=str(e)
            )

    def decompress_file(self, compressed_path: str, output_path: Optional[str] = None) -> Optional[bytes]:
        """
        Descomprime un archivo de log.

        Args:
            compressed_path: Ruta al archivo comprimido
            output_path: Ruta de salida (si None, retorna bytes)

        Returns:
            Contenido descomprimido o None si falla
        """
        if not os.path.exists(compressed_path):
            logger.error(f"Compressed file not found: {compressed_path}")
            return None

        try:
            with open(compressed_path, 'rb') as f:
                compressed = f.read()

            if compressed_path.endswith('.lz4'):
                data = lz4.frame.decompress(compressed)
            else:
                data = gzip.decompress(compressed)

            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(data)

            return data

        except Exception as e:
            logger.error(f"Decompression failed for {compressed_path}: {e}")
            return None

    def compress_directory(
        self,
        directory: str,
        pattern: str = "*.log",
        delete_original: bool = False
    ) -> List[CompressionResult]:
        """
        Comprime todos los archivos de log en un directorio.

        Args:
            directory: Directorio a procesar
            pattern: Patrón de archivos a comprimir
            delete_original: Si eliminar originales después de comprimir

        Returns:
            Lista de CompressionResult
        """
        results = []

        for root, _, files in os.walk(directory):
            for file in files:
                if re.match(pattern.replace('*', '.*'), file):
                    file_path = os.path.join(root, file)
                    result = self.compress_file(file_path, delete_original)
                    results.append(result)

        return results

    def compress_old_logs(
        self,
        directory: str,
        days_old: int = MAX_LOG_AGE_DAYS,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Comprime logs antiguos (mayores a N días).

        Args:
            directory: Directorio de logs
            days_old: Comprimir logs mayores a N días
            dry_run: Solo simular sin comprimir

        Returns:
            Estadísticas de la operación
        """
        current_time = datetime.now().timestamp()
        cutoff_time = current_time - (days_old * 86400)

        old_logs = []
        total_original_size = 0
        total_compressed_size = 0

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    mtime = os.path.getmtime(file_path)

                    if mtime < cutoff_time:
                        original_size = os.path.getsize(file_path)
                        old_logs.append(file_path)
                        total_original_size += original_size

        if dry_run:
            return {
                'dry_run': True,
                'files_found': len(old_logs),
                'total_size': total_original_size,
                'files': old_logs
            }

        results = []
        for file_path in old_logs:
            result = self.compress_file(file_path, delete_original=True)
            results.append(result)
            if result.success:
                total_compressed_size += result.compressed_size

        return {
            'dry_run': False,
            'files_processed': len(results),
            'original_size': total_original_size,
            'compressed_size': total_compressed_size,
            'space_saved': total_original_size - total_compressed_size,
            'compression_ratio': ((total_original_size - total_compressed_size) / total_original_size * 100) if total_original_size > 0 else 0
        }

    def get_log_info(self, file_path: str) -> Optional[LogFileInfo]:
        """
        Obtiene información de un archivo de log.

        Args:
            file_path: Ruta al archivo

        Returns:
            LogFileInfo o None si no existe
        """
        if not os.path.exists(file_path):
            return None

        try:
            original_size = os.path.getsize(file_path)

            compressed_path = file_path + '.lz4' if os.path.exists(file_path + '.lz4') else file_path + '.gz'
            compressed_size = os.path.getsize(compressed_path) if os.path.exists(compressed_path) else 0

            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            mtime = os.path.getmtime(file_path)
            last_modified = datetime.fromtimestamp(mtime)

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)

            return LogFileInfo(
                path=file_path,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                last_modified=last_modified,
                line_count=line_count
            )

        except Exception as e:
            logger.error(f"Failed to get log info for {file_path}: {e}")
            return None

    def search_compressed_logs(self, directory: str, pattern: str) -> List[str]:
        """
        Busca en logs comprimidos usando descompresión temporal.

        Args:
            directory: Directorio a buscar
            pattern: Patrón regex a buscar

        Returns:
            Lista de líneas coincidentes
        """
        matches = []

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.log.lz4', '.log.gz')):
                    file_path = os.path.join(root, file)
                    content = self.decompress_file(file_path)

                    if content:
                        try:
                            text = content.decode('utf-8', errors='ignore')
                            for line in text.split('\n'):
                                if re.search(pattern, line, re.IGNORECASE):
                                    matches.append(f"{file_path}: {line}")
                        except Exception as e:
                            logger.error(f"Search failed in {file_path}: {e}")

        return matches

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de compresión."""
        with self._lock:
            stats = self._stats.copy()

        if stats['total_original_size'] > 0:
            stats['overall_ratio'] = ((stats['total_original_size'] - stats['total_compressed_size']) / stats['total_original_size']) * 100
        else:
            stats['overall_ratio'] = 0.0

        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        with self._lock:
            self._stats = {
                'total_compressed': 0,
                'total_original_size': 0,
                'total_compressed_size': 0,
                'failed': 0
            }


def create_compressor(compression_level: int = 3) -> LogCompressor:
    """
    Factory function para crear el compresor.
    """
    return LogCompressor(compression_level=compression_level)


def quick_compress(file_path: str, delete: bool = False) -> CompressionResult:
    """
    Función de conveniencia para compresión rápida.
    """
    compressor = LogCompressor()
    return compressor.compress_file(file_path, delete_original=delete)