"""
Status Bar Feedback
===================
Feedback visual en barra de estado (verde/rojo).
"""

from typing import Optional, Dict


class StatusBarFeedback:
    COLORS = {"success": "green", "warning": "yellow", "error": "red", "info": "blue"}

    def __init__(self):
        self.current_status = "info"

    def set_status(self, status: str, message: str = "") -> Dict:
        if status not in self.COLORS:
            status = "info"

        self.current_status = status
        return {"status": status, "color": self.COLORS[status], "message": message}

    def get_status_color(self) -> str:
        return self.COLORS.get(self.current_status, "blue")


def update_status_bar(status: str, message: str = "") -> Dict:
    feedback = StatusBarFeedback()
    return feedback.set_status(status, message)