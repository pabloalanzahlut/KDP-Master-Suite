"""
Signature Validator
===================
Validador de firma digital al iniciar.
"""

import os
import json
import logging
import hashlib
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


class SignatureValidator:
    """Validador de firmas digitales."""

    def validate_manifest_signature(self, manifest_path: str) -> Tuple[bool, str]:
        if not os.path.exists(manifest_path):
            return False, "Manifiesto no existe"

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            if "signature" not in manifest:
                return False, "Sin firma"

            if "public_key" not in manifest:
                return False, "Sin clave pública"

            stored_sig = manifest["signature"]
            manifest_copy = manifest.copy()
            manifest_copy.pop("signature", None)

            content = json.dumps(manifest_copy, sort_keys=True)
            computed_sig = hashlib.sha256(content.encode()).hexdigest()

            if stored_sig == computed_sig:
                return True, "Firma válida"

            return False, "Firma inválida"

        except Exception as e:
            return False, f"Error: {e}"

    def verify_backup_integrity(self, backup_dir: str) -> Tuple[bool, str]:
        manifest_path = os.path.join(backup_dir, "manifest.json")

        if not os.path.exists(manifest_path):
            return False, "Sin manifisto"

        return self.validate_manifest_signature(manifest_path)


def verify_signature(manifest_path: str) -> Tuple[bool, str]:
    validator = SignatureValidator()
    return validator.validate_manifest_signature(manifest_path)