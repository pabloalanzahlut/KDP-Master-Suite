"""
Timeout Predictor
=================
Predice tiempo de operación.
"""

from typing import Dict


class TimeoutPredictor:
    def predict(self, file_count: int, size_mb: float, rate_mbps: float = 10) -> Dict:
        time_sec = size_mb / rate_mbps if rate_mbps > 0 else 0
        return {"estimated_seconds": round(time_sec, 1), "estimated_minutes": round(time_sec / 60, 1)}


def get_timeout_predictor():
    return TimeoutPredictor()