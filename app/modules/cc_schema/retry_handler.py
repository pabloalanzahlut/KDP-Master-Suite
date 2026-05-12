"""
CC Schema Monitor - Módulo 17: Sistema de Reintentos con Backoff
=================================================================
Reintenta fetch de subtítulos con espera exponencial (1s, 2s, 4s, 8s)
si falla por rate-limit o timeout.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import time
import logging
import threading
from typing import Optional, Callable, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"


@dataclass
class RetryResult:
    success: bool
    attempts: int
    total_time: float
    error: Optional[str]
    last_error_type: Optional[str]


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.1
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retry_on: Optional[List[str]] = None


class RetryHandler:
    """
    Sistema de Reintentos con Backoff
    Reintenta operaciones con espera exponencial.
    """

    DEFAULT_CONFIG = RetryConfig()

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or self.DEFAULT_CONFIG
        self._lock = threading.Lock()
        self._stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'total_attempts': 0,
        }

    def execute(self, func: Callable, *args, **kwargs) -> Tuple[Any, RetryResult]:
        """
        Ejecuta función con reintentos.

        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados

        Returns:
            (result, RetryResult)
        """
        start_time = time.time()
        attempts = 0
        last_error = None
        last_error_type = None

        while attempts < self.config.max_attempts:
            attempts += 1
            self._stats['total_attempts'] += 1

            try:
                result = func(*args, **kwargs)

                if isinstance(result, tuple) and len(result) == 2:
                    success, error = result[0], result[1] if len(result) > 1 else None
                    if not success and attempts < self.config.max_attempts:
                        if self._should_retry(error):
                            delay = self._calculate_delay(attempts)
                            time.sleep(delay)
                            continue
                        else:
                            last_error = error
                            last_error_type = type(error).__name__ if error else None
                            break
                    elif not success:
                        last_error = error
                        last_error_type = type(error).__name__ if error else None

                self._stats['successful_retries'] += 1
                total_time = time.time() - start_time

                return result, RetryResult(
                    success=True,
                    attempts=attempts,
                    total_time=total_time,
                    error=None,
                    last_error_type=None
                )

            except Exception as e:
                last_error = str(e)
                last_error_type = type(e).__name__

                if not self._should_retry_error(e) or attempts >= self.config.max_attempts:
                    break

                delay = self._calculate_delay(attempts)
                time.sleep(delay)

        self._stats['failed_retries'] += 1
        total_time = time.time() - start_time

        return None, RetryResult(
            success=False,
            attempts=attempts,
            total_time=total_time,
            error=last_error,
            last_error_type=last_error_type
        )

    def _should_retry(self, error: Any) -> bool:
        """Determina si debe reintentar basado en el error."""
        if self.config.retry_on is None:
            return True

        error_str = str(error).lower()
        for pattern in self.config.retry_on:
            if pattern.lower() in error_str:
                return True
        return False

    def _should_retry_error(self, error: Exception) -> bool:
        """Determina si debe reintentar una excepción."""
        retry_exceptions = ['Timeout', 'RateLimit', 'Connection', 'HTTP']
        error_name = type(error).__name__

        for pattern in retry_exceptions:
            if pattern in error_name:
                return True

        error_str = str(error).lower()
        for pattern in ['timeout', 'rate limit', 'connection', '429', '503', 'connection reset']:
            if pattern in error_str:
                return True

        return False

    def _calculate_delay(self, attempt: int) -> float:
        """Calcula delay para el intento dado."""
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self.config.base_delay * self._fibonacci(attempt)
        else:
            delay = self.config.base_delay

        delay = min(delay, self.config.max_delay)

        if self.config.jitter > 0:
            jitter_amount = delay * self.config.jitter
            delay += (hash(str(time.time())) % 1000) / 1000 * jitter_amount * 2 - jitter_amount

        return delay

    def _fibonacci(self, n: int) -> int:
        """Calcula n-ésimo número de Fibonacci."""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b

    def get_stats(self) -> dict:
        """Retorna estadísticas."""
        with self._lock:
            return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        with self._lock:
            self._stats = {
                'total_retries': 0,
                'successful_retries': 0,
                'failed_retries': 0,
                'total_attempts': 0,
            }


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[List[str]] = None
):
    """
    Decorador para reintentar funciones con backoff exponencial.

    Args:
        max_attempts: Número máximo de intentos
        base_delay: Delay base en segundos
        max_delay: Delay máximo en segundos
        exponential_base: Base del exponente
        retry_on: Patrones de error que justifican reintento
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                retry_on=retry_on
            ))
            result, retry_result = handler.execute(func, *args, **kwargs)
            return result
        return wrapper
    return decorator


def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Función de conveniencia para reintentar con backoff.

    Args:
        func: Función a ejecutar
        max_attempts: Número máximo de intentos
        base_delay: Delay base en segundos

    Returns:
        Resultado de la función
    """
    config = RetryConfig(max_attempts=max_attempts, base_delay=base_delay, **kwargs)
    handler = RetryHandler(config)
    result, _ = handler.execute(func)
    return result


def quick_retry(func: Callable, *args, max_attempts: int = 3, **kwargs) -> Any:
    """
    Función de conveniencia para retry rápido.
    """
    return retry_with_backoff(func, max_attempts=max_attempts)(*args, **kwargs)