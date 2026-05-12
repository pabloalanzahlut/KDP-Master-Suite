"""
CC Schema Monitor - Módulo 11: Cache de Metadatos CC
======================================================
Almacena respuesta de disponibilidad de CC por video_id por 24h
para evitar re-fetch innecesario en colas masivas.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import json
import time
import hashlib
import logging
import sqlite3
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CCMetadataCache:
    video_id: str
    available: bool
    formats: List[str]
    language: Optional[str]
    auto_generated: bool
    subtitle_count: int
    confidence_score: float
    cached_at: float
    expires_at: float
    metadata_json: Optional[str] = None


class CCMetadataCacheManager:
    """
    Cache de Metadatos de Subtítulos/CC
    Almacena respuestas por 24h para evitar re-fetches innecesarios.
    """

    DEFAULT_TTL_SECONDS = 86400
    CLEANUP_INTERVAL_HOURS = 6
    MAX_CACHE_SIZE_MB = 50

    def __init__(self, db_path: Optional[str] = None, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.db_path = db_path or self._get_default_db_path()
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._memory_cache: Dict[str, CCMetadataCache] = {}
        self._init_cache_db()
        self._last_cleanup = time.time()

    def _get_default_db_path(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "data", "cc_metadata_cache.db")

    def _init_cache_db(self):
        """Inicializa la base de datos del cache."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cc_metadata_cache (
                video_id TEXT PRIMARY KEY,
                available INTEGER,
                formats TEXT,
                language TEXT,
                auto_generated INTEGER,
                subtitle_count INTEGER,
                confidence_score REAL,
                cached_at REAL,
                expires_at REAL,
                metadata_json TEXT,
                hit_count INTEGER DEFAULT 0,
                last_hit_at REAL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires ON cc_metadata_cache(expires_at)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_stats (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()

    def get(self, video_id: str) -> Optional[CCMetadataCache]:
        """
        Obtiene metadatos cacheados para un video.

        Args:
            video_id: ID del video

        Returns:
            CCMetadataCache si existe y no ha expirado, None si no
        """
        current_time = time.time()

        if video_id in self._memory_cache:
            cached = self._memory_cache[video_id]
            if cached.expires_at > current_time:
                self._update_hit_count(video_id)
                return cached
            else:
                del self._memory_cache[video_id]

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM cc_metadata_cache
                WHERE video_id = ? AND expires_at > ?
            """, (video_id, current_time))

            row = cursor.fetchone()
            conn.close()

            if row:
                cache_entry = CCMetadataCache(
                    video_id=row[0],
                    available=bool(row[1]),
                    formats=row[2].split(',') if row[2] else [],
                    language=row[3],
                    auto_generated=bool(row[4]),
                    subtitle_count=row[5],
                    confidence_score=row[6],
                    cached_at=row[7],
                    expires_at=row[8],
                    metadata_json=row[9]
                )

                self._memory_cache[video_id] = cache_entry
                self._update_hit_count(video_id)
                return cache_entry

        except Exception as e:
            logger.error(f"Cache get failed for {video_id}: {e}")

        return None

    def set(
        self,
        video_id: str,
        available: bool,
        formats: List[str],
        language: Optional[str] = None,
        auto_generated: bool = False,
        subtitle_count: int = 0,
        confidence_score: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Almacena metadatos en cache.

        Args:
            video_id: ID del video
            available: Si hay CC disponible
            formats: Formatos disponibles
            language: Idioma de subtítulos
            auto_generated: Si son auto-generados
            subtitle_count: Cantidad de subtítulos
            confidence_score: Score de confianza
            metadata: Metadatos adicionales

        Returns:
            True si se almacenó correctamente
        """
        self._maybe_cleanup()

        current_time = time.time()
        expires_at = current_time + self.ttl_seconds

        cache_entry = CCMetadataCache(
            video_id=video_id,
            available=available,
            formats=formats,
            language=language,
            auto_generated=auto_generated,
            subtitle_count=subtitle_count,
            confidence_score=confidence_score,
            cached_at=current_time,
            expires_at=expires_at,
            metadata_json=json.dumps(metadata) if metadata else None
        )

        self._memory_cache[video_id] = cache_entry

        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO cc_metadata_cache
                (video_id, available, formats, language, auto_generated,
                 subtitle_count, confidence_score, cached_at, expires_at,
                 metadata_json, hit_count, last_hit_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    available=excluded.available,
                    formats=excluded.formats,
                    language=excluded.language,
                    auto_generated=excluded.auto_generated,
                    subtitle_count=excluded.subtitle_count,
                    confidence_score=excluded.confidence_score,
                    cached_at=excluded.cached_at,
                    expires_at=excluded.expires_at,
                    metadata_json=excluded.metadata_json
            """, (
                video_id, 1 if available else 0, ','.join(formats), language,
                1 if auto_generated else 0, subtitle_count, confidence_score,
                current_time, expires_at, cache_entry.metadata_json, current_time
            ))

            conn.commit()
            conn.close()

            logger.debug(f"Cache set for {video_id}")
            return True

        except Exception as e:
            logger.error(f"Cache set failed for {video_id}: {e}")
            return False

    def invalidate(self, video_id: str):
        """
        Invalida cache para un video específico.

        Args:
            video_id: ID del video
        """
        if video_id in self._memory_cache:
            del self._memory_cache[video_id]

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cc_metadata_cache WHERE video_id = ?", (video_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cache invalidation failed for {video_id}: {e}")

    def invalidate_pattern(self, pattern: str):
        """
        Invalida todos los videos que coincidan con un patrón.

        Args:
            pattern: Patrón de video_id (ej: 'channel_' al inicio)
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM cc_metadata_cache WHERE video_id LIKE ?",
                (f"{pattern}%",)
            )
            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            keys_to_remove = [k for k in self._memory_cache if k.startswith(pattern)]
            for k in keys_to_remove:
                del self._memory_cache[k]

            logger.info(f"Invalidated {deleted} cache entries matching '{pattern}'")

        except Exception as e:
            logger.error(f"Pattern invalidation failed: {e}")

    def _update_hit_count(self, video_id: str):
        """Actualiza contador de hits."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cc_metadata_cache
                SET hit_count = hit_count + 1, last_hit_at = ?
                WHERE video_id = ?
            """, (time.time(), video_id))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _maybe_cleanup(self):
        """Ejecuta cleanup si es necesario."""
        current_time = time.time()
        interval_seconds = self.CLEANUP_INTERVAL_HOURS * 3600

        if current_time - self._last_cleanup < interval_seconds:
            return

        self._last_cleanup = current_time
        self._cleanup_expired()

    def _cleanup_expired(self):
        """Limpia entradas expiradas."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()

            current_time = time.time()
            cursor.execute("DELETE FROM cc_metadata_cache WHERE expires_at < ?", (current_time,))
            deleted = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(f"Cache cleanup: removed {deleted} expired entries")

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM cc_metadata_cache")
            total_entries = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cc_metadata_cache WHERE expires_at > ?", (time.time(),))
            active_entries = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(hit_count) FROM cc_metadata_cache")
            total_hits = cursor.fetchone()[0] or 0

            conn.close()

            cache_size = 0
            try:
                cache_size = os.path.getsize(self.db_path) / (1024 * 1024)
            except Exception:
                pass

            return {
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': total_entries - active_entries,
                'total_hits': total_hits,
                'cache_size_mb': cache_size,
                'ttl_seconds': self.ttl_seconds,
                'memory_cache_size': len(self._memory_cache)
            }

        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            return {}

    def clear_all(self):
        """Limpia todo el cache."""
        self._memory_cache.clear()

        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cc_metadata_cache")
            conn.commit()
            conn.close()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Clear all failed: {e}")

    def prefetch(self, video_ids: List[str]) -> Dict[str, CCMetadataCache]:
        """
        Precarga cache para múltiples videos.

        Args:
            video_ids: Lista de IDs de video

        Returns:
            Dict con videos encontrados en cache
        """
        results = {}
        missing = []

        for vid in video_ids:
            cached = self.get(vid)
            if cached:
                results[vid] = cached
            else:
                missing.append(vid)

        return results

    def get_cache_hit_ratio(self) -> float:
        """Calcula ratio de cache hits."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("SELECT SUM(hit_count), COUNT(*) FROM cc_metadata_cache")
            hits, total = cursor.fetchone()
            conn.close()

            if total and total > 0:
                return hits / total if hits else 0.0
            return 0.0

        except Exception:
            return 0.0


def create_cache_manager(db_path: Optional[str] = None, ttl: int = 86400) -> CCMetadataCacheManager:
    """
    Factory function para crear el cache manager.
    """
    return CCMetadataCacheManager(db_path=db_path, ttl_seconds=ttl)


def quick_cache_check(video_id: str) -> Optional[CCMetadataCache]:
    """
    Función de conveniencia para check rápido de cache.
    """
    cache = CCMetadataCacheManager()
    return cache.get(video_id)