"""
Access Control
==============
Control de acceso a backups.
"""

from typing import Dict, List


class AccessControl:
    def __init__(self):
        self.allowed_users: List[str] = []

    def check_access(self, user: str, resource: str) -> Dict:
        allowed = user in self.allowed_users
        return {"allowed": allowed, "user": user, "resource": resource}


def get_access_control():
    return AccessControl()