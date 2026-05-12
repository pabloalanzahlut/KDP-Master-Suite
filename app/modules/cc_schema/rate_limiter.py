"""
CC Schema Monitor - Módulo 10: Limiter de Requests por Dominio
==============================================================
Controla frecuencia de peticiones a youtube.com/vimeo.com con backoff
exponencial para evitar bloqueos por patrones.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import time
import threading
import logging
import hashlib
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DomainStats:
    request_count: int = 0
    error_count: int = 0
    last_request_time: float = 0.0
    last_error_time: float = 0.0
    backoff_until: float = 0.0
    consecutive_errors: int = 0
    total_backoff_seconds: float = 0.0


@dataclass
class RateLimitResult:
    allowed: bool
    wait_seconds: float
    reason: str
    backoff_level: int


class DomainRateLimiter:
    """
    Limiter de Requests por Dominio
    Controla frecuencia de peticiones con backoff exponencial.
    """

    DEFAULT_CONFIG = {
        'youtube.com': {
            'requests_per_minute': 20,
            'requests_per_hour': 180,
            'min_interval': 2.0,
            'max_backoff': 300,
            'initial_backoff': 1.0,
        },
        'vimeo.com': {
            'requests_per_minute': 30,
            'requests_per_hour': 500,
            'min_interval': 1.0,
            'max_backoff': 120,
            'initial_backoff': 0.5,
        },
        'default': {
            'requests_per_minute': 60,
            'requests_per_hour': 2000,
            'min_interval': 0.5,
            'max_backoff': 60,
            'initial_backoff': 0.25,
        }
    }

    def __init__(self, custom_config: Optional[Dict] = None):
        self.config = {**self.DEFAULT_CONFIG, **(custom_config or {})}
        self._domains: Dict[str, DomainStats] = defaultdict(DomainStats)
        self._lock = threading.Lock()
        self._request_timestamps: Dict[str, list] = defaultdict(list)

    def _get_domain_config(self, domain: str) -> Dict:
        """Obtiene configuración para un dominio."""
        for domain_key in self.config:
            if domain_key != 'default' and domain_key in domain:
                return self.config[domain_key]
        return self.config['default']

    def _extract_domain(self, url: str) -> str:
        """Extrae el dominio de una URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            parts = url.split('/')
            if len(parts) >= 3:
                return parts[2].lower()
            return 'unknown'

    def can_make_request(self, url: str) -> RateLimitResult:
        """
        Verifica si se puede hacer un request al dominio.

        Args:
            url: URL del request

        Returns:
            RateLimitResult con decisión y tiempo de espera
        """
        domain = self._extract_domain(url)
        current_time = time.time()

        with self._lock:
            stats = self._domains[domain]
            config = self._get_domain_config(domain)

            if stats.backoff_until > current_time:
                wait_time = stats.backoff_until - current_time
                return RateLimitResult(
                    allowed=False,
                    wait_seconds=wait_time,
                    reason=f"Backing off until {stats.backoff_until}",
                    backoff_level=stats.consecutive_errors
                )

            recent_requests = self._get_recent_request_count(domain, minutes=1)
            if recent_requests >= config['requests_per_minute']:
                oldest = self._request_timestamps[domain][0] if self._request_timestamps[domain] else current_time
                wait_time = max(0, 60 - (current_time - oldest))
                return RateLimitResult(
                    allowed=False,
                    wait_seconds=wait_time,
                    reason=f"Rate limit: {recent_requests}/{config['requests_per_minute']} req/min",
                    backoff_level=0
                )

            hour_requests = self._get_recent_request_count(domain, minutes=60)
            if hour_requests >= config['requests_per_hour']:
                oldest = self._request_timestamps[domain][0] if self._request_timestamps[domain] else current_time
                wait_time = max(0, 3600 - (current_time - oldest))
                return RateLimitResult(
                    allowed=False,
                    wait_seconds=wait_time,
                    reason=f"Rate limit: {hour_requests}/{config['requests_per_hour']} req/hour",
                    backoff_level=0
                )

            min_interval = config['min_interval']
            if stats.last_request_time > 0:
                elapsed = current_time - stats.last_request_time
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    return RateLimitResult(
                        allowed=False,
                        wait_seconds=wait_time,
                        reason=f"Min interval not reached ({elapsed:.1f}s < {min_interval}s)",
                        backoff_level=0
                    )

            return RateLimitResult(
                allowed=True,
                wait_seconds=0.0,
                reason="Request allowed",
                backoff_level=stats.consecutive_errors
            )

    def record_request(self, url: str, success: bool = True, error: Optional[str] = None):
        """
        Registra un request para tracking.

        Args:
            url: URL del request
            success: Si el request fue exitoso
            error: Mensaje de error si falló
        """
        domain = self._extract_domain(url)
        current_time = time.time()

        with self._lock:
            stats = self._domains[domain]
            config = self._get_domain_config(domain)

            self._request_timestamps[domain].append(current_time)
            self._cleanup_timestamps(domain)

            if success:
                stats.request_count += 1
                stats.last_request_time = current_time

                if stats.consecutive_errors > 0:
                    stats.consecutive_errors = 0
                    logger.info(f"Domain {domain} recovered from errors")

            else:
                stats.error_count += 1
                stats.last_error_time = current_time
                stats.consecutive_errors += 1

                initial = config['initial_backoff']
                max_backoff = config['max_backoff']
                backoff_seconds = min(initial * (2 ** stats.consecutive_errors), max_backoff)

                stats.backoff_until = current_time + backoff_seconds
                stats.total_backoff_seconds += backoff_seconds

                logger.warning(
                    f"Domain {domain} backoff: {backoff_seconds}s "
                    f"(level {stats.consecutive_errors}, error: {error})"
                )

    def _get_recent_request_count(self, domain: str, minutes: int) -> int:
        """Cuenta requests en los últimos N minutos."""
        current_time = time.time()
        cutoff = current_time - (minutes * 60)

        timestamps = self._request_timestamps.get(domain, [])
        return sum(1 for ts in timestamps if ts > cutoff)

    def _cleanup_timestamps(self, domain: str):
        """Limpia timestamps antiguos para evitar memoria leaks."""
        current_time = time.time()
        cutoff = current_time - 7200

        self._request_timestamps[domain] = [
            ts for ts in self._request_timestamps[domain] if ts > cutoff
        ]

    def wait_if_needed(self, url: str) -> float:
        """
        Espera si es necesario antes de hacer un request.

        Args:
            url: URL del request

        Returns:
            Tiempo de espera real
        """
        result = self.can_make_request(url)

        if not result.allowed:
            logger.info(f"Rate limit hit for {url}: waiting {result.wait_seconds:.1f}s")
            time.sleep(result.wait_seconds)

        return result.wait_seconds

    def get_domain_stats(self, domain: str) -> Dict:
        """Retorna estadísticas de un dominio."""
        with self._lock:
            stats = self._domains.get(domain, DomainStats())
            return {
                'domain': domain,
                'total_requests': stats.request_count,
                'total_errors': stats.error_count,
                'last_request': datetime.fromtimestamp(stats.last_request_time).isoformat() if stats.last_request_time else None,
                'last_error': datetime.fromtimestamp(stats.last_error_time).isoformat() if stats.last_error_time else None,
                'backoff_level': stats.consecutive_errors,
                'backoff_until': datetime.fromtimestamp(stats.backoff_until).isoformat() if stats.backoff_until > time.time() else None,
                'total_backoff_seconds': stats.total_backoff_seconds,
                'requests_last_minute': self._get_recent_request_count(domain, 1),
                'requests_last_hour': self._get_recent_request_count(domain, 60),
            }

    def reset_domain(self, domain: str):
        """Resetea contadores de un dominio."""
        with self._lock:
            if domain in self._domains:
                self._domains[domain] = DomainStats()
            if domain in self._request_timestamps:
                self._request_timestamps[domain] = []

    def reset_all(self):
        """Resetea todos los dominios."""
        with self._lock:
            self._domains.clear()
            self._request_timestamps.clear()

    def get_all_stats(self) -> Dict[str, Dict]:
        """Retorna estadísticas de todos los dominios."""
        with self._lock:
            return {domain: self.get_domain_stats(domain) for domain in self._domains.keys()}


class AdaptiveRateLimiter(DomainRateLimiter):
    """
    Rate limiter adaptativo que ajusta automáticamente los límites
    basado en respuestas de error 429 y otros indicadores.
    """

    ERROR_THRESHOLD = 3
    SUCCESS_THRESHOLD = 10

    def __init__(self, custom_config: Optional[Dict] = None):
        super().__init__(custom_config)
        self._adaptive_config: Dict[str, Dict] = {}
        self._consecutive_successes: Dict[str, int] = defaultdict(int)

    def record_request(self, url: str, success: bool = True, error: Optional[str] = None):
        """Registra request y adapta límites si es necesario."""
        domain = self._extract_domain(url)

        with self._lock:
            if success:
                self._consecutive_successes[domain] = self._consecutive_successes.get(domain, 0) + 1

                if self._consecutive_successes[domain] >= self.SUCCESS_THRESHOLD:
                    self._increase_rate_limit(domain)

            else:
                self._consecutive_successes[domain] = 0

                if '429' in str(error) or 'rate' in str(error).lower():
                    self._decrease_rate_limit(domain)

        super().record_request(url, success, error)

    def _increase_rate_limit(self, domain: str):
        """Aumenta límites si hay éxito consistente."""
        if domain not in self._adaptive_config:
            self._adaptive_config[domain] = {'multiplier': 1.0}

        current = self._adaptive_config[domain]['multiplier']
        new_multiplier = min(current + 0.1, 2.0)
        self._adaptive_config[domain]['multiplier'] = new_multiplier

        logger.info(f"Domain {domain} rate limit increased: {new_multiplier:.1f}x")

    def _decrease_rate_limit(self, domain: str):
        """Disminuye límites si hay errores de rate limit."""
        if domain not in self._adaptive_config:
            self._adaptive_config[domain] = {'multiplier': 1.0}

        current = self._adaptive_config[domain]['multiplier']
        new_multiplier = max(current - 0.2, 0.5)
        self._adaptive_config[domain]['multiplier'] = new_multiplier

        logger.warning(f"Domain {domain} rate limit decreased: {new_multiplier:.1f}x")


def create_limiter(adaptive: bool = False) -> DomainRateLimiter:
    """
    Factory function para crear el limiter.
    """
    if adaptive:
        return AdaptiveRateLimiter()
    return DomainRateLimiter()


def quick_throttle(url: str) -> Tuple[bool, float]:
    """
    Función de conveniencia para throttle rápido.
    Retorna (allowed, wait_seconds)
    """
    limiter = DomainRateLimiter()
    result = limiter.can_make_request(url)
    return result.allowed, result.wait_seconds