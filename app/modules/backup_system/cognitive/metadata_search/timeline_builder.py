"""
Timeline Builder
================
Construye timeline de backups.
"""

from typing import List, Dict
import os


class TimelineBuilder:
    def build(self, backup_files: List[str]) -> List[Dict]:
        timeline = []
        for bf in backup_files:
            try:
                timeline.append({"path": bf, "size": os.path.getsize(bf), "ctime": os.path.getctime(bf)})
            except:
                pass
        return sorted(timeline, key=lambda x: x["ctime"], reverse=True)


def get_timeline_builder():
    return TimelineBuilder()