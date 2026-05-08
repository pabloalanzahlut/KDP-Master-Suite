import os
import json
import logging
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
import socket
import urllib.request
from typing import Dict, List, Tuple, Optional

class EnvManager:
    """
    [MÓDULO US-CONFIG-CENTRAL]
    Gestor centralizado de variables de entorno (.env) con soporte para
    múltiples perfiles, cifrado de secretos y validación dinámica.
    Implementa principios SOLID para extensibilidad y seguridad.
    """
    def __init__(self, base_dir: str, master_key: Optional[bytes] = None):
        self.base_dir = Path(base_dir)
        self.master_key = master_key or self._get_or_create_key()
        self.fernet = Fernet(self.master_key)
        self.current_env_file = self.base_dir / ".env"
        self.history_file = self.base_dir / "data" / "env_history.json"
        os.makedirs(self.history_file.parent, exist_ok=True)

    def _get_or_create_key(self) -> bytes:
        """Genera o recupera la clave maestra para cifrado de secretos local."""
        key_path = self.base_dir / "data" / ".master.key"
        if key_path.exists():
            return key_path.read_bytes()
        key = Fernet.generate_key()
        os.makedirs(key_path.parent, exist_ok=True)
        key_path.write_bytes(key)
        return key

    def load_env(self, file_path: Optional[Path] = None) -> Dict[str, str]:
        """Carga variables desde un archivo .env de forma atómica."""
        target = file_path if file_path else self.current_env_file
        if not target.exists():
            return {}
        
        env_data = {}
        with open(target, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_data[key.strip()] = value.strip()
        return env_data

    def save_env(self, data: Dict[str, str], file_path: Optional[Path] = None, user: str = "system") -> bool:
        """Guarda variables en el .env activo y registra la auditoría del cambio."""
        target = file_path if file_path else self.current_env_file
        old_data = self.load_env(target)
        
        with open(target, 'w', encoding='utf-8') as f:
            for key, value in data.items():
                f.write(f"{key}={value}\n")
        
        self._log_history(user, old_data, data)
        return True

    def encrypt_secret(self, value: str) -> str:
        """Cifra un valor sensible usando AES vía Fernet."""
        return self.fernet.encrypt(value.encode()).decode()

    def decrypt_secret(self, encrypted_value: str) -> str:
        """Descifra un valor sensible; si falla, devuelve el original (fallback)."""
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except Exception:
            return encrypted_value

    def _log_history(self, user: str, old_data: Dict, new_data: Dict):
        """Registra el historial de cambios para auditoría (Feature 7)."""
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception: pass
        
        changes = {k: v for k, v in new_data.items() if old_data.get(k) != v}
        if not changes: return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "changes": changes
        }
        history.append(entry)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history[-100:], f, indent=2)

    def validate_service_connectivity(self, service_name: str, url: str) -> Tuple[bool, str]:
        """Verifica disponibilidad de servicios (Feature 2 y 8)."""
        try:
            if "ollama" in service_name.lower():
                host = "127.0.0.1"
                port = 11434
                with socket.create_connection((host, port), timeout=2):
                    return True, "Conexión exitosa con Ollama"
            else:
                req = urllib.request.Request(url, method='HEAD')
                with urllib.request.urlopen(req, timeout=3) as response:
                    return response.status < 400, f"Servicio activo (Status {response.status})"
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"

    # === [FEATURE 4: EXPORT/IMPORT JSON] START ===
    def export_env_json(self, export_path: Path) -> bool:
        """Exporta la configuración actual a un archivo JSON."""
        data = self.load_env()
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception: return False

    def import_env_json(self, import_path: Path) -> bool:
        """Importa configuración desde un JSON y la guarda en el .env actual."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.save_env(data)
        except Exception: return False
    # === [FEATURE 4: EXPORT/IMPORT JSON] END ===

    def get_template_diff(self, template_path: Path) -> List[str]:
        """Mapeo de variables faltantes respecto al template (Feature 9 y 10)."""
        template = self.load_env(template_path)
        current = self.load_env()
        return [k for k in template if k not in current]