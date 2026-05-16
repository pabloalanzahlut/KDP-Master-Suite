"""
Cache Manager
=============
Gestor de caché para operaciones de backup.
"""

import threading
import time
from typing import Any, Optional, Dict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    key: str
    value: Any
    timestamp: float
    ttl: float


class CacheManager:
    def __init__(self, max_entries: int = 1000, default_ttl: float = 3600):
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                self._misses += 1
                return None
            if time.time() - entry.timestamp > entry.ttl:
                del self._cache[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        with self._lock:
            if len(self._cache) >= self.max_entries:
                oldest = min(self._cache.values(), key=lambda e: e.timestamp)
                del self._cache[oldest.key]
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl
            )

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "entries": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate * 100, 2)
            }


_global_cache = None


def get_cache_manager(max_entries: int = 1000, default_ttl: float = 3600) -> CacheManager:
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager(max_entries, default_ttl)
    return _global_cache