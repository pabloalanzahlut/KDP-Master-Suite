"""
Service Reactivator
===================
Reinicio de servicios post-backup.
"""

import threading
import time
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ServiceState:
    name: str
    status: str
    last_start: Optional[datetime]
    restart_count: int = 0


class ServiceReactivator:
    def __init__(self):
        self.services: Dict[str, ServiceState] = {}
        self._lock = threading.Lock()
        self._pending_restarts: List[Callable] = []

    def register_service(self, name: str):
        with self._lock:
            if name not in self.services:
                self.services[name] = ServiceState(
                    name=name,
                    status="stopped",
                    last_start=None,
                    restart_count=0
                )

    def mark_running(self, name: str):
        with self._lock:
            if name in self.services:
                self.services[name].status = "running"
                self.services[name].last_start = datetime.now()

    def mark_stopped(self, name: str):
        with self._lock:
            if name in self.services:
                self.services[name].status = "stopped"

    def needs_restart(self, name: str) -> bool:
        with self._lock:
            svc = self.services.get(name)
            if not svc:
                return False
            return svc.status == "stopped" and svc.last_start is not None

    def trigger_restart(self, name: str, restart_callback: Callable[[], None]) -> bool:
        with self._lock:
            svc = self.services.get(name)
            if not svc:
                return False
            svc.restart_count += 1
        restart_callback()
        return True

    def get_service_status(self, name: str) -> Optional[Dict]:
        with self._lock:
            svc = self.services.get(name)
            if not svc:
                return None
            return {
                "name": svc.name,
                "status": svc.status,
                "last_start": svc.last_start.isoformat() if svc.last_start else None,
                "restart_count": svc.restart_count
            }

    def get_all_status(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "name": s.name,
                    "status": s.status,
                    "last_start": s.last_start.isoformat() if s.last_start else None,
                    "restart_count": s.restart_count
                }
                for s in self.services.values()
            ]

    def auto_reactivate(self, name: str, restart_callback: Callable[[], None]) -> bool:
        if self.needs_restart(name):
            return self.trigger_restart(name, restart_callback)
        return False


_global_reactivator = None


def get_service_reactivator() -> ServiceReactivator:
    global _global_reactivator
    if _global_reactivator is None:
        _global_reactivator = ServiceReactivator()
    return _global_reactivator