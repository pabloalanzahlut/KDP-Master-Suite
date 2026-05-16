"""
AES Encryptor
=============
Cifrado AES-256-GCM del paquete final del backup.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

KEY_SIZE = 32
NONCE_SIZE = 12


class AESEncryptor:
    """Cifrador AES-256-GCM."""

    def __init__(self, key: bytes = None):
        if key is None:
            self.key = os.urandom(KEY_SIZE)
        else:
            if len(key) != KEY_SIZE:
                raise ValueError(f"Key must be {KEY_SIZE} bytes")
            self.key = key
        self.aesgcm = AESGCM(self.key)

    def encrypt_file(self, input_file: str, output_file: str = None) -> Tuple[bool, str]:
        if not os.path.exists(input_file):
            return False, "Archivo no existe"

        if output_file is None:
            output_file = input_file + ".enc"

        try:
            nonce = os.urandom(NONCE_SIZE)

            with open(input_file, 'rb') as f:
                plaintext = f.read()

            ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)

            with open(output_file, 'wb') as f:
                f.write(nonce)
                f.write(ciphertext)

            return True, f"Cifrado: {output_file}"

        except Exception as e:
            logger.error(f"Error encrypting {input_file}: {e}")
            return False, str(e)

    def decrypt_file(self, input_file: str, output_file: str = None) -> Tuple[bool, str]:
        if not os.path.exists(input_file):
            return False, "Archivo cifrado no existe"

        if output_file is None:
            output_file = input_file.replace(".enc", ".dec")

        try:
            with open(input_file, 'rb') as f:
                nonce = f.read(NONCE_SIZE)
                ciphertext = f.read()

            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)

            with open(output_file, 'wb') as f:
                f.write(plaintext)

            return True, f"Descifrado: {output_file}"

        except Exception as e:
            logger.error(f"Error decrypting {input_file}: {e}")
            return False, str(e)

    def get_key(self) -> bytes:
        return self.key

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode())


def encrypt_file(input_file: str, password: str = None) -> Tuple[bool, str]:
    if password:
        salt = os.urandom(16)
        key = AESEncryptor.derive_key_from_password(password, salt)
        with open(input_file + ".salt", 'wb') as f:
            f.write(salt)
    else:
        key = None

    enc = AESEncryptor(key)
    return enc.encrypt_file(input_file)


def decrypt_file(input_file: str, password: str = None) -> Tuple[bool, str]:
    salt_file = input_file + ".salt"
    if password and os.path.exists(salt_file):
        with open(salt_file, 'rb') as f:
            salt = f.read()
        key = AESEncryptor.derive_key_from_password(password, salt)
        enc = AESEncryptor(key)
    else:
        enc = AESEncryptor()

    return enc.decrypt_file(input_file)