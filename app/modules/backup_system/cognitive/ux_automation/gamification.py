"""
Gamification
============
Gamificación del sistema de backup.
"""

from typing import Dict


class Gamification:
    def __init__(self):
        self.points = 0

    def award_points(self, action: str, amount: int = 10):
        self.points += amount
        return {"points": self.points, "action": action, "level": "novice" if self.points < 100 else "expert"}

    def get_stats(self) -> Dict:
        return {"total_points": self.points}


def get_gamification():
    return Gamification()