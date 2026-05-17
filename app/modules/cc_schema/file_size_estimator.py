"""
File Size Estimator - Módulo 22 de URL Intelligence
==================================================
Calcula tamaño estimado basado en duración y calidad.
Pre-verificar espacio en disco disponible.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FileSizeEstimate:
    estimated_bytes: int
    estimated_mb: float
    estimated_gb: float
    quality: str
    has_audio: bool


class FileSizeEstimator:
    """
    Estimador de tamaño de archivo de video.
    Basado en duración y calidad promedio.
    """

    QUALITY_BITRATES = {
        '144p': 250000,
        '240p': 400000,
        '360p': 750000,
        '480p': 1000000,
        '720p': 2500000,
        '720p60': 3500000,
        '1080p': 5000000,
        '1080p60': 8000000,
        '1440p': 16000000,
        '4k': 45000000,
    }

    AUDIO_BITRATE = 128000

    def __init__(self, default_quality: str = '720p'):
        self.default_quality = default_quality

    def estimate(
        self,
        duration_seconds: int,
        quality: Optional[str] = None,
        has_audio: bool = True
    ) -> FileSizeEstimate:
        """
        Estima tamaño de archivo.

        Args:
            duration_seconds: Duración en segundos
            quality: Calidad deseada
            has_audio: Si incluye audio

        Returns:
            FileSizeEstimate con tamaño estimado
        """
        quality = quality or self.default_quality

        video_bitrate = self.QUALITY_BITRATES.get(quality, 1000000)
        video_bytes = (video_bitrate // 8) * duration_seconds

        audio_bytes = 0
        if has_audio:
            audio_bytes = (self.AUDIO_BITRATE // 8) * duration_seconds

        total_bytes = video_bytes + audio_bytes

        return FileSizeEstimate(
            estimated_bytes=total_bytes,
            estimated_mb=total_bytes / (1024 * 1024),
            estimated_gb=total_bytes / (1024 * 1024 * 1024),
            quality=quality,
            has_audio=has_audio
        )

    def estimate_batch(self, items: list) -> list:
        """Estima tamaño para múltiples videos."""
        return [self.estimate(item['duration'], item.get('quality')) for item in items]


def create_file_size_estimator(
    default_quality: str = '720p'
) -> FileSizeEstimator:
    """Factory function."""
    return FileSizeEstimator(default_quality=default_quality)