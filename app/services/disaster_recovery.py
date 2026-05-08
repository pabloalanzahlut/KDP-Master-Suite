import sqlite3
import shutil
import zipfile
import os
from pathlib import Path
from typing import Tuple, List
from datetime import datetime

class RecoveryManager:
    """
    [US-050/US-060] Enterprise Disaster Recovery & Auditing.
    Manages multiple restore points and integrity validation.
    """
    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / "backups" / "restore_points"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def verify_system_integrity(self) -> Tuple[bool, str]:
        """Corporate integrity check (US-060)."""
        db_path = self.base_dir / "knowledge" / "knowledge_base.db"
        
        if not db_path.exists():
            return False, "Knowledge Database missing"
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                row = cursor.fetchone()
                
                if row and row[0] == "ok":
                    return True, "System integrity verified (SQLite PRAGMA OK)"
                return False, f"Corruption detected: {row[0]}"
                
        except sqlite3.Error as e:
            return False, f"SQLite error during integrity check: {e}"
        except Exception as e:
            return False, f"Integrity check failed: {e}"

    def create_restore_point(self, label: str = "auto") -> str:
        """Creates a timestamped snapshot of the Knowledge Base and Config."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.backup_dir / f"RP_{ts}_{label}.zip"
        
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zf:
            for folder in ["knowledge", "data"]:
                src = self.base_dir / folder
                if src.exists():
                    for file in src.rglob("*"):
                        if file.is_file():
                            zf.write(file, file.relative_to(self.base_dir))
        return str(target)

    def list_restore_points(self) -> List[Path]:
        """Returns available restore points sorted by newest."""
        return sorted(list(self.backup_dir.glob("RP_*.zip")), reverse=True)

    def restore_to_point(self, rp_path: str) -> Tuple[bool, str]:
        """Full system rollback to a specific restore point."""
        if not os.path.exists(rp_path):
            return False, "Restore point file not found."
        
        try:
            # Wipe current state
            for folder in ["knowledge", "data"]:
                target_path = self.base_dir / folder
                if target_path.exists():
                    shutil.rmtree(target_path)
            
            # Extract archive
            with zipfile.ZipFile(rp_path, 'r') as zf:
                zf.extractall(self.base_dir)
            
            return True, "Rollback successful. System state restored."
        except Exception as e:
            return False, f"Restore failed: {str(e)}"

    # --- [US-060] Corporate Compliance Auditing ---
    def audit_log_action(self, action: str, user: str = "system", details: str = ""):
        """
        Records sensitive operations with enhanced metadata for corporate compliance.
        """
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        audit_file = log_dir / "compliance_audit.log"
        
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [AUDIT] USER:{user} | ACTION:{action} | DETAILS:{details}\n"
        
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(entry)
    # --- END [US-060] ---