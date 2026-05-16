"""
Change Detector
===============
Detecta cambios entre versiones de archivos.
"""

from typing import Dict, List
import hashlib


class ChangeDetector:
    def detect(self, old: str, new: str) -> Dict:
        old_hash = hashlib.md5(old.encode()).hexdigest()
        new_hash = hashlib.md5(new.encode()).hexdigest()
        return {"changed": old_hash != new_hash, "old_hash": old_hash, "new_hash": new_hash}


def get_change_detector():
    return ChangeDetector()