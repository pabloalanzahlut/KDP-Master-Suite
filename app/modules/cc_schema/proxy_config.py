"""
Proxy Configuration Validator - Módulo 12 de URL Intelligence
============================================================
Verifica configuración de proxy antes de realizar petición.
Asegura que proxy esté activo y funcional.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import os
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProxyStatus(Enum):
    NOT_CONFIGURED = "not_configured"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class ProxyConfig:
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None


@dataclass
class ProxyValidationResult:
    status: ProxyStatus
    http_proxy: Optional[str]
    https_proxy: Optional[str]
    is_valid: bool
    error: Optional[str]
    auth_required: bool


class ProxyConfigValidator:
    """
    Validador de configuración de proxy.
    Lee variables de entorno y valida formato.
    """

    ENV_VARS = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'no_proxy', 'NO_PROXY']

    def __init__(self):
        self._session = None

    def get_config(self) -> ProxyConfig:
        """Obtiene configuración de proxy desde entorno."""
        return ProxyConfig(
            http_proxy=os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY'),
            https_proxy=os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY'),
            no_proxy=os.environ.get('no_proxy') or os.environ.get('NO_PROXY')
        )

    def validate(self, proxy_url: Optional[str] = None) -> ProxyValidationResult:
        """
        Valida configuración de proxy.

        Args:
            proxy_url: URL de proxy específica (opcional)

        Returns:
            ProxyValidationResult con estado
        """
        if not proxy_url:
            config = self.get_config()
            if not config.http_proxy and not config.https_proxy:
                return ProxyValidationResult(
                    status=ProxyStatus.NOT_CONFIGURED,
                    http_proxy=None,
                    https_proxy=None,
                    is_valid=False,
                    error="No proxy configurado",
                    auth_required=False
                )
            proxy_url = config.http_proxy or config.https_proxy

        if not proxy_url:
            return ProxyValidationResult(
                status=ProxyStatus.NOT_CONFIGURED,
                http_proxy=None,
                https_proxy=None,
                is_valid=False,
                error="Proxy URL vacía",
                auth_required=False
            )

        if not proxy_url.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            return ProxyValidationResult(
                status=ProxyStatus.ERROR,
                http_proxy=proxy_url,
                https_proxy=None,
                is_valid=False,
                error=f"Protocolo de proxy inválido: {proxy_url}",
                auth_required=False
            )

        auth_required = '@' in proxy_url.replace('://', '')

        try:
            session = requests.Session()
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }

            response = session.head('https://www.google.com', timeout=5)
            session.close()

            return ProxyValidationResult(
                status=ProxyStatus.ACTIVE,
                http_proxy=proxy_url,
                https_proxy=proxy_url,
                is_valid=True,
                error=None,
                auth_required=auth_required
            )

        except Exception as e:
            return ProxyValidationResult(
                status=ProxyStatus.INACTIVE,
                http_proxy=proxy_url,
                https_proxy=proxy_url,
                is_valid=False,
                error=f"Proxy inaccesible: {str(e)}",
                auth_required=auth_required
            )

    def is_configured(self) -> bool:
        """Verifica si hay proxy configurado."""
        config = self.get_config()
        return bool(config.http_proxy or config.https_proxy)

    def get_proxy_dict(self) -> Dict[str, str]:
        """Obtiene diccionario de proxies para requests."""
        config = self.get_config()
        proxies = {}
        if config.http_proxy:
            proxies['http'] = config.http_proxy
        if config.https_proxy:
            proxies['https'] = config.https_proxy
        return proxies


def create_proxy_config_validator() -> ProxyConfigValidator:
    """Factory function."""
    return ProxyConfigValidator()