"""
Login Requirement Detector - Módulo 16 de URL Intelligence
========================================================
Detecta si la URL requiere login para acceder.
Identificar videos privados o solo para miembros del canal.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LoginStatus(Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    MEMBERS_ONLY = "members_only"
    UNKNOWN = "error"


@dataclass
class LoginResult:
    status: LoginStatus
    requires_auth: bool
    auth_type: str
    is_blocked: bool
    action_required: str
    error: Optional[str]


class LoginRequirementDetector:
    """
    Detector de requisitos de autenticación.
    Identifica URLs que requieren login o suscripción.
    """

    def __init__(self):
        self._session = requests.Session()

    def detect(self, url: str) -> LoginResult:
        """
        Detecta requisitos de login.

        Args:
            url: URL a analizar

        Returns:
            LoginResult con requisitos
        """
        try:
            response = self._session.head(url, timeout=10, allow_redirects=True)
            status = response.status_code
            headers = response.headers

            if status == 401:
                return LoginResult(
                    status=LoginStatus.REQUIRED,
                    requires_auth=True,
                    auth_type="Basic/Auth",
                    is_blocked=True,
                    action_required="Autenticación requerida",
                    error=None
                )

            if status == 403:
                www_auth = headers.get('WWW-Authenticate', '').lower()
                if 'login' in www_auth or 'basic' in www_auth:
                    return LoginResult(
                        status=LoginStatus.REQUIRED,
                        requires_auth=True,
                        auth_type="HTTP Auth",
                        is_blocked=True,
                        action_required="Login requerido",
                        error=None
                    )

                location = headers.get('Location', '')
                if 'login' in location.lower() or 'signin' in location.lower():
                    return LoginResult(
                        status=LoginStatus.REQUIRED,
                        requires_auth=True,
                        auth_type="Redirect to login",
                        is_blocked=True,
                        action_required="Redirige a login",
                        error=None
                    )

            if status == 200:
                return LoginResult(
                    status=LoginStatus.NOT_REQUIRED,
                    requires_auth=False,
                    auth_type="None",
                    is_blocked=False,
                    action_required="Acceso público",
                    error=None
                )

            return LoginResult(
                status=LoginStatus.UNKNOWN,
                requires_auth=False,
                auth_type="Unknown",
                is_blocked=False,
                action_required="Verificar manualmente",
                error=f"Status code: {status}"
            )

        except Exception as e:
            return LoginResult(
                status=LoginStatus.UNKNOWN,
                requires_auth=False,
                auth_type="Error",
                is_blocked=False,
                action_required="Error de conexión",
                error=str(e)
            )

    def requires_login(self, url: str) -> bool:
        """Verifica si URL requiere login."""
        result = self.detect(url)
        return result.requires_auth


def create_login_requirement_detector() -> LoginRequirementDetector:
    """Factory function."""
    return LoginRequirementDetector()