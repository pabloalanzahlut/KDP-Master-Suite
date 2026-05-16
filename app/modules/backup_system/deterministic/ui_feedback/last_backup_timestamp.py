"""
Last Backup Timestamp
=====================
Gestión de timestamp del último backup exitoso.
"""

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict


class LastBackupTimestamp:
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".kdp_master" / "backup_state.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._data = self._load()

    def _load(self) -> Dict:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"last_backup": None, "last_restore": None, "count": 0}

    def save(self):
        with self._lock:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)

    def update_backup(self, backup_path: str, size_bytes: int) -> Dict:
        with self._lock:
            self._data["last_backup"] = {
                "timestamp": datetime.now().isoformat(),
                "backup_path": backup_path,
                "size_bytes": size_bytes,
                "count": self._data.get("count", 0) + 1
            }
            self.save()
        return self._data["last_backup"]

    def update_restore(self, restore_path: str) -> Dict:
        with self._lock:
            self._data["last_restore"] = {
                "timestamp": datetime.now().isoformat(),
                "restore_path": restore_path
            }
            self.save()
        return self._data["last_restore"]

    def get_last_backup(self) -> Optional[Dict]:
        return self._data.get("last_backup")

    def get_last_restore(self) -> Optional[Dict]:
        return self._data.get("last_restore")

    def get_backup_count(self) -> int:
        return self._data.get("count", 0)

    def get_since_last_backup(self) -> Optional[float]:
        last = self.get_last_backup()
        if not last:
            return None
        last_time = datetime.fromisoformat(last["timestamp"])
        return (datetime.now() - last_time).total_seconds()


_global_timestamp = None


def get_last_backup_timestamp(storage_path: Optional[str] = None) -> LastBackupTimestamp:
    global _global_timestamp
    if _global_timestamp is None:
        _global_timestamp = LastBackupTimestamp(storage_path)
    return _global_timestamp