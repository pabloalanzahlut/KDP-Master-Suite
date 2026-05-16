"""
Copyright Detector
==================
Detecta contenido con copyright.
"""

from typing import Dict, List


class CopyrightDetector:
    def __init__(self):
        self.markers = ["©", "copyright", "rights reserved", "license"]

    def detect(self, content: str) -> Dict:
        found = [m for m in self.markers if m.lower() in content.lower()]
        return {"has_copyright": len(found) > 0, "markers": found}


def get_copyright_detector():
    return CopyrightDetector()