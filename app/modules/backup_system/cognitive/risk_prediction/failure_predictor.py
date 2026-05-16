"""
Failure Predictor
=================
Predice probabilidad de fallo.
"""

from typing import Dict


class FailurePredictor:
    def __init__(self):
        self.factors = {"low_disk": 0.3, "high_cpu": 0.2, "locked_files": 0.4}

    def predict(self, checks: Dict) -> Dict:
        risk = sum(self.factors.get(k, 0) for k, v in checks.items() if v)
        return {"risk_level": "high" if risk > 0.5 else "medium" if risk > 0.2 else "low", "risk_score": round(risk, 2)}


def get_failure_predictor():
    return FailurePredictor()