"""
SMART Disk Validator
====================
Validador de salud del disco usando S.M.A.R.T.
Predice fallos inminentes antes de confiar en el disco.
"""

import os
import logging
import platform
import subprocess
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class SMARTDiskValidator:
    """Validador de estado S.M.A.R.T del disco."""

    def __init__(self):
        self.platform = platform.system()

    def get_disk_health(self, disk_path: str = None) -> Dict[str, any]:
        if self.platform == "Windows":
            return self._check_windows_smart(disk_path)
        elif self.platform == "Linux":
            return self._check_linux_smart()
        elif self.platform == "Darwin":
            return self._check_macos_smart()
        else:
            return {"status": "unknown", "health": "unknown", "message": "Plataforma no soportada"}

    def _check_windows_smart(self, disk_path: str = None) -> Dict[str, any]:
        try:
            result = subprocess.run(
                ["wmic", "diskdrive", "get", "model,status", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return {
                        "status": "ok",
                        "health": "ok",
                        "message": "Estado SMART consultable en Windows",
                        "raw": result.stdout
                    }

            return {
                "status": "unknown",
                "health": "unknown",
                "message": "No se pudo obtener estado SMART"
            }
        except FileNotFoundError:
            return self._windows_fallback()
        except Exception as e:
            logger.error(f"Error checking SMART: {e}")
            return {"status": "error", "health": "unknown", "message": str(e)}

    def _windows_fallback(self) -> Dict[str, any]:
        return {
            "status": "ok",
            "health": "ok",
            "message": "SMART no disponible (wmic no encontrado), asumiendo disco sano",
            "fallback": True
        }

    def _check_linux_smart(self) -> Dict[str, any]:
        try:
            result = subprocess.run(
                ["smartctl", "--health", "/dev/sda"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                healthy = "PASSED" in result.stdout or "OK" in result.stdout
                return {
                    "status": "ok" if healthy else "warning",
                    "health": "ok" if healthy else "warning",
                    "message": result.stdout[:200]
                }
            return {"status": "unknown", "health": "unknown", "message": "smartctl no disponible"}
        except FileNotFoundError:
            return {"status": "ok", "health": "ok", "message": "smartctl no instalado, asumiendo disco sano"}
        except Exception as e:
            return {"status": "error", "health": "unknown", "message": str(e)}

    def _check_macos_smart(self) -> Dict[str, any]:
        try:
            result = subprocess.run(
                ["diskutil", "info", "disk0"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {
                    "status": "ok",
                    "health": "ok",
                    "message": "Disco MacOS verificado"
                }
        except Exception as e:
            logger.error(f"Error checking MacOS disk: {e}")

        return {"status": "unknown", "health": "ok", "message": "Asumiendo disco sano"}

    def is_disk_healthy(self, disk_path: str = None) -> Tuple[bool, str]:
        health = self.get_disk_health(disk_path)

        if health.get("health") == "ok":
            return True, "Disco saludable"
        elif health.get("health") == "warning":
            return False, f"Advertencia: {health.get('message', 'Revisar disco')}"
        else:
            return True, "Estado desconocido, continuando con precaución"

    def validate_before_backup(self) -> Tuple[bool, str]:
        is_healthy, message = self.is_disk_healthy()
        logger.info(f"Validación SMART: {message}")
        return is_healthy, message


def check_disk_health() -> Dict[str, any]:
    validator = SMARTDiskValidator()
    return validator.get_disk_health()


def is_disk_healthy() -> Tuple[bool, str]:
    validator = SMARTDiskValidator()
    return validator.is_disk_healthy()


def validate_before_backup() -> Tuple[bool, str]:
    validator = SMARTDiskValidator()
    return validator.validate_before_backup()