"""
Restore Rollback
================
Rollback si restauración falla.
"""

from typing import Dict


class RestoreRollback:
    def rollback(self, original_state: Dict) -> Dict:
        return {"status": "rolled_back", "restored_state": original_state}


def get_restore_rollback():
    return RestoreRollback()