"""
SHA256 Hasher
=============
Generador de hash SHA-256 individual por archivo.
Genera checksum para cada archivo respaldado.
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_BUFFER_SIZE = 1024 * 1024


class SHA256Hasher:
    """Generador de hashes SHA-256."""

    def __init__(self, buffer_size: int = DEFAULT_BUFFER_SIZE):
        self.buffer_size = buffer_size
        self.hashes_computed = []

    def compute_file_hash(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        if not os.path.exists(file_path):
            return False, "Archivo no existe", None

        try:
            sha256_hash = hashlib.sha256()

            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.buffer_size)
                    if not chunk:
                        break
                    sha256_hash.update(chunk)

            hash_value = sha256_hash.hexdigest()

            self.hashes_computed.append({
                "file": file_path,
                "hash": hash_value
            })

            logger.info(f"Hash computed for {file_path}: {hash_value[:16]}...")
            return True, hash_value, hash_value

        except Exception as e:
            logger.error(f"Error computing hash for {file_path}: {e}")
            return False, str(e), None

    def compute_directory_hashes(self, directory: str) -> Dict[str, str]:
        hashes = {}

        if not os.path.exists(directory):
            return hashes

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                success, hash_value, _ = self.compute_file_hash(file_path)
                if success:
                    hashes[file_path] = hash_value

        return hashes

    def verify_file_hash(self, file_path: str, expected_hash: str) -> Tuple[bool, str]:
        success, computed_hash, _ = self.compute_file_hash(file_path)

        if not success:
            return False, computed_hash

        if computed_hash.lower() == expected_hash.lower():
            return True, "Hash válido"

        return False, f"Hash no coincide: {computed_hash[:16]}... vs {expected_hash[:16]}..."

    def generate_manifest(self, files: List[str], output_path: str = None) -> Dict:
        manifest = {
            "version": "1.0.0",
            "algorithm": "SHA-256",
            "files": {}
        }

        for file_path in files:
            success, hash_value, _ = self.compute_file_hash(file_path)
            if success:
                rel_path = os.path.basename(file_path)
                manifest["files"][rel_path] = hash_value

        if output_path:
            import json
            with open(output_path, 'w') as f:
                json.dump(manifest, f, indent=2)

        return manifest


def compute_hash(file_path: str) -> Tuple[bool, str, Optional[str]]:
    hasher = SHA256Hasher()
    return hasher.compute_file_hash(file_path)


def verify_hash(file_path: str, expected_hash: str) -> Tuple[bool, str]:
    hasher = SHA256Hasher()
    return hasher.verify_file_hash(file_path, expected_hash)