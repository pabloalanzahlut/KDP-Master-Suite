"""
Key Derivation
=============
Gestor de derivación de claves (PBKDF2).
"""

import os
import logging
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Optional

DEFAULT_ITERATIONS = 100000
SALT_SIZE = 32


class KeyDerivation:
    """Gestor de derivación de claves."""

    def __init__(self, iterations: int = DEFAULT_ITERATIONS):
        self.iterations = iterations

    def generate_salt(self) -> bytes:
        return os.urandom(SALT_SIZE)

    def derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def verify_key(self, password: str, salt: bytes, expected_key: bytes) -> bool:
        derived = self.derive_key(password, salt)
        return derived == expected_key

    def create_key_package(self, password: str) -> dict:
        salt = self.generate_salt()
        key = self.derive_key(password, salt)
        return {
            "salt": salt.hex(),
            "key": key.hex(),
            "iterations": self.iterations
        }


def derive_key_from_password(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    kd = KeyDerivation()
    if salt is None:
        salt = kd.generate_salt()
    key = kd.derive_key(password, salt)
    return key, salt