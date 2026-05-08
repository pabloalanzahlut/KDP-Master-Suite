import threading

class AppState:
    """Estado global thread-safe para comunicación UI ↔ Backend ↔ Dashboard"""
    _lock = threading.Lock()
    _state = {
        "monitor_running": False,
        "last_sync": None,
        "error_count": 0,
        "queue_size": 0
    }

    @classmethod
    def get(cls, key, default=None):
        with cls._lock:
            return cls._state.get(key, default)

    @classmethod
    def set(cls, key, value):
        with cls._lock:
            cls._state[key] = value

    @classmethod
    def increment(cls, key, amount=1):
        with cls._lock:
            cls._state[key] = cls._state.get(key, 0) + amount