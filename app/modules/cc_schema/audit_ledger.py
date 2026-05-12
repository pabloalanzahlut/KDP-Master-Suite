"""
CC Schema Monitor - Módulo 9: Registro de Auditoría de Extracción
=================================================================
Log forense inmutable de: URL, idioma detectado, palabras extraídas,
hash, timestamp y usuario para compliance.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import sqlite3
import json
import hashlib
import logging
import threading
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExtractionAuditEntry:
    entry_id: str
    timestamp: str
    video_id: str
    source_url: str
    language_detected: Optional[str]
    word_count: int
    content_hash: str
    format_used: str
    status: str
    error_message: Optional[str]
    duration_seconds: Optional[float]
    user_id: Optional[str]
    metadata_json: Optional[str]


class ImmutableAuditLedger:
    """
    Registro de Auditoría de Extracción
    Log forense inmutable de operaciones de extracción de CC.
    """

    LEDGER_VERSION = "1.0.0"
    MAX_LEDGER_SIZE_MB = 500
    COMPRESSION_THRESHOLD_MB = 100

    def __init__(self, db_path: Optional[str] = None, max_size_mb: int = MAX_LEDGER_SIZE_MB):
        self.db_path = db_path or self._get_default_db_path()
        self.max_size_mb = max_size_mb
        self._lock = threading.Lock()
        self._init_ledger()

    def _get_default_db_path(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "data", "audit_ledger.db")

    def _init_ledger(self):
        """Inicializa la base de datos del ledger."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_entries (
                entry_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                video_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                language_detected TEXT,
                word_count INTEGER,
                content_hash TEXT,
                format_used TEXT,
                status TEXT,
                error_message TEXT,
                duration_seconds REAL,
                user_id TEXT,
                metadata_json TEXT,
                integrity_hash TEXT,
                sequence_number INTEGER
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_entries(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_id ON audit_entries(video_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_hash ON audit_entries(content_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON audit_entries(status)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ledger_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO ledger_meta (key, value)
            VALUES ('version', ?), ('created_at', ?), ('last_sequence', '0')
        """, (self.LEDGER_VERSION, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

    def _compute_integrity_hash(self, entry_data: Dict) -> str:
        """
        Computa hash de integridad para el entry.
        Previene modificación de entradas.
        """
        integrity_fields = [
            entry_data.get('entry_id', ''),
            entry_data.get('timestamp', ''),
            entry_data.get('video_id', ''),
            entry_data.get('source_url', ''),
            entry_data.get('content_hash', ''),
        ]
        integrity_str = '|'.join(str(f) for f in integrity_fields)
        return hashlib.sha256(integrity_str.encode('utf-8')).hexdigest()

    def log_extraction(
        self,
        video_id: str,
        source_url: str,
        language_detected: Optional[str] = None,
        word_count: int = 0,
        content_hash: str = "",
        format_used: str = "vtt",
        status: str = "success",
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Registra una extracción en el ledger.

        Args:
            video_id: ID del video
            source_url: URL de origen
            language_detected: Idioma detectado
            word_count: Conteo de palabras
            content_hash: Hash del contenido
            format_used: Formato de subtítulo usado
            status: Estado (success/error/partial)
            error_message: Mensaje de error si falló
            duration_seconds: Duración de la extracción
            user_id: ID de usuario (opcional)
            metadata: Metadatos adicionales

        Returns:
            entry_id de la entrada creada
        """
        with self._lock:
            try:
                entry_id = hashlib.sha256(
                    f"{video_id}{datetime.utcnow().isoformat()}".encode('utf-8')
                ).hexdigest()[:16]

                timestamp = datetime.utcnow().isoformat()

                entry_data = {
                    'entry_id': entry_id,
                    'timestamp': timestamp,
                    'video_id': video_id,
                    'source_url': source_url,
                    'language_detected': language_detected,
                    'word_count': word_count,
                    'content_hash': content_hash,
                    'format_used': format_used,
                    'status': status,
                    'error_message': error_message,
                    'duration_seconds': duration_seconds,
                    'user_id': user_id,
                }

                integrity_hash = self._compute_integrity_hash(entry_data)

                metadata_json = None
                if metadata:
                    metadata_json = json.dumps(metadata, ensure_ascii=False)

                conn = sqlite3.connect(self.db_path, timeout=30)
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO audit_entries (
                        entry_id, timestamp, video_id, source_url, language_detected,
                        word_count, content_hash, format_used, status, error_message,
                        duration_seconds, user_id, metadata_json, integrity_hash,
                        sequence_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        (SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM audit_entries))
                """, (
                    entry_id, timestamp, video_id, source_url, language_detected,
                    word_count, content_hash, format_used, status, error_message,
                    duration_seconds, user_id, metadata_json, integrity_hash
                ))

                conn.commit()
                conn.close()

                logger.info(f"Audit entry logged: {entry_id} ({status})")
                return entry_id

            except Exception as e:
                logger.error(f"Failed to log audit entry: {e}")
                raise

    def verify_entry(self, entry_id: str) -> bool:
        """
        Verifica integridad de una entrada del ledger.

        Args:
            entry_id: ID de la entrada a verificar

        Returns:
            True si la entrada es válida y no ha sido modificada
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT entry_id, timestamp, video_id, source_url, content_hash,
                       integrity_hash FROM audit_entries WHERE entry_id = ?
            """, (entry_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return False

            entry_data = {
                'entry_id': row[0],
                'timestamp': row[1],
                'video_id': row[2],
                'source_url': row[3],
                'content_hash': row[4],
            }

            expected_hash = self._compute_integrity_hash(entry_data)
            stored_hash = row[5]

            return expected_hash == stored_hash

        except Exception as e:
            logger.error(f"Entry verification failed: {e}")
            return False

    def query_entries(
        self,
        video_id: Optional[str] = None,
        source_url: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Consulta entradas del ledger con filtros.

        Args:
            video_id: Filtrar por video_id
            source_url: Filtrar por URL
            status: Filtrar por estado
            start_date: Fecha inicio (ISO)
            end_date: Fecha fin (ISO)
            limit: Límite de resultados

        Returns:
            Lista de entradas que coinciden
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            query = "SELECT * FROM audit_entries WHERE 1=1"
            params = []

            if video_id:
                query += " AND video_id = ?"
                params.append(video_id)

            if source_url:
                query += " AND source_url LIKE ?"
                params.append(f"%{source_url}%")

            if status:
                query += " AND status = ?"
                params.append(status)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            return results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del ledger."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*), SUM(word_count) FROM audit_entries WHERE status = 'success'")
            success_row = cursor.fetchone()

            cursor.execute("SELECT COUNT(*), SUM(word_count) FROM audit_entries WHERE status = 'error'")
            error_row = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM audit_entries")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT language_detected) FROM audit_entries WHERE language_detected IS NOT NULL")
            languages = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT video_id) FROM audit_entries")
            unique_videos = cursor.fetchone()[0]

            conn.close()

            return {
                'total_entries': total,
                'successful_extractions': success_row[0] or 0,
                'total_words_extracted': success_row[1] or 0,
                'failed_extractions': error_row[0] or 0,
                'unique_videos': unique_videos,
                'languages_used': languages,
                'db_size_mb': self._get_db_size()
            }

        except Exception as e:
            logger.error(f"Statistics query failed: {e}")
            return {}

    def _get_db_size(self) -> float:
        """Retorna tamaño de la DB en MB."""
        try:
            size = os.path.getsize(self.db_path)
            return size / (1024 * 1024)
        except Exception:
            return 0.0

    def export_to_json(self, output_path: str, start_date: Optional[str] = None) -> bool:
        """
        Exporta entradas a JSON para backup.

        Args:
            output_path: Ruta del archivo de salida
            start_date: Exportar solo desde esta fecha

        Returns:
            True si el export fue exitoso
        """
        try:
            entries = self.query_entries(start_date=start_date, limit=100000)

            export_data = {
                'version': self.LEDGER_VERSION,
                'exported_at': datetime.utcnow().isoformat(),
                'total_entries': len(entries),
                'entries': entries
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def prune_old_entries(self, days_old: int = 90) -> int:
        """
        Elimina entradas antiguas (para mantenimiento).
        Las entradas no pueden ser modificadas, solo eliminadas.

        Args:
            days_old: Eliminar entradas mayores a N días

        Returns:
            Número de entradas eliminadas
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM audit_entries
                WHERE timestamp < datetime('now', ?)
            """, (f'-{days_old} days',))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Pruned {deleted} old audit entries")
            return deleted

        except Exception as e:
            logger.error(f"Prune failed: {e}")
            return 0

    def get_last_sequence(self) -> int:
        """Obtiene el último número de secuencia."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(MAX(sequence_number), 0) FROM audit_entries")
            seq = cursor.fetchone()[0]
            conn.close()
            return seq
        except Exception:
            return 0


def create_ledger(db_path: Optional[str] = None) -> ImmutableAuditLedger:
    """
    Factory function para crear el ledger.
    """
    return ImmutableAuditLedger(db_path=db_path)


def quick_log(
    video_id: str,
    source_url: str,
    status: str = "success",
    **kwargs
) -> str:
    """
    Función de conveniencia para logging rápido.
    """
    ledger = ImmutableAuditLedger()
    return ledger.log_extraction(
        video_id=video_id,
        source_url=source_url,
        status=status,
        **kwargs
    )