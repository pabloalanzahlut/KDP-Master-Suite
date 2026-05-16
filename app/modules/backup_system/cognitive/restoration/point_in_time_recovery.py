"""
Point In Time Recovery
=======================
Recuperación a punto específico en tiempo.
"""

from typing import Dict, List


class PointInTimeRecovery:
    def recover(self, timestamp: str, backups: List[Dict]) -> List[Dict]:
        return [b for b in backups if b.get("timestamp", "") <= timestamp]


def get_point_in_time_recovery():
    return PointInTimeRecovery()