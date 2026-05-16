"""
File Permission Validator
==========================
Valida permisos de archivos antes y después del backup.
"""

import os
import stat
import threading
from typing import Dict, List, Optional
from pathlib import Path


class FilePermissionValidator:
    def __init__(self):
        self._lock = threading.Lock()
        self._validated_files: Dict[str, Dict] = {}

    def validate_file(self, file_path: str) -> Dict:
        try:
            path = Path(file_path)
            if not path.exists():
                return {"status": "not_found", "path": file_path}

            st = path.stat()
            mode = st.st_mode

            is_readable = os.access(file_path, os.R_OK)
            is_writable = os.access(file_path, os.W_OK)
            is_executable = os.access(file_path, os.X_OK)

            result = {
                "status": "ok",
                "path": file_path,
                "mode": oct(stat.S_IMODE(mode)),
                "readable": is_readable,
                "writable": is_writable,
                "executable": is_executable,
                "size_bytes": st.st_size
            }

            with self._lock:
                self._validated_files[file_path] = result

            return result
        except Exception as e:
            return {"status": "error", "path": file_path, "error": str(e)}

    def validate_directory(self, dir_path: str, recursive: bool = False) -> List[Dict]:
        results = []
        try:
            path = Path(dir_path)
            if not path.exists():
                return [{"status": "not_found", "path": dir_path}]

            if recursive:
                for item in path.rglob("*"):
                    if item.is_file():
                        results.append(self.validate_file(str(item)))
            else:
                for item in path.iterdir():
                    if item.is_file():
                        results.append(self.validate_file(str(item)))
        except Exception as e:
            results.append({"status": "error", "path": dir_path, "error": str(e)})

        return results

    def check_write_permission(self, file_path: str) -> bool:
        try:
            test_path = f"{file_path}.test"
            with open(test_path, "w") as f:
                f.write("test")
            os.remove(test_path)
            return True
        except Exception:
            return False

    def get_validated_files(self) -> Dict:
        with self._lock:
            return self._validated_files.copy()


_global_validator = None


def get_file_permission_validator() -> FilePermissionValidator:
    global _global_validator
    if _global_validator is None:
        _global_validator = FilePermissionValidator()
    return _global_validator