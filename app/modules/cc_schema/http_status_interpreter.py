"""
HTTP Status Code Interpreter - Módulo 7 de URL Intelligence
===========================================================
Interpreta códigos de respuesta (200, 403, 404, 429) y sugiere acciones.
Diferencia entre "video privado" (403) y "no existe" (404).

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HTTPStatusCategory(Enum):
    SUCCESS = "success"
    REDIRECT = "redirect"
    CLIENT_ERROR = "client_error"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


class RecommendedAction(Enum):
    PROCEED = "proceed"
    RETRY = "retry"
    RETRY_LATER = "retry_later"
    BLOCK = "block"
    MANUAL_REVIEW = "manual_review"
    AUTHENTICATE = "authenticate"


@dataclass
class HTTPStatusInterpretation:
    status_code: int
    category: HTTPStatusCategory
    reason_phrase: str
    description: str
    recommended_action: RecommendedAction
    is_blocking: bool
    retry_after_seconds: Optional[int]
    youtube_specific: Optional[str]


class HTTPStatusInterpreter:
    """
    Intérprete de códigos de estado HTTP con recomendaciones de acción.
    Especializado en códigos comunes de YouTube y plataformas de video.
    """

    STATUS_MESSAGES = {
        200: ("OK", "Solicitud exitosa"),
        201: ("Created", "Recurso creado exitosamente"),
        204: ("No Content", "Solicitud exitosa sin contenido"),
        301: ("Moved Permanently", "Recurso movido permanentemente"),
        302: ("Found", "Recurso temporalmente en otra ubicación"),
        304: ("Not Modified", "Recursos no modificado desde última solicitud"),
        400: ("Bad Request", "Solicitud malformada"),
        401: ("Unauthorized", "Requiere autenticación"),
        403: ("Forbidden", "Acceso denegado"),
        404: ("Not Found", "Recurso no encontrado"),
        410: ("Gone", "Recurso eliminado permanentemente"),
        429: ("Too Many Requests", "Demasiadas solicitudes - rate limit"),
        500: ("Internal Server Error", "Error interno del servidor"),
        502: ("Bad Gateway", "Gateway inválido"),
        503: ("Service Unavailable", "Servicio no disponible"),
        504: ("Gateway Timeout", "Timeout del gateway"),
    }

    YOUTUBE_SPECIFIC = {
        403: {
            "private": "Video privado - requiere acceso",
            "geoblock": "Video bloqueado geográficamente",
            "age_restricted": "Video con restricción de edad",
            "deleted": "Video eliminado",
            "copyright": "Video eliminado por copyright"
        },
        404: {
            "not_found": "Video no existe o fue eliminado",
            "unavailable": "Video no disponible"
        },
        429: {
            "rate_limit": "YouTube impone rate limit - esperar antes de reintentar"
        }
    }

    def __init__(self):
        pass

    def interpret(self, status_code: int, headers: Optional[Dict[str, str]] = None) -> HTTPStatusInterpretation:
        """
        Interpreta código HTTP y sugiere acción.

        Args:
            status_code: Código de estado HTTP
            headers: Headers de respuesta (opcional)

        Returns:
            HTTPStatusInterpretation con análisis y recomendación
        """
        headers = headers or {}

        reason_phrase, base_description = self.STATUS_MESSAGES.get(
            status_code,
            ("Unknown", "Código de estado desconocido")
        )

        category = self._get_category(status_code)
        recommended_action, is_blocking, retry_after = self._get_recommendation(status_code, headers)
        youtube_specific = self._get_youtube_specific(status_code, headers)

        description = base_description
        if youtube_specific:
            description = f"{base_description}: {youtube_specific}"

        return HTTPStatusInterpretation(
            status_code=status_code,
            category=category,
            reason_phrase=reason_phrase,
            description=description,
            recommended_action=recommended_action,
            is_blocking=is_blocking,
            retry_after_seconds=retry_after,
            youtube_specific=youtube_specific
        )

    def _get_category(self, status_code: int) -> HTTPStatusCategory:
        """Determina categoría del código."""
        if 200 <= status_code < 300:
            return HTTPStatusCategory.SUCCESS
        elif 300 <= status_code < 400:
            return HTTPStatusCategory.REDIRECT
        elif 400 <= status_code < 500:
            return HTTPStatusCategory.CLIENT_ERROR
        elif 500 <= status_code < 600:
            return HTTPStatusCategory.SERVER_ERROR
        return HTTPStatusCategory.UNKNOWN

    def _get_recommendation(self, status_code: int, headers: Dict[str, str]) -> tuple:
        """Determina acción recomendada y si es blocking."""
        retry_after = None

        if status_code == 200:
            return RecommendedAction.PROCEED, False, None

        elif status_code == 204:
            return RecommendedAction.PROCEED, False, None

        elif status_code in [301, 302, 304]:
            return RecommendedAction.PROCEED, False, None

        elif status_code == 400:
            return RecommendedAction.BLOCK, True, None

        elif status_code == 401:
            return RecommendedAction.AUTHENTICATE, True, None

        elif status_code == 403:
            return RecommendedAction.BLOCK, True, None

        elif status_code == 404:
            return RecommendedAction.BLOCK, True, None

        elif status_code == 410:
            return RecommendedAction.BLOCK, True, None

        elif status_code == 429:
            retry_after = self._parse_retry_after(headers.get('Retry-After'))
            return RecommendedAction.RETRY_LATER, True, retry_after

        elif status_code == 500:
            return RecommendedAction.RETRY, True, 60

        elif status_code in [502, 503, 504]:
            retry_after = 30 if status_code == 502 else 60
            return RecommendedAction.RETRY, False, retry_after

        return RecommendedAction.MANUAL_REVIEW, True, None

    def _get_youtube_specific(self, status_code: int, headers: Dict[str, str]) -> Optional[str]:
        """Detecta información específica de YouTube."""
        if status_code not in self.YOUTUBE_SPECIFIC:
            return None

        x_youtube_message = headers.get('X-YouTube-Message', '')
        x_youtube_error = headers.get('X-YouTube-Error', '')

        if 'private' in x_youtube_message.lower() or 'private' in x_youtube_error.lower():
            return self.YOUTUBE_SPECIFIC[403]['private']

        if 'geo' in x_youtube_message.lower() or 'geo' in x_youtube_error.lower():
            return self.YOUTUBE_SPECIFIC[403]['geoblock']

        if 'age' in x_youtube_message.lower() or 'age' in x_youtube_error.lower():
            return self.YOUTUBE_SPECIFIC[403]['age_restricted']

        if status_code == 403:
            return self.YOUTUBE_SPECIFIC[403]['private']

        if status_code == 404:
            return self.YOUTUBE_SPECIFIC[404]['not_found']

        if status_code == 429:
            return self.YOUTUBE_SPECIFIC[429]['rate_limit']

        return None

    def _parse_retry_after(self, retry_after: Optional[str]) -> Optional[int]:
        """Parsea header Retry-After."""
        if not retry_after:
            return None

        try:
            return int(retry_after)
        except ValueError:
            from email.utils import parsedate_to_datetime
            try:
                dt = parsedate_to_datetime(retry_after)
                import time
                return max(0, int(dt.timestamp() - time.time()))
            except Exception:
                return None

    def should_proceed(self, status_code: int) -> bool:
        """Determina si se debe proceder con la solicitud."""
        interpretation = self.interpret(status_code)
        return interpretation.recommended_action == RecommendedAction.PROCEED

    def is_blocking(self, status_code: int) -> bool:
        """Determina si el código de estado bloquea la operación."""
        interpretation = self.interpret(status_code)
        return interpretation.is_blocking


def create_http_status_interpreter() -> HTTPStatusInterpreter:
    """Factory function."""
    return HTTPStatusInterpreter()