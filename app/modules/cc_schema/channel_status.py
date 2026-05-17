"""
Channel Status Checker - Módulo 26 de URL Intelligence
=====================================================
Verifica si el canal está verificado o tiene strikes.
Alertar sobre canales con problemas.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PARTNER = "partner"
    UNKNOWN = "unknown"


@dataclass
class ChannelStatusResult:
    is_verified: bool
    verification_status: VerificationStatus
    has_strikes: bool
    strike_count: int
    is_safe: bool
    error: Optional[str]


class ChannelStatusChecker:
    """
    Verificador de estado del canal.
    Detecta verificación y strikes.
    """

    def __init__(self):
        pass

    def check(self, metadata: dict) -> ChannelStatusResult:
        """
        Verifica estado del canal.

        Args:
            metadata: Metadatos del video

        Returns:
            ChannelStatusResult con estado
        """
        is_verified = metadata.get('channel_is_verified') or metadata.get('is_verified') or False

        if is_verified:
            verification = VerificationStatus.VERIFIED
        elif metadata.get('channel_is_partner') or metadata.get('is_partner'):
            verification = VerificationStatus.PARTNER
        else:
            verification = VerificationStatus.UNVERIFIED

        has_strikes = metadata.get('channel_has_strikes') or metadata.get('has_strikes') or False
        strike_count = metadata.get('strike_count') or metadata.get('channel_strikes') or 0

        is_safe = not has_strikes and verification in [VerificationStatus.VERIFIED, VerificationStatus.PARTNER]

        return ChannelStatusResult(
            is_verified=is_verified,
            verification_status=verification,
            has_strikes=has_strikes,
            strike_count=strike_count,
            is_safe=is_safe,
            error=None
        )

    def is_verified(self, metadata: dict) -> bool:
        """Verifica si canal está verificado."""
        result = self.check(metadata)
        return result.is_verified


def create_channel_status_checker() -> ChannelStatusChecker:
    """Factory function."""
    return ChannelStatusChecker()