"""
Quality Scorer
==============
Puntúa calidad de backup.
"""

from typing import Dict


class QualityScorer:
    def score(self, backup: Dict) -> Dict:
        score = 0
        if backup.get("verified"): score += 0.3
        if backup.get("encrypted"): score += 0.2
        if backup.get("compressed"): score += 0.2
        if backup.get("complete"): score += 0.3
        return {"quality": round(score, 2), "grade": "A" if score > 0.8 else "B" if score > 0.6 else "C"}


def get_quality_scorer():
    return QualityScorer()