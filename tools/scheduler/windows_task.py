"""
KDP_MASTER - Windows Task Scheduler Integration
================================================
Integración con Windows Task Scheduler (schtasks.exe)
"""

import subprocess
import logging
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class WindowsTaskScheduler:
    """Wrapper para Windows Task Scheduler"""

    def __init__(self, app_path: str = None, app_name: str = "KDP_Master_Suite"):
        self.app_path = app_path
        self.app_name = app_name
        self.task_prefix = f"KDP_{app_name}_"

    def create_task(self, task_name: str, time: str = "03:00",
                   daily: bool = True, enabled: bool = True) -> bool:
        """Crea una tarea programada en Windows

        Args:
            task_name: Nombre identificador de la tarea
            time: Hora de ejecución (HH:MM)
            daily: Si es daily o solo una vez
            enabled: Si la tarea está habilitada

        Returns:
            True si éxito, False si falla
        """
        if not self.app_path:
            logger.error("app_path no configurado")
            return False

        full_task_name = f"{self.task_prefix}{task_name}"

        schedule_type = "DAILY" if daily else "ONCE"

        cmd = [
            "schtasks",
            "/Create",
            "/TN", full_task_name,
            "/TR", f'"{self.app_path}" --scheduled-task {task_name}',
            "/SC", schedule_type,
            "/ST", time,
            "/F"
        ]

        if not enabled:
            cmd.extend(["/DISABLE"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Tarea '{full_task_name}' creada exitosamente")
                return True
            else:
                logger.error(f"Error creando tarea: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Excepción creando tarea: {e}")
            return False

    def delete_task(self, task_name: str) -> bool:
        """Elimina una tarea programada"""
        full_task_name = f"{self.task_prefix}{task_name}"

        cmd = ["schtasks", "/Delete", "/TN", full_task_name, "/F"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Tarea '{full_task_name}' eliminada")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando tarea: {e}")
            return False

    def enable_task(self, task_name: str) -> bool:
        """Habilita una tarea"""
        full_task_name = f"{self.task_prefix}{task_name}"
        cmd = ["schtasks", "/Change", "/TN", full_task_name, "/ENABLE"]

        try:
            return subprocess.run(cmd, capture_output=True).returncode == 0
        except:
            return False

    def disable_task(self, task_name: str) -> bool:
        """Deshabilita una tarea"""
        full_task_name = f"{self.task_prefix}{task_name}"
        cmd = ["schtasks", "/Change", "/TN", full_task_name, "/DISABLE"]

        try:
            return subprocess.run(cmd, capture_output=True).returncode == 0
        except:
            return False

    def list_tasks(self) -> List[Dict[str, str]]:
        """Lista las tareas de KDP"""
        cmd = ["schtasks", "/Query", "/FO", "LIST"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return []

            tasks = []
            current_task = {}

            for line in result.stdout.split('\n'):
                if 'TaskName:' in line:
                    task_name = line.split('TaskName:')[1].strip()
                    if self.task_prefix in task_name:
                        current_task = {"name": task_name}
                elif 'Status:' in line and current_task:
                    current_task["status"] = line.split('Status:')[1].strip()
                    tasks.append(current_task)
                    current_task = {}

            return tasks
        except Exception as e:
            logger.error(f"Error listando tareas: {e}")
            return []

    def run_task_now(self, task_name: str) -> bool:
        """Ejecuta una tarea inmediatamente"""
        full_task_name = f"{self.task_prefix}{task_name}"
        cmd = ["schtasks", "/Run", "/TN", full_task_name]

        try:
            return subprocess.run(cmd, capture_output=True).returncode == 0
        except:
            return False

    def get_task_info(self, task_name: str) -> Optional[Dict[str, str]]:
        """Obtiene información de una tarea"""
        full_task_name = f"{self.task_prefix}{task_name}"
        cmd = ["schtasks", "/Query", "/TN", full_task_name, "/FO", "LIST"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return None

            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()

            return info
        except:
            return None


def create_windows_task(app_path: str, task_name: str, time: str = "03:00") -> bool:
    """Factory para crear una tarea de Windows"""
    scheduler = WindowsTaskScheduler(app_path=app_path)
    return scheduler.create_task(task_name, time=time)


def remove_windows_task(task_name: str) -> bool:
    """Factory para eliminar una tarea de Windows"""
    scheduler = WindowsTaskScheduler()
    return scheduler.delete_task(task_name)