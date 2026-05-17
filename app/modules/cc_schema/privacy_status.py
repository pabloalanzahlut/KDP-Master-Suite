"""
Privacy Status Checker - Módulo 19 de URL Intelligence
======================================================
Verifica si video es público, no listado o privado.
Rechazar videos privados automáticamente.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PrivacyStatus(Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"
    UNKNOWN = "unknown"


@dataclass
class PrivacyResult:
    status: PrivacyStatus
    is_public: bool
    is_blocked: bool
    action_required: str
    error: Optional[str]


class PrivacyStatusChecker:
    """
    Verificador de estado de privacidad de video.
    Diferencia entre público, no-listado y privado.
    """

    def __init__(self):
        self._session = requests.Session()

    def check(self, url: str) -> PrivacyResult:
        """
        Verifica estado de privacidad.

        Args:
            url: URL del video

        Returns:
            PrivacyResult con estado
        """
        try:
            response = self._session.head(url, timeout=10, allow_redirects=False)
            status = response.status_code

            if status == 200:
                return PrivacyResult(
                    status=PrivacyStatus.PUBLIC,
                    is_public=True,
                    is_blocked=False,
                    action_required="Video público - procesar",
                    error=None
                )

            if status == 404:
                return PrivacyResult(
                    status=PrivacyStatus.PRIVATE,
                    is_public=False,
                    is_blocked=True,
                    action_required="Video no encontrado - puede ser privado",
                    error=None
                )

            if status == 301 or status == 302:
                location = response.headers.get('Location', '').lower()
                if 'login' in location or 'unavailable' in location:
                    return PrivacyResult(
                        status=PrivacyStatus.PRIVATE,
                        is_public=False,
                        is_blocked=True,
                        action_required="Video privado o no disponible",
                        error=None
                    )

            return PrivacyResult(
                status=PrivacyStatus.UNLISTED,
                is_public=False,
                is_blocked=False,
                action_required="Video no-listado - procesar",
                error=None
            )

        except Exception as e:
            return PrivacyResult(
                status=PrivacyStatus.UNKNOWN,
                is_public=False,
                is_blocked=False,
                action_required="Error al verificar",
                error=str(e)
            )

    def is_public(self, url: str) -> bool:
        """Verifica si video es público."""
        result = self.check(url)
        return result.is_public

    def is_private(self, url: str) -> bool:
        """Verifica si video es privado."""
        result = self.check(url)
        return result.status == PrivacyStatus.PRIVATE


def create_privacy_status_checker() -> PrivacyStatusChecker:
    """Factory function."""
    return PrivacyStatusChecker()