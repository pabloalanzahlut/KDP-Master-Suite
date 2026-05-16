"""
Tag Based Search
================
Búsqueda por tags/metadata.
"""

from typing import List, Dict


class TagBasedSearch:
    def __init__(self):
        self.tags: Dict[str, List[str]] = {}

    def add_tag(self, file_path: str, tag: str):
        if tag not in self.tags:
            self.tags[tag] = []
        self.tags[tag].append(file_path)

    def search(self, tag: str) -> List[str]:
        return self.tags.get(tag, [])

    def search_multiple(self, tags: List[str]) -> List[str]:
        result = set()
        for t in tags:
            result.update(self.tags.get(t, []))
        return list(result)


def get_tag_based_search():
    return TagBasedSearch()