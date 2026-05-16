"""
Secure Keyring
==============
Almacenamiento seguro de claves en OS Keyring.
"""

import os
import logging
import json
from typing import Optional, Dict

logger = logging.getLogger(__name__)

KEYRING_FILE = os.path.expanduser("~/.kdp_master_keyring")


class SecureKeyring:
    """Gestor de keyring seguro."""

    def __init__(self, keyring_path: str = None):
        self.keyring_path = keyring_path or KEYRING_FILE
        self._ensure_keyring()

    def _ensure_keyring(self):
        if not os.path.exists(self.keyring_path):
            os.makedirs(os.path.dirname(self.keyring_path), exist_ok=True)

    def store_key(self, service: str, key: str) -> bool:
        try:
            keys = self._load_keys()
            keys[service] = key
            with open(self.keyring_path, 'w') as f:
                json.dump(keys, f)
            return True
        except Exception as e:
            logger.error(f"Error storing key: {e}")
            return False

    def retrieve_key(self, service: str) -> Optional[str]:
        try:
            keys = self._load_keys()
            return keys.get(service)
        except Exception as e:
            logger.error(f"Error retrieving key: {e}")
            return None

    def _load_keys(self) -> Dict:
        if os.path.exists(self.keyring_path):
            with open(self.keyring_path, 'r') as f:
                return json.load(f)
        return {}

    def delete_key(self, service: str) -> bool:
        try:
            keys = self._load_keys()
            if service in keys:
                del keys[service]
                with open(self.keyring_path, 'w') as f:
                    json.dump(keys, f)
            return True
        except Exception as e:
            logger.error(f"Error deleting key: {e}")
            return False


def store_encryption_key(service: str, key: str) -> bool:
    kr = SecureKeyring()
    return kr.store_key(service, key)


def retrieve_encryption_key(service: str) -> Optional[str]:
    kr = SecureKeyring()
    return kr.retrieve_key(service)