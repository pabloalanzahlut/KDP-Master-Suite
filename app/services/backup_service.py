"""
KDP Master Suite - Servicio de Backup Automático
Garantiza la persistencia y seguridad de los datos al cerrar.
"""

import shutil
import os
from datetime import datetime
from pathlib import Path

class BackupManager:
    def __init__(self, db_path: str, backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_automatic_backup(self) -> bool:
        try:
            if not self.db_path.exists():
                return False
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"kdp_backup_auto_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            shutil.copy2(self.db_path, backup_path)
            print(f"[BACKUP] Respaldo generado con éxito: {backup_path}")
            return True
        except Exception as e:
            print(f"[ERROR] No se pudo realizar el backup: {e}")
            return False

    def create_backup(self) -> bool:
        return self.create_automatic_backup()

    def verify_file_integrity(self) -> tuple:
        try:
            if not self.db_path.exists():
                return False, "Archivo no existe"
            if self.db_path.stat().st_size == 0:
                return False, "Archivo vacío"
            return True, "OK"
        except Exception as e:
            return False, str(e)

    def restore_latest_backup(self) -> tuple:
        try:
            if not self.backup_dir.exists():
                return False, "Directorio de backups no existe"
            backups = sorted(self.backup_dir.glob("kdp_backup_auto_*.db"), reverse=True)
            if not backups:
                return False, "No hay backups disponibles"
            latest = backups[0]
            shutil.copy2(latest, self.db_path)
            return True, f"Restaurado desde {latest.name}"
        except Exception as e:
            return False, str(e)

    def sync_to_github(self, repo_url: str):
        pass


BackupService = BackupManager
