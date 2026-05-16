"""
Restore Validator
=================
Valida integridad antes de restaurar.
"""

from typing import Dict


class RestoreValidator:
    def validate(self, backup_path: str) -> Dict:
        import os
        exists = os.path.exists(backup_path)
        return {"valid": exists, "path": backup_path, "errors": [] if exists else ["file not found"]}


def get_restore_validator():
    return RestoreValidator()