"""
CC Schema Monitor - Módulo 20: Persistencia Atómica de Transcripción
====================================================================
Guarda .txt limpio inmediatamente tras extracción exitosa con
transacción SQLite, antes de cualquier análisis.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import time
import sqlite3
import logging
import threading
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class PersistedTranscription:
    id: int
    video_id: str
    source_url: str
    content: str
    word_count: int
    char_count: int
    language: str
    format: str
    content_hash: str
    created_at: str
    updated_at: str
    state: str


class AtomicPersistenceManager:
    """
    Persistencia Atómica de Transcripción
    Guarda texto limpio con transacción SQLite para integridad.
    """

    DB_VERSION = 1

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._get_default_db_path()
        self._lock = threading.Lock()
        self._init_db()
        self._current_transaction = None

    def _get_default_db_path(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "data", "transcriptions.db")

    def _init_db(self):
        """Inicializa la base de datos."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                char_count INTEGER,
                language TEXT DEFAULT 'unknown',
                format TEXT DEFAULT 'vtt',
                content_hash TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                state TEXT DEFAULT 'pending'
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_video_hash
            ON transcriptions(video_id, content_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_id
            ON transcriptions(video_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_hash
            ON transcriptions(content_hash)
        """)

        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS transcriptions_fts
            USING fts5(content, content=transcriptions, content_rowid=id)
        """)

        conn.commit()
        conn.close()

    @contextmanager
    def transaction(self):
        """
        Context manager para transacciones atómicas.

        Usage:
            with manager.transaction() as txn:
                manager.save(txn, ...)
        """
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("BEGIN IMMEDIATE")
        self._current_transaction = conn

        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed")

        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise

        finally:
            conn.close()
            self._current_transaction = None

    def save(self, content: str, video_id: str, source_url: str, **kwargs) -> Tuple[bool, str]:
        """
        Guarda transcripción con persistencia atómica.

        Args:
            content: Texto de la transcripción
            video_id: ID del video
            source_url: URL de origen
            **kwargs: Metadatos adicionales

        Returns:
            (success, message)
        """
        try:
            content_hash = self._compute_hash(content)
            word_count = len(content.split())
            char_count = len(content)
            language = kwargs.get('language', 'unknown')
            format = kwargs.get('format', 'vtt')

            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id FROM transcriptions
                WHERE content_hash = ?
            """, (content_hash,))

            existing = cursor.fetchone()
            if existing:
                conn.close()
                return True, f"Transcription already exists (id: {existing[0]})"

            cursor.execute("""
                INSERT INTO transcriptions
                (video_id, source_url, content, word_count, char_count,
                 language, format, content_hash, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (video_id, source_url, content, word_count, char_count,
                  language, format, content_hash))

            trans_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO transcriptions_fts (rowid, content)
                VALUES (?, ?)
            """, (trans_id, content))

            conn.commit()
            conn.close()

            logger.info(f"Transcription saved: {video_id} (id: {trans_id})")
            return True, f"Saved successfully (id: {trans_id})"

        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in str(e):
                return True, "Duplicate content - already saved"
            logger.error(f"Integrity error: {e}")
            return False, str(e)

        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False, str(e)

    def save_batch(self, transcriptions: List[Dict]) -> Dict[str, Any]:
        """
        Guarda múltiples transcripciones en lote.

        Args:
            transcriptions: Lista de diccionarios con datos

        Returns:
            Estadísticas del proceso
        """
        stats = {
            'total': len(transcriptions),
            'saved': 0,
            'duplicates': 0,
            'failed': 0,
            'errors': []
        }

        for trans in transcriptions:
            success, msg = self.save(
                content=trans.get('content', ''),
                video_id=trans.get('video_id', ''),
                source_url=trans.get('source_url', ''),
                language=trans.get('language', 'unknown'),
                format=trans.get('format', 'vtt')
            )

            if success:
                if 'already exists' in msg or 'Duplicate' in msg:
                    stats['duplicates'] += 1
                else:
                    stats['saved'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append(f"{trans.get('video_id')}: {msg}")

        return stats

    def get(self, video_id: str, content_hash: Optional[str] = None) -> Optional[PersistedTranscription]:
        """
        Obtiene transcripción por video_id.

        Args:
            video_id: ID del video
            content_hash: Hash del contenido (opcional)

        Returns:
            PersistedTranscription o None
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            if content_hash:
                cursor.execute("""
                    SELECT * FROM transcriptions
                    WHERE video_id = ? AND content_hash = ?
                """, (video_id, content_hash))
            else:
                cursor.execute("""
                    SELECT * FROM transcriptions
                    WHERE video_id = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (video_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return PersistedTranscription(
                    id=row[0],
                    video_id=row[1],
                    source_url=row[2],
                    content=row[3],
                    word_count=row[4],
                    char_count=row[5],
                    language=row[6],
                    format=row[7],
                    content_hash=row[8],
                    created_at=row[9],
                    updated_at=row[10],
                    state=row[11]
                )

        except Exception as e:
            logger.error(f"Get failed: {e}")

        return None

    def update_state(self, video_id: str, new_state: str) -> bool:
        """Actualiza estado de una transcripción."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE transcriptions
                SET state = ?, updated_at = datetime('now')
                WHERE video_id = ?
            """, (new_state, video_id))

            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return updated

        except Exception as e:
            logger.error(f"Update state failed: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Busca transcripciones usando FTS5.

        Args:
            query: Query de búsqueda
            limit: Límite de resultados

        Returns:
            Lista de resultados
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT t.* FROM transcriptions t
                JOIN transcriptions_fts fts ON t.id = fts.rowid
                WHERE transcriptions_fts MATCH ?
                LIMIT ?
            """, (query, limit))

            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'video_id': row[1],
                    'source_url': row[2],
                    'word_count': row[4],
                    'language': row[6],
                    'format': row[7],
                    'created_at': row[9],
                    'state': row[11]
                })

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de la base."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*), SUM(word_count) FROM transcriptions")
            total, total_words = cursor.fetchone()

            cursor.execute("SELECT COUNT(*), SUM(word_count) FROM transcriptions WHERE state = 'pending'")
            pending, pending_words = cursor.fetchone()

            cursor.execute("SELECT COUNT(DISTINCT language) FROM transcriptions WHERE language != 'unknown'")
            languages = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT video_id) FROM transcriptions")
            unique_videos = cursor.fetchone()[0]

            conn.close()

            return {
                'total_transcriptions': total or 0,
                'total_words': total_words or 0,
                'pending_count': pending or 0,
                'pending_words': pending_words or 0,
                'unique_videos': unique_videos or 0,
                'languages': languages or 0
            }

        except Exception as e:
            logger.error(f"Statistics query failed: {e}")
            return {}

    def _compute_hash(self, text: str) -> str:
        """Computa hash SHA-256 del contenido."""
        import hashlib
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def vacuum(self):
        """Optimiza la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            logger.info("Database vacuumed")
        except Exception as e:
            logger.error(f"Vacuum failed: {e}")


def create_persistence_manager(db_path: Optional[str] = None) -> AtomicPersistenceManager:
    """
    Factory function para crear el manager.
    """
    return AtomicPersistenceManager(db_path=db_path)


def quick_save(content: str, video_id: str, source_url: str = "") -> Tuple[bool, str]:
    """
    Función de conveniencia para guardar rápido.
    """
    manager = AtomicPersistenceManager()
    return manager.save(content, video_id, source_url)