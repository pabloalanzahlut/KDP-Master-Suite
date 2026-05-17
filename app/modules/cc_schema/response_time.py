"""
Response Time Measurer - Módulo 13 de URL Intelligence
======================================================
Mide latencia de respuesta del servidor en milisegundos.
Alertar si servidor responde >5s (posible bloqueo).

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import time
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseSpeed(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    SLOW = "slow"
    VERY_SLOW = "very_slow"


@dataclass
class ResponseTimeResult:
    url: str
    response_time_ms: float
    speed_category: ResponseSpeed
    is_blocked: bool
    timestamp: float
    error: Optional[str]


class ResponseTimeMeasurer:
    """
    Medidor de tiempo de respuesta HTTP.
    Clasifica velocidad y detecta servidores lentos/bloqueados.
    """

    THRESHOLDS = {
        ResponseSpeed.EXCELLENT: 200,
        ResponseSpeed.GOOD: 500,
        ResponseSpeed.ACCEPTABLE: 1000,
        ResponseSpeed.SLOW: 3000,
    }

    BLOCK_THRESHOLD = 5000

    def __init__(
        self,
        timeout: float = 10.0,
        slow_threshold_ms: int = 3000
    ):
        self.timeout = timeout
        self.slow_threshold_ms = slow_threshold_ms
        self._history: Dict[str, list] = {}

    def measure(self, url: str) -> ResponseTimeResult:
        """
        Mide tiempo de respuesta de URL.

        Args:
            url: URL a medir

        Returns:
            ResponseTimeResult con timing y clasificación
        """
        start_time = time.time()

        try:
            response = requests.head(url, timeout=self.timeout, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000

            speed = self._classify_speed(response_time)
            is_blocked = response_time > self.BLOCK_THRESHOLD

            self._record_measurement(url, response_time)

            return ResponseTimeResult(
                url=url,
                response_time_ms=response_time,
                speed_category=speed,
                is_blocked=is_blocked,
                timestamp=time.time(),
                error=None
            )

        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return ResponseTimeResult(
                url=url,
                response_time_ms=response_time,
                speed_category=ResponseSpeed.VERY_SLOW,
                is_blocked=True,
                timestamp=time.time(),
                error=f"Timeout después de {self.timeout}s"
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ResponseTimeResult(
                url=url,
                response_time_ms=response_time,
                speed_category=ResponseSpeed.VERY_SLOW,
                is_blocked=True,
                timestamp=time.time(),
                error=str(e)
            )

    def _classify_speed(self, response_time_ms: float) -> ResponseSpeed:
        """Clasifica velocidad según tiempo."""
        if response_time_ms <= self.THRESHOLDS[ResponseSpeed.EXCELLENT]:
            return ResponseSpeed.EXCELLENT
        elif response_time_ms <= self.THRESHOLDS[ResponseSpeed.GOOD]:
            return ResponseSpeed.GOOD
        elif response_time_ms <= self.THRESHOLDS[ResponseSpeed.ACCEPTABLE]:
            return ResponseSpeed.ACCEPTABLE
        elif response_time_ms <= self.THRESHOLDS[ResponseSpeed.SLOW]:
            return ResponseSpeed.SLOW
        else:
            return ResponseSpeed.VERY_SLOW

    def _record_measurement(self, url: str, response_time: float):
        """Registra medición en historial."""
        if url not in self._history:
            self._history[url] = []
        self._history[url].append(response_time)

        if len(self._history[url]) > 100:
            self._history[url] = self._history[url][-100:]

    def get_average_time(self, url: str) -> Optional[float]:
        """Obtiene tiempo promedio de URL."""
        if url in self._history and self._history[url]:
            return sum(self._history[url]) / len(self._history[url])
        return None

    def is_consistently_slow(self, url: str, threshold: int = 3) -> bool:
        """Verifica si URL es consistentemente lenta."""
        if url not in self._history or len(self._history[url]) < threshold:
            return False

        recent = self._history[url][-threshold:]
        avg = sum(recent) / len(recent)
        return avg > self.slow_threshold_ms

    def clear_history(self, url: Optional[str] = None):
        """Limpia historial."""
        if url:
            self._history.pop(url, None)
        else:
            self._history.clear()


def create_response_time_measurer(
    timeout: float = 10.0,
    slow_threshold_ms: int = 3000
) -> ResponseTimeMeasurer:
    """Factory function."""
    return ResponseTimeMeasurer(
        timeout=timeout,
        slow_threshold_ms=slow_threshold_ms
    )