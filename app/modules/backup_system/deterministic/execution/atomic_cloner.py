"""
Atomic Cloner
=============
Motor de clonado atómico de archivos de texto con buffers optimizados.
Copia archivos sin riesgo de truncamiento o interrupción.
"""

import os
import shutil
import logging
import hashlib
from pathlib import Path
from typing import Tuple, List, Optional, Dict

logger = logging.getLogger(__name__)

DEFAULT_BUFFER_SIZE = 1024 * 1024


class AtomicCloner:
    """Motor de clonado atómico de archivos."""

    def __init__(self, buffer_size: int = DEFAULT_BUFFER_SIZE):
        self.buffer_size = buffer_size
        self.copied_files = []
        self.failed_files = []

    def clone_file(self, source: str, destination: str, verify: bool = True) -> Tuple[bool, str]:
        try:
            source_path = Path(source)
            dest_path = Path(destination)

            if not source_path.exists():
                return False, f"Fuente no existe: {source}"

            dest_path.parent.mkdir(parents=True, exist_ok=True)

            temp_dest = dest_path.with_suffix(dest_path.suffix + ".tmp")

            with open(source_path, 'rb') as src:
                with open(temp_dest, 'wb') as dst:
                    while True:
                        chunk = src.read(self.buffer_size)
                        if not chunk:
                            break
                        dst.write(chunk)
                        dst.flush()
                    os.fsync(dst.fileno())

            os.replace(temp_dest, dest_path)

            if verify:
                src_size = source_path.stat().st_size
                dst_size = dest_path.stat().st_size
                if src_size != dst_size:
                    return False, f"Tamaño no coincide: {src_size} vs {dst_size}"

            self.copied_files.append(source)
            logger.info(f"Clonado: {source} -> {destination}")
            return True, f"Copiado: {destination}"

        except Exception as e:
            self.failed_files.append({"source": source, "error": str(e)})
            logger.error(f"Error clonando {source}: {e}")
            return False, str(e)

    def clone_directory(self, source_dir: str, dest_dir: str,
                        patterns: Optional[List[str]] = None) -> Tuple[bool, Dict]:
        if not os.path.exists(source_dir):
            return False, {"error": f"Directorio fuente no existe: {source_dir}"}

        self.copied_files = []
        self.failed_files = []

        results = {"success": [], "failed": [], "skipped": 0}

        for root, dirs, files in os.walk(source_dir):
            rel_path = os.path.relpath(root, source_dir)
            dest_root = os.path.join(dest_dir, rel_path) if rel_path != "." else dest_dir

            os.makedirs(dest_root, exist_ok=True)

            for file in files:
                if patterns and not any(file.endswith(p.replace("*", "")) for p in patterns):
                    results["skipped"] += 1
                    continue

                source_file = os.path.join(root, file)
                dest_file = os.path.join(dest_root, file)

                success, msg = self.clone_file(source_file, dest_file)
                if success:
                    results["success"].append(source_file)
                else:
                    results["failed"].append({"file": source_file, "error": msg})

        all_success = len(results["failed"]) == 0
        return all_success, results

    def get_copy_stats(self) -> Dict:
        return {
            "copied_count": len(self.copied_files),
            "failed_count": len(self.failed_files),
            "total_copied": len(self.copied_files)
        }


def clone_file(source: str, dest: str, verify: bool = True) -> Tuple[bool, str]:
    cloner = AtomicCloner()
    return cloner.clone_file(source, dest, verify)


def clone_directory(source: str, dest: str) -> Tuple[bool, Dict]:
    cloner = AtomicCloner()
    return cloner.clone_directory(source, dest)