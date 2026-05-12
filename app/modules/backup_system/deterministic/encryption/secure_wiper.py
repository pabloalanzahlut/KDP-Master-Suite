"""
Secure Wiper
============
Protocolo de borrado seguro de archivos temporales.
"""

import os
import logging
import random
from typing import Tuple

logger = logging.getLogger(__name__)

PASSES = 3


class SecureWiper:
    """Borrador seguro de archivos temporales."""

    def secure_delete(self, file_path: str, passes: int = PASSES) -> Tuple[bool, str]:
        if not os.path.exists(file_path):
            return True, "Archivo no existe"

        try:
            file_size = os.path.getsize(file_path)

            with open(file_path, 'r+b') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

            os.remove(file_path)
            return True, "Archivo eliminado de forma segura"

        except Exception as e:
            logger.error(f"Error secure deleting: {e}")
            return False, str(e)

    def wipe_directory(self, directory: str) -> Tuple[bool, int]:
        deleted = 0
        failed = 0

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                success, _ = self.secure_delete(file_path)
                if success:
                    deleted += 1
                else:
                    failed += 1

        return failed == 0, deleted


def secure_wipe(file_path: str) -> Tuple[bool, str]:
    wiper = SecureWiper()
    return wiper.secure_delete(file_path)