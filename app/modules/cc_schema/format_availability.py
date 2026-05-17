"""
Format Availability Checker - Módulo 29 de URL Intelligence
==========================================================
Verifica formatos disponibles (mp4, webm, etc.).
Asegurar que exista formato compatible.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FormatType(Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"
    FLV = "flv"
    UNKNOWN = "unknown"


@dataclass
class FormatAvailabilityResult:
    available_formats: List[str]
    has_compatible_format: bool
    is_valid: bool
    error: Optional[str]


class FormatAvailabilityChecker:
    """
    Verificador de formatos disponibles.
    Detecta si existe formato compatible.
    """

    COMPATIBLE_FORMATS = ['mp4', 'webm']

    def __init__(self, preferred_formats: Optional[List[str]] = None):
        self.preferred_formats = preferred_formats or self.COMPATIBLE_FORMATS

    def check(self, metadata: dict) -> FormatAvailabilityResult:
        """
        Verifica formatos disponibles.

        Args:
            metadata: Metadatos del video

        Returns:
            FormatAvailabilityResult con formatos
        """
        formats = metadata.get('formats') or metadata.get('available_formats') or []

        if isinstance(formats, str):
            formats = [formats]

        if not formats:
            return FormatAvailabilityResult(
                available_formats=[],
                has_compatible_format=False,
                is_valid=False,
                error="Formatos no disponibles"
            )

        has_compatible = any(
            fmt.lower() in self.preferred_formats
            for fmt in formats
        )

        return FormatAvailabilityResult(
            available_formats=formats,
            has_compatible_format=has_compatible,
            is_valid=True,
            error=None
        )

    def supports_format(self, metadata: dict, format: str) -> bool:
        """Verifica si soporta un formato."""
        result = self.check(metadata)
        return format.lower() in result.available_formats


def create_format_availability_checker() -> FormatAvailabilityChecker:
    """Factory function."""
    return FormatAvailabilityChecker()