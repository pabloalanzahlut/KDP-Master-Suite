"""
Headless Mode Manager
=====================
Gestor de modo headless para operaciones sin UI.
"""

import os
import sys
import threading
from typing import Dict, Optional, Callable


class HeadlessModeManager:
    def __init__(self):
        self._is_headless = not sys.stdout.isatty()
        self._callbacks: Dict[str, Callable] = {}
        self._log_file = None
        self._lock = threading.Lock()

    def is_headless(self) -> bool:
        return self._is_headless

    def set_headless(self, value: bool):
        self._is_headless = value

    def enable_logging(self, log_path: str):
        with self._lock:
            self._log_file = open(log_path, "a", encoding="utf-8")

    def disable_logging(self):
        with self._lock:
            if self._log_file:
                self._log_file.close()
                self._log_file = None

    def log(self, message: str):
        with self._lock:
            if self._log_file:
                self._log_file.write(f"{message}\n")
                self._log_file.flush()

    def output(self, message: str):
        if self._is_headless:
            self.log(message)
        else:
            print(message)

    def register_callback(self, event: str, callback: Callable):
        self._callbacks[event] = callback

    def trigger_event(self, event: str, *args, **kwargs):
        cb = self._callbacks.get(event)
        if cb:
            cb(*args, **kwargs)


_global_manager = None


def get_headless_mode_manager() -> HeadlessModeManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = HeadlessModeManager()
    return _global_manager