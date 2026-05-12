"""
Módulo 5: Deduplicador por Hash de Contenido Textual
Compara hash SHA-256 del texto extraído vs. KB existente para evitar redundancia semántica.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import hashlib
import logging
import sqlite3
from typing import Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationResult:
    is_duplicate: bool
    existing_id: Optional[str]
    similarity_score: float
    hash: str
    content_preview: str


class ContentHasher:
    """
    Generador de hash SHA-256 para contenido textual.
    """

    @staticmethod
    def compute_hash(content: str) -> str:
        """
        Computa hash SHA-256 normalizado del contenido.

        Args:
            content: Texto a hashear

        Returns:
            Hash SHA-256 hex
        """
        normalized = content.strip().lower()
        normalized = ' '.join(normalized.split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_partial_hash(content: str, length: int = 500) -> str:
        """
        Computa hash de los primeros N caracteres (para comparación rápida).

        Args:
            content: Texto a hashear
            length: Longitud del fragmento

        Returns:
            Hash parcial SHA-256 hex
        """
        fragment = content[:length].strip().lower()
        fragment = ' '.join(fragment.split())
        return hashlib.sha256(fragment.encode('utf-8')).hexdigest()


class ContentDeduplicator:
    """
    Deduplicador por Hash de Contenido Textual
    Compara hash SHA-256 del texto vs. KB existente para evitar duplicados.
    """

    DEFAULT_TABLE = "content_hashes"

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._get_default_db_path()
        self._init_db()

    def _get_default_db_path(self) -> str:
        from app.core.config import Config
        try:
            config = Config()
            return config.get("db.path", "knowledge_base.db")
        except Exception:
            return "knowledge_base.db"

    def _init_db(self):
        """
        Inicializa tabla de hashes si no existe.
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_hashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    partial_hash TEXT,
                    video_id TEXT,
                    source_url TEXT,
                    title TEXT,
                    content_preview TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash ON content_hashes(hash)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_partial_hash ON content_hashes(partial_hash)
            """)

            conn.commit()
            conn.close()
            logger.info(f"Content deduplicator initialized: {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to init deduplicator DB: {e}")

    def check_duplicate(self, content: str, video_id: Optional[str] = None) -> DeduplicationResult:
        """
        Verifica si el contenido ya existe en la KB.

        Args:
            content: Contenido textual a verificar
            video_id: ID del video (opcional, para metadata)

        Returns:
            DeduplicationResult con estado de duplicación
        """
        full_hash = ContentHasher.compute_hash(content)
        partial_hash = ContentHasher.compute_partial_hash(content)
        preview = content[:200].strip() if len(content) > 200 else content.strip()

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, hash, video_id, title, content_preview
                FROM content_hashes
                WHERE hash = ? OR partial_hash = ?
            """, (full_hash, partial_hash))

            row = cursor.fetchone()
            conn.close()

            if row:
                return DeduplicationResult(
                    is_duplicate=True,
                    existing_id=str(row[0]),
                    similarity_score=1.0 if row[1] == full_hash else 0.85,
                    hash=full_hash,
                    content_preview=row[4] or preview
                )

            return DeduplicationResult(
                is_duplicate=False,
                existing_id=None,
                similarity_score=0.0,
                hash=full_hash,
                content_preview=preview
            )

        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return DeduplicationResult(
                is_duplicate=False,
                existing_id=None,
                similarity_score=0.0,
                hash=full_hash,
                content_preview=preview
            )

    def register_content(
        self,
        content: str,
        video_id: Optional[str] = None,
        source_url: Optional[str] = None,
        title: Optional[str] = None
    ) -> bool:
        """
        Registra el contenido en la tabla de hashes.

        Args:
            content: Contenido textual
            video_id: ID del video
            source_url: URL de origen
            title: Título del video

        Returns:
            True si se registró correctamente
        """
        full_hash = ContentHasher.compute_hash(content)
        partial_hash = ContentHasher.compute_partial_hash(content)
        preview = content[:200].strip() if len(content) > 200 else content.strip()

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR IGNORE INTO content_hashes
                (hash, partial_hash, video_id, source_url, title, content_preview)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (full_hash, partial_hash, video_id, source_url, title, preview))

            inserted = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return inserted

        except Exception as e:
            logger.error(f"Failed to register content hash: {e}")
            return False

    def get_duplicate_count(self) -> int:
        """Retorna el total de hashes registrados."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM content_hashes")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def clear_duplicates(self, older_than_days: int = 90) -> int:
        """
        Limpia hashes antiguos para mantenimiento.

        Args:
            older_than_days: Eliminar hashes más antiguos que N días

        Returns:
            Número de hashes eliminados
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM content_hashes
                WHERE created_at < datetime('now', ?)
            """, (f'-{older_than_days} days',))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Cleared {deleted} old content hashes")
            return deleted

        except Exception as e:
            logger.error(f"Failed to clear old hashes: {e}")
            return 0

    def find_similar_content(self, content: str, threshold: float = 0.8) -> List[dict]:
        """
        Encuentra contenido similar en la KB.

        Args:
            content: Contenido a comparar
            threshold: Umbral de similitud (0.0-1.0)

        Returns:
            Lista de contenidos similares
        """
        partial_hash = ContentHasher.compute_partial_hash(content)

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, hash, video_id, title, content_preview, source_url
                FROM content_hashes
                WHERE partial_hash = ?
            """, (partial_hash,))

            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'hash': row[1],
                    'video_id': row[2],
                    'title': row[3],
                    'preview': row[4],
                    'source': row[5],
                    'similarity': 0.85
                })

            return results

        except Exception as e:
            logger.error(f"Similar search failed: {e}")
            return []


def create_deduplicator(db_path: Optional[str] = None) -> ContentDeduplicator:
    """
    Factory function para crear el deduplicador.
    """
    return ContentDeduplicator(db_path=db_path)


def compute_content_hash(content: str) -> str:
    """
    Función de conveniencia para computar hash.
    """
    return ContentHasher.compute_hash(content)