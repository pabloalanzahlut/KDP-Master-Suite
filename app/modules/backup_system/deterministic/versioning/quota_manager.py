"""
Quota Manager
=============
Gestor de cuotas de espacio por proyecto.
"""

import os
import logging
from typing import Dict, Optional


class QuotaManager:
    """Gestor de cuotas."""

    def __init__(self, quotas: Dict[str, int] = None):
        self.quotas = quotas or {}

    def set_quota(self, project: str, max_mb: int) -> None:
        self.quotas[project] = max_mb

    def get_usage(self, project_path: str) -> int:
        total = 0
        if os.path.exists(project_path):
            for root, _, files in os.walk(project_path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
        return total

    def check_quota(self, project: str, project_path: str) -> Dict:
        max_bytes = self.quotas.get(project, 0) * 1024 * 1024
        used = self.get_usage(project_path)

        return {
            "project": project,
            "quota_mb": self.quotas.get(project, 0),
            "used_mb": round(used / (1024 * 1024), 2),
            "percent": round((used / max_bytes * 100) if max_bytes > 0 else 0, 1),
            "within_quota": used <= max_bytes
        }


def check_project_quota(project: str, path: str, max_mb: int) -> Dict:
    manager = QuotaManager()
    manager.set_quota(project, max_mb)
    return manager.check_quota(project, path)