"""
Video ID Extractor - Módulo 2 de URL Intelligence
===================================================
Parsea y extrae el identificador único del video desde diferentes formatos de URL.
Normaliza "youtu.be/abc123" y "youtube.com/watch?v=abc123" al mismo ID.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    UNKNOWN = "unknown"


@dataclass
class VideoIDResult:
    platform: Platform
    video_id: Optional[str]
    is_valid: bool
    original_url: str
    normalized_url: Optional[str]
    error: Optional[str]


class VideoIDExtractor:
    """
    Extrae IDs de video de diferentes plataformas y formatos de URL.
    Soporta YouTube (varios formatos) y Vimeo.
    """

    YOUTUBE_PATTERNS = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]+)',
        r'youtube\.com/channel/([a-zA-Z0-9_-]{24})',
        r'youtube\.com/user/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_-]+)',
        r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]+)',
    ]

    VIMEO_PATTERNS = [
        r'(?:vimeo\.com/|player\.vimeo\.com/video/)(\d+)',
        r'vimeo\.com/(\d+)',
    ]

    def __init__(self):
        self.youtube_regex = [re.compile(p, re.IGNORECASE) for p in self.YOUTUBE_PATTERNS]
        self.vimeo_regex = [re.compile(p, re.IGNORECASE) for p in self.VIMEO_PATTERNS]

    def extract(self, url: str) -> VideoIDResult:
        """
        Extrae ID de video de URL.

        Args:
            url: URL del video

        Returns:
            VideoIDResult con plataforma, ID y estado
        """
        if not url or not isinstance(url, str):
            return VideoIDResult(
                platform=Platform.UNKNOWN,
                video_id=None,
                is_valid=False,
                original_url=url or "",
                normalized_url=None,
                error="URL vacía o inválida"
            )

        url = url.strip()

        youtube_match = self._extract_youtube(url)
        if youtube_match:
            normalized = self._normalize_youtube_url(youtube_match)
            return VideoIDResult(
                platform=Platform.YOUTUBE,
                video_id=youtube_match,
                is_valid=True,
                original_url=url,
                normalized_url=normalized,
                error=None
            )

        vimeo_match = self._extract_vimeo(url)
        if vimeo_match:
            normalized = f"https://vimeo.com/{vimeo_match}"
            return VideoIDResult(
                platform=Platform.VIMEO,
                video_id=vimeo_match,
                is_valid=True,
                original_url=url,
                normalized_url=normalized,
                error=None
            )

        return VideoIDResult(
            platform=Platform.UNKNOWN,
            video_id=None,
            is_valid=False,
            original_url=url,
            normalized_url=None,
            error="Plataforma no reconocida o URL no válida"
        )

    def _extract_youtube(self, url: str) -> Optional[str]:
        """Extrae ID de video de YouTube."""
        for regex in self.youtube_regex:
            match = regex.search(url)
            if match:
                video_id = match.group(1)
                if 1 <= len(video_id) <= 50:
                    return video_id
        return None

    def _extract_vimeo(self, url: str) -> Optional[str]:
        """Extrae ID de Vimeo."""
        for regex in self.vimeo_regex:
            match = regex.search(url)
            if match:
                return match.group(1)
        return None

    def _normalize_youtube_url(self, video_id: str) -> str:
        """Normaliza URL de YouTube a formato estándar."""
        return f"https://www.youtube.com/watch?v={video_id}"

    def extract_batch(self, urls: List[str]) -> List[VideoIDResult]:
        """Extrae IDs de múltiples URLs."""
        return [self.extract(url) for url in urls]

    def get_channel_id(self, url: str) -> Optional[str]:
        """Extrae ID de canal de URL de YouTube."""
        channel_pattern = r'youtube\.com/channel/([a-zA-Z0-9_-]{24})'
        match = re.search(channel_pattern, url, re.IGNORECASE)
        return match.group(1) if match else None

    def get_playlist_id(self, url: str) -> Optional[str]:
        """Extrae ID de playlist de URL de YouTube."""
        playlist_pattern = r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)'
        match = re.search(playlist_pattern, url, re.IGNORECASE)
        return match.group(1) if match else None

    def is_video_url(self, url: str) -> bool:
        """Verifica si URL es de video individual."""
        result = self.extract(url)
        return result.is_valid and result.platform in [Platform.YOUTUBE, Platform.VIMEO]


def create_video_id_extractor() -> VideoIDExtractor:
    """Factory function."""
    return VideoIDExtractor()