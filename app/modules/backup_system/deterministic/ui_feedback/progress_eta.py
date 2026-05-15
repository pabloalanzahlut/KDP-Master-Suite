"""
Progress ETA
============
Indicador de progreso con tiempo剩余 real.
"""

import time
from typing import Dict, Optional


class ProgressETA:
    def __init__(self):
        self.start_time = None
        self.total_items = 0
        self.processed_items = 0

    def start(self, total: int):
        self.start_time = time.time()
        self.total_items = total
        self.processed_items = 0

    def update(self, processed: int):
        self.processed_items = processed

    def get_eta(self) -> Dict:
        if not self.start_time or self.processed_items == 0:
            return {"eta_seconds": 0, "percent": 0}

        elapsed = time.time() - self.start_time
        rate = self.processed_items / elapsed
        remaining = self.total_items - self.processed_items
        eta = remaining / rate if rate > 0 else 0

        return {
            "eta_seconds": int(eta),
            "eta_formatted": f"{int(eta // 60)}m {int(eta % 60)}s",
            "percent": round(self.processed_items / self.total_items * 100, 1),
            "processed": self.processed_items,
            "total": self.total_items
        }


def calculate_eta(processed: int, total: int, elapsed: float) -> Dict:
    if processed == 0:
        return {"eta": "calculating...", "percent": 0}

    rate = processed / elapsed
    remaining = total - processed
    eta = remaining / rate

    return {
        "eta_seconds": int(eta),
        "eta_formatted": f"{int(eta // 60)}m {int(eta % 60)}s",
        "percent": round(processed / total * 100, 1)
    }