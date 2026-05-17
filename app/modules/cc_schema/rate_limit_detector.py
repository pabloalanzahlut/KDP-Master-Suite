"""
Rate Limit Detector - Módulo 11 de URL Intelligence
====================================================
Detecta respuestas 429 y calcula tiempo de espera antes de reintentar.
Evita baneos temporales por exceso de peticiones.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    domain: str
    requests_made: int
    requests_allowed: int
    reset_time: Optional[datetime]
    retry_after_seconds: int
    is_rate_limited: bool


class RateLimitDetector:
    """
    Detector de rate limiting 429.
    Calcula tiempo de espera y registra historial de requests.
    """

    DEFAULT_LIMIT = 100
    DEFAULT_WINDOW = 60

    def __init__(
        self,
        requests_limit: int = DEFAULT_LIMIT,
        time_window: int = DEFAULT_WINDOW,
        max_retry_after: int = 300
    ):
        self.requests_limit = requests_limit
        self.time_window = time_window
        self.max_retry_after = max_retry_after
        self._history: Dict[str, list] = {}
        self._lock = Lock()

    def record_request(self, domain: str) -> RateLimitInfo:
        """Registra request y verifica rate limit."""
        with self._lock:
            now = time.time()
            if domain not in self._history:
                self._history[domain] = []

            self._history[domain] = [
                t for t in self._history[domain]
                if now - t < self.time_window
            ]

            self._history[domain].append(now)

            requests_made = len(self._history[domain])
            is_limited = requests_made >= self.requests_limit

            return RateLimitInfo(
                domain=domain,
                requests_made=requests_made,
                requests_allowed=self.requests_limit,
                reset_time=datetime.now() + timedelta(seconds=self.time_window),
                retry_after_seconds=self._calculate_retry_after(domain),
                is_rate_limited=is_limited
            )

    def _calculate_retry_after(self, domain: str) -> int:
        """Calcula segundos de espera."""
        if domain not in self._history:
            return 0

        now = time.time()
        oldest = min(self._history[domain])
        elapsed = now - oldest

        if elapsed < self.time_window:
            remaining = self.time_window - int(elapsed)
            return min(remaining, self.max_retry_after)

        return 0

    def check_status(self, domain: str) -> RateLimitInfo:
        """Verifica estado de rate limit."""
        return self.record_request(domain)

    def reset_domain(self, domain: str):
        """Resetea contador para dominio."""
        with self._lock:
            if domain in self._history:
                self._history[domain] = []

    def get_wait_time(self, domain: str) -> int:
        """Obtiene tiempo de espera recomendado."""
        return self._calculate_retry_after(domain)

    def should_retry(self, domain: str) -> bool:
        """Determina si debe reintentar."""
        info = self.check_status(domain)
        return not info.is_rate_limited


def create_rate_limit_detector(
    requests_limit: int = 100,
    time_window: int = 60
) -> RateLimitDetector:
    """Factory function."""
    return RateLimitDetector(
        requests_limit=requests_limit,
        time_window=time_window
    )