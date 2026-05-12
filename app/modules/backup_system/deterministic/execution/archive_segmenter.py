"""
Archive Segmenter
=================
Segmentador de archivos grandes (Split Archives).
Divide el backup en partes de 2GB si excede el límite.
"""

import os
import shutil
import logging
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)

DEFAULT_MAX_SEGMENT_GB = 2
BYTES_TO_GB = 1024 ** 3


class ArchiveSegmenter:
    """Segmentador de archivos comprimidos."""

    def __init__(self, max_size_gb: float = DEFAULT_MAX_SEGMENT_GB):
        self.max_size_bytes = int(max_size_gb * BYTES_TO_GB)

    def create_segmented_archive(self, source_files: List[str],
                                  output_base: str,
                                  archive_format: str = "zip") -> Tuple[bool, List[str], str]:
        try:
            total_size = sum(os.path.getsize(f) for f in source_files if os.path.exists(f))

            if total_size <= self.max_size_bytes:
                return self._create_single_archive(source_files, output_base)

            return self._create_segmented(source_files, output_base, archive_format)

        except Exception as e:
            logger.error(f"Error creating segmented archive: {e}")
            return False, [], str(e)

    def _create_single_archive(self, files: List[str], output: str) -> Tuple[bool, List[str], str]:
        if not output.endswith(".zip"):
            output += ".zip"

        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                if os.path.exists(file):
                    zf.write(file, os.path.basename(file))

        return True, [output], f"Archivo único: {os.path.getsize(output) / BYTES_TO_GB:.2f}GB"

    def _create_segmented(self, files: List[str], base_name: str, fmt: str) -> Tuple[bool, List[str], str]:
        segments = []
        current_segment_num = 1
        current_zip = None

        for file in files:
            if not os.path.exists(file):
                continue

            file_size = os.path.getsize(file)

            if current_zip is None or current_zip.getinfo(os.path.basename(file)) is None:
                if current_zip:
                    current_zip.close()
                    segments.append(current_name)

                current_name = f"{base_name}.part{current_segment_num:03d}.zip"
                current_zip = zipfile.ZipFile(current_name, 'w', zipfile.ZIP_DEFLATED)
                current_segment_num += 1

                if os.path.exists(current_name) and os.path.getsize(current_name) > self.max_size_bytes:
                    current_zip.close()
                    segments.append(current_name)
                    current_zip = None
                    continue

            current_zip.write(file, os.path.basename(file))

        if current_zip:
            current_zip.close()
            segments.append(current_name)

        return True, segments, f"Dividido en {len(segments)} partes"

    def extract_segments(self, segments: List[str], output_dir: str) -> Tuple[bool, List[str]]:
        extracted = []

        try:
            os.makedirs(output_dir, exist_ok=True)

            for segment in segments:
                with zipfile.ZipFile(segment, 'r') as zf:
                    zf.extractall(output_dir)
                    extracted.extend(zf.namelist())

            return True, extracted

        except Exception as e:
            logger.error(f"Error extracting segments: {e}")
            return False, []

    def get_segment_info(self, segments: List[str]) -> Dict:
        total_size = sum(os.path.getsize(s) for s in segments if os.path.exists(s))

        return {
            "segment_count": len(segments),
            "total_size_mb": round(total_size / (1024 ** 2), 2),
            "max_size_mb": round(self.max_size_bytes / (1024 ** 2), 2),
            "segments": segments
        }


def create_segmented_backup(files: List[str], output_base: str) -> Tuple[bool, List[str], str]:
    segmenter = ArchiveSegmenter()
    return segmenter.create_segmented_archive(files, output_base)


def extract_backup_segments(segments: List[str], output_dir: str) -> Tuple[bool, List[str]]:
    segmenter = ArchiveSegmenter()
    return segmenter.extract_segments(segments, output_dir)