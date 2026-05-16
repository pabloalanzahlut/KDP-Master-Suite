"""
Restore Planner
================
Planifica restauración de archivos.
"""

from typing import Dict, List


class RestorePlanner:
    def plan(self, backup_files: List[str], target_dir: str) -> Dict:
        return {"files": len(backup_files), "target": target_dir, "steps": ["extract", "verify", "copy"]}


def get_restore_planner():
    return RestorePlanner()