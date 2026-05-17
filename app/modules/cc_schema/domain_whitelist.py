"""
Domain Whitelist Validator - Módulo 3 de URL Intelligence
===========================================================
Valida que el dominio sea youtube.com, vimeo.com u otros permitidos en whitelist.
Bloquea dominios sospechosos o no soportados.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import re
from typing import Optional, List, Set, Dict, Any
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DomainStatus(Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class DomainValidationResult:
    is_allowed: bool
    status: DomainStatus
    domain: Optional[str]
    tld: Optional[str]
    is_subdomain: bool
    category: Optional[str]
    reason: Optional[str]


class DomainWhitelist:
    """
    Validador de dominios permitidos para procesamiento.
    Mantiene whitelist de dominios soportados y categorías.
    """

    DEFAULT_WHITELIST = {
        'youtube.com',
        'www.youtube.com',
        'm.youtube.com',
        'youtu.be',
        'www.youtu.be',
        'vimeo.com',
        'www.vimeo.com',
        'player.vimeo.com',
    }

    VIDEO_PLATFORMS = {
        'youtube.com': 'video',
        'youtu.be': 'video',
        'vimeo.com': 'video',
    }

    DEFAULT_BLACKLIST = {
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
    }

    SUSPICIOUS_TLDS = {
        'xyz', 'top', 'work', 'click', 'link', 'buzz', 'gq', 'cf', 'tk', 'ml', 'ga'
    }

    def __init__(
        self,
        whitelist: Optional[Set[str]] = None,
        blacklist: Optional[Set[str]] = None,
        allow_subdomains: bool = True
    ):
        self.whitelist = whitelist or self.DEFAULT_WHITELIST
        self.blacklist = blacklist or self.DEFAULT_BLACKLIST
        self.allow_subdomains = allow_subdomains

    def validate(self, url: str) -> DomainValidationResult:
        """
        Valida si dominio está en whitelist.

        Args:
            url: URL a validar

        Returns:
            DomainValidationResult con estado y detalles
        """
        if not url:
            return DomainValidationResult(
                is_allowed=False,
                status=DomainStatus.UNKNOWN,
                domain=None,
                tld=None,
                is_subdomain=False,
                category=None,
                reason="URL vacía"
            )

        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()

            if not netloc:
                return DomainValidationResult(
                    is_allowed=False,
                    status=DomainStatus.UNKNOWN,
                    domain=None,
                    tld=None,
                    is_subdomain=False,
                    category=None,
                    reason="Dominio no encontrado en URL"
                )

            port = ''
            if ':' in netloc:
                parts = netloc.rsplit(':', 1)
                netloc = parts[0]
                port = parts[1] if parts[1].isdigit() else ''

            domain = netloc.split(':')[0]

            if not domain:
                return DomainValidationResult(
                    is_allowed=False,
                    status=DomainStatus.UNKNOWN,
                    domain=None,
                    tld=None,
                    is_subdomain=False,
                    category=None,
                    reason="Dominio inválido"
                )

            tld = self._extract_tld(domain)
            is_subdomain = self._is_subdomain(domain)

            if domain in self.blacklist:
                return DomainValidationResult(
                    is_allowed=False,
                    status=DomainStatus.BLOCKED,
                    domain=domain,
                    tld=tld,
                    is_subdomain=is_subdomain,
                    category=None,
                    reason=f"Dominio en blacklist: {domain}"
                )

            if tld in self.SUSPICIOUS_TLDS:
                return DomainValidationResult(
                    is_allowed=False,
                    status=DomainStatus.BLOCKED,
                    domain=domain,
                    tld=tld,
                    is_subdomain=is_subdomain,
                    category=None,
                    reason=f"TLD sospechoso: {tld}"
                )

            if domain in self.whitelist:
                category = self.VIDEO_PLATFORMS.get(domain, 'video')
                return DomainValidationResult(
                    is_allowed=True,
                    status=DomainStatus.ALLOWED,
                    domain=domain,
                    tld=tld,
                    is_subdomain=is_subdomain,
                    category=category,
                    reason=None
                )

            if self.allow_subdomains:
                for whitelisted in self.whitelist:
                    if domain.endswith('.' + whitelisted):
                        category = self.VIDEO_PLATFORMS.get(whitelisted, 'video')
                        return DomainValidationResult(
                            is_allowed=True,
                            status=DomainStatus.ALLOWED,
                            domain=domain,
                            tld=tld,
                            is_subdomain=is_subdomain,
                            category=category,
                            reason=f"Subdominio de {whitelisted}"
                        )

            return DomainValidationResult(
                is_allowed=False,
                status=DomainStatus.BLOCKED,
                domain=domain,
                tld=tld,
                is_subdomain=is_subdomain,
                category=None,
                reason=f"Dominio no en whitelist: {domain}"
            )

        except Exception as e:
            logger.error(f"Error validando dominio: {e}")
            return DomainValidationResult(
                is_allowed=False,
                status=DomainStatus.UNKNOWN,
                domain=None,
                tld=None,
                is_subdomain=False,
                category=None,
                reason=f"Error: {str(e)}"
            )

    def _extract_tld(self, domain: str) -> Optional[str]:
        """Extrae TLD del dominio."""
        parts = domain.split('.')
        if len(parts) >= 2:
            return parts[-1]
        return None

    def _is_subdomain(self, domain: str) -> bool:
        """Determina si es subdominio."""
        for whitelisted in self.whitelist:
            if domain != whitelisted and domain.endswith('.' + whitelisted):
                return True
        return False

    def add_to_whitelist(self, domain: str):
        """Agrega dominio a whitelist."""
        self.whitelist.add(domain.lower())

    def remove_from_whitelist(self, domain: str):
        """Remueve dominio de whitelist."""
        self.whitelist.discard(domain.lower())

    def add_to_blacklist(self, domain: str):
        """Agrega dominio a blacklist."""
        self.blacklist.add(domain.lower())

    def get_allowed_domains(self) -> List[str]:
        """Retorna lista de dominios permitidos."""
        return sorted(list(self.whitelist))


def create_domain_whitelist(
    whitelist: Optional[Set[str]] = None,
    allow_subdomains: bool = True
) -> DomainWhitelist:
    """Factory function."""
    return DomainWhitelist(
        whitelist=whitelist,
        allow_subdomains=allow_subdomains
    )