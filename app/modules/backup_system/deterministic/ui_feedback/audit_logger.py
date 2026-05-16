"""
Audit Logger
============
Sistema de logging de auditoría para operaciones de backup.
"""

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class AuditLogger:
    def __init__(self, audit_dir: Optional[str] = None):
        if audit_dir:
            self.audit_dir = Path(audit_dir)
        else:
            self.audit_dir = Path.home() / ".kdp_master" / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_log = self.audit_dir / f"backup_session_{self._current_session}.jsonl"

    def log(self, action: str, details: Dict, status: str = "success") -> Dict:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session": self._current_session,
            "action": action,
            "status": status,
            "details": details
        }
        with self._lock:
            with open(self._session_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def log_backup_start(self, backup_name: str, size_bytes: int) -> Dict:
        return self.log("backup_start", {
            "backup_name": backup_name,
            "size_bytes": size_bytes
        })

    def log_backup_complete(self, backup_name: str, duration_seconds: float) -> Dict:
        return self.log("backup_complete", {
            "backup_name": backup_name,
            "duration_seconds": duration_seconds
        }, "success")

    def log_backup_error(self, backup_name: str, error: str) -> Dict:
        return self.log("backup_error", {
            "backup_name": backup_name,
            "error": error
        }, "error")

    def log_restore_start(self, backup_name: str) -> Dict:
        return self.log("restore_start", {"backup_name": backup_name})

    def log_restore_complete(self, backup_name: str, duration_seconds: float) -> Dict:
        return self.log("restore_complete", {
            "backup_name": backup_name,
            "duration_seconds": duration_seconds
        }, "success")

    def get_session_entries(self, limit: int = 100) -> List[Dict]:
        entries = []
        with self._lock:
            if self._session_log.exists():
                with open(self._session_log, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entries.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        return entries[-limit:]


_global_audit_logger = None


def get_audit_logger(audit_dir: Optional[str] = None) -> AuditLogger:
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger(audit_dir)
    return _global_audit_logger