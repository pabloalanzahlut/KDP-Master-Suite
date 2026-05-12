"""
File Lock Detector
==================
Detector de archivos bloqueados por otros procesos.
Identifica archivos .part u otros locks antes del backup.
"""

import os
import logging
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

LOCK_EXTENSIONS = [".part", ".lock", ".tmp", ".crdownload", ".download"]


class FileLockDetector:
    """Detector de archivos bloqueados por otros procesos."""

    def __init__(self, lock_extensions: List[str] = None):
        self.platform = platform.system()
        self.lock_extensions = lock_extensions or LOCK_EXTENSIONS

    def scan_for_locked_files(self, directory: str) -> List[Dict[str, any]]:
        locked_files = []

        if not os.path.exists(directory):
            return locked_files

        try:
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    lock_info = self.check_file_lock(full_path)

                    if lock_info["locked"]:
                        locked_files.append({
                            "path": full_path,
                            "filename": filename,
                            "extension": os.path.splitext(filename)[1],
                            "reason": lock_info["reason"],
                            "size_bytes": lock_info.get("size", 0)
                        })
        except PermissionError as e:
            logger.warning(f"Permission denied scanning {directory}: {e}")
        except Exception as e:
            logger.error(f"Error scanning for locks: {e}")

        return locked_files

    def check_file_lock(self, file_path: str) -> Dict[str, any]:
        result = {
            "locked": False,
            "reason": "ok",
            "size": 0
        }

        if not os.path.exists(file_path):
            result["locked"] = True
            result["reason"] = "file_not_found"
            return result

        ext = os.path.splitext(file_path)[1].lower()

        if ext in self.lock_extensions:
            result["locked"] = True
            result["reason"] = f"temp_extension_{ext}"
            try:
                result["size"] = os.path.getsize(file_path)
            except:
                pass
            return result

        if self.platform == "Windows":
            return self._check_windows_lock(file_path, result)
        elif self.platform == "Linux":
            return self._check_linux_lock(file_path, result)
        elif self.platform == "Darwin":
            return self._check_macos_lock(file_path, result)

        return result

    def _check_windows_lock(self, file_path: str, result: Dict) -> Dict:
        try:
            import ctypes
            GENERIC_READ = 0x80000000
            OPEN_EXISTING = 3

            handle = ctypes.windll.kernel32.CreateFileW(
                file_path,
                GENERIC_READ,
                0,
                None,
                OPEN_EXISTING,
                0,
                None
            )

            if handle == -1:
                error = ctypes.get_last_error()
                if error == 32:
                    result["locked"] = True
                    result["reason"] = "file_in_use"
                    return result

            ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass

        return result

    def _check_linux_lock(self, file_path: str, result: Dict) -> Dict:
        try:
            proc_path = f"/proc/locks"
            if os.path.exists(proc_path):
                with open(proc_path, 'r') as f:
                    locks_content = f.read()
                    if file_path in locks_content:
                        result["locked"] = True
                        result["reason"] = "process_lock"
        except:
            pass
        return result

    def _check_macos_lock(self, file_path: str, result: Dict) -> Dict:
        return result

    def validate_for_backup(self, directory: str) -> Tuple[bool, List[Dict[str, any]]]:
        locked_files = self.scan_for_locked_files(directory)

        critical_locks = [
            f for f in locked_files
            if f["extension"] in [".part", ".lock", ".crdownload"]
        ]

        if critical_locks:
            logger.warning(f"Found {len(critical_locks)} critical locked files")
            return False, critical_locks

        return True, locked_files

    def get_largest_locked(self, directory: str, top_n: int = 5) -> List[Dict[str, any]]:
        locked_files = self.scan_for_locked_files(directory)
        sorted_files = sorted(locked_files, key=lambda x: x.get("size_bytes", 0), reverse=True)
        return sorted_files[:top_n]


def detect_locked_files(directory: str) -> List[Dict[str, any]]:
    detector = FileLockDetector()
    return detector.scan_for_locked_files(directory)


def validate_for_backup(directory: str) -> Tuple[bool, List[Dict[str, any]]]:
    detector = FileLockDetector()
    return detector.validate_for_backup(directory)