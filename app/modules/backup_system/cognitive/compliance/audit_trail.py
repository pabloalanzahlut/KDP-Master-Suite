"""
Audit Trail
===========
Genera trail de auditoría.
"""

from typing import Dict, List
from datetime import datetime


class AuditTrail:
    def __init__(self):
        self.entries: List[Dict] = []

    def log(self, action: str, details: Dict):
        self.entries.append({"timestamp": datetime.now().isoformat(), "action": action, "details": details})

    def get_trail(self) -> List[Dict]:
        return self.entries


def get_audit_trail():
    return AuditTrail()