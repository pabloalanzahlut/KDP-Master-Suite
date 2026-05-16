"""
Ransomware Detector
===================
Detector de actividad de ransomware en ruta de backup.
"""

import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

RANSOMWARE_EXTENSIONS = [
    ".locked", ".encrypted", ".crypt", ".crypto", ".ransom",
    ".pay", ".btc", ".wallet", ".encrypted", ".lock"
]

RANSOMWARE_PATTERNS = [
    "ransom", "encrypt", "pay", "bitcoin", "btc", "unlock"
]


class RansomwareDetector:
    """Detector de ransomware."""

    def scan_directory(self, directory: str) -> List[Dict]:
        threats = []

        if not os.path.exists(directory):
            return threats

        for entry in os.scandir(directory):
            if entry.is_file():
                ext = os.path.splitext(entry.name)[1].lower()
                if ext in RANSOMWARE_EXTENSIONS:
                    threats.append({
                        "type": "extension",
                        "file": entry.name,
                        "path": entry.path
                    })

                name_lower = entry.name.lower()
                for pattern in RANSOMWARE_PATTERNS:
                    if pattern in name_lower:
                        threats.append({
                            "type": "pattern",
                            "file": entry.name,
                            "path": entry.path,
                            "pattern": pattern
                        })

        return threats

    def is_safe_for_backup(self, directory: str) -> bool:
        threats = self.scan_directory(directory)
        return len(threats) == 0

    def validate_destination(self, dest_path: str) -> tuple:
        if self.is_safe_for_backup(dest_path):
            return True, "Destino seguro"

        threats = self.scan_directory(dest_path)
        return False, f"Advertencia: {len(threats)} posibles amenazas detectadas"


def detect_ransomware(directory: str) -> List[Dict]:
    detector = RansomwareDetector()
    return detector.scan_directory(directory)