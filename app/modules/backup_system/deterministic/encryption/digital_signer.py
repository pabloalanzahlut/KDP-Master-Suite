"""
Digital Signer
==============
Firma digital del manifiesto de backup.
"""

import os
import json
import logging
import hashlib
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DigitalSigner:
    """Firmador digital de manifiestos."""

    def __init__(self, private_key: str = None):
        self.private_key = private_key or os.urandom(32).hex()
        self.public_key = hashlib.sha256(self.private_key.encode()).hexdigest()

    def sign_manifest(self, manifest_data: Dict) -> Dict:
        manifest = manifest_data.copy()
        manifest["signature"] = self._generate_signature(manifest)
        manifest["signed_at"] = datetime.now().isoformat()
        manifest["public_key"] = self.public_key
        return manifest

    def _generate_signature(self, data: Dict) -> str:
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def verify_signature(self, signed_manifest: Dict) -> bool:
        if "signature" not in signed_manifest:
            return False

        stored_sig = signed_manifest["signature"]
        manifest_copy = signed_manifest.copy()
        manifest_copy.pop("signature", None)

        computed_sig = self._generate_signature(manifest_copy)
        return stored_sig == computed_sig

    def save_signed_manifest(self, manifest: Dict, output_file: str) -> bool:
        try:
            signed = self.sign_manifest(manifest)
            with open(output_file, 'w') as f:
                json.dump(signed, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")
            return False


def sign_backup_manifest(manifest: Dict) -> Dict:
    signer = DigitalSigner()
    return signer.sign_manifest(manifest)