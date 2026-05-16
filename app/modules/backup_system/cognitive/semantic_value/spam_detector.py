"""
Spam Detector
=============
Detector de archivos spam o no relevantes.
"""

import os
from typing import List


class SpamDetector:
    def __init__(self):
        self.spam_patterns = ["temp", "cache", "tmp", "backup_old", "trash", "deleted"]

    def is_spam(self, file_path: str) -> bool:
        file_lower = os.path.basename(file_path).lower()
        return any(p in file_lower for p in self.spam_patterns)

    def scan_directory(self, dir_path: str) -> List[str]:
        spam_files = []
        for root, _, files in os.walk(dir_path):
            for f in files:
                full_path = os.path.join(root, f)
                if self.is_spam(full_path):
                    spam_files.append(full_path)
        return spam_files


def get_spam_detector():
    return SpamDetector()