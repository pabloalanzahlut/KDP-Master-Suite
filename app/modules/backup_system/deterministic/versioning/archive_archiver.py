"""
Archive Archiver
================
Archivador de backups antiguos a carpeta _archive.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from typing import List


class ArchiveArchiver:
    """Archivador de backups."""

    def __init__(self, archive_dir: str = "_archive"):
        self.archive_dir = archive_dir

    def archive_old_backups(self, backup_dir: str, days_threshold: int = 30) -> List[str]:
        archived = []
        archive_path = os.path.join(backup_dir, self.archive_dir)

        if not os.path.exists(backup_dir):
            return archived

        os.makedirs(archive_path, exist_ok=True)

        cutoff = datetime.now() - timedelta(days=days_threshold)

        for f in os.listdir(backup_dir):
            if f.startswith("_"):
                continue

            if not f.endswith((".zip", ".tar", ".gz")):
                continue

            path = os.path.join(backup_dir, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))

            if mtime < cutoff:
                try:
                    dest = os.path.join(archive_path, f)
                    shutil.move(path, dest)
                    archived.append(f)
                except Exception as e:
                    logging.error(f"Error archiving {f}: {e}")

        return archived


def archive_old_backups(backup_dir: str) -> List[str]:
    archiver = ArchiveArchiver()
    return archiver.archive_old_backups(backup_dir)