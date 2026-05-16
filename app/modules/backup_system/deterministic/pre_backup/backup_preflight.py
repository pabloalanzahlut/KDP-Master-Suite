"""
Backup Preflight Validator
==========================
Coordinador de validación previa al backup (Pre-Flight Check).
Ejecuta los 10 módulos de pre-backup antes de una operación de backup.
"""

import os
import logging
from typing import Tuple, List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

from app.modules.backup_system.deterministic.pre_backup import (
    storage_quota_validator,
    atomic_write_lock,
    ram_buffer_flusher,
    critical_path_validator,
    permission_scanner,
    smart_disk_validator,
    hardware_temp_monitor,
    external_media_verifier,
    sqlite_integrity_validator,
    file_lock_detector
)


class BackupPreflightValidator:
    """Coordinador de validación previa al backup."""

    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getcwd()
        self.validation_results = {}
        self.critical_paths = ["knowledge", "data", "outputs"]

    def run_all_validations(self, destination: str = None) -> Tuple[bool, str, Dict]:
        dest = destination or os.path.join(self.base_path, "backups")

        self.validation_results = {
            "storage_quota": {"status": "pending", "message": ""},
            "atomic_lock": {"status": "pending", "message": ""},
            "buffer_flush": {"status": "pending", "message": ""},
            "critical_paths": {"status": "pending", "message": ""},
            "permissions": {"status": "pending", "message": ""},
            "disk_health": {"status": "pending", "message": ""},
            "hardware_temp": {"status": "pending", "message": ""},
            "external_media": {"status": "pending", "message": ""},
            "db_integrity": {"status": "pending", "message": ""},
            "file_locks": {"status": "pending", "message": ""}
        }

        all_passed = True
        messages = []

        is_valid, msg = storage_quota_validator.validate_backup_quota(
            [os.path.join(self.base_path, p) for p in self.critical_paths],
            dest
        )
        self.validation_results["storage_quota"] = {"status": "pass" if is_valid else "fail", "message": msg}
        if not is_valid:
            all_passed = False
            messages.append(f"Storage: {msg}")

        acquired = atomic_write_lock.acquire_atomic_lock(timeout=30)
        self.validation_results["atomic_lock"] = {"status": "pass" if acquired else "fail", "message": "Lock acquired" if acquired else "Could not acquire lock"}
        if not acquired:
            all_passed = False
            messages.append("Atomic Lock: Could not acquire")

        success, msg = ram_buffer_flusher.flush_ram_buffers()
        self.validation_results["buffer_flush"] = {"status": "pass" if success else "fail", "message": msg}

        is_valid, results = critical_path_validator.validate_critical_paths(self.base_path)
        path_status = "pass" if is_valid else "fail"
        missing = [k for k, v in results.items() if not v.get("valid", False)]
        if missing:
            path_msg = f"Rutas faltantes: {', '.join(missing)}"
        else:
            path_msg = "Todas las rutas críticas OK"
        self.validation_results["critical_paths"] = {"status": path_status, "message": path_msg}
        if not is_valid:
            all_passed = False
            messages.append(f"Critical Paths: {path_msg}")

        files_to_check = []
        for p in self.critical_paths:
            folder = os.path.join(self.base_path, p)
            if os.path.exists(folder):
                for root, _, files in os.walk(folder):
                    for f in files:
                        files_to_check.append(os.path.join(root, f))

        if files_to_check:
            is_valid, invalid = permission_scanner.validate_files_for_backup(files_to_check)
            perm_status = "pass" if is_valid else "fail"
            self.validation_results["permissions"] = {"status": perm_status, "message": f"{len(files_to_check)} archivos verificados"}
            if not is_valid:
                all_passed = False
                messages.append(f"Permissions: {len(invalid)} archivos sin acceso")

        is_valid, msg = smart_disk_validator.validate_before_backup()
        self.validation_results["disk_health"] = {"status": "pass" if is_valid else "warning", "message": msg}
        if not is_valid:
            all_passed = False
            messages.append(f"Disk Health: {msg}")

        is_valid, msg = hardware_temp_monitor.validate_for_backup()
        self.validation_results["hardware_temp"] = {"status": "pass" if is_valid else "warning", "message": msg}

        media = external_media_verifier.detect_external_media()
        self.validation_results["external_media"] = {"status": "pass", "message": f"{len(media)} medios externos detectados"}

        db_paths = [
            os.path.join(self.base_path, "data", "channel_monitor.db"),
            os.path.join(self.base_path, "knowledge", "knowledge.db")
        ]
        existing_dbs = [p for p in db_paths if os.path.exists(p)]
        if existing_dbs:
            all_db_ok = True
            for db_path in existing_dbs:
                is_valid, msg, _ = sqlite_integrity_validator.validate_sqlite(db_path)
                if not is_valid:
                    all_db_ok = False
                    messages.append(f"DB Integrity: {msg}")
            self.validation_results["db_integrity"] = {"status": "pass" if all_db_ok else "fail", "message": f"{len(existing_dbs)} DBs validadas"}
            if not all_db_ok:
                all_passed = False
        else:
            self.validation_results["db_integrity"] = {"status": "skip", "message": "No hay DBs encontradas"}

        knowledge_path = os.path.join(self.base_path, "knowledge")
        if os.path.exists(knowledge_path):
            is_valid, locked = file_lock_detector.validate_for_backup(knowledge_path)
            lock_status = "pass" if is_valid else "fail"
            self.validation_results["file_locks"] = {"status": lock_status, "message": f"{len(locked)} archivos bloqueados" if locked else "Sin locks"}
            if not is_valid:
                all_passed = False
                messages.append(f"File Locks: {len(locked)} archivos bloqueados")
        else:
            self.validation_results["file_locks"] = {"status": "skip", "message": " knowledge no existe"}

        final_message = "Todas las validaciones pasaron" if all_passed else "Validaciones fallidas: " + "; ".join(messages)

        return all_passed, final_message, self.validation_results

    def release_locks(self) -> None:
        atomic_write_lock.release_atomic_lock()


def run_preflight_check(base_path: str = None, destination: str = None) -> Tuple[bool, str, Dict]:
    validator = BackupPreflightValidator(base_path=base_path)
    return validator.run_all_validations(destination)


def release_locks() -> None:
    validator = BackupPreflightValidator()
    validator.release_locks()