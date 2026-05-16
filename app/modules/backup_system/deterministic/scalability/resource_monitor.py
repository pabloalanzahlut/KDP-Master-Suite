"""
Resource Monitor
================
Monitor de recursos del sistema para backup.
"""

import threading
import time
import os
from typing import Dict, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class ResourceMonitor:
    def __init__(self):
        self._lock = threading.Lock()
        self._history: list = []
        self._max_history = 100

    def get_current_stats(self) -> Dict:
        if PSUTIL_AVAILABLE:
            try:
                return {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "timestamp": time.time()
                }
            except Exception:
                pass
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "timestamp": time.time()
        }

    def record_stats(self):
        with self._lock:
            stats = self.get_current_stats()
            self._history.append(stats)
            if len(self._history) > self._max_history:
                self._history.pop(0)

    def get_average_stats(self) -> Optional[Dict]:
        with self._lock:
            if not self._history:
                return None
            return {
                "avg_cpu": sum(s["cpu_percent"] for s in self._history) / len(self._history),
                "avg_memory": sum(s["memory_percent"] for s in self._history) / len(self._history)
            }

    def is_resource_available(self, max_cpu: float = 80, max_memory: float = 85) -> bool:
        stats = self.get_current_stats()
        return stats["cpu_percent"] < max_cpu and stats["memory_percent"] < max_memory


_global_monitor = None


def get_resource_monitor() -> ResourceMonitor:
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
    return _global_monitor