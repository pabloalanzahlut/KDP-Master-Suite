"""
HTTP HEAD Request Validator - Módulo 5 de URL Intelligence
=========================================================
Realiza petición HEAD para verificar disponibilidad sin descargar contenido.
Confirma que el video existe sin gastar ancho de banda.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HTTPValidationStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    REDIRECT = "redirect"
    ERROR = "error"


@dataclass
class HTTPHeadResult:
    status: HTTPValidationStatus
    url: str
    final_url: Optional[str]
    status_code: int
    content_type: Optional[str]
    content_length: Optional[int]
    server: Optional[str]
    headers: Dict[str, str]
    error: Optional[str]
    response_time_ms: float


class HTTPHeadValidator:
    """
    Validador de disponibilidad via HTTP HEAD request.
    Verifica existencia de recursos sin descargar cuerpo.
    """

    DEFAULT_TIMEOUT = 10.0
    MAX_REDIRECTS = 5
    ALLOWED_STATUS_CODES = {200, 201, 204}

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_redirects: int = MAX_REDIRECTS,
        follow_redirects: bool = True
    ):
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.follow_redirects = follow_redirects
        self._session = requests.Session()

    def validate(self, url: str, allow_status_codes: Optional[List[int]] = None) -> HTTPHeadResult:
        """
        Valida disponibilidad de URL via HEAD request.

        Args:
            url: URL a validar
            allow_status_codes: Códigos adicionales a considerar como disponibles

        Returns:
            HTTPHeadResult con estado de disponibilidad
        """
        if not url:
            return HTTPHeadResult(
                status=HTTPValidationStatus.ERROR,
                url=url or "",
                final_url=None,
                status_code=0,
                content_type=None,
                content_length=None,
                server=None,
                headers={},
                error="URL vacía",
                response_time_ms=0
            )

        allowed = allow_status_codes or []
        allowed_codes = self.ALLOWED_STATUS_CODES.union(set(allowed))

        start_time = __import__('time').time()

        try:
            response = self._session.head(
                url,
                timeout=self.timeout,
                allow_redirects=self.follow_redirects,
                verify=True
            )

            response_time = (__import__('time').time() - start_time) * 1000

            final_url = response.url
            status_code = response.status_code
            content_type = response.headers.get('Content-Type')
            content_length = response.headers.get('Content-Length')
            server = response.headers.get('Server')

            headers_dict = {k: v for k, v in response.headers.items()}

            if status_code in allowed_codes:
                return HTTPHeadResult(
                    status=HTTPValidationStatus.AVAILABLE,
                    url=url,
                    final_url=final_url,
                    status_code=status_code,
                    content_type=content_type,
                    content_length=int(content_length) if content_length and content_length.isdigit() else None,
                    server=server,
                    headers=headers_dict,
                    error=None,
                    response_time_ms=response_time
                )

            if 300 <= status_code < 400:
                return HTTPHeadResult(
                    status=HTTPValidationStatus.REDIRECT,
                    url=url,
                    final_url=final_url,
                    status_code=status_code,
                    content_type=content_type,
                    content_length=int(content_length) if content_length and content_length.isdigit() else None,
                    server=server,
                    headers=headers_dict,
                    error=f"Redirección: {status_code}",
                    response_time_ms=response_time
                )

            return HTTPHeadResult(
                status=HTTPValidationStatus.UNAVAILABLE,
                url=url,
                final_url=final_url,
                status_code=status_code,
                content_type=content_type,
                content_length=int(content_length) if content_length and content_length.isdigit() else None,
                server=server,
                headers=headers_dict,
                error=f"Código de estado: {status_code}",
                response_time_ms=response_time
            )

        except requests.exceptions.Timeout:
            response_time = (__import__('time').time() - start_time) * 1000
            return HTTPHeadResult(
                status=HTTPValidationStatus.ERROR,
                url=url,
                final_url=None,
                status_code=0,
                content_type=None,
                content_length=None,
                server=None,
                headers={},
                error=f"Timeout después de {self.timeout}s",
                response_time_ms=response_time
            )

        except requests.exceptions.ConnectionError as e:
            response_time = (__import__('time').time() - start_time) * 1000
            return HTTPHeadResult(
                status=HTTPValidationStatus.ERROR,
                url=url,
                final_url=None,
                status_code=0,
                content_type=None,
                content_length=None,
                server=None,
                headers={},
                error=f"Error de conexión: {str(e)}",
                response_time_ms=response_time
            )

        except Exception as e:
            response_time = (__import__('time').time() - start_time) * 1000
            logger.error(f"Error validando URL {url}: {e}")
            return HTTPHeadResult(
                status=HTTPValidationStatus.ERROR,
                url=url,
                final_url=None,
                status_code=0,
                content_type=None,
                content_length=None,
                server=None,
                headers={},
                error=str(e),
                response_time_ms=response_time
            )

    def validate_batch(self, urls: List[str]) -> List[HTTPHeadResult]:
        """Valida múltiples URLs."""
        return [self.validate(url) for url in urls]

    def is_available(self, url: str) -> bool:
        """Verifica si URL está disponible."""
        result = self.validate(url)
        return result.status == HTTPValidationStatus.AVAILABLE

    def get_content_type(self, url: str) -> Optional[str]:
        """Obtiene Content-Type de URL."""
        result = self.validate(url)
        return result.content_type

    def close(self):
        """Cierra sesión HTTP."""
        self._session.close()


def create_http_head_validator(
    timeout: float = 10.0,
    follow_redirects: bool = True
) -> HTTPHeadValidator:
    """Factory function."""
    return HTTPHeadValidator(
        timeout=timeout,
        follow_redirects=follow_redirects
    )