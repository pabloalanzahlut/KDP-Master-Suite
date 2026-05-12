"""
Hidden File Collector
=====================
Recolector de archivos ocultos y de sistema.
Incluye archivos .git, .DS_Store, configs ocultas.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)

HIDDEN_PATTERNS = [
    ".git",
    ".gitignore",
    ".DS_Store",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".vscode",
    ".idea",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".env",
    ".secrets",
    ".config",
    ".cache"
]

SYSTEM_FILES = [
    ".app.lock",
    ".master.key",
    "settings.json",
    "config.json"
]


class HiddenFileCollector:
    """Recolector de archivos ocultos y de sistema."""

    def __init__(self, include_git: bool = True, include_cache: bool = False):
        self.include_git = include_git
        self.include_cache = include_cache

    def find_hidden_files(self, root_path: str) -> List[str]:
        hidden_files = []

        if not os.path.exists(root_path):
            return hidden_files

        for entry in os.scandir(root_path):
            if self._is_hidden(entry):
                hidden_files.append(entry.path)

            if entry.is_dir():
                if self._should_scan_directory(entry.name):
                    hidden_files.extend(self._scan_directory(entry.path))

        return hidden_files

    def _is_hidden(self, entry: os.DirEntry) -> bool:
        name = entry.name

        if name.startswith('.'):
            if not self.include_git and name == ".git":
                return False
            return True

        if name in ["Thumbs.db", "desktop.ini"]:
            return True

        return False

    def _should_scan_directory(self, dirname: str) -> bool:
        if dirname == "__pycache__":
            return self.include_cache
        if dirname in [".git", ".vscode", ".idea"]:
            return self.include_git
        if dirname.startswith("."):
            return True
        return False

    def _scan_directory(self, directory: str) -> List[str]:
        results = []

        try:
            for entry in os.scandir(directory):
                if entry.is_file() and self._is_hidden(entry):
                    results.append(entry.path)
                elif entry.is_dir() and self._should_scan_directory(entry.name):
                    results.extend(self._scan_directory(entry.path))
        except PermissionError:
            pass

        return results

    def collect_system_files(self, root_path: str) -> List[str]:
        system_files = []

        for sys_file in SYSTEM_FILES:
            file_path = os.path.join(root_path, sys_file)
            if os.path.exists(file_path):
                system_files.append(file_path)

        hidden_config = os.path.join(root_path, ".config")
        if os.path.exists(hidden_config):
            for entry in os.scandir(hidden_config):
                if entry.is_file():
                    system_files.append(entry.path)

        return system_files

    def create_hidden_files_manifest(self, root_path: str) -> Dict:
        hidden = self.find_hidden_files(root_path)
        system = self.collect_system_files(root_path)

        return {
            "hidden_count": len(hidden),
            "system_count": len(system),
            "total": len(hidden) + len(system),
            "hidden_files": hidden,
            "system_files": system
        }

    def validate_hidden_files(self, original_root: str, restored_root: str) -> Tuple[bool, Dict]:
        orig_manifest = self.create_hidden_files_manifest(original_root)
        rest_manifest = self.create_hidden_files_manifest(restored_root)

        orig_hidden = set(orig_manifest["hidden_files"])
        rest_hidden = set(rest_manifest["hidden_files"])

        missing = orig_hidden - rest_hidden

        return len(missing) == 0, {
            "missing_hidden": list(missing),
            "original_count": orig_manifest["total"],
            "restored_count": rest_manifest["total"]
        }


def find_hidden_files(root_path: str) -> List[str]:
    collector = HiddenFileCollector()
    return collector.find_hidden_files(root_path)


def collect_all_special_files(root_path: str) -> Dict:
    collector = HiddenFileCollector()
    return collector.create_hidden_files_manifest(root_path)