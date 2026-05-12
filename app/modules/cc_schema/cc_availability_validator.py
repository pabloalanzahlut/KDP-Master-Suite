"""
CC Schema Monitor con Auto-Adaptación de Parser
================================================
Módulo 1: Validador de Disponibilidad de Subtítulos/CC
Detecta cambios en la estructura de subtítulos de YouTube y adapta el parser automáticamente.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import time
import hashlib
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class CCFormat(Enum):
    VTT = "vtt"
    SRT = "srt"
    JSON = "json"
    TXT = "txt"
    UNKNOWN = "unknown"


@dataclass
class CCCheckResult:
    available: bool
    formats: List[CCFormat]
    language: Optional[str]
    auto_generated: bool
    duration_seconds: Optional[int]
    subtitle_count: Optional[int]
    confidence_score: float
    error_message: Optional[str] = None
    schema_version: Optional[str] = None


@dataclass
class CCSchemaInfo:
    format_type: str
    version: str
    has_timestamps: bool
    has_speaker_tags: bool
    has_style_tags: bool
    encoding: str


class CCAvailabilityValidator:
    """
    Valida disponibilidad de subtítulos/CC antes de iniciar fetch.
    Evita intentos fallidos en videos sin CC.
    """

    CACHE_TTL_HOURS = 24
    MIN_WORD_DENSITY = 30

    def __init__(self, db_path: Optional[str] = None, cache_enabled: bool = True):
        self.db_path = db_path or self._get_default_db_path()
        self.cache_enabled = cache_enabled
        self._cache = {}
        self._init_cache_db()

    def _get_default_db_path(self) -> str:
        from app.core.config import Config
        try:
            config = Config()
            return config.get("db.path", "knowledge_base.db")
        except Exception:
            return "knowledge_base.db"

    def _init_cache_db(self):
        if not self.cache_enabled or not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cc_cache (
                    video_id TEXT PRIMARY KEY,
                    available INTEGER,
                    formats TEXT,
                    language TEXT,
                    auto_generated INTEGER,
                    duration_seconds INTEGER,
                    subtitle_count INTEGER,
                    confidence_score REAL,
                    checked_at TEXT
                )
            """)
            conn.close()
        except Exception as e:
            logger.warning(f"Cache DB init failed: {e}")
            self.cache_enabled = False

    def check_availability(
        self,
        url: str,
        video_id: str,
        format_priority: List[CCFormat] = None
    ) -> CCCheckResult:
        """
        Verifica disponibilidad de CC/subtítulos para un video.

        Args:
            url: URL del video de YouTube
            video_id: ID del video
            format_priority: Prioridad de formatos a buscar

        Returns:
            CCCheckResult con estado de disponibilidad
        """
        if format_priority is None:
            format_priority = [CCFormat.VTT, CCFormat.SRT, CCFormat.JSON, CCFormat.TXT]

        cached = self._get_from_cache(video_id)
        if cached:
            logger.debug(f"CC cache hit for {video_id}")
            return cached

        try:
            result = self._probe_cc_availability(url, video_id, format_priority)
            self._store_in_cache(video_id, result)
            return result
        except Exception as e:
            logger.error(f"CC availability check failed for {video_id}: {e}")
            return CCCheckResult(
                available=False,
                formats=[],
                language=None,
                auto_generated=False,
                duration_seconds=None,
                subtitle_count=None,
                confidence_score=0.0,
                error_message=str(e)
            )

    def _probe_cc_availability(
        self,
        url: str,
        video_id: str,
        format_priority: List[CCFormat]
    ) -> CCCheckResult:
        """
        Realiza el probe real para verificar disponibilidad.
        Usa yt-dlp para extraer información de subtítulos.
        """
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                return CCCheckResult(
                    available=False,
                    formats=[],
                    language=None,
                    auto_generated=False,
                    duration_seconds=None,
                    subtitle_count=None,
                    confidence_score=0.0,
                    error_message="No info extracted"
                )

            duration = info.get('duration')
            subtitles = info.get('subtitles') or {}
            automatic_captions = info.get('automatic_captions') or {}

            available_formats = []
            language = None
            auto_generated = False
            subtitle_count = 0
            total_confidence = 0.0

            all_subs = {**subtitles}
            if automatic_captions:
                for lang in automatic_captions:
                    if lang not in all_subs:
                        all_subs[lang] = automatic_captions[lang]

            if all_subs:
                for fmt in format_priority:
                    fmt_name = fmt.value
                    if fmt_name in all_subs:
                        available_formats.append(fmt)

                primary_lang = list(all_subs.keys())[0]
                language = primary_lang

                for lang, subs in all_subs.items():
                    if isinstance(subs, list) and subs:
                        subtitle_count += len(subs)

                        is_auto = lang in automatic_captions
                        if is_auto:
                            auto_generated = True

                        confidence = self._calculate_confidence(subs, is_auto)
                        total_confidence += confidence

                avg_confidence = total_confidence / len(all_subs) if all_subs else 0.0

                schema_version = self._detect_schema_version(all_subs)

                return CCCheckResult(
                    available=True,
                    formats=available_formats,
                    language=language,
                    auto_generated=auto_generated,
                    duration_seconds=duration,
                    subtitle_count=subtitle_count,
                    confidence_score=avg_confidence,
                    schema_version=schema_version
                )
            else:
                return CCCheckResult(
                    available=False,
                    formats=[],
                    language=None,
                    auto_generated=False,
                    duration_seconds=duration,
                    subtitle_count=0,
                    confidence_score=0.0,
                    error_message="No subtitles available"
                )

        except Exception as e:
            logger.error(f"Probe failed: {e}")
            return CCCheckResult(
                available=False,
                formats=[],
                language=None,
                auto_generated=False,
                duration_seconds=None,
                subtitle_count=None,
                confidence_score=0.0,
                error_message=str(e)
            )

    def _calculate_confidence(self, subtitle_entries: List[dict], is_auto: bool) -> float:
        """
        Calcula confidence score basado en calidad de subtítulos.
        """
        if not subtitle_entries:
            return 0.0

        base_confidence = 0.7 if is_auto else 1.0

        timestamps_count = 0
        for entry in subtitle_entries[:10]:
            if 'start' in entry and 'duration' in entry:
                timestamps_count += 1

        timestamp_ratio = timestamps_count / min(len(subtitle_entries), 10)

        estimated_words = sum(
            len(entry.get('text', '').split()) for entry in subtitle_entries[:5]
        )
        has_content = estimated_words > 10

        score = (base_confidence * 0.5) + (timestamp_ratio * 0.3) + (0.2 if has_content else 0)
        return min(score, 1.0)

    def _detect_schema_version(self, subtitles: dict) -> Optional[str]:
        """
        Detecta la versión del schema de subtítulos.
        Útil para auto-adaptación del parser.
        """
        if not subtitles:
            return None

        sample = None
        for lang_subs in subtitles.values():
            if isinstance(lang_subs, list) and lang_subs:
                sample = lang_subs[0]
                break

        if not sample:
            return "unknown_v1"

        has_offsets = 'offset' in sample
        has_end = 'duration' in sample or 'end' in sample
        has_settings = 'settings' in sample

        if has_offsets and has_end and has_settings:
            return "vtt_enhanced"
        elif has_end:
            return "vtt_standard"
        else:
            return "srt_legacy"

    def _get_from_cache(self, video_id: str) -> Optional[CCCheckResult]:
        if not self.cache_enabled:
            return None

        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cc_cache WHERE video_id = ? AND datetime(checked_at) > datetime('now', '-1 hour')",
                (video_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return CCCheckResult(
                    available=bool(row[1]),
                    formats=[CCFormat(f) for f in row[2].split(',') if f],
                    language=row[3],
                    auto_generated=bool(row[4]),
                    duration_seconds=row[5],
                    subtitle_count=row[6],
                    confidence_score=row[7]
                )
        except Exception:
            pass
        return None

    def _store_in_cache(self, video_id: str, result: CCCheckResult):
        if not self.cache_enabled:
            return

        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cc_cache
                (video_id, available, formats, language, auto_generated,
                 duration_seconds, subtitle_count, confidence_score, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                video_id,
                1 if result.available else 0,
                ','.join(f.value for f in result.formats),
                result.language,
                1 if result.auto_generated else 0,
                result.duration_seconds,
                result.subtitle_count,
                result.confidence_score
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Cache store failed: {e}")

    def validate_quality_threshold(self, result: CCCheckResult, min_confidence: float = 0.6) -> bool:
        """
        Valida si el resultado cumple el umbral de calidad.

        Args:
            result: Resultado del check de disponibilidad
            min_confidence: Score mínimo de confianza (0.0-1.0)

        Returns:
            True si pasa el umbral
        """
        if not result.available:
            return False

        if result.auto_generated and result.confidence_score < min_confidence:
            logger.info(f"Auto-generated CC below threshold: {result.confidence_score}")
            return False

        if result.subtitle_count and result.subtitle_count < 5:
            return False

        return True

    def get_preferred_format(self, result: CCCheckResult) -> Optional[CCFormat]:
        """
        Retorna el mejor formato disponible según prioridad.
        """
        if not result.formats:
            return None

        priority_order = [CCFormat.VTT, CCFormat.SRT, CCFormat.JSON, CCFormat.TXT]
        for fmt in priority_order:
            if fmt in result.formats:
                return fmt

        return result.formats[0] if result.formats else None


def create_validator(db_path: Optional[str] = None) -> CCAvailabilityValidator:
    """
    Factory function para crear el validador.
    """
    return CCAvailabilityValidator(db_path=db_path)