"""
HealthChecker - Módulo 43
=========================
Monitor de salud de cada módulo del sistema.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    module_name: str
    status: HealthStatus
    timestamp: float
    response_time_ms: float
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    overall_status: HealthStatus
    timestamp: float
    modules: Dict[str, HealthCheck]
    total_modules: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int


class HealthChecker:
    """
    Monitor de salud del sistema.
    Verifica estado de módulos críticos.
    """

    DEFAULT_TIMEOUT_MS = 5000
    DEGRADED_THRESHOLD_MS = 2000

    def __init__(self):
        self._modules: Dict[str, Callable] = {}
        self._health_cache: Dict[str, HealthCheck] = {}
        self._cache_ttl = 30
        self._last_full_check = 0

    def register_module(self, name: str, check_func: Callable):
        """
        Registra módulo para monitoreo.

        Args:
            name: Nombre del módulo
            check_func: Función que retorna dict {status, details}
        """
        self._modules[name] = check_func
        logger.info(f"HealthChecker: Registrado módulo '{name}'")

    def check_module(self, name: str) -> HealthCheck:
        """Verifica salud de un módulo específico."""
        now = time.time()

        cached = self._health_cache.get(name)
        if cached and (now - cached.timestamp) < self._cache_ttl:
            return cached

        check_func = self._modules.get(name)
        if not check_func:
            return HealthCheck(
                module_name=name,
                status=HealthStatus.UNKNOWN,
                timestamp=now,
                response_time_ms=0,
                error="Módulo no registrado"
            )

        start_time = time.time()
        try:
            result = check_func()
            response_time = (time.time() - start_time) * 1000

            status = HealthStatus(result.get('status', 'healthy'))
            if status == HealthStatus.HEALTHY and response_time > self.DEGRADED_THRESHOLD_MS:
                status = HealthStatus.DEGRADED

            health = HealthCheck(
                module_name=name,
                status=status,
                timestamp=now,
                response_time_ms=response_time,
                details=result.get('details', {})
            )

        except Exception as e:
            health = HealthCheck(
                module_name=name,
                status=HealthStatus.UNHEALTHY,
                timestamp=now,
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )

        self._health_cache[name] = health
        return health

    def check_all(self, force: bool = False) -> SystemHealth:
        """Verifica salud de todos los módulos."""
        now = time.time()

        if not force and (now - self._last_full_check) < self._cache_ttl:
            return self._get_cached_health()

        self._last_full_check = now
        modules = {}

        for name in self._modules:
            modules[name] = self.check_module(name)

        healthy = sum(1 for h in modules.values() if h.status == HealthStatus.HEALTHY)
        degraded = sum(1 for h in modules.values() if h.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for h in modules.values() if h.status == HealthStatus.UNHEALTHY)

        if unhealthy > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall = HealthStatus.DEGRADED
        elif healthy == len(modules):
            overall = HealthStatus.HEALTHY
        else:
            overall = HealthStatus.UNKNOWN

        return SystemHealth(
            overall_status=overall,
            timestamp=now,
            modules=modules,
            total_modules=len(modules),
            healthy_count=healthy,
            degraded_count=degraded,
            unhealthy_count=unhealthy
        )

    def _get_cached_health(self) -> SystemHealth:
        """Retorna salud desde cache."""
        modules = {}
        now = time.time()

        for name, cached in self._health_cache.items():
            modules[name] = cached

        healthy = sum(1 for h in modules.values() if h.status == HealthStatus.HEALTHY)
        degraded = sum(1 for h in modules.values() if h.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for h in modules.values() if h.status == HealthStatus.UNHEALTHY)

        overall = HealthStatus.HEALTHY
        if unhealthy > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall = HealthStatus.DEGRADED

        return SystemHealth(
            overall_status=overall,
            timestamp=now,
            modules=modules,
            total_modules=len(modules),
            healthy_count=healthy,
            degraded_count=degraded,
            unhealthy_count=unhealthy
        )

    def get_module_health(self, name: str) -> HealthStatus:
        """Obtiene estado de un módulo."""
        health = self.check_module(name)
        return health.status

    def is_module_healthy(self, name: str) -> bool:
        """Verifica si módulo está saludable."""
        return self.check_module(name).status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    def get_unhealthy_modules(self) -> List[str]:
        """Retorna lista de módulos no saludables."""
        health = self.check_all()
        return [
            name for name, check in health.modules.items()
            if check.status == HealthStatus.UNHEALTHY
        ]

    def invalidate_cache(self):
        """Invalida cache."""
        self._health_cache.clear()


health_checker_instance = HealthChecker()


def create_health_checker() -> HealthChecker:
    """Factory function."""
    return HealthChecker()