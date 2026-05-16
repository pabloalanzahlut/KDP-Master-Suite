"""
Config Backup Manager
=====================
Copiador de configuraciones de entorno (.env) y archivos de configuración.
Incluye específicamente archivos ocultos de configuración.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILES = [
    ".env",
    "settings.json",
    "config.json",
    "secrets.json",
    ".secrets",
    "queue_state.json",
    "session_state.json",
    ".master.key",
    ".app.lock"
]


class ConfigBackupManager:
    """Gestor de backup de archivos de configuración."""

    def __init__(self, config_files: List[str] = None):
        self.config_files = config_files or DEFAULT_CONFIG_FILES

    def find_config_files(self, base_path: str) -> List[Tuple[str, str]]:
        found_configs = []

        for config_file in self.config_files:
            config_path = os.path.join(base_path, config_file)
            if os.path.exists(config_path):
                found_configs.append((config_path, config_file))
                logger.info(f"Found config: {config_file}")

        hidden_dir = os.path.join(base_path, ".config")
        if os.path.exists(hidden_dir):
            for item in os.listdir(hidden_dir):
                item_path = os.path.join(hidden_dir, item)
                if os.path.isfile(item_path):
                    dest = os.path.join(".config", item)
                    found_configs.append((item_path, dest))

        return found_configs

    def backup_configs(self, base_path: str, dest_dir: str) -> Tuple[bool, Dict]:
        found = self.find_config_files(base_path)

        results = {"success": [], "failed": [], "skipped": []}

        for source, relative_dest in found:
            try:
                dest_path = os.path.join(dest_dir, relative_dest)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(source, dest_path)
                results["success"].append(relative_dest)
                logger.info(f"Config backed up: {relative_dest}")
            except Exception as e:
                results["failed"].append({"file": relative_dest, "error": str(e)})
                logger.error(f"Error backing up {relative_dest}: {e}")

        return len(results["failed"]) == 0, results

    def validate_config_integrity(self, config_path: str) -> Tuple[bool, str]:
        if not os.path.exists(config_path):
            return False, "Config no existe"

        try:
            if config_path.endswith(".json"):
                import json
                with open(config_path, 'r') as f:
                    json.load(f)
                return True, "Config válido"

            if config_path.endswith((".env", ".key", ".lock")):
                return True, "Config binario/texto"

            return True, "Config accesible"

        except Exception as e:
            return False, f"Config corrupto: {e}"


def find_all_configs(base_path: str) -> List[Tuple[str, str]]:
    manager = ConfigBackupManager()
    return manager.find_config_files(base_path)


def backup_all_configs(base_path: str, dest_dir: str) -> Tuple[bool, Dict]:
    manager = ConfigBackupManager()
    return manager.backup_configs(base_path, dest_dir)