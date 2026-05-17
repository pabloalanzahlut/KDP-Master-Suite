"""
Redirect Chain Follower - Módulo 8 de URL Intelligence
===================================================
Sigue redirecciones HTTP (301, 302) hasta URL final.
Resuelve URLs acortadas como "youtu.be" a URL completa.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RedirectType(Enum):
    NONE = "none"
    PERMANENT = "permanent"  # 301
    TEMPORARY = "temporary"  # 302
    FOUND = "found"  # 302
    SEE_OTHER = "see_other"  # 303
    TEMPORARY_REDIRECT = "temporary_redirect"  # 307
    PERMANENT_REDIRECT = "permanent_redirect"  # 308


@dataclass
class RedirectHop:
    url: str
    status_code: int
    redirect_type: RedirectType
    location: Optional[str]


@dataclass
class RedirectChainResult:
    original_url: str
    final_url: str
    hops: List[RedirectHop]
    total_hops: int
    is_circular: bool
    chain_broken: bool
    error: Optional[str]


class RedirectChain:
    """
    Sigue cadena de redirecciones HTTP hasta URL final.
    Detecta URLs acortadas y ciclos de redirección.
    """

    MAX_HOPS = 10
    DEFAULT_TIMEOUT = 10.0

    PERMANENT_CODES = {301, 308}
    TEMPORARY_CODES = {302, 303, 307}

    def __init__(
        self,
        max_hops: int = MAX_HOPS,
        timeout: float = DEFAULT_TIMEOUT,
        follow_external: bool = False
    ):
        self.max_hops = max_hops
        self.timeout = timeout
        self.follow_external = follow_external
        self._session = requests.Session()

    def follow(self, url: str) -> RedirectChainResult:
        """
        Sigue redirecciones hasta URL final.

        Args:
            url: URL inicial

        Returns:
            RedirectChainResult con toda la cadena de redirecciones
        """
        if not url:
            return RedirectChainResult(
                original_url=url or "",
                final_url="",
                hops=[],
                total_hops=0,
                is_circular=False,
                chain_broken=True,
                error="URL vacía"
            )

        hops: List[RedirectHop] = []
        current_url = url
        visited = set()

        try:
            for _ in range(self.max_hops):
                visited.add(current_url)

                response = self._session.head(
                    current_url,
                    timeout=self.timeout,
                    allow_redirects=False,
                    verify=True
                )

                status_code = response.status_code
                redirect_type = self._get_redirect_type(status_code)
                location = response.headers.get('Location')

                hops.append(RedirectHop(
                    url=current_url,
                    status_code=status_code,
                    redirect_type=redirect_type,
                    location=location
                ))

                if status_code not in self.PERMANENT_CODES.union(self.TEMPORARY_CODES):
                    break

                if not location:
                    break

                if not location.startswith('http'):
                    from urllib.parse import urljoin
                    from urllib.parse import urlparse

                    parsed = urlparse(current_url)
                    location = urljoin(
                        f"{parsed.scheme}://{parsed.netloc}",
                        location
                    )

                if location in visited:
                    return RedirectChainResult(
                        original_url=url,
                        final_url=current_url,
                        hops=hops,
                        total_hops=len(hops),
                        is_circular=True,
                        chain_broken=False,
                        error="Ciclo de redirección detectado"
                    )

                current_url = location

            return RedirectChainResult(
                original_url=url,
                final_url=current_url,
                hops=hops,
                total_hops=len(hops),
                is_circular=False,
                chain_broken=False,
                error=None
            )

        except requests.exceptions.Timeout:
            return RedirectChainResult(
                original_url=url,
                final_url=current_url,
                hops=hops,
                total_hops=len(hops),
                is_circular=False,
                chain_broken=True,
                error=f"Timeout después de {self.timeout}s"
            )

        except requests.exceptions.RequestException as e:
            return RedirectChainResult(
                original_url=url,
                final_url=current_url,
                hops=hops,
                total_hops=len(hops),
                is_circular=False,
                chain_broken=True,
                error=str(e)
            )

        except Exception as e:
            logger.error(f"Error siguiendo redirecciones de {url}: {e}")
            return RedirectChainResult(
                original_url=url,
                final_url=current_url,
                hops=hops,
                total_hops=len(hops),
                is_circular=False,
                chain_broken=True,
                error=str(e)
            )

    def _get_redirect_type(self, status_code: int) -> RedirectType:
        """Determina tipo de redirección."""
        if status_code == 301:
            return RedirectType.PERMANENT
        elif status_code == 302:
            return RedirectType.TEMPORARY
        elif status_code == 303:
            return RedirectType.SEE_OTHER
        elif status_code == 307:
            return RedirectType.TEMPORARY_REDIRECT
        elif status_code == 308:
            return RedirectType.PERMANENT_REDIRECT
        return RedirectType.NONE

    def resolve_short_url(self, url: str) -> Optional[str]:
        """
        Resuelve URL acortada a URL completa.

        Args:
            url: URL acortada (ej: youtu.be/abc123)

        Returns:
            URL completa o None si falla
        """
        result = self.follow(url)
        if not result.error and not result.is_circular:
            return result.final_url
        return None

    def has_redirect(self, url: str) -> bool:
        """Verifica si URL tiene redirecciones."""
        result = self.follow(url)
        return result.total_hops > 0 and not result.is_circular

    def get_redirect_count(self, url: str) -> int:
        """Retorna número de redirecciones."""
        result = self.follow(url)
        return result.total_hops

    def close(self):
        """Cierra sesión HTTP."""
        self._session.close()


def create_redirect_chain(
    max_hops: int = 10,
    timeout: float = 10.0
) -> RedirectChain:
    """Factory function."""
    return RedirectChain(max_hops=max_hops, timeout=timeout)