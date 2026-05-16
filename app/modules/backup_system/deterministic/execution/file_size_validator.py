"""
File Size Validator
===================
Validador de tamaño de archivos post-copia.
Compara tamaño original vs copiado byte por byte.
"""

import os
import logging
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger(__name__)


class FileSizeValidator:
    """Validador de tamaño de archivos."""

    def __init__(self):
        self.validation_results = []

    def validate_file(self, original_path: str, copied_path: str) -> Tuple[bool, str]:
        if not os.path.exists(original_path):
            return False, "Archivo original no existe"

        if not os.path.exists(copied_path):
            return False, "Archivo copiado no existe"

        original_size = os.path.getsize(original_path)
        copied_size = os.path.getsize(copied_path)

        if original_size == copied_size:
            result = {
                "file": copied_path,
                "original_size": original_size,
                "copied_size": copied_size,
                "valid": True
            }
            self.validation_results.append(result)
            return True, f"Tamaño OK: {original_size} bytes"

        result = {
            "file": copied_path,
            "original_size": original_size,
            "copied_size": copied_size,
            "valid": False,
            "difference": copied_size - original_size
        }
        self.validation_results.append(result)
        return False, f"Tamaño diverge: {original_size} vs {copied_size}"

    def validate_batch(self, file_pairs: List[Tuple[str, str]]) -> Tuple[bool, List[Dict]]:
        results = []

        for original, copied in file_pairs:
            is_valid, msg = self.validate_file(original, copied)
            results.append({
                "original": original,
                "copied": copied,
                "valid": is_valid,
                "message": msg
            })

        all_valid = all(r["valid"] for r in results)
        return all_valid, results

    def get_validation_summary(self) -> Dict:
        total = len(self.validation_results)
        valid = sum(1 for r in self.validation_results if r.get("valid", False))
        invalid = total - valid

        return {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "success_rate": f"{(valid/total*100):.1f}%" if total > 0 else "0%"
        }


def validate_file_size(original: str, copied: str) -> Tuple[bool, str]:
    validator = FileSizeValidator()
    return validator.validate_file(original, copied)


def validate_batch_sizes(pairs: List[Tuple[str, str]]) -> Tuple[bool, List[Dict]]:
    validator = FileSizeValidator()
    return validator.validate_batch(pairs)