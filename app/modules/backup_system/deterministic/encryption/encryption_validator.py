"""
Encryption Validator
====================
Validador de integridad del cifrado.
"""

import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class EncryptionValidator:
    """Validador de cifrado."""

    def validate_encrypted_file(self, file_path: str) -> Tuple[bool, str]:
        if not os.path.exists(file_path):
            return False, "Archivo no existe"

        if not file_path.endswith(".enc"):
            return False, "No es archivo cifrado"

        try:
            with open(file_path, 'rb') as f:
                data = f.read(24)

            if len(data) < 12:
                return False, "Archivo demasiado pequeño"

            return True, "Archivo cifrado válido"

        except Exception as e:
            return False, f"Error: {e}"

    def verify_decryptable(self, encrypted_file: str, key: bytes) -> Tuple[bool, str]:
        from app.modules.backup_system.deterministic.encryption.aes_encryptor import AESEncryptor
        enc = AESEncryptor(key)
        test_file = encrypted_file + ".test"

        success, _ = enc.decrypt_file(encrypted_file, test_file)

        if os.path.exists(test_file):
            os.remove(test_file)

        return success, "Verificación completada"


def validate_encryption(file_path: str) -> Tuple[bool, str]:
    validator = EncryptionValidator()
    return validator.validate_encrypted_file(file_path)