"""
Cache Indexer
=============
Indexa archivos en caché para búsqueda rápida.
"""

from typing import Dict, List


class CacheIndexer:
    def __init__(self):
        self.cache: Dict[str, Dict] = {}

    def index(self, path: str, metadata: Dict):
        self.cache[path] = metadata

    def get(self, path: str) -> Dict:
        return self.cache.get(path, {})

    def search(self, key: str, value: str) -> List[str]:
        return [p for p, m in self.cache.items() if m.get(key) == value]


def get_cache_indexer():
    return CacheIndexer()