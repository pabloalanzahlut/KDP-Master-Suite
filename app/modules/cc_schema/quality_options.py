"""
Quality Options Detector - Módulo 30 de URL Intelligence
========================================================
Detecta calidades disponibles (360p, 720p, 1080p, 4K).
Validar que exista calidad mínima requerida.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


QUALITY_ORDER = ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '4k', '2160p']


@dataclass
class QualityOptionsResult:
    available_qualities: List[str]
    highest_quality: str
    has_minimum_required: bool
    is_valid: bool
    error: Optional[str]


class QualityOptionsDetector:
    """
    Detector de opciones de calidad disponibles.
    Verifica calidad mínima requerida.
    """

    DEFAULT_MIN_QUALITY = '480p'

    def __init__(self, min_quality: str = DEFAULT_MIN_QUALITY):
        self.min_quality = min_quality

    def detect(self, metadata: dict) -> QualityOptionsResult:
        """
        Detecta calidades disponibles.

        Args:
            metadata: Metadatos del video

        Returns:
            QualityOptionsResult con calidades
        """
        qualities = metadata.get('qualities') or metadata.get('available_qualities') or []

        if isinstance(qualities, str):
            qualities = [qualities]

        if not qualities:
            return QualityOptionsResult(
                available_qualities=[],
                highest_quality='',
                has_minimum_required=False,
                is_valid=False,
                error="Calidades no disponibles"
            )

        sorted_qualities = sorted(qualities, key=lambda q: QUALITY_ORDER.index(q) if q in QUALITY_ORDER else 999)
        highest = sorted_qualities[-1] if sorted_qualities else ''

        min_idx = QUALITY_ORDER.index(self.min_quality) if self.min_quality in QUALITY_ORDER else 2
        has_minimum = any(q in QUALITY_ORDER[:min_idx+1] for q in qualities)

        return QualityOptionsResult(
            available_qualities=qualities,
            highest_quality=highest,
            has_minimum_required=has_minimum,
            is_valid=True,
            error=None
        )

    def has_quality(self, metadata: dict, quality: str) -> bool:
        """Verifica si tiene una calidad específica."""
        result = self.detect(metadata)
        return quality in result.available_qualities


def create_quality_options_detector(
    min_quality: str = '480p'
) -> QualityOptionsDetector:
    """Factory function."""
    return QualityOptionsDetector(min_quality=min_quality)