"""
Channel Existence Validator - Módulo 25 de URL Intelligence
===========================================================
Verifica que el canal del video exista y esté activo.
Evitar videos de canales eliminados.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ChannelStatus(Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


@dataclass
class ChannelExistenceResult:
    channel_id: Optional[str]
    channel_name: Optional[str]
    status: ChannelStatus
    is_valid: bool
    error: Optional[str]


class ChannelExistenceValidator:
    """
    Validador de existencia de canal.
    Verifica que el canal esté activo.
    """

    def __init__(self):
        pass

    def validate(self, metadata: dict) -> ChannelExistenceResult:
        """
        Valida existencia del canal.

        Args:
            metadata: Metadatos del video

        Returns:
            ChannelExistenceResult con estado del canal
        """
        channel_id = metadata.get('channel_id') or metadata.get('channelId')
        channel_name = metadata.get('channel') or metadata.get('channel_name') or metadata.get('uploader')

        if not channel_id:
            return ChannelExistenceResult(
                channel_id=None,
                channel_name=channel_name,
                status=ChannelStatus.UNKNOWN,
                is_valid=False,
                error="ID de canal no encontrado"
            )

        if metadata.get('channel_deleted') or metadata.get('channel_is_deleted'):
            return ChannelExistenceResult(
                channel_id=channel_id,
                channel_name=channel_name,
                status=ChannelStatus.DELETED,
                is_valid=False,
                error="Canal eliminado"
            )

        if metadata.get('channel_suspended') or metadata.get('channel_is_suspended'):
            return ChannelExistenceResult(
                channel_id=channel_id,
                channel_name=channel_name,
                status=ChannelStatus.SUSPENDED,
                is_valid=False,
                error="Canal suspendido"
            )

        return ChannelExistenceResult(
            channel_id=channel_id,
            channel_name=channel_name,
            status=ChannelStatus.ACTIVE,
            is_valid=True,
            error=None
        )

    def is_active(self, metadata: dict) -> bool:
        """Verifica si canal está activo."""
        result = self.validate(metadata)
        return result.status == ChannelStatus.ACTIVE


def create_channel_existence_validator() -> ChannelExistenceValidator:
    """Factory function."""
    return ChannelExistenceValidator()