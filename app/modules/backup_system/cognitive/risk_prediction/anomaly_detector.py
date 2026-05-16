"""
Anomaly Detector
================
Detecta anomalías en patrones de backup.
"""

from typing import Dict, List
import os


class AnomalyDetector:
    def __init__(self):
        self.baseline_size_mb = 500
        self.baseline_files = 100

    def detect(self, current_size_mb: float, current_files: int) -> Dict:
        size_anomaly = current_size_mb > self.baseline_size_mb * 2
        file_anomaly = current_files > self.baseline_files * 2
        return {"anomaly": size_anomaly or file_anomaly, "size_warning": size_anomaly, "file_warning": file_anomaly}


def get_anomaly_detector():
    return AnomalyDetector()