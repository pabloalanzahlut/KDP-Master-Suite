"""
Hardware Temperature Monitor
===========================
Monitor de temperatura de CPU y disco para evitar thermal throttling.
"""

import os
import logging
import platform
import subprocess
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)

CRITICAL_TEMP_C = 85
WARNING_TEMP_C = 75


class HardwareTempMonitor:
    """Monitor de temperatura de hardware."""

    def __init__(self, critical_temp: int = CRITICAL_TEMP_C,
                 warning_temp: int = WARNING_TEMP_C):
        self.critical_temp = critical_temp
        self.warning_temp = warning_temp
        self.platform = platform.system()

    def get_cpu_temperature(self) -> Optional[int]:
        try:
            if self.platform == "Windows":
                return self._get_cpu_temp_windows()
            elif self.platform == "Linux":
                return self._get_cpu_temp_linux()
            elif self.platform == "Darwin":
                return self._get_cpu_temp_macos()
        except Exception as e:
            logger.warning(f"Could not get CPU temperature: {e}")
            return None

    def _get_cpu_temp_windows(self) -> Optional[int]:
        try:
            result = subprocess.run(
                ["wmic", "Temperature", "get", "CurrentTemperature", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and "," in line:
                        parts = line.split(",")
                        if len(parts) > 1 and parts[1].strip().isdigit():
                            temp_kelvin = int(parts[1].strip())
                            return (temp_kelvin - 2732) // 10
            return None
        except:
            return None

    def _get_cpu_temp_linux(self) -> Optional[int]:
        temp_paths = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input",
            "/sys/class/hwmon/hwmon1/temp1_input"
        ]
        for path in temp_paths:
            try:
                with open(path, 'r') as f:
                    temp_millidegrees = int(f.read().strip())
                    return temp_millidegrees // 1000
            except:
                continue
        return None

    def _get_cpu_temp_macos(self) -> Optional[int]:
        try:
            result = subprocess.run(
                ["osx-cpu-temp"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return int(result.stdout.strip().replace("°C", "").replace("C", ""))
        except:
            pass
        return None

    def get_system_temperature_status(self) -> Dict[str, any]:
        cpu_temp = self.get_cpu_temperature()

        if cpu_temp is None:
            return {
                "available": False,
                "status": "unknown",
                "message": "Sensor de temperatura no disponible"
            }

        status = "ok"
        if cpu_temp >= self.critical_temp:
            status = "critical"
        elif cpu_temp >= self.warning_temp:
            status = "warning"

        return {
            "available": True,
            "cpu_temp_c": cpu_temp,
            "status": status,
            "message": f"CPU: {cpu_temp}°C"
        }

    def validate_for_backup(self) -> Tuple[bool, str]:
        temp_status = self.get_system_temperature_status()

        if not temp_status.get("available"):
            return True, "Temperatura no medible, continuando"

        if temp_status["status"] == "critical":
            temp_c = temp_status["cpu_temp_c"]
            return False, f"Temperatura crítica: {temp_c}°C (≥{self.critical_temp}°C)"

        if temp_status["status"] == "warning":
            temp_c = temp_status["cpu_temp_c"]
            return True, f"Advertencia temperatura: {temp_c}°C"

        return True, temp_status["message"]


def get_temperature_status() -> Dict[str, any]:
    monitor = HardwareTempMonitor()
    return monitor.get_system_temperature_status()


def validate_for_backup() -> Tuple[bool, str]:
    monitor = HardwareTempMonitor()
    return monitor.validate_for_backup()