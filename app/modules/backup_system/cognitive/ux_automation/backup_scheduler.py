"""
Backup Scheduler
================
Programación automática de backups.
"""

from typing import Dict


class BackupScheduler:
    def __init__(self):
        self.schedule = {}

    def schedule_backup(self, name: str, cron: str) -> Dict:
        self.schedule[name] = cron
        return {"scheduled": True, "name": name, "cron": cron}


def get_backup_scheduler():
    return BackupScheduler()