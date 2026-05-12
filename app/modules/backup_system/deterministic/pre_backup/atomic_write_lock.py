"""
Atomic Write Lock
=================
Bloqueo atómico de operaciones de escritura durante el backup.
Pausa colas de descarga y monitoreo de canales.
"""

import logging
import threading
import time
from typing import Optional, Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AtomicWriteLock:
    """Gestor de bloqueo atómico para operaciones de backup."""

    _instance = None
    _lock = threading.Lock()
    _write_lock = threading.RLock()
    _active = False
    _paused_operations = []

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.logger = logging.getLogger(__name__)

    def acquire(self, timeout: float = 30.0) -> bool:
        acquired = self._write_lock.acquire(timeout=timeout)
        if acquired:
            AtomicWriteLock._active = True
            self.logger.info("Atomic write lock acquired")
        else:
            self.logger.warning("Failed to acquire atomic write lock")
        return acquired

    def release(self) -> None:
        try:
            self._write_lock.release()
            AtomicWriteLock._active = False
            self.logger.info("Atomic write lock released")
        except RuntimeError:
            pass

    @contextmanager
    def locked(self, timeout: float = 30.0):
        acquired = self.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError("Could not acquire atomic write lock")
        try:
            yield self
        finally:
            self.release()

    def is_active(self) -> bool:
        return AtomicWriteLock._active

    def register_pause_callback(self, callback: Callable[[], Any]) -> None:
        with self._lock:
            AtomicWriteLock._paused_operations.append(callback)

    def execute_with_lock(self, func: Callable, *args, **kwargs) -> Any:
        with self.locked():
            self.logger.info(f"Executing {func.__name__} with atomic lock")
            return func(*args, **kwargs)


def acquire_atomic_lock(timeout: float = 30.0) -> bool:
    lock = AtomicWriteLock()
    return lock.acquire(timeout)


def release_atomic_lock() -> None:
    lock = AtomicWriteLock()
    lock.release()


def is_lock_active() -> bool:
    lock = AtomicWriteLock()
    return lock.is_active()


@contextmanager
def atomic_backup_context(timeout: float = 30.0):
    lock = AtomicWriteLock()
    with lock.locked(timeout):
        yield lock