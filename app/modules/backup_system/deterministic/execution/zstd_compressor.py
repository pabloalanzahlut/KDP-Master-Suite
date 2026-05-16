"""
ZSTD Compressor
==============
Motor de compresión ZSTD (Nivel Ultra).
Usa compresión más eficiente que ZIP estándar.
"""

import os
import logging
import subprocess
import shutil
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)

ZSTD_LEVELS = {
    "fast": 1,
    "default": 3,
    "good": 10,
    "ultra": 19
}


class ZSTDCompressor:
    """Motor de compresión ZSTD."""

    def __init__(self, compression_level: str = "default"):
        self.level = ZSTD_LEVELS.get(compression_level, 3)
        self.compressed_files = []

    def is_zstd_available(self) -> bool:
        try:
            result = subprocess.run(
                ["zstd", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def compress_file(self, input_file: str, output_file: str = None) -> Tuple[bool, str]:
        if output_file is None:
            output_file = input_file + ".zst"

        if not os.path.exists(input_file):
            return False, "Archivo de entrada no existe"

        try:
            result = subprocess.run(
                ["zstd", f"-{self.level}", "-f", input_file, "-o", output_file],
                capture_output=True,
                timeout=300
            )

            if result.returncode == 0:
                orig_size = os.path.getsize(input_file)
                comp_size = os.path.getsize(output_file)
                ratio = (1 - comp_size / orig_size) * 100 if orig_size > 0 else 0

                self.compressed_files.append({
                    "original": input_file,
                    "compressed": output_file,
                    "ratio": ratio
                })

                return True, f"Comprimido: {ratio:.1f}%"

            return False, f"Error: {result.stderr.decode()}"

        except FileNotFoundError:
            return self._fallback_compress(input_file, output_file)
        except Exception as e:
            return False, str(e)

    def _fallback_compress(self, input_file: str, output_file: str) -> Tuple[bool, str]:
        import gzip

        output_zip = output_file.replace(".zst", ".gz")

        try:
            with gzip.open(output_zip, 'wb') as gz_out:
                with open(input_file, 'rb') as f_in:
                    shutil.copyfileobj(f_in, gz_out)

            orig_size = os.path.getsize(input_file)
            comp_size = os.path.getsize(output_zip)
            ratio = (1 - comp_size / orig_size) * 100 if orig_size > 0 else 0

            return True, f"Fallback GZIP: {ratio:.1f}%"

        except Exception as e:
            return False, f"Fallback falló: {e}"

    def decompress_file(self, compressed_file: str, output_file: str = None) -> Tuple[bool, str]:
        if not os.path.exists(compressed_file):
            return False, "Archivo comprimido no existe"

        if output_file is None:
            output_file = compressed_file.replace(".zst", "").replace(".gz", "")

        try:
            if compressed_file.endswith(".zst"):
                result = subprocess.run(
                    ["zstd", "-d", compressed_file, "-o", output_file],
                    capture_output=True,
                    timeout=300
                )
            else:
                import gzip
                with gzip.open(compressed_file, 'rb') as gz_in:
                    with open(output_file, 'wb') as f_out:
                        f_out.write(gz_in.read())
                result = type('obj', (object,), {'returncode': 0})()

            if result.returncode == 0:
                return True, f"Descomprimido: {output_file}"
            return False, "Error en descompresión"

        except Exception as e:
            return False, str(e)

    def get_compression_stats(self) -> Dict:
        if not self.compressed_files:
            return {"total": 0, "avg_ratio": 0}

        total = len(self.compressed_files)
        avg_ratio = sum(f["ratio"] for f in self.compressed_files) / total

        return {"total": total, "avg_ratio": round(avg_ratio, 1)}


def compress_file(input_file: str, output_file: str = None) -> Tuple[bool, str]:
    compressor = ZSTDCompressor()
    return compressor.compress_file(input_file, output_file)


def decompress_file(compressed_file: str, output_file: str = None) -> Tuple[bool, str]:
    compressor = ZSTDCompressor()
    return compressor.decompress_file(compressed_file, output_file)