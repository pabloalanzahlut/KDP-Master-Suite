"""
Toast Notifier
=============
Sistema de notificaciones toast para UI.
"""

from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import threading


@dataclass
class ToastMessage:
    title: str
    message: str
    level: str
    timestamp: datetime
    duration: int = 5


class ToastNotifier:
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history: List[ToastMessage] = []
        self._lock = threading.Lock()

    def notify(self, title: str, message: str, level: str = "info", duration: int = 5) -> ToastMessage:
        toast = ToastMessage(
            title=title,
            message=message,
            level=level,
            timestamp=datetime.now(),
            duration=duration
        )
        with self._lock:
            self.history.append(toast)
            if len(self.history) > self.max_history:
                self.history.pop(0)
        return toast

    def success(self, title: str, message: str) -> ToastMessage:
        return self.notify(title, message, "success", 5)

    def error(self, title: str, message: str) -> ToastMessage:
        return self.notify(title, message, "error", 8)

    def warning(self, title: str, message: str) -> ToastMessage:
        return self.notify(title, message, "warning", 6)

    def info(self, title: str, message: str) -> ToastMessage:
        return self.notify(title, message, "info", 4)

    def get_history(self, limit: int = 10) -> List[Dict]:
        with self._lock:
            recent = self.history[-limit:]
            return [
                {
                    "title": t.title,
                    "message": t.message,
                    "level": t.level,
                    "timestamp": t.timestamp.isoformat()
                }
                for t in recent
            ]

    def clear_history(self):
        with self._lock:
            self.history.clear()


_global_notifier = None


def get_toast_notifier() -> ToastNotifier:
    global _global_notifier
    if _global_notifier is None:
        _global_notifier = ToastNotifier()
    return _global_notifier