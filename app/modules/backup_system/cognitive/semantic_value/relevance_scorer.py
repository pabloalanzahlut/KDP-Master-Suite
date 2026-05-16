"""
Relevance Scorer
================
Puntúa relevancia de archivos para backup.
"""

from typing import Dict, List


class RelevanceScorer:
    def __init__(self):
        self.weights = {
            "database": 1.0,
            "config": 0.9,
            "source": 0.8,
            "document": 0.6,
            "media": 0.4,
            "log": 0.2
        }

    def score(self, file_path: str, metadata: Dict) -> Dict:
        category = metadata.get("category", "unknown")
        score = self.weights.get(category, 0.5)
        return {"score": round(score, 2), "category": category}

    def rank_files(self, files: List[Dict]) -> List[Dict]:
        scored = [self.score(f.get("path", ""), f) for f in files]
        return sorted(scored, key=lambda x: x["score"], reverse=True)


def get_relevance_scorer():
    return RelevanceScorer()