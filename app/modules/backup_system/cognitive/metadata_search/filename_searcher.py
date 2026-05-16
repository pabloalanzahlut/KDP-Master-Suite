"""
Filename Searcher
=================
Búsqueda por nombre de archivo.
"""

import fnmatch
from typing import List


class FilenameSearcher:
    def __init__(self):
        self.files: List[str] = []

    def add_file(self, path: str):
        self.files.append(path)

    def search(self, pattern: str) -> List[str]:
        return [f for f in self.files if fnmatch.fnmatch(f.lower(), f"*{pattern.lower()}*")]


def get_filename_searcher():
    return FilenameSearcher()