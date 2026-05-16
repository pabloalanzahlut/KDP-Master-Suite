"""
Backup Priority Classifier
==========================
Clasificador de prioridad de backup usando IA.
"""

import os
import json
from typing import Dict, Optional, List
from pathlib import Path


class BackupPriorityClassifier:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._priority_cache: Dict[str, float] = {}

    def classify_priority(self, file_path: str, metadata: Dict) -> Dict:
        file_name = os.path.basename(file_path)
        ext = Path(file_path).suffix.lower()

        priority_scores = {
            ".db": 1.0,
            ".json": 0.9,
            ".sqlite": 1.0,
            ".kv": 0.85,
            ".txt": 0.5,
            ".log": 0.3,
            ".py": 0.7,
            ".md": 0.6
        }

        score = priority_scores.get(ext, 0.5)
        size_mb = metadata.get("size_mb", 0)
        if size_mb > 100:
            score *= 0.8

        priority = "high" if score > 0.8 else "medium" if score > 0.5 else "low"

        return {
            "priority": priority,
            "score": round(score, 2),
            "file": file_name
        }

    def batch_classify(self, files: List[Dict]) -> List[Dict]:
        results = []
        for f in files:
            result = self.classify_priority(f.get("path", ""), f)
            results.append(result)
        return results


_global_classifier = None


def get_priority_classifier(model_path: Optional[str] = None) -> BackupPriorityClassifier:
    global _global_classifier
    if _global_classifier is None:
        _global_classifier = BackupPriorityClassifier(model_path)
    return _global_classifier