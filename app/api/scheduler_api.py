"""
KDP_MASTER - Scheduler REST API
================================
API REST para controlar el scheduler remotamente.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SchedulerAPI:
    """API REST para el scheduler"""

    def __init__(self, scheduler_manager, host: str = "localhost", port: int = 8765):
        self.scheduler = scheduler_manager
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self._running = False

    def start(self):
        """Inicia el servidor API"""
        if self._running:
            logger.warning("API ya está corriendo")
            return

        self._running = True
        self.server = HTTPServer((self.host, self.port), _SchedulerRequestHandler)
        self.server.scheduler = self.scheduler

        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()

        logger.info(f"Scheduler API iniciada en http://{self.host}:{self.port}")

    def stop(self):
        """Detiene el servidor API"""
        if self.server:
            self.server.shutdown()
            self._running = False
            logger.info("Scheduler API detenida")

    def is_running(self) -> bool:
        return self._running


class _SchedulerRequestHandler(BaseHTTPRequestHandler):
    """Manejador de requests HTTP"""

    def do_GET(self):
        """Maneja GET requests"""
        try:
            scheduler = getattr(self.server, 'scheduler', None)
            if not scheduler:
                self.send_error(500, "Scheduler no disponible")
                return

            if self.path == "/tasks":
                self._send_json(self._get_tasks_list(scheduler))
            elif self.path == "/stats":
                self._send_json(scheduler.get_stats())
            elif self.path == "/history":
                self._send_json(scheduler.get_history_from_db(limit=50))
            elif self.path == "/health":
                self._send_json({"status": "ok", "running": scheduler.running})
            elif self.path.startswith("/task/"):
                task_id = self.path.split("/")[-1]
                task = scheduler.get_task(task_id)
                if task:
                    self._send_json(task.to_dict())
                else:
                    self.send_error(404, "Tarea no encontrada")
            else:
                self.send_error(404, "Endpoint no encontrado")

        except Exception as e:
            logger.error(f"Error en GET {self.path}: {e}")
            self.send_error(500, str(e))

    def do_POST(self):
        """Maneja POST requests"""
        try:
            scheduler = getattr(self.server, 'scheduler', None)
            if not scheduler:
                self.send_error(500, "Scheduler no disponible")
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            if self.path == "/start":
                scheduler.start()
                self._send_json({"status": "started"})
            elif self.path == "/stop":
                scheduler.stop()
                self._send_json({"status": "stopped"})
            elif self.path == "/tasks":
                self._create_task(scheduler, data)
            elif self.path.startswith("/execute/"):
                task_id = self.path.split("/")[-1]
                self._execute_task(scheduler, task_id)
            else:
                self.send_error(404, "Endpoint no encontrado")

        except Exception as e:
            logger.error(f"Error en POST {self.path}: {e}")
            self.send_error(500, str(e))

    def do_DELETE(self):
        """Maneja DELETE requests"""
        try:
            scheduler = getattr(self.server, 'scheduler', None)
            if not scheduler:
                self.send_error(500, "Scheduler no disponible")
                return

            if self.path.startswith("/task/"):
                task_id = self.path.split("/")[-1]
                if scheduler.remove_task(task_id):
                    self._send_json({"status": "deleted", "task_id": task_id})
                else:
                    self.send_error(404, "Tarea no encontrada")
            else:
                self.send_error(404, "Endpoint no encontrado")

        except Exception as e:
            logger.error(f"Error en DELETE {self.path}: {e}")
            self.send_error(500, str(e))

    def _send_json(self, data: Dict[str, Any]):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _get_tasks_list(self, scheduler) -> Dict[str, Any]:
        tasks = scheduler.get_all_tasks()
        return {
            "total": len(tasks),
            "active": scheduler.get_active_count(),
            "tasks": [t.to_dict() for t in tasks]
        }

    def _create_task(self, scheduler, data: Dict[str, Any]):
        from app.core.scheduler import ScheduleTask
        try:
            task = ScheduleTask(**data)
            task_id = scheduler.add_task(task)
            if task_id:
                self._send_json({"status": "created", "task_id": task_id})
            else:
                self.send_error(400, "No se pudo crear la tarea")
        except Exception as e:
            self.send_error(400, f"Error creando tarea: {e}")

    def _execute_task(self, scheduler, task_id: str):
        task = scheduler.get_task(task_id)
        if task:
            scheduler._execute_task(task)
            self._send_json({"status": "executed", "task_id": task_id})
        else:
            self.send_error(404, "Tarea no encontrada")

    def log_message(self, format, *args):
        pass


def create_scheduler_api(scheduler, host: str = "localhost", port: int = 8765) -> SchedulerAPI:
    """Factory para crear la API del scheduler"""
    return SchedulerAPI(scheduler, host, port)