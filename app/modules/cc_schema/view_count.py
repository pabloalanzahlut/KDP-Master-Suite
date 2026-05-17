"""
View Count Verifier - Módulo 24 de URL Intelligence
==================================================
Obtiene contador de visualizaciones.
Filtrar videos con <X vistas (posible spam).

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ViewCountResult:
    view_count: Optional[int]
    formatted_count: Optional[str]
    is_suspicious: bool
    is_valid: bool
    error: Optional[str]


class ViewCountVerifier:
    """
    Verificador de contador de visualizaciones.
    Detecta videos con pocas vistas (posible spam).
    """

    MIN_VIEWS_FOR_VALID = 100
    SUSPICIOUS_THRESHOLD = 10

    def __init__(
        self,
        min_views: int = MIN_VIEWS_FOR_VALID,
        suspicious_threshold: int = SUSPICIOUS_THRESHOLD
    ):
        self.min_views = min_views
        self.suspicious_threshold = suspicious_threshold

    def verify(self, metadata: dict) -> ViewCountResult:
        """
        Verifica conteo de visualizaciones.

        Args:
            metadata: Metadatos del video

        Returns:
            ViewCountResult con conteo
        """
        view_count = metadata.get('view_count') or metadata.get('views')

        if view_count is None:
            return ViewCountResult(
                view_count=None,
                formatted_count=None,
                is_suspicious=False,
                is_valid=False,
                error="Conteo de vistas no encontrado"
            )

        if isinstance(view_count, str):
            try:
                view_count = int(view_count.replace(',', ''))
            except ValueError:
                return ViewCountResult(
                    view_count=None,
                    formatted_count=None,
                    is_suspicious=False,
                    is_valid=False,
                    error=f"No se pudo parsear vistas: {view_count}"
                )

        formatted = self._format_count(view_count)
        is_suspicious = view_count < self.suspicious_threshold

        return ViewCountResult(
            view_count=view_count,
            formatted_count=formatted,
            is_suspicious=is_suspicious,
            is_valid=True,
            error=None
        )

    def _format_count(self, count: int) -> str:
        """Formatea número de vistas."""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)

    def has_minimum_views(self, metadata: dict) -> bool:
        """Verifica si tiene vistas mínimas."""
        result = self.verify(metadata)
        return result.view_count is not None and result.view_count >= self.min_views


def create_view_count_verifier(
    min_views: int = 100,
    suspicious_threshold: int = 10
) -> ViewCountVerifier:
    """Factory function."""
    return ViewCountVerifier(
        min_views=min_views,
        suspicious_threshold=suspicious_threshold
    )