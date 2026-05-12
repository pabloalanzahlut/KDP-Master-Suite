"""
Directory Structure Validator
============================
Validador de estructura de directorios.
Recrea la jerarquía de carpetas en el backup.
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class DirectoryStructureValidator:
    """Validador de estructura de directorios."""

    def __init__(self):
        self.validation_results = []

    def map_directory_structure(self, root_path: str) -> Dict:
        if not os.path.exists(root_path):
            return {"error": "Ruta no existe"}

        structure = {
            "root": os.path.basename(root_path) or root_path,
            "type": "directory",
            "children": []
        }

        try:
            for entry in os.scandir(root_path):
                if entry.is_dir():
                    structure["children"].append({
                        "name": entry.name,
                        "type": "directory",
                        "children": self._map_subtree(entry.path)
                    })
                else:
                    structure["children"].append({
                        "name": entry.name,
                        "type": "file"
                    })
        except PermissionError:
            structure["error"] = "Permission denied"

        return structure

    def _map_subtree(self, path: str) -> List[Dict]:
        children = []
        try:
            for entry in os.scandir(path):
                if entry.is_dir():
                    children.append({
                        "name": entry.name,
                        "type": "directory",
                        "children": self._map_subtree(entry.path)
                    })
                else:
                    children.append({
                        "name": entry.name,
                        "type": "file"
                    })
        except PermissionError:
            pass
        return children

    def validate_structure(self, original_root: str, restored_root: str) -> Tuple[bool, Dict]:
        orig_structure = self.map_directory_structure(original_root)
        rest_structure = self.map_directory_structure(restored_root)

        results = {
            "original": orig_structure,
            "restored": rest_structure,
            "valid": True,
            "differences": []
        }

        orig_files = self._flatten_files(orig_structure)
        rest_files = self._flatten_files(rest_structure)

        orig_set = set(orig_files)
        rest_set = set(rest_files)

        missing = orig_set - rest_set
        extra = rest_set - orig_set

        if missing:
            results["differences"].append(f"Archivos faltantes: {len(missing)}")
            results["valid"] = False

        if extra:
            results["differences"].append(f"Archivos extra: {len(extra)}")

        return results["valid"], results

    def _flatten_files(self, structure: Dict) -> List[str]:
        files = []
        if "name" in structure and structure.get("type") == "file":
            return [structure["name"]]

        children = structure.get("children", [])
        for child in children:
            if child.get("type") == "file":
                files.append(child["name"])
            else:
                files.extend(self._flatten_files(child))

        return files

    def generate_structure_manifest(self, root_path: str, output_file: str) -> Tuple[bool, str]:
        structure = self.map_directory_structure(root_path)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2)

            return True, f"Manifiesto creado: {output_file}"

        except Exception as e:
            return False, str(e)


def map_directory(root_path: str) -> Dict:
    validator = DirectoryStructureValidator()
    return validator.map_directory_structure(root_path)


def validate_restore_structure(original: str, restored: str) -> Tuple[bool, Dict]:
    validator = DirectoryStructureValidator()
    return validator.validate_structure(original, restored)