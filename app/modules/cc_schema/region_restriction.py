"""
Region Restriction Validator - Módulo 18 de URL Intelligence
============================================================
Detecta bloqueos geográficos del contenido.
Identificar videos no disponibles en tu región.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class RegionRestrictionStatus(Enum):
    NOT_RESTRICTED = "not_restricted"
    REGION_RESTRICTED = "region_restricted"
    UNKNOWN = "unknown"


@dataclass
class RegionRestrictionResult:
    status: RegionRestrictionStatus
    is_restricted: bool
    allowed_regions: list
    blocked_regions: list
    is_blocked: bool
    action_required: str
    error: Optional[str]


class RegionRestrictionValidator:
    """
    Validador de restricciones geográficas.
    Detecta bloqueos por región en videos.
    """

    def __init__(self):
        self._session = requests.Session()

    def validate(self, url: str, user_region: Optional[str] = None) -> RegionRestrictionResult:
        """
        Valida restricciones de región.

        Args:
            url: URL del video
            user_region: Región del usuario (opcional)

        Returns:
            RegionRestrictionResult con estado
        """
        try:
            response = self._session.head(url, timeout=10, allow_redirects=True)
            headers = response.headers

            x_youtube_error = headers.get('X-YouTube-Error', '').lower()
            www_auth = headers.get('WWW-Authenticate', '').lower()

            if 'geo' in x_youtube_error or 'geo' in www_auth:
                return RegionRestrictionResult(
                    status=RegionRestrictionStatus.REGION_RESTRICTED,
                    is_restricted=True,
                    allowed_regions=[],
                    blocked_regions=["Unknown"],
                    is_blocked=True,
                    action_required="Video no disponible en tu región",
                    error=None
                )

            if response.status_code == 403:
                content_type = headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    return RegionRestrictionResult(
                        status=RegionRestrictionStatus.REGION_RESTRICTED,
                        is_restricted=True,
                        allowed_regions=[],
                        blocked_regions=["Tu región"],
                        is_blocked=True,
                        action_required="Verificar disponibilidad por región",
                        error=None
                    )

            return RegionRestrictionResult(
                status=RegionRestrictionStatus.NOT_RESTRICTED,
                is_restricted=False,
                allowed_regions=["Global"],
                blocked_regions=[],
                is_blocked=False,
                action_required="Sin restricciones",
                error=None
            )

        except Exception as e:
            return RegionRestrictionResult(
                status=RegionRestrictionStatus.UNKNOWN,
                is_restricted=False,
                allowed_regions=[],
                blocked_regions=[],
                is_blocked=False,
                action_required="Error al verificar",
                error=str(e)
            )

    def is_region_blocked(self, url: str) -> bool:
        """Verifica si video está bloqueado por región."""
        result = self.validate(url)
        return result.is_restricted


def create_region_restriction_validator() -> RegionRestrictionValidator:
    """Factory function."""
    return RegionRestrictionValidator()