"""
Max Age Validator
=================
Validador de antigüedad máxima de backups.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict


class MaxAgeValidator:
    """Validador de antigüedad de backups."""

    def __init__(self, max_age_days: int = 7):
        self.max_age_days = max_age_days

    def check_backup_age(self, backup_path: str) -> Dict:
        if not os.path.exists(backup_path):
            return {"exists": False, "age_days": 0, "stale": False}

        mtime = datetime.fromtimestamp(os.path.getmtime(backup_path))
        age = (datetime.now() - mtime).days

        return {
            "exists": True,
            "age_days": age,
            "stale": age > self.max_age_days,
            "last_backup": mtime.isoformat()
        }

    def check_all_backups(self, backup_dir: str) -> Tuple[bool, Dict]:
        if not os.path.exists(backup_dir):
            return False, {"error": "Backup dir not found"}

        results = {"backups": [], "has_stale": False}

        for f in os.listdir(backup_dir):
            if f.endswith((".zip", ".tar", ".gz")):
                path = os.path.join(backup_dir, f)
                info = self.check_backup_age(path)
                results["backups"].append({f: info})
                if info.get("stale"):
                    results["has_stale"] = True

        return not results["has_stale"], results


def validate_backup_age(backup_dir: str) -> Tuple[bool, Dict]:
    validator = MaxAgeValidator()
    return validator.check_all_backups(backup_dir)