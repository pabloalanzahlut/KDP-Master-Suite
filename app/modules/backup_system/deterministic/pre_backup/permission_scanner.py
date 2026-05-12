"""
Permission Scanner
==================
Escáner de permisos de lectura/escritura sobre archivos y DB.
"""

import os
import stat
import logging
import platform
from pathlib import Path
from typing import Tuple, List, Optional, Dict

logger = logging.getLogger(__name__)


class PermissionScanner:
    """Escáner de permisos del sistema de archivos."""

    def __init__(self):
        self.platform = platform.system()

    def check_path_permissions(self, path: str) -> Dict[str, bool]:
        if not os.path.exists(path):
            return {"exists": False, "readable": False, "writable": False}

        return {
            "exists": True,
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
            "executable": os.access(path, os.X_OK) if self.platform != "Windows" else True
        }

    def scan_paths(self, paths: List[str]) -> Dict[str, Dict[str, bool]]:
        results = {}
        for path in paths:
            results[path] = self.check_path_permissions(path)
        return results

    def validate_files_for_backup(self, files: List[str]) -> Tuple[bool, List[str]]:
        invalid_files = []

        for file_path in files:
            perms = self.check_path_permissions(file_path)
            if not perms["readable"]:
                invalid_files.append(f"Sin lectura: {file_path}")
            elif not perms["writable"]:
                logger.warning(f"Archivo sin escritura: {file_path}")

        return len(invalid_files) == 0, invalid_files

    def get_file_permissions_string(self, path: str) -> str:
        try:
            st = os.stat(path)
            mode = st.st_mode

            perms = []
            perms.append("r" if mode & stat.S_IRUSR else "-")
            perms.append("w" if mode & stat.S_IWUSR else "-")
            perms.append("x" if mode & stat.S_IXUSR else "-")
            perms.append("r" if mode & stat.S_IRGRP else "-")
            perms.append("w" if mode & stat.S_IWGRP else "-")
            perms.append("x" if mode & stat.S_IXGRP else "-")
            perms.append("r" if mode & stat.S_IROTH else "-")
            perms.append("w" if mode & stat.S_IWOTH else "-")
            perms.append("x" if mode & stat.S_IXOTH else "-")

            return "".join(perms)
        except Exception as e:
            logger.error(f"Error getting permissions for {path}: {e}")
            return "unknown"

    def verify_database_permissions(self, db_path: str) -> Tuple[bool, str]:
        perms = self.check_path_permissions(db_path)

        if not perms["exists"]:
            return False, f"Base de datos no existe: {db_path}"

        if not perms["readable"]:
            return False, f"Sin permisos de lectura: {db_path}"

        temp_file = db_path + ".perm_test"
        try:
            with open(temp_file, 'w') as f:
                f.write("test")
            os.remove(temp_file)
            return True, f"Permisos OK: {db_path}"
        except Exception as e:
            return False, f"Sin permisos de escritura: {e}"


def check_permissions(path: str) -> Dict[str, bool]:
    scanner = PermissionScanner()
    return scanner.check_path_permissions(path)


def validate_files_for_backup(files: List[str]) -> Tuple[bool, List[str]]:
    scanner = PermissionScanner()
    return scanner.validate_files_for_backup(files)


def verify_db_permissions(db_path: str) -> Tuple[bool, str]:
    scanner = PermissionScanner()
    return scanner.verify_database_permissions(db_path)