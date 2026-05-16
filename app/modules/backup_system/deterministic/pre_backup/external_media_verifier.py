"""
External Media Verifier
=======================
Verifica conexión de medios externos (USB, NAS) para backup redundante.
"""

import os
import logging
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ExternalMediaVerifier:
    """Verificador de medios externos conectados."""

    def __init__(self):
        self.platform = platform.system()

    def detect_external_media(self) -> List[Dict[str, str]]:
        media = []

        if self.platform == "Windows":
            media = self._detect_windows_media()
        elif self.platform == "Linux":
            media = self._detect_linux_media()
        elif self.platform == "Darwin":
            media = self._detect_macos_media()

        logger.info(f"Medios externos detectados: {len(media)}")
        return media

    def _detect_windows_media(self) -> List[Dict[str, str]]:
        media = []
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    stat = os.statvfs(drive)
                    if stat.f_fsid != os.statvfs("C:\\").f_fsid:
                        label = self._get_volume_label(letter)
                        media.append({
                            "drive": drive,
                            "type": "usb" if self._is_removable(letter) else "external",
                            "label": label or f"Drive {letter}",
                            "path": drive
                        })
                except:
                    continue
        return media

    def _get_volume_label(self, drive_letter: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["vol", f"{drive_letter}:"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout
                if "Volume Label" in output:
                    parts = output.split("Volume Label is")
                    if len(parts) > 1:
                        label = parts[1].split()[0].strip()
                        return label if label != "The" else None
        except:
            pass
        return None

    def _is_removable(self, drive_letter: str) -> bool:
        try:
            result = subprocess.run(
                ["wmic", "logicaldisk", "where", f"DeviceID='{drive_letter}:'",
                 "get", "DriveType", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and "2" in result.stdout:
                return True
        except:
            pass
        return False

    def _detect_linux_media(self) -> List[Dict[str, str]]:
        media = []
        mount_points = ["/media", "/mnt", "/run/media"]

        for mp in mount_points:
            if os.path.exists(mp):
                try:
                    for root, dirs, files in os.walk(mp):
                        for d in dirs:
                            full_path = os.path.join(root, d)
                            if os.path.ismount(full_path):
                                media.append({
                                    "path": full_path,
                                    "type": "usb" if "/usb" in full_path else "mount",
                                    "label": d,
                                    "drive": full_path
                                })
                except PermissionError:
                    continue
        return media

    def _detect_macos_media(self) -> List[Dict[str, str]]:
        media = []
        volumes_path = "/Volumes"

        if os.path.exists(volumes_path):
            try:
                for entry in os.listdir(volumes_path):
                    full_path = os.path.join(volumes_path, entry)
                    if os.path.ismount(full_path):
                        media.append({
                            "path": full_path,
                            "type": "external",
                            "label": entry,
                            "drive": full_path
                        })
            except PermissionError:
                pass
        return media

    def verify_external_write(self, path: str) -> Tuple[bool, str]:
        try:
            test_file = os.path.join(path, ".backup_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True, f"Escritura OK: {path}"
        except Exception as e:
            return False, f"Sin permisos de escritura: {e}"

    def get_best_external_drive(self) -> Optional[Dict[str, str]]:
        media = self.detect_external_media()

        for m in media:
            is_writable, _ = self.verify_external_write(m["path"])
            if is_writable:
                return m

        return None


def detect_external_media() -> List[Dict[str, str]]:
    verifier = ExternalMediaVerifier()
    return verifier.detect_external_media()


def get_external_drive() -> Optional[Dict[str, str]]:
    verifier = ExternalMediaVerifier()
    return verifier.get_best_external_drive()


def verify_external_write(path: str) -> Tuple[bool, str]:
    verifier = ExternalMediaVerifier()
    return verifier.verify_external_write(path)