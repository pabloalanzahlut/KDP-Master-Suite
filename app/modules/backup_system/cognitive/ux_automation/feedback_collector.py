"""
Feedback Collector
==================
Recolecta feedback del usuario.
"""

from typing import Dict


class FeedbackCollector:
    def __init__(self):
        self.feedback: list = []

    def collect(self, rating: int, comment: str):
        self.feedback.append({"rating": rating, "comment": comment})

    def get_feedback(self) -> list:
        return self.feedback


def get_feedback_collector():
    return FeedbackCollector()