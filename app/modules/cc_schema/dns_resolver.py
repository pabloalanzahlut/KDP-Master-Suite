"""
DNS Resolver - Módulo 4 de URL Intelligence
==========================================
Resuelve el DNS del dominio con timeout configurable (default 3s).
Detecta dominios inexistentes sin bloquear la UI.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import socket
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)


class DNSStatus(Enum):
    RESOLVED = "resolved"
    TIMEOUT = "timeout"
    NXDOMAIN = "nxdomain"
    ERROR = "error"


@dataclass
class DNSResult:
    status: DNSStatus
    domain: str
    ip_addresses: List[str]
    resolution_time_ms: float
    error: Optional[str]
    ttl: Optional[int]


class DNSResolver:
    """
    Resolvedor DNS con timeout configurable y cacheo de resultados.
    Implementa resolución síncrona y asíncrona.
    """

    DEFAULT_TIMEOUT = 3.0
    DEFAULT_CACHE_TTL = 300

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        use_system_dns: bool = True
    ):
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.use_system_dns = use_system_dns
        self._cache: Dict[str, DNSResult] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)

    def resolve(self, domain: str) -> DNSResult:
        """
        Resuelve dominio a IP con timeout.

        Args:
            domain: Dominio a resolver (sin http/https)

        Returns:
            DNSResult con IPs o error
        """
        if not domain:
            return DNSResult(
                status=DNSStatus.ERROR,
                domain=domain or "",
                ip_addresses=[],
                resolution_time_ms=0,
                error="Dominio vacío",
                ttl=None
            )

        domain = domain.lower().strip()
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        if '/' in domain:
            domain = domain.split('/')[0]
        if ':' in domain:
            domain = domain.split(':')[0]

        cached = self._get_from_cache(domain)
        if cached:
            return cached

        start_time = time.time()

        try:
            socket.setdefaulttimeout(self.timeout)

            ip_addresses = []
            result = socket.getaddrinfo(
                domain,
                None,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM
            )

            for res in result:
                ip = res[4][0]
                if ip not in ip_addresses:
                    ip_addresses.append(ip)

            resolution_time = (time.time() - start_time) * 1000

            dns_result = DNSResult(
                status=DNSStatus.RESOLVED,
                domain=domain,
                ip_addresses=ip_addresses,
                resolution_time_ms=resolution_time,
                error=None,
                ttl=self.cache_ttl
            )

            self._add_to_cache(domain, dns_result)
            return dns_result

        except socket.gaierror as e:
            resolution_time = (time.time() - start_time) * 1000

            if e.errno == socket.EAI_NONAME:
                return DNSResult(
                    status=DNSStatus.NXDOMAIN,
                    domain=domain,
                    ip_addresses=[],
                    resolution_time_ms=resolution_time,
                    error="Dominio no encontrado (NXDOMAIN)",
                    ttl=None
                )
            else:
                return DNSResult(
                    status=DNSStatus.ERROR,
                    domain=domain,
                    ip_addresses=[],
                    resolution_time_ms=resolution_time,
                    error=f"Error DNS: {e}",
                    ttl=None
                )

        except socket.timeout:
            resolution_time = (time.time() - start_time) * 1000
            return DNSResult(
                status=DNSStatus.TIMEOUT,
                domain=domain,
                ip_addresses=[],
                resolution_time_ms=resolution_time,
                error=f"Timeout después de {self.timeout}s",
                ttl=None
            )

        except Exception as e:
            resolution_time = (time.time() - start_time) * 1000
            logger.error(f"Error resolviendo {domain}: {e}")
            return DNSResult(
                status=DNSStatus.ERROR,
                domain=domain,
                ip_addresses=[],
                resolution_time_ms=resolution_time,
                error=str(e),
                ttl=None
            )

    async def resolve_async(self, domain: str) -> DNSResult:
        """Resuelve dominio de forma asíncrona."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.resolve, domain)

    def resolve_batch(self, domains: List[str]) -> List[DNSResult]:
        """Resuelve múltiples dominios."""
        return [self.resolve(d) for d in domains]

    def _get_from_cache(self, domain: str) -> Optional[DNSResult]:
        """Obtiene resultado de cache."""
        if domain in self._cache:
            cached = self._cache[domain]
            return cached
        return None

    def _add_to_cache(self, domain: str, result: DNSResult):
        """Agrega resultado a cache."""
        self._cache[domain] = result

    def clear_cache(self):
        """Limpia cache de DNS."""
        self._cache.clear()

    def is_resolvable(self, domain: str) -> bool:
        """Verifica si dominio es resoluble."""
        result = self.resolve(domain)
        return result.status == DNSStatus.RESOLVED and len(result.ip_addresses) > 0

    def get_primary_ip(self, domain: str) -> Optional[str]:
        """Obtiene IP primaria del dominio."""
        result = self.resolve(domain)
        if result.ip_addresses:
            return result.ip_addresses[0]
        return None


def create_dns_resolver(
    timeout: float = 3.0,
    cache_ttl: int = 300
) -> DNSResolver:
    """Factory function."""
    return DNSResolver(timeout=timeout, cache_ttl=cache_ttl)