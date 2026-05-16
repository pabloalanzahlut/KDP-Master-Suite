"""
Date Range Searcher
==================
Búsqueda por rango de fechas.
"""

import os
from typing import List, Dict
from datetime import datetime, timedelta


class DateRangeSearcher:
    def search(self, files: List[str], start_date: str, end_date: str) -> List[Dict]:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        results = []
        for f in files:
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(f))
                if start <= mtime <= end:
                    results.append({"path": f, "modified": mtime.isoformat()})
            except:
                pass
        return results


def get_date_range_searcher():
    return DateRangeSearcher()