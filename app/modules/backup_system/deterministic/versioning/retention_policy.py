"""
Retention Policy
================
Política de retención rotativa (GFS - Grandfather-Father-Son).
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List


class RetentionPolicy:
    """Política de retención GFS."""

    def __init__(self, daily: int = 7, weekly: int = 4, monthly: int = 12):
        self.daily_keep = daily
        self.weekly_keep = weekly
        self.monthly_keep = monthly

    def analyze_backups(self, backup_dir: str) -> Dict:
        backups = []

        if not os.path.exists(backup_dir):
            return {"daily": [], "weekly": [], "monthly": [], "to_delete": []}

        for f in os.listdir(backup_dir):
            if f.endswith(".zip") or f.endswith(".tar"):
                path = os.path.join(backup_dir, f)
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                backups.append({"name": f, "date": mtime})

        backups.sort(key=lambda x: x["date"], reverse=True)

        daily = [b for b in backups if datetime.now() - b["date"] <= timedelta(days=7)]
        weekly = [b for b in backups if timedelta(days=7) < datetime.now() - b["date"] <= timedelta(days=30)]
        monthly = [b for b in backups if timedelta(days=30) < datetime.now() - b["date"] <= timedelta(days=365)]

        to_delete = backups[self.daily_keep + self.weekly_keep + self.monthly_keep:]

        return {
            "daily": daily[:self.daily_keep],
            "weekly": weekly[:self.weekly_keep],
            "monthly": monthly[:self.monthly_keep],
            "to_delete": [b["name"] for b in to_delete]
        }

    def cleanup_old_backups(self, backup_dir: str) -> List[str]:
        analysis = self.analyze_backups(backup_dir)
        deleted = []

        for name in analysis["to_delete"]:
            path = os.path.join(backup_dir, name)
            try:
                os.remove(path)
                deleted.append(name)
            except Exception as e:
                logging.error(f"Error deleting {name}: {e}")

        return deleted


def apply_retention_policy(backup_dir: str) -> List[str]:
    policy = RetentionPolicy()
    return policy.cleanup_old_backups(backup_dir)