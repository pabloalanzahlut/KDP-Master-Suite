"""
Video Duration Parser - Módulo 21 de URL Intelligence
=====================================================
Extrae duración del video desde metadatos.
Validar que duración sea >0 y <límite configurado.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import re
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DurationResult:
    duration_seconds: Optional[int]
    duration_formatted: Optional[str]
    is_valid: bool
    error: Optional[str]


class VideoDurationParser:
    """
    Parser de duración de video de YouTube.
    Extrae duración desde various formatos.
    """

    DURATION_PATTERNS = [
        r'(\d+):(\d+)',
        r'(\d+):(\d+):(\d+)',
        r'PT(\d+)M(\d+)S',
        r'PT(\d+)H(\d+)M(\d+)S',
    ]

    def __init__(self, min_duration: int = 30, max_duration: int = 14400):
        self.min_duration = min_duration
        self.max_duration = max_duration

    def parse(self, metadata: dict) -> DurationResult:
        """
        Parsea duración desde metadatos.

        Args:
            metadata: Diccionario con metadatos del video

        Returns:
            DurationResult con duración parsed
        """
        duration = metadata.get('duration') or metadata.get('length')

        if not duration:
            return DurationResult(
                duration_seconds=None,
                duration_formatted=None,
                is_valid=False,
                error="Duración no encontrada en metadatos"
            )

        if isinstance(duration, int):
            seconds = duration
        elif isinstance(duration, str):
            seconds = self._parse_duration_string(duration)
        else:
            return DurationResult(
                duration_seconds=None,
                duration_formatted=None,
                is_valid=False,
                error=f"Tipo de duración desconocido: {type(duration)}"
            )

        if seconds is None:
            return DurationResult(
                duration_seconds=None,
                duration_formatted=None,
                is_valid=False,
                error="No se pudo parsear duración"
            )

        formatted = self._format_duration(seconds)
        is_valid = self.min_duration <= seconds <= self.max_duration

        return DurationResult(
            duration_seconds=seconds,
            duration_formatted=formatted,
            is_valid=is_valid,
            error=None if is_valid else f"Duración fuera de rango: {seconds}s"
        )

    def _parse_duration_string(self, duration: str) -> Optional[int]:
        """Parsea string de duración a segundos."""
        if ':' in duration:
            parts = duration.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return None

    def _format_duration(self, seconds: int) -> str:
        """Formatea segundos a HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


def create_video_duration_parser(
    min_duration: int = 30,
    max_duration: int = 14400
) -> VideoDurationParser:
    """Factory function."""
    return VideoDurationParser(
        min_duration=min_duration,
        max_duration=max_duration
    )