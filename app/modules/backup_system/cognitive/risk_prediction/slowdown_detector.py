"""
Slowdown Detector
=================
Detiene backups si el sistema se ralentiza.
"""

from typing import Dict


class SlowdownDetector:
    def detect(self, current_rps: float, baseline_rps: float) -> Dict:
        ratio = current_rps / baseline_rps if baseline_rps > 0 else 1
        return {"slowdown": ratio < 0.5, "ratio": round(ratio, 2)}


def get_slowdown_detector():
    return SlowdownDetector()