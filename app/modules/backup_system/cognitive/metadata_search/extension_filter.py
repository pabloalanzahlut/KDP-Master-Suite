"""
Extension Filter
================
Filtra archivos por extensión.
"""

from typing import List


class ExtensionFilter:
    def __init__(self):
        self.extensions = {".py", ".json", ".txt", ".db", ".sqlite"}

    def filter(self, files: List[str], extensions: List[str] = None) -> List[str]:
        exts = extensions or list(self.extensions)
        return [f for f in files if any(f.endswith(e) for e in exts)]


def get_extension_filter():
    return ExtensionFilter()