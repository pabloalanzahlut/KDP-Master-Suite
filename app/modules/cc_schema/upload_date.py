"""
Upload Date Validator - Módulo 23 de URL Intelligence
====================================================
Verifica fecha de publicación del video.
Filtrar videos más antiguos de X días.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RecencyStatus(Enum):
    RECENT = "recent"
    OLD = "old"
    VERY_OLD = "very_old"
    UNKNOWN = "unknown"


@dataclass
class UploadDateResult:
    upload_date: Optional[datetime]
    recency: RecencyStatus
    days_since_upload: Optional[int]
    is_valid: bool
    error: Optional[str]


class UploadDateValidator:
    """
    Validador de fecha de publicación de video.
    Clasifica por recencia y filtra según antigüedad.
    """

    RECENT_THRESHOLD = 30
    OLD_THRESHOLD = 365

    def __init__(
        self,
        recent_days: int = RECENT_THRESHOLD,
        old_days: int = OLD_THRESHOLD
    ):
        self.recent_days = recent_days
        self.old_days = old_days

    def validate(self, metadata: dict) -> UploadDateResult:
        """
        Valida fecha de publicación.

        Args:
            metadata: Metadatos del video

        Returns:
            UploadDateResult con fecha y recencia
        """
        upload_date = metadata.get('upload_date') or metadata.get('published') or metadata.get('uploaded')

        if not upload_date:
            return UploadDateResult(
                upload_date=None,
                recency=RecencyStatus.UNKNOWN,
                days_since_upload=None,
                is_valid=False,
                error="Fecha de publicación no encontrada"
            )

        if isinstance(upload_date, str):
            try:
                upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    upload_date = datetime.strptime(upload_date, '%Y-%m-%d')
                except ValueError:
                    return UploadDateResult(
                        upload_date=None,
                        recency=RecencyStatus.UNKNOWN,
                        days_since_upload=None,
                        is_valid=False,
                        error=f"No se pudo parsear fecha: {upload_date}"
                    )

        days_since = (datetime.now() - upload_date).days

        if days_since <= self.recent_days:
            recency = RecencyStatus.RECENT
        elif days_since <= self.old_days:
            recency = RecencyStatus.OLD
        else:
            recency = RecencyStatus.VERY_OLD

        return UploadDateResult(
            upload_date=upload_date,
            recency=recency,
            days_since_upload=days_since,
            is_valid=True,
            error=None
        )

    def is_recent(self, metadata: dict) -> bool:
        """Verifica si video es reciente."""
        result = self.validate(metadata)
        return result.recency == RecencyStatus.RECENT

    def filter_by_age(self, videos: list, max_days: int) -> list:
        """Filtra videos por antigüedad máxima."""
        return [
            v for v in videos
            if self.validate(v).days_since_upload is not None
            and self.validate(v).days_since_upload <= max_days
        ]


def create_upload_date_validator(
    recent_days: int = 30,
    old_days: int = 365
) -> UploadDateValidator:
    """Factory function."""
    return UploadDateValidator(
        recent_days=recent_days,
        old_days=old_days
    )