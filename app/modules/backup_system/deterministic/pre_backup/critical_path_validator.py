"""
Critical Path Validator
=======================
Verifica integridad de rutas críticas (knowledge, data, outputs).
"""

import os
import logging
from pathlib import Path
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_CRITICAL_PATHS = ["knowledge", "data", "outputs"]


class CriticalPathValidator:
    """Validador de rutas críticas del sistema."""

    def __init__(self, base_path: Optional[str] = None,
                 critical_paths: Optional[List[str]] = None):
        self.base_path = base_path or os.getcwd()
        self.critical_paths = critical_paths or DEFAULT_CRITICAL_PATHS

    def validate_all_critical_paths(self) -> Tuple[bool, dict]:
        results = {}
        all_valid = True

        for path_name in self.critical_paths:
            full_path = os.path.join(self.base_path, path_name)
            is_valid, status = self.validate_critical_path(full_path)
            results[path_name] = {"path": full_path, "valid": is_valid, "status": status}
            if not is_valid:
                all_valid = False

        return all_valid, results

    def validate_critical_path(self, path: str) -> Tuple[bool, str]:
        path_obj = Path(path)

        if not path_obj.exists():
            return False, "Ruta no existe"

        if not os.access(path, os.R_OK):
            return False, "Sin permisos de lectura"

        if not os.access(path, os.W_OK):
            return False, "Sin permisos de escritura"

        if not path_obj.is_dir():
            return False, "No es un directorio"

        try:
            test_file = os.path.join(path, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True, "Ruta accesible y escribible"
        except PermissionError:
            return False, "Sin permisos de escritura"
        except Exception as e:
            return False, f"Error de acceso: {str(e)}"

    def get_missing_paths(self) -> List[str]:
        missing = []
        for path_name in self.critical_paths:
            full_path = os.path.join(self.base_path, path_name)
            if not os.path.exists(full_path):
                missing.append(full_path)
        return missing

    def create_missing_paths(self) -> Tuple[bool, dict]:
        results = {}
        all_created = True

        for path_name in self.critical_paths:
            full_path = os.path.join(self.base_path, path_name)
            if not os.path.exists(full_path):
                try:
                    os.makedirs(full_path, exist_ok=True)
                    results[path_name] = f"Creado: {full_path}"
                    logger.info(f"Created missing path: {full_path}")
                except Exception as e:
                    results[path_name] = f"Error: {str(e)}"
                    all_created = False
            else:
                results[path_name] = "Ya existe"

        return all_created, results


def validate_critical_paths(base_path: str = None) -> Tuple[bool, dict]:
    validator = CriticalPathValidator(base_path=base_path)
    return validator.validate_all_critical_paths()


def get_missing_critical_paths(base_path: str = None) -> List[str]:
    validator = CriticalPathValidator(base_path=base_path)
    return validator.get_missing_paths()


def ensure_critical_paths(base_path: str = None) -> Tuple[bool, dict]:
    validator = CriticalPathValidator(base_path=base_path)
    return validator.create_missing_paths()