"""
Age Restriction Checker - Módulo 17 de URL Intelligence
=======================================================
Verifica si el video tiene restricción de edad.
Alertar que se requiere cuenta verificada.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgeRestrictionStatus(Enum):
    NOT_RESTRICTED = "not_restricted"
    AGE_RESTRICTED = "age_restricted"
    UNKNOWN = "unknown"


@dataclass
class AgeRestrictionResult:
    status: AgeRestrictionStatus
    is_restricted: bool
    restriction_level: str
    is_blocked: bool
    action_required: str
    error: Optional[str]


class AgeRestrictionChecker:
    """
    Verificador de restricción de edad.
    Detecta videos con age-restriction en YouTube.
    """

    def __init__(self):
        self._session = requests.Session()

    def check(self, url: str) -> AgeRestrictionResult:
        """
        Verifica restricción de edad.

        Args:
            url: URL del video

        Returns:
            AgeRestrictionResult con estado
        """
        try:
            response = self._session.head(url, timeout=10, allow_redirects=True)
            headers = response.headers

            x_youtube = headers.get('X-YouTube-Error', '').lower()
            www_auth = headers.get('WWW-Authenticate', '').lower()

            if 'age' in x_youtube or 'age' in www_auth:
                return AgeRestrictionResult(
                    status=AgeRestrictionStatus.AGE_RESTRICTED,
                    is_restricted=True,
                    restriction_level="18+",
                    is_blocked=True,
                    action_required="Requiere cuenta verificada por edad",
                    error=None
                )

            if response.status_code == 403:
                if 'confirm' in www_auth or 'age' in www_auth:
                    return AgeRestrictionResult(
                        status=AgeRestrictionStatus.AGE_RESTRICTED,
                        is_restricted=True,
                        restriction_level="18+",
                        is_blocked=True,
                        action_required="Verificación de edad requerida",
                        error=None
                    )

            return AgeRestrictionResult(
                status=AgeRestrictionStatus.NOT_RESTRICTED,
                is_restricted=False,
                restriction_level="None",
                is_blocked=False,
                action_required="Sin restricción",
                error=None
            )

        except Exception as e:
            return AgeRestrictionResult(
                status=AgeRestrictionStatus.UNKNOWN,
                is_restricted=False,
                restriction_level="Unknown",
                is_blocked=False,
                action_required="Error al verificar",
                error=str(e)
            )

    def is_age_restricted(self, url: str) -> bool:
        """Verifica si video tiene restricción de edad."""
        result = self.check(url)
        return result.is_restricted


def create_age_restriction_checker() -> AgeRestrictionChecker:
    """Factory function."""
    return AgeRestrictionChecker()