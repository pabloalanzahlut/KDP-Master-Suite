"""
Dashboard Widget
================
Widget para dashboard de backup.
"""

from typing import Dict


class DashboardWidget:
    def get_data(self) -> Dict:
        return {"backups_today": 3, "storage_used": "45%", "last_backup": "2 hours ago"}


def get_dashboard_widget():
    return DashboardWidget()