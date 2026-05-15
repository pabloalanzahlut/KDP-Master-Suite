"""
Post Backup Space Validator
===========================
Valida el espacio disponible después del backup.
"""

import os
import shutil
from typing import Dict, Tuple, Optional
from pathlib import Path


class PostBackupSpaceValidator:
    def __init__(self, min_free_gb: float = 1.0):
        self.min_free_gb = min_free_gb

    def validate(self, backup_path: Optional[str] = None) -> Dict:
        try:
            stat = shutil.disk_usage("/")
            free_gb = stat.free / (1024 ** 3)
            free_percent = (stat.free / stat.total) * 100

            status = "ok" if free_gb >= self.min_free_gb else "low"

            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "free_percent": round(free_percent, 2),
                "total_gb": round(stat.total / (1024 ** 3), 2),
                "used_gb": round(stat.used / (1024 ** 3), 2),
                "min_required_gb": self.min_free_gb,
                "path": backup_path or "/"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def validate_custom_path(self, path: str) -> Dict:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                path_obj = path_obj.parent
            stat = shutil.disk_usage(str(path_obj))
            free_gb = stat.free / (1024 ** 3)
            status = "ok" if free_gb >= self.min_free_gb else "low"

            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "path": str(path_obj)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def is_space_sufficient(self) -> bool:
        result = self.validate()
        return result.get("status") == "ok"


_global_validator = None


def get_post_backup_validator(min_free_gb: float = 1.0) -> PostBackupSpaceValidator:
    global _global_validator
    if _global_validator is None:
        _global_validator = PostBackupSpaceValidator(min_free_gb)
    return _global_validator