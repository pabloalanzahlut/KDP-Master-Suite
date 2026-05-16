"""
Semantic Indexer
================
Crea índice semántico de archivos para búsqueda.
"""

from typing import Dict, List
import os


class SemanticIndexer:
    def __init__(self):
        self.index: Dict[str, List[str]] = {}

    def index_file(self, file_path: str, tags: List[str]):
        for tag in tags:
            if tag not in self.index:
                self.index[tag] = []
            self.index[tag].append(file_path)

    def search(self, query: str) -> List[str]:
        return self.index.get(query.lower(), [])

    def get_all_tags(self) -> List[str]:
        return list(self.index.keys())


_global_indexer = None


def get_semantic_indexer() -> SemanticIndexer:
    global _global_indexer
    if _global_indexer is None:
        _global_indexer = SemanticIndexer()
    return _global_indexer