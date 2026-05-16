"""
Delta Detector
==============
Detector de backups redundantes mediante comparación.
"""

import os
import hashlib
import logging
from typing import Dict, List, Tuple


class DeltaDetector:
    """Detector de backups idénticos."""

    def calculate_backup_hash(self, backup_path: str) -> str:
        hasher = hashlib.sha256()

        if os.path.isfile(backup_path):
            with open(backup_path, 'rb') as f:
                hasher.update(f.read())
        elif os.path.isdir(backup_path):
            for root, _, files in os.walk(backup_path):
                for file in sorted(files):
                    with open(os.path.join(root, file), 'rb') as f:
                        hasher.update(f.read())

        return hasher.hexdigest()

    def find_duplicates(self, backup_dir: str) -> Dict[str, List[str]]:
        hashes = {}
        duplicates = {}

        if not os.path.exists(backup_dir):
            return duplicates

        for f in os.listdir(backup_dir):
            if f.endswith((".zip", ".tar", ".gz")):
                path = os.path.join(backup_dir, f)
                h = self.calculate_backup_hash(path)

                if h in hashes:
                    if h not in duplicates:
                        duplicates[h] = [hashes[h]]
                    duplicates[h].append(f)
                else:
                    hashes[h] = f

        return duplicates


def detect_duplicates(backup_dir: str) -> Dict[str, List[str]]:
    detector = DeltaDetector()
    return detector.find_duplicates(backup_dir)