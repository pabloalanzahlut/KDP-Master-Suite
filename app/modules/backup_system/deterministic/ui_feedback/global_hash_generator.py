"""
Global Hash Generator
=====================
Generador de hash global para integridad de backup.
"""

import hashlib
import os
import threading
from typing import Dict, List, Optional
from pathlib import Path


class GlobalHashGenerator:
    def __init__(self, algorithm: str = "sha256"):
        self.algorithm = algorithm
        self._lock = threading.Lock()
        self._current_hash = None
        self._files_processed = 0

    def hash_file(self, file_path: str) -> str:
        hasher = hashlib.new(self.algorithm)
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            return f"error:{str(e)}"

    def hash_string(self, data: str) -> str:
        hasher = hashlib.new(self.algorithm)
        hasher.update(data.encode("utf-8"))
        return hasher.hexdigest()

    def generate_manifest_hash(self, file_list: List[str]) -> str:
        hasher = hashlib.new(self.algorithm)
        for f in sorted(file_list):
            file_hash = self.hash_file(f)
            hasher.update(file_hash.encode())
        return hasher.hexdigest()

    def verify_manifest(self, file_list: List[str], expected_hash: str) -> bool:
        actual_hash = self.generate_manifest_hash(file_list)
        return actual_hash == expected_hash

    def update_from_file(self, file_path: str):
        with self._lock:
            file_hash = self.hash_file(file_path)
            hasher = hashlib.new(self.algorithm)
            if self._current_hash:
                hasher.update(self._current_hash.encode())
            hasher.update(file_hash.encode())
            self._current_hash = hasher.hexdigest()
            self._files_processed += 1

    def get_global_hash(self) -> Optional[str]:
        with self._lock:
            return self._current_hash

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "algorithm": self.algorithm,
                "current_hash": self._current_hash,
                "files_processed": self._files_processed
            }

    def reset(self):
        with self._lock:
            self._current_hash = None
            self._files_processed = 0


_global_generator = None


def get_global_hash_generator(algorithm: str = "sha256") -> GlobalHashGenerator:
    global _global_generator
    if _global_generator is None:
        _global_generator = GlobalHashGenerator(algorithm)
    return _global_generator