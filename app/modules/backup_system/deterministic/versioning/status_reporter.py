"""
Status Reporter
===============
Generador de reporte visual de estado de backups.
"""

import os
import json
from datetime import datetime
from typing import Dict, List


class StatusReporter:
    """Generador de reportes de estado."""

    def generate_backup_status(self, backup_dir: str) -> Dict:
        if not os.path.exists(backup_dir):
            return {"error": "Backup directory not found"}

        backups = []
        total_size = 0

        for f in os.listdir(backup_dir):
            if f.startswith("_") or not f.endswith((".zip", ".tar", ".gz")):
                continue

            path = os.path.join(backup_dir, f)
            size = os.path.getsize(path)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))

            backups.append({
                "name": f,
                "size_mb": round(size / (1024 * 1024), 2),
                "date": mtime.isoformat(),
                "age_days": (datetime.now() - mtime).days
            })
            total_size += size

        return {
            "backup_count": len(backups),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "backups": sorted(backups, key=lambda x: x["date"], reverse=True),
            "generated_at": datetime.now().isoformat()
        }

    def save_report(self, backup_dir: str, output_file: str = None) -> str:
        status = self.generate_backup_status(backup_dir)

        if output_file is None:
            output_file = os.path.join(backup_dir, "backup_status.json")

        with open(output_file, 'w') as f:
            json.dump(status, f, indent=2)

        return output_file


def generate_status_report(backup_dir: str) -> Dict:
    reporter = StatusReporter()
    return reporter.generate_backup_status(backup_dir)