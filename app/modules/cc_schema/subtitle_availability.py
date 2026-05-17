"""
Subtitle Availability Checker - Módulo 27 de URL Intelligence
============================================================
Verifica disponibilidad de subtítulos/closed captions.
Validar que existan subtítulos antes de encolar.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SubtitleAvailabilityStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    AUTO_ONLY = "auto_only"
    UNKNOWN = "unknown"


@dataclass
class SubtitleAvailabilityResult:
    status: SubtitleAvailabilityStatus
    has_subtitles: bool
    has_cc: bool
    languages: List[str]
    is_valid: bool
    error: Optional[str]


class SubtitleAvailabilityChecker:
    """
    Verificador de disponibilidad de subtítulos.
    Detecta CC y subtítulos en diferentes idiomas.
    """

    def __init__(self):
        pass

    def check(self, metadata: dict) -> SubtitleAvailabilityResult:
        """
        Verifica disponibilidad de subtítulos.

        Args:
            metadata: Metadatos del video

        Returns:
            SubtitleAvailabilityResult con disponibilidad
        """
        has_subtitles = metadata.get('subtitles') or metadata.get('has_subtitles') or False

        if not has_subtitles:
            return SubtitleAvailabilityResult(
                status=SubtitleAvailabilityStatus.UNAVAILABLE,
                has_subtitles=False,
                has_cc=False,
                languages=[],
                is_valid=False,
                error="Subtítulos no disponibles"
            )

        has_cc = metadata.get('closed_captions') or metadata.get('has_cc') or metadata.get('subtitles') == True

        languages = metadata.get('subtitle_languages') or metadata.get('caption_languages') or []

        if isinstance(languages, str):
            languages = [languages] if languages else []

        if not languages and has_subtitles:
            status = SubtitleAvailabilityStatus.AUTO_ONLY
        else:
            status = SubtitleAvailabilityStatus.AVAILABLE

        return SubtitleAvailabilityResult(
            status=status,
            has_subtitles=has_subtitles,
            has_cc=has_cc,
            languages=languages,
            is_valid=has_subtitles,
            error=None
        )

    def has_subtitles(self, metadata: dict) -> bool:
        """Verifica si tiene subtítulos."""
        result = self.check(metadata)
        return result.has_subtitles

    def has_cc(self, metadata: dict) -> bool:
        """Verifica si tiene closed captions."""
        result = self.check(metadata)
        return result.has_cc


def create_subtitle_availability_checker() -> SubtitleAvailabilityChecker:
    """Factory function."""
    return SubtitleAvailabilityChecker()