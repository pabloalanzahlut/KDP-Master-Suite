import json
import os
from datetime import datetime
from pathlib import Path

class AuditLogger:
    """Módulo de gobernanza para trazabilidad inmutable de la KB (Fase 1)."""
    def __init__(self, base_dir: Path):
        self.log_file = base_dir / "logs" / "kb_distribution.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, action: str, source: str, targets: list, status: str, confidence: float = 1.0, metadata: dict = None):
        """Registra un evento de distribución en formato JSONL."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "source_file": source,
            "targets": targets,
            "confidence": confidence,
            "status": status,
            "metadata": metadata or {}
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Error en AuditLogger: {e}")

    def get_last_events(self, limit: int = 50):
        """Recupera los últimos eventos para el dashboard."""
        if not self.log_file.exists():
            return []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return [json.loads(line) for line in lines[-limit:]]
        except:
            return []