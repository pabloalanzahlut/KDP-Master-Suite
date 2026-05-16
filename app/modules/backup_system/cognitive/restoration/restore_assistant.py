"""
Restore Assistant
================
Asistente de restauración de backups.
"""

from typing import Dict, List


class RestoreAssistant:
    def suggest_restore_point(self, backups: List[Dict]) -> Dict:
        if not backups:
            return {"suggested": None, "reason": "no backups"}
        latest = max(backups, key=lambda x: x.get("date", ""))
        return {"suggested": latest.get("path"), "reason": "latest backup", "date": latest.get("date")}


def get_restore_assistant():
    return RestoreAssistant()