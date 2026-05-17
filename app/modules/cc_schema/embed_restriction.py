"""
Embed Restriction Detector - Módulo 20 de URL Intelligence
==========================================================
Detecta si el video permite incrustación externa.
Identificar videos con restricciones de embed.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EmbedStatus(Enum):
    EMBED_ALLOWED = "embed_allowed"
    EMBED_BLOCKED = "embed_blocked"
    UNKNOWN = "unknown"


@dataclass
class EmbedRestrictionResult:
    status: EmbedStatus
    is_embed_allowed: bool
    is_blocked: bool
    action_required: str
    error: Optional[str]


class EmbedRestrictionDetector:
    """
    Detector de restricciones de incrustación (embed).
    Identifica videos que no pueden ser embebidos.
    """

    def __init__(self):
        self._session = requests.Session()

    def detect(self, url: str) -> EmbedRestrictionResult:
        """
        Detecta restricciones de embed.

        Args:
            url: URL del video

        Returns:
            EmbedRestrictionResult con estado
        """
        try:
            embed_url = self._get_embed_url(url)
            if not embed_url:
                return EmbedRestrictionResult(
                    status=EmbedStatus.UNKNOWN,
                    is_embed_allowed=False,
                    is_blocked=False,
                    action_required="No se pudo determinar URL de embed",
                    error="Plataforma no soportada"
                )

            response = self._session.head(embed_url, timeout=10, allow_redirects=True)
            status = response.status_code

            if status == 200:
                return EmbedRestrictionResult(
                    status=EmbedStatus.EMBED_ALLOWED,
                    is_embed_allowed=True,
                    is_blocked=False,
                    action_required="Embed permitido - procesar",
                    error=None
                )

            if status == 403:
                return EmbedRestrictionResult(
                    status=EmbedStatus.EMBED_BLOCKED,
                    is_embed_allowed=False,
                    is_blocked=False,
                    action_required="Embed no permitido - intentar descarga directa",
                    error=None
                )

            return EmbedRestrictionResult(
                status=EmbedStatus.UNKNOWN,
                is_embed_allowed=False,
                is_blocked=False,
                action_required="Estado de embed desconocido",
                error=f"Status: {status}"
            )

        except Exception as e:
            return EmbedRestrictionResult(
                status=EmbedStatus.UNKNOWN,
                is_embed_allowed=False,
                is_blocked=False,
                action_required="Error al verificar",
                error=str(e)
            )

    def _get_embed_url(self, url: str) -> str:
        """Convierte URL normal a URL de embed."""
        if 'youtube.com/watch' in url:
            video_id = self._extract_video_id(url)
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return ""

    def _extract_video_id(self, url: str) -> str:
        """Extrae video ID de URL."""
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        return ""

    def is_embed_allowed(self, url: str) -> bool:
        """Verifica si embed está permitido."""
        result = self.detect(url)
        return result.is_embed_allowed


def create_embed_restriction_detector() -> EmbedRestrictionDetector:
    """Factory function."""
    return EmbedRestrictionDetector()