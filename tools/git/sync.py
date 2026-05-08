import subprocess
import time
from pathlib import Path
from datetime import datetime

class GitSync:
    """Automatización de auto-commit y tagging de la KB (Fase 4.3)."""
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def auto_commit(self, source_file: str) -> bool:
        """Ejecuta el ciclo de persistencia en Git."""
        try:
            # 1. Verificar/Init
            if not (self.repo_path / ".git").exists():
                subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)

            # 2. Commit atómico
            subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
            msg = f"KB sync: {source_file} at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(["git", "commit", "-m", msg], cwd=self.repo_path, check=True, capture_output=True)
            
            # 3. Tagging (Versionado automático)
            tag = f"kb-v{int(time.time())}"
            subprocess.run(["git", "tag", "-a", tag, "-m", f"Versionado Fase 4: {tag}"], cwd=self.repo_path, check=True)
            return True
        except Exception:
            return False