"""
Notification Preferences
========================
Gestiona preferencias de notificaciones.
"""

from typing import Dict


class NotificationPreferences:
    def __init__(self):
        self.prefs = {"email": True, "push": True, "sound": False}

    def set(self, key: str, value: bool):
        self.prefs[key] = value

    def get(self) -> Dict:
        return self.prefs


def get_notification_preferences():
    return NotificationPreferences()