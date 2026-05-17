"""
Content-Type Validator - Módulo 14 de URL Intelligence
====================================================
Verifica que Content-Type sea texto/html o aplicación/json válido.
Detecta páginas de error o CAPTCHA.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from typing import Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentTypeStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class ContentTypeResult:
    status: ContentTypeStatus
    content_type: Optional[str]
    mime_type: Optional[str]
    charset: Optional[str]
    is_valid: bool
    error: Optional[str]


class ContentTypeValidator:
    """
    Validador de Content-Type HTTP.
    Verifica que el contenido sea del tipo esperado.
    """

    VALID_HTML_TYPES = {
        'text/html',
        'application/xhtml+xml',
    }

    VALID_JSON_TYPES = {
        'application/json',
        'application/json+xml',
    }

    ERROR_TYPES = {
        'application/pdf',
        'application/zip',
        'application/octet-stream',
        'image/',
    }

    def __init__(self):
        self._session = requests.Session()

    def validate(self, url: str) -> ContentTypeResult:
        """
        Valida Content-Type de URL.

        Args:
            url: URL a validar

        Returns:
            ContentTypeResult con tipo y validación
        """
        try:
            response = self._session.head(url, timeout=10, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '')

            if not content_type:
                return ContentTypeResult(
                    status=ContentTypeStatus.INVALID,
                    content_type=None,
                    mime_type=None,
                    charset=None,
                    is_valid=False,
                    error="No Content-Type en respuesta"
                )

            mime_type, charset = self._parse_content_type(content_type)

            if any(error_type in mime_type.lower() for error_type in self.ERROR_TYPES):
                return ContentTypeResult(
                    status=ContentTypeStatus.INVALID,
                    content_type=content_type,
                    mime_type=mime_type,
                    charset=charset,
                    is_valid=False,
                    error=f"Content-Type no válido para video: {mime_type}"
                )

            is_valid = (
                mime_type.lower() in self.VALID_HTML_TYPES or
                mime_type.lower() in self.VALID_JSON_TYPES
            )

            return ContentTypeResult(
                status=ContentTypeStatus.VALID if is_valid else ContentTypeStatus.INVALID,
                content_type=content_type,
                mime_type=mime_type,
                charset=charset,
                is_valid=is_valid,
                error=None if is_valid else f"Content-Type no soportado: {mime_type}"
            )

        except Exception as e:
            return ContentTypeResult(
                status=ContentTypeStatus.ERROR,
                content_type=None,
                mime_type=None,
                charset=None,
                is_valid=False,
                error=str(e)
            )

    def _parse_content_type(self, content_type: str) -> tuple:
        """Parsea Content-Type en mime y charset."""
        parts = content_type.split(';')
        mime_type = parts[0].strip()
        charset = None

        for part in parts[1:]:
            if 'charset' in part.lower():
                charset = part.split('=')[1].strip().strip('"\'')
                break

        return mime_type, charset

    def is_html(self, url: str) -> bool:
        """Verifica si URL retorna HTML."""
        result = self.validate(url)
        return result.mime_type in self.VALID_HTML_TYPES if result.mime_type else False

    def is_json(self, url: str) -> bool:
        """Verifica si URL retorna JSON."""
        result = self.validate(url)
        return result.mime_type in self.VALID_JSON_TYPES if result.mime_type else False


def create_content_type_validator() -> ContentTypeValidator:
    """Factory function."""
    return ContentTypeValidator()