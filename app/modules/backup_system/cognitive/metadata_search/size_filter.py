"""
Size Filter
===========
Filtra archivos por tamaño.
"""

from typing import List, Dict


class SizeFilter:
    def filter(self, files: List[str], min_mb: float = 0, max_mb: float = 999999) -> List[str]:
        import os
        result = []
        for f in files:
            try:
                size_mb = os.path.getsize(f) / (1024*1024)
                if min_mb <= size_mb <= max_mb:
                    result.append(f)
            except:
                pass
        return result


def get_size_filter():
    return SizeFilter()