"""
Content Deduplicator
====================
Elimina contenido duplicado usando hashing.
"""

import hashlib
from typing import Dict, List, Set


class ContentDeduplicator:
    def __init__(self):
        self.seen_hashes: Set[str] = set()

    def get_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def is_duplicate(self, content: str) -> bool:
        h = self.get_hash(content)
        if h in self.seen_hashes:
            return True
        self.seen_hashes.add(h)
        return False

    def deduplicate(self, items: List[str]) -> List[str]:
        unique = []
        for item in items:
            if not self.is_duplicate(item):
                unique.append(item)
        return unique

    def reset(self):
        self.seen_hashes.clear()


_global_dedup = None


def get_content_deduplicator() -> ContentDeduplicator:
    global _global_dedup
    if _global_dedup is None:
        _global_dedup = ContentDeduplicator()
    return _global_dedup