"""
Pattern Recognizer
==================
Reconoce patrones en nombres de archivos.
"""

import re
from typing import Dict, List, Pattern


class PatternRecognizer:
    def __init__(self):
        self.patterns = {
            "date": r"\d{4}[-_]\d{2}[-_]\d{2}",
            "version": r"v\d+\.\d+",
            "timestamp": r"\d{10,13}",
            "hash": r"[a-f0-9]{32,64}"
        }

    def recognize(self, filename: str) -> Dict:
        found = {}
        for name, pattern in self.patterns.items():
            if re.search(pattern, filename):
                found[name] = True
        return found

    def categorize(self, filename: str) -> str:
        patterns = self.recognize(filename)
        if patterns.get("date"):
            return "dated"
        if patterns.get("version"):
            return "versioned"
        if patterns.get("hash"):
            return "hashed"
        return "regular"


_global_recognizer = None


def get_pattern_recognizer() -> PatternRecognizer:
    global _global_recognizer
    if _global_recognizer is None:
        _global_recognizer = PatternRecognizer()
    return _global_recognizer