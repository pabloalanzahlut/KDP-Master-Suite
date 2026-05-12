"""
Integrity Verifier
==================
Verificador de integridad de red para sync.
"""

import os
import hashlib
import logging
from typing import Tuple


class IntegrityVerifier:
    """Verificador de integridad post-sync."""

    def calculate_file_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_file_integrity(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        if not os.path.exists(local_path):
            return False, "Local file not found"

        local_hash = self.calculate_file_hash(local_path)

        if os.path.exists(remote_path):
            remote_hash = self.calculate_file_hash(remote_path)
            if local_hash == remote_hash:
                return True, "Integrity verified"
            return False, "Hash mismatch"

        return False, "Remote file not found"


def verify_sync_integrity(local: str, remote: str) -> Tuple[bool, str]:
    verifier = IntegrityVerifier()
    return verifier.verify_file_integrity(local, remote)