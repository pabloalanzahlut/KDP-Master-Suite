"""
Connection Pool Manager - Módulo 10 de URL Intelligence
===================================================
Gestiona pool de conexiones HTTP reutilizables.
Mejora rendimiento en verificaciones masivas.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from threading import Lock
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    total_connections: int
    active_connections: int
    idle_connections: int
    connections_created: int
    connections_reused: int
    requests_sent: int
    failed_requests: int


class ConnectionPool:
    """
    Gestor de pool de conexiones HTTP con reutilización.
    Configurable para diferentes workloads de validación de URLs.
    """

    DEFAULT_POOL_SIZE = 10
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 0.3

    def __init__(
        self,
        pool_size: int = DEFAULT_POOL_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        pool_block: bool = False
    ):
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.pool_block = pool_block

        self._session: Optional[requests.Session] = None
        self._lock = Lock()
        self._stats = {
            'created': 0,
            'reused': 0,
            'requests': 0,
            'failed': 0
        }

    def get_session(self) -> requests.Session:
        """
        Obtiene sesión HTTP configurada del pool.

        Returns:
            Session de requests configurada
        """
        with self._lock:
            if self._session is None:
                self._session = self._create_session()
                self._stats['created'] += 1
                logger.info(f"Creada nueva sesión HTTP con pool_size={self.pool_size}")
            else:
                self._stats['reused'] += 1
            return self._session

    def _create_session(self) -> requests.Session:
        """Crea sesión HTTP con pool de conexiones y retry strategy."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(
            pool_connections=self.pool_size,
            pool_maxsize=self.pool_size,
            max_retries=retry_strategy,
            pool_block=self.pool_block
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def head(self, url: str, **kwargs) -> requests.Response:
        """
        Ejecuta request HEAD usando el pool.

        Args:
            url: URL destino
            **kwargs: Argumentos adicionales para requests

        Returns:
            Response de requests
        """
        session = self.get_session()
        self._stats['requests'] += 1
        try:
            response = session.head(url, **kwargs)
            return response
        except Exception as e:
            self._stats['failed'] += 1
            raise

    def get(self, url: str, **kwargs) -> requests.Response:
        """Ejecuta request GET usando el pool."""
        session = self.get_session()
        self._stats['requests'] += 1
        try:
            response = session.get(url, **kwargs)
            return response
        except Exception as e:
            self._stats['failed'] += 1
            raise

    def post(self, url: str, **kwargs) -> requests.Response:
        """Ejecuta request POST usando el pool."""
        session = self.get_session()
        self._stats['requests'] += 1
        try:
            response = session.post(url, **kwargs)
            return response
        except Exception as e:
            self._stats['failed'] += 1
            raise

    def get_stats(self) -> PoolStats:
        """Retorna estadísticas del pool."""
        with self._lock:
            return PoolStats(
                total_connections=self.pool_size,
                active_connections=1 if self._session else 0,
                idle_connections=self.pool_size - (1 if self._session else 0),
                connections_created=self._stats['created'],
                connections_reused=self._stats['reused'],
                requests_sent=self._stats['requests'],
                failed_requests=self._stats['failed']
            )

    def close(self):
        """Cierra el pool de conexiones."""
        with self._lock:
            if self._session:
                self._session.close()
                self._session = None
                logger.info("Pool de conexiones cerrado")

    def reset_stats(self):
        """Resetea estadísticas."""
        with self._lock:
            self._stats = {
                'created': 0,
                'reused': 0,
                'requests': 0,
                'failed': 0
            }

    def __enter__(self):
        """Context manager entry."""
        self.get_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class ConnectionPoolRegistry:
    """Registro global de connection pools."""

    _pools: Dict[str, ConnectionPool] = {}
    _lock = Lock()

    @classmethod
    def get_or_create(
        cls,
        name: str,
        pool_size: int = 10,
        max_retries: int = 3
    ) -> ConnectionPool:
        """Obtiene pool existente o crea nuevo."""
        with cls._lock:
            if name not in cls._pools:
                cls._pools[name] = ConnectionPool(
                    pool_size=pool_size,
                    max_retries=max_retries
                )
                logger.info(f"Creado pool '{name}' con pool_size={pool_size}")
            return cls._pools[name]

    @classmethod
    def get(cls, name: str) -> Optional[ConnectionPool]:
        """Obtiene pool por nombre."""
        with cls._lock:
            return cls._pools.get(name)

    @classmethod
    def close_all(cls):
        """Cierra todos los pools."""
        with cls._lock:
            for pool in cls._pools.values():
                pool.close()
            cls._pools.clear()
            logger.info("Todos los pools de conexiones cerrados")


def create_connection_pool(
    pool_size: int = 10,
    max_retries: int = 3
) -> ConnectionPool:
    """Factory function."""
    return ConnectionPool(pool_size=pool_size, max_retries=max_retries)