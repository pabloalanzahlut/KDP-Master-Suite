"""
CircuitBreaker - Módulo 42
==========================
Previene cascadas de errores cuando un servicio falla repetidamente.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    call_timeout_seconds: float = 5.0


@dataclass
class CircuitMetrics:
    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    state: CircuitState = CircuitState.CLOSED


class CircuitBreaker:
    """
    Circuit Breaker pattern para prevenir cascadas de errores.
    Monitoriza fallos y abre el circuito cuando se excede el umbral.
    """

    def __init__(self, name: str, config: Optional[CircuitConfig] = None):
        self.name = name
        self.config = config or CircuitConfig()
        self._metrics = CircuitMetrics()
        self._lock = Lock()
        self._callable: Optional[Callable] = None

    def set_callable(self, callable_func: Callable):
        """Setea la función a proteger."""
        self._callable = callable_func

    def call(self, *args, **kwargs):
        """
        Ejecuta función con protección de circuit breaker.

        Returns:
            Resultado de la función o raise CircuitOpenError
        """
        with self._lock:
            self._check_state_transition()

            if self._metrics.state == CircuitState.OPEN:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")

        try:
            result = self._callable(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _check_state_transition(self):
        """Verifica transiciones de estado."""
        if self._metrics.state == CircuitState.OPEN:
            time_since_open = time.time() - self._metrics.last_failure_time
            if time_since_open >= self.config.timeout_seconds:
                self._metrics.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit {self.name}: OPEN → HALF_OPEN")

    def _on_success(self):
        """Maneja éxito."""
        with self._lock:
            self._metrics.successes += 1
            self._metrics.last_success_time = time.time()

            if self._metrics.state == CircuitState.HALF_OPEN:
                if self._metrics.successes >= self.config.success_threshold:
                    self._metrics.state = CircuitState.CLOSED
                    self._metrics.failures = 0
                    self._metrics.successes = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN → CLOSED")

    def _on_failure(self):
        """Maneja fallo."""
        with self._lock:
            self._metrics.failures += 1
            self._metrics.last_failure_time = time.time()

            if self._metrics.state == CircuitState.HALF_OPEN:
                self._metrics.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: HALF_OPEN → OPEN (failure)")
            elif self._metrics.state == CircuitState.CLOSED:
                if self._metrics.failures >= self.config.failure_threshold:
                    self._metrics.state = CircuitState.OPEN
                    logger.warning(f"Circuit {self.name}: CLOSED → OPEN (threshold reached)")

    def get_state(self) -> CircuitState:
        """Retorna estado actual."""
        with self._lock:
            self._check_state_transition()
            return self._metrics.state

    def is_closed(self) -> bool:
        """Verifica si está cerrado."""
        return self.get_state() == CircuitState.CLOSED

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas."""
        with self._lock:
            return {
                'name': self.name,
                'state': self._metrics.state.value,
                'failures': self._metrics.failures,
                'successes': self._metrics.successes,
                'last_failure': self._metrics.last_failure_time,
                'last_success': self._metrics.last_success_time
            }

    def reset(self):
        """Resetea circuit breaker."""
        with self._lock:
            self._metrics = CircuitMetrics()
            logger.info(f"Circuit {self.name}: RESET")


class CircuitOpenError(Exception):
    """Excepción cuando el circuit breaker está abierto."""
    pass


class CircuitBreakerRegistry:
    """Registro global de circuit breakers."""

    _breakers: Dict[str, CircuitBreaker] = {}
    _lock = Lock()

    @classmethod
    def register(cls, name: str, breaker: CircuitBreaker):
        """Registra un circuit breaker."""
        with cls._lock:
            cls._breakers[name] = breaker

    @classmethod
    def get(cls, name: str) -> Optional[CircuitBreaker]:
        """Obtiene circuit breaker por nombre."""
        return cls._breakers.get(name)

    @classmethod
    def get_all_states(cls) -> Dict[str, str]:
        """Obtiene estados de todos los breakers."""
        with cls._lock:
            return {name: cb.get_state().value for name, cb in cls._breakers.items()}

    @classmethod
    def reset_all(cls):
        """Resetea todos los breakers."""
        with cls._lock:
            for cb in cls._breakers.values():
                cb.reset()


def create_circuit_breaker(name: str, config: Optional[CircuitConfig] = None) -> CircuitBreaker:
    """Factory function para crear circuit breaker."""
    breaker = CircuitBreaker(name, config)
    CircuitBreakerRegistry.register(name, breaker)
    return breaker