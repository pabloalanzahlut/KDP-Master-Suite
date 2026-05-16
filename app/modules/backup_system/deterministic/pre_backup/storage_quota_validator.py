"""
Storage Quota Validator
=======================
Valida cuotas de almacenamiento en tiempo real antes del backup.
Calcula tamaño total de archivos a respaldar y verifica espacio disponible.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

BYTES_TO_GB = 1024 ** 3
MIN_FREE_PERCENT = 10


class StorageQuotaValidator:
    """Validador de cuotas de almacenamiento para operaciones de backup."""

    def __init__(self, min_free_percent: float = MIN_FREE_PERCENT):
        self.min_free_percent = min_free_percent

    def calculate_backup_size(self, paths: List[str]) -> int:
        total_size = 0
        for path in paths:
            path_obj = Path(path)
            if path_obj.is_file():
                total_size += path_obj.stat().st_size
            elif path_obj.is_dir():
                total_size += self._get_directory_size(path_obj)
        return total_size

    def _get_directory_size(self, directory: Path) -> int:
        total = 0
        try:
            for entry in directory.rglob('*'):
                if entry.is_file():
                    try:
                        total += entry.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot access directory {directory}: {e}")
        return total

    def get_disk_info(self, path: str) -> dict:
        try:
            import shutil
            usage = shutil.disk_usage(path if os.path.exists(path) else os.getcwd())
            total_bytes = usage.total
            free_bytes = usage.free
            used_bytes = usage.used
            free_percent = (free_bytes / total_bytes * 100) if total_bytes > 0 else 0

            return {
                "total_gb": round(total_bytes / BYTES_TO_GB, 2),
                "free_gb": round(free_bytes / BYTES_TO_GB, 2),
                "used_gb": round(used_bytes / BYTES_TO_GB, 2),
                "free_percent": round(free_percent, 2)
            }
        except Exception as e:
            logger.error(f"Error getting disk info: {e}")
            return {"total_gb": 0, "free_gb": 0, "used_gb": 0, "free_percent": 0}

    def validate_backup_quota(self, paths_to_backup: List[str],
                              destination_path: str) -> Tuple[bool, str]:
        backup_size = self.calculate_backup_size(paths_to_backup)
        backup_size_gb = round(backup_size / BYTES_TO_GB, 2)

        disk_info = self.get_disk_info(destination_path)

        if disk_info["free_percent"] < self.min_free_percent:
            return False, (
                f"Espacio insuficiente: {disk_info['free_gb']}GB libre "
                f"({disk_info['free_percent']:.1f}% < {self.min_free_percent}%)"
            )

        required_space = backup_size * 1.1
        if disk_info["free_gb"] * BYTES_TO_GB < required_space:
            return False, (
                f"Espacio insuficiente para backup: requiere ~{backup_size_gb}GB "
                f"pero solo {disk_info['free_gb']}GB disponible"
            )

        return True, (
            f"Quota OK: Backup ~{backup_size_gb}GB, "
            f"Espacio disponible: {disk_info['free_gb']}GB ({disk_info['free_percent']:.1f}%)"
        )


def validate_backup_quota(paths: List[str], dest: str) -> Tuple[bool, str]:
    validator = StorageQuotaValidator()
    return validator.validate_backup_quota(paths, dest)


def get_disk_info(path: str) -> dict:
    validator = StorageQuotaValidator()
    return validator.get_disk_info(path)