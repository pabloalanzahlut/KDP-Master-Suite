"""
RateLimitEnforcer - Módulo 41
=============================
Fuerza límites de rate entre módulos para prevenir sobrecarga.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    calls_per_second: float = 10.0
    calls_per_minute: float = 100.0
    calls_per_hour: float = 1000.0
    burst_size: int = 5
    enabled: bool = True


@dataclass
class RateLimitMetrics:
    total_calls: int = 0
    allowed_calls: int = 0
    rejected_calls: int = 0
    last_call_time: float = 0.0
    last_rejection_time: float = 0.0


class RateLimitEnforcer:
    """
    Limitador de rate que enforce límites entre módulos.
    Implementa token bucket algorithm.
    """

    def __init__(self, name: str, config: Optional[RateLimitConfig] = None):
        self.name = name
        self.config = config or RateLimitConfig()
        self._metrics = RateLimitMetrics()
        self._tokens: Dict[str, float] = {}
        self._last_refill: Dict[str, float] = {}
        self._lock = Lock()
        self._init_tokens()

    def _init_tokens(self):
        """Inicializa tokens para cada nivel."""
        self._tokens = {
            'second': self.config.burst_size,
            'minute': self.config.calls_per_minute,
            'hour': self.config.calls_per_hour
        }
        now = time.time()
        self._last_refill = {
            'second': now,
            'minute': now,
            'hour': now
        }

    def allow(self) -> bool:
        """
        Verifica si se permite una llamada.

        Returns:
            True si se permite, False si se rechaza
        """
        if not self.config.enabled:
            return True

        with self._lock:
            now = time.time()
            self._refill_tokens(now)

            if self._tokens['second'] >= 1:
                self._tokens['second'] -= 1
                self._metrics.total_calls += 1
                self._metrics.allowed_calls += 1
                self._metrics.last_call_time = now
                return True

            self._metrics.total_calls += 1
            self._metrics.rejected_calls += 1
            self._metrics.last_rejection_time = now
            return False

    def _refill_tokens(self, now: float):
        """Rellena tokens según tiempo transcurrido."""
        for level, rate in [('second', self.config.calls_per_second),
                           ('minute', self.config.calls_per_minute),
                           ('hour', self.config.calls_per_hour)]:
            elapsed = now - self._last_refill[level]
            refill_amount = elapsed * rate
            max_tokens = self.config.burst_size if level == 'second' else rate
            self._tokens[level] = min(max_tokens, self._tokens[level] + refill_amount)
            self._last_refill[level] = now

    def wait_if_needed(self, max_wait_ms: float = 1000) -> bool:
        """
        Espera si se agotó el rate limit.

        Args:
            max_wait_ms: Máximo tiempo a esperar en ms

        Returns:
            True si se permitió, False si timeout
        """
        if self.allow():
            return True

        start = time.time()
        while time.time() - start < max_wait_ms / 1000:
            time.sleep(0.05)
            if self.allow():
                return True

        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas."""
        with self._lock:
            return {
                'name': self.name,
                'total_calls': self._metrics.total_calls,
                'allowed_calls': self._metrics.allowed_calls,
                'rejected_calls': self._metrics.rejected_calls,
                'allow_rate': self._metrics.allowed_calls / max(self._metrics.total_calls, 1),
                'last_call': self._metrics.last_call_time,
                'last_rejection': self._metrics.last_rejection_time,
                'tokens': self._tokens.copy()
            }

    def reset(self):
        """Resetea limitador."""
        with self._lock:
            self._metrics = RateLimitMetrics()
            self._init_tokens()


class RateLimitRegistry:
    """Registro global de rate limiters."""

    _limiters: Dict[str, RateLimitEnforcer] = {}
    _lock = Lock()

    @classmethod
    def register(cls, name: str, limiter: RateLimitEnforcer):
        """Registra un limitador."""
        with cls._lock:
            cls._limiters[name] = limiter

    @classmethod
    def get(cls, name: str) -> Optional[RateLimitEnforcer]:
        """Obtiene limitador por nombre."""
        return cls._limiters.get(name)

    @classmethod
    def create_and_register(cls, name: str, config: Optional[RateLimitConfig] = None) -> RateLimitEnforcer:
        """Crea y registra un limitador."""
        limiter = RateLimitEnforcer(name, config)
        cls.register(name, limiter)
        return limiter

    @classmethod
    def allow_all(cls) -> bool:
        """Permite llamada en todos los limitadores."""
        with cls._lock:
            return all(limiter.allow() for limiter in cls._limiters.values())

    @classmethod
    def reset_all(cls):
        """Resetea todos los limitadores."""
        with cls._lock:
            for limiter in cls._limiters.values():
                limiter.reset()


def create_rate_limiter(name: str, config: Optional[RateLimitConfig] = None) -> RateLimitEnforcer:
    """Factory function."""
    limiter = RateLimitEnforcer(name, config)
    RateLimitRegistry.register(name, limiter)
    return limiter