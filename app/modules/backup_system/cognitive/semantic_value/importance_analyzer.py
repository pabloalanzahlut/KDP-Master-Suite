"""
Importance Analyzer
===================
Analiza importancia de archivos basada en contenido.
"""

from typing import Dict, List


class ImportanceAnalyzer:
    def __init__(self):
        self.important_keywords = ["password", "config", "secret", "key", "api", "database", "critical"]

    def analyze(self, content: str) -> Dict:
        content_lower = content.lower()
        found = [kw for kw in self.important_keywords if kw in content_lower]
        score = min(len(found) * 0.2, 1.0)
        return {"score": round(score, 2), "keywords": found, "important": len(found) > 0}


def get_importance_analyzer():
    return ImportanceAnalyzer()