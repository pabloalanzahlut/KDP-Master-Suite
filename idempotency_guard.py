import hashlib
import json
import os
from pathlib import Path

class IdempotencyGuard:
    """Garantiza que el mismo bloque de conocimiento no se procese dos veces (Fase 1)."""
    def __init__(self, base_dir: Path):
        self.state_file = base_dir / "data" / "processed_hashes.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.hashes = self._load_hashes()

    def _load_hashes(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def get_content_hash(self, content: str) -> str:
        """Normaliza contenido para evitar duplicados por espacios o mayúsculas."""
        normalized = " ".join(content.lower().split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def is_duplicate(self, content: str) -> bool:
        h = self.get_content_hash(content)
        return h in self.hashes

    def register_processed(self, content: str):
        """Registra el hash y persiste el estado."""
        h = self.get_content_hash(content)
        self.hashes.add(h)
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.hashes), f)
        except Exception as e:
            print(f"Error guardando hashes: {e}")