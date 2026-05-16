"""
CPU Predictor
=============
Predice uso de CPU durante backup.
"""

from typing import Dict


class CPUPredictor:
    def predict(self, file_count: int, total_size_mb: float) -> Dict:
        estimated = min(file_count * 0.5 + total_size_mb * 0.01, 100)
        return {"predicted_cpu": round(estimated, 1), "risk": "low" if estimated < 50 else "medium" if estimated < 80 else "high"}


def get_cpu_predictor():
    return CPUPredictor()