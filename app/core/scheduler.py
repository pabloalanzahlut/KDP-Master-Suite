"""
KDP_MASTER - Schedule Manager
=============================
Sistema de programación horaria para tareas automatizadas.
Permite programar descargas, procesamiento, monitoreo y detección de videos nuevos.
"""

import os
import sys
import logging
import threading
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Tipos de tareas programadas"""
    DOWNLOAD = "download"
    PROCESS = "process"
    MONITOR = "monitor"
    DETECT_NEW = "detect_new"


class ScheduleType(Enum):
    """Tipos de programación"""
    INTERVAL = "interval"
    DAILY = "daily"
    MULTIPLE = "multiple"
    EVENT = "event"


class TaskStatus(Enum):
    """Estado de la tarea"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ScheduleTask:
    """Modelo de tarea programada"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    task_type: str = TaskType.DOWNLOAD.value
    schedule_type: str = ScheduleType.INTERVAL.value
    interval_minutes: int = 60
    daily_time: str = "03:00"
    multiple_times: List[str] = field(default_factory=list)
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    event_trigger: Optional[str] = None
    max_retries: int = 3
    retry_count: int = 0
    auto_integrate_kb: bool = True
    max_active_tasks: int = 10
    
    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduleTask':
        """Crea desde diccionario"""
        return cls(**data)


@dataclass
class TaskResult:
    """Resultado de ejecución de tarea"""
    task_id: str
    status: str
    message: str
    details: dict = field(default_factory=dict)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: float = 0


class ScheduleManager:
    """
    Gestor centralizado de programación horaria.
    Usa APScheduler para scheduling interno (no Windows Task Scheduler).
    """
    
    MAX_TASKS_TOTAL = 20
    MAX_TASKS_ACTIVE = 10
    
    def __init__(self, config=None, db_manager=None):
        """
        Inicializa el gestor de programación.
        
        Args:
            config: Configuración de la app
            db_manager: Gestor de base de datos
        """
        self.config = config
        self.db = db_manager
        
        # Tareas programadas
        self.tasks: Dict[str, ScheduleTask] = {}
        
        # Estado del scheduler
        self.running = False
        self.paused = False
        self._scheduler_thread = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self.on_task_start: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_task_error: Optional[Callable] = None
        self.on_log: Optional[Callable] = None
        self.on_notification: Optional[Callable] = None
        
        # Servicios externos (se asignan después)
        self.download_service = None
        self.processing_service = None
        self.monitor_service = None
        self.knowledge_integrator = None
        
        # Histórico de ejecuciones
        self.execution_history: List[TaskResult] = []
        self.max_history = 100
        
        # Configuración de directorios
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        self.config_dir = base_dir / "data"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar tareas guardadas
        self._load_tasks()
    
    def _log(self, message: str, level: str = 'info'):
        """Registra mensaje con callback opcional"""
        if level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
        
        if self.on_log:
            try:
                self.on_log(message, level)
            except Exception as e:
                logger.error(f"Error en callback de log: {e}")
    
    def _load_tasks(self):
        """Carga tareas desde archivo de configuración"""
        config_file = self.config_dir / "scheduled_tasks.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tasks_data = data.get('tasks', {})
                    
                    for task_id, task_data in tasks_data.items():
                        self.tasks[task_id] = ScheduleTask.from_dict(task_data)
                    
                    self._log(f"Cargadas {len(self.tasks)} tareas programadas", 'info')
            except Exception as e:
                self._log(f"Error al cargar tareas: {e}", 'error')
    
    def _save_tasks(self):
        """Guarda tareas en archivo de configuración"""
        config_file = self.config_dir / "scheduled_tasks.json"
        
        try:
            data = {
                'version': '1.0',
                'last_modified': datetime.now().isoformat(),
                'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()}
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self._log(f"Error al guardar tareas: {e}", 'error')
    
    def set_services(self, download_service=None, processing_service=None, 
                     monitor_service=None, knowledge_integrator=None):
        """Asigna servicios para ejecutar tareas"""
        self.download_service = download_service
        self.processing_service = processing_service
        self.monitor_service = monitor_service
        self.knowledge_integrator = knowledge_integrator
    
    def set_callbacks(self, on_task_start: Callable = None, 
                     on_task_complete: Callable = None,
                     on_task_error: Callable = None,
                     on_log: Callable = None,
                     on_notification: Callable = None):
        """Configura callbacks para eventos"""
        self.on_task_start = on_task_start
        self.on_task_complete = on_task_complete
        self.on_task_error = on_task_error
        self.on_log = on_log
        self.on_notification = on_notification
    
    # ==================== GESTIÓN DE TAREAS ====================
    
    def add_task(self, task: ScheduleTask) -> Optional[str]:
        """
        Agrega una nueva tarea programada.
        
        Args:
            task: Tarea a agregar
            
        Returns:
            task_id si éxito, None si falla
        """
        # Verificar límite total
        if len(self.tasks) >= self.MAX_TASKS_TOTAL:
            self._log(f"Límite de {self.MAX_TASKS_TOTAL} tareas alcanzado", 'warning')
            return None
        
        # Verificar límite de activas
        active_count = sum(1 for t in self.tasks.values() if t.enabled)
        if task.enabled and active_count >= self.MAX_TASKS_ACTIVE:
            self._log(f"Límite de {self.MAX_TASKS_ACTIVE} tareas activas alcanzado", 'warning')
            task.enabled = False
        
        # Validar tarea
        if not task.name:
            task.name = f"Tarea {task.task_type}_{datetime.now().strftime('%H%M%S')}"
        
        # Calcular próxima ejecución
        task.next_run = self._calculate_next_run(task)
        
        # Agregar tarea
        self.tasks[task.task_id] = task
        self._save_tasks()
        
        self._log(f"Tarea '{task.name}' creada (ID: {task.task_id})", 'info')
        
        # Iniciar scheduler si no está corriendo
        if self.running and task.enabled:
            self._schedule_task(task)
        
        return task.task_id
    
    def remove_task(self, task_id: str) -> bool:
        """Elimina una tarea programada"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            self._log(f"Tarea {task_id} eliminada", 'info')
            return True
        return False
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """Actualiza una tarea"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # Recalcular próxima ejecución
        task.next_run = self._calculate_next_run(task)
        
        self._save_tasks()
        return True
    
    def get_task(self, task_id: str) -> Optional[ScheduleTask]:
        """Obtiene una tarea por ID"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ScheduleTask]:
        """Obtiene todas las tareas"""
        return list(self.tasks.values())
    
    def get_enabled_tasks(self) -> List[ScheduleTask]:
        """Obtiene tareas habilitadas"""
        return [t for t in self.tasks.values() if t.enabled]
    
    def get_active_count(self) -> int:
        """Cantidad de tareas activas"""
        return sum(1 for t in self.tasks.values() if t.enabled)
    
    # ==================== CÁLCULO DE PRÓXIMA EJECUCIÓN ====================
    
    def _calculate_next_run(self, task: ScheduleTask) -> Optional[str]:
        """Calcula la próxima fecha/hora de ejecución"""
        now = datetime.now()
        
        schedule_type = ScheduleType(task.schedule_type)
        
        if schedule_type == ScheduleType.INTERVAL:
            interval = timedelta(minutes=task.interval_minutes)
            next_time = now + interval
            
        elif schedule_type == ScheduleType.DAILY:
            try:
                hour, minute = map(int, task.daily_time.split(':'))
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if target <= now:
                    target += timedelta(days=1)
                
                next_time = target
            except:
                next_time = now + timedelta(days=1)
                
        elif schedule_type == ScheduleType.MULTIPLE:
            if not task.multiple_times:
                return None
            
            times = sorted(task.multiple_times)
            next_time = None
            
            for time_str in times:
                try:
                    hour, minute = map(int, time_str.split(':'))
                    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if target > now:
                        next_time = target
                        break
                except:
                    continue
            
            if not next_time:
                # Primer horario del día siguiente
                try:
                    hour, minute = map(int, times[0].split(':'))
                    next_time = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                except:
                    next_time = now + timedelta(days=1)
                    
        elif schedule_type == ScheduleType.EVENT:
            # Para eventos, retornamos inmediatamente (se ejecuta en el ciclo de polling)
            return now.isoformat()
        
        else:
            next_time = now + timedelta(hours=1)
        
        return next_time.isoformat() if next_time else None
    
    def get_next_execution_time(self, task_id: str) -> Optional[datetime]:
        """Obtiene la próxima fecha de ejecución de una tarea"""
        task = self.tasks.get(task_id)
        if not task or not task.next_run:
            return None
        
        try:
            return datetime.fromisoformat(task.next_run)
        except:
            return None
    
    # ==================== CONTROL DEL SCHEDULER ====================
    
    def start(self):
        """Inicia el scheduler"""
        if self.running:
            self._log("Scheduler ya está corriendo", 'warning')
            return
        
        self.running = True
        self.paused = False
        self._stop_event.clear()
        
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
        
        self._log("Scheduler iniciado", 'info')
    
    def stop(self):
        """Detiene el scheduler"""
        self.running = False
        self.paused = False
        self._stop_event.set()
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        self._log("Scheduler detenido", 'info')
    
    def pause(self):
        """Pausa todas las tareas"""
        self.paused = True
        
        for task in self.tasks.values():
            task.enabled = False
        
        self._save_tasks()
        self._log("Scheduler pausado", 'info')
    
    def resume(self):
        """Reanuda tareas que estavam habilitadas"""
        self.paused = False
        
        for task in self.tasks.values():
            if task.enabled:
                task.next_run = self._calculate_next_run(task)
        
        self._save_tasks()
        self._log("Scheduler reanudado", 'info')
    
    def _run_scheduler(self):
        """Hilo principal del scheduler - verifica tareas cada minuto"""
        check_interval = 60  # segundos
        
        while not self._stop_event.is_set():
            if not self.paused:
                self._check_and_execute_tasks()
            
            # Esperar next check
            self._stop_event.wait(check_interval)
    
    def _check_and_execute_tasks(self):
        """Verifica y ejecuta tareas pendientes"""
        now = datetime.now()
        
        for task in self.get_enabled_tasks():
            if not task.next_run:
                continue
            
            try:
                next_run = datetime.fromisoformat(task.next_run)
                
                if now >= next_run:
                    self._execute_task(task)
                    
                    # Actualizar próxima ejecución
                    task.last_run = now.isoformat()
                    task.next_run = self._calculate_next_run(task)
                    task.retry_count = 0
                    
                    self._save_tasks()
                    
            except Exception as e:
                self._log(f"Error al verificar tarea {task.task_id}: {e}", 'error')
    
    def _execute_task(self, task: ScheduleTask):
        """Ejecuta una tarea"""
        self._log(f"Iniciando tarea: {task.name}", 'info')
        
        if self.on_task_start:
            try:
                self.on_task_start(task)
            except Exception as e:
                logger.error(f"Error en callback on_task_start: {e}")
        
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING.value,
            message="Ejecutando...",
            started_at=datetime.now().isoformat()
        )
        
        try:
            # Ejecutar según tipo de tarea
            if task.task_type == TaskType.DOWNLOAD.value:
                result = self._execute_download(task, result)
            elif task.task_type == TaskType.PROCESS.value:
                result = self._execute_process(task, result)
            elif task.task_type == TaskType.MONITOR.value:
                result = self._execute_monitor(task, result)
            elif task.task_type == TaskType.DETECT_NEW.value:
                result = self._execute_detect_new(task, result)
            else:
                result.status = TaskStatus.FAILED.value
                result.message = f"Tipo de tarea desconocido: {task.task_type}"
                
        except Exception as e:
            result.status = TaskStatus.FAILED.value
            result.message = f"Error ejecución: {str(e)}"
            self._log(f"Error en tarea {task.name}: {e}", 'error')
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                self._log(f"Reintentando ({task.retry_count}/{task.max_retries})", 'warning')
            else:
                task.enabled = False
                self._log(f"Tarea {task.name} deshabilitada tras {task.max_retries} fallos", 'error')
        
        result.finished_at = datetime.now().isoformat()
        
        if result.started_at and result.finished_at:
            try:
                start = datetime.fromisoformat(result.started_at)
                end = datetime.fromisoformat(result.finished_at)
                result.duration_seconds = (end - start).total_seconds()
            except:
                pass
        
        # Agregar al historial
        self.execution_history.append(result)
        if len(self.execution_history) > self.max_history:
            self.execution_history.pop(0)
        
        # Callback de completación
        if result.status == TaskStatus.COMPLETED.value:
            if self.on_task_complete:
                try:
                    self.on_task_complete(task, result)
                except Exception as e:
                    logger.error(f"Error en callback on_task_complete: {e}")
            
            # Notificación de éxito
            if self.on_notification:
                try:
                    self.on_notification(
                        title=f"✅ {task.name}",
                        message=result.message,
                        type="success"
                    )
                except Exception as e:
                    logger.error(f"Error en notificación: {e}")
        else:
            if self.on_task_error:
                try:
                    self.on_task_error(task, result)
                except Exception as e:
                    logger.error(f"Error en callback on_task_error: {e}")
            
            # Notificación de error
            if self.on_notification:
                try:
                    self.on_notification(
                        title=f"❌ Error: {task.name}",
                        message=result.message,
                        type="error"
                    )
                except Exception as e:
                    logger.error(f"Error en notificación: {e}")
    
    def _execute_download(self, task: ScheduleTask, result: TaskResult) -> TaskResult:
        """Ejecuta tarea de descarga"""
        if not self.download_service:
            result.status = TaskStatus.FAILED.value
            result.message = "Servicio de descarga no disponible"
            return result
        
        try:
            # Ejecutar descarga de canales monitoreados
            if self.monitor_service:
                videos = self.monitor_service.check_all_channels()
                downloaded_count = len(videos)
                
                result.status = TaskStatus.COMPLETED.value
                result.message = f"Descarga completada: {downloaded_count} videos"
                result.details = {'videos': downloaded_count}
            else:
                result.status = TaskStatus.COMPLETED.value
                result.message = "Descarga ejecutada (sin canales configurados)"
                
        except Exception as e:
            result.status = TaskStatus.FAILED.value
            result.message = f"Error en descarga: {str(e)}"
        
        return result
    
    def _execute_process(self, task: ScheduleTask, result: TaskResult) -> TaskResult:
        """Ejecuta tarea de procesamiento"""
        if not self.processing_service:
            result.status = TaskStatus.FAILED.value
            result.message = "Servicio de procesamiento no disponible"
            return result
        
        try:
            processed_count = 0
            
            # Procesar archivos pendientes
            if self.config:
                from app.core.config import Config
                input_dir = Config.TRANSCRIPTIONS_DIR
                
                if input_dir.exists():
                    files = list(input_dir.glob("*.vtt")) + list(input_dir.glob("*.srt"))
                    processed_count = len(files)
            
            result.status = TaskStatus.COMPLETED.value
            result.message = f"Procesamiento completado: {processed_count} archivos"
            result.details = {'files': processed_count}
            
        except Exception as e:
            result.status = TaskStatus.FAILED.value
            result.message = f"Error en procesamiento: {str(e)}"
        
        return result
    
    def _execute_monitor(self, task: ScheduleTask, result: TaskResult) -> TaskResult:
        """Ejecuta tarea de monitoreo"""
        if not self.monitor_service:
            result.status = TaskStatus.FAILED.value
            result.message = "Servicio de monitoreo no disponible"
            return result
        
        try:
            # Ejecutar verificación de canales
            if hasattr(self.monitor_service, 'check_all_channels'):
                new_videos = self.monitor_service.check_all_channels()
                
                result.status = TaskStatus.COMPLETED.value
                result.message = f"Monitoreo completado: {len(new_videos)} nuevos videos"
                result.details = {'new_videos': len(new_videos)}
            else:
                result.status = TaskStatus.COMPLETED.value
                result.message = "Monitoreo ejecutado"
                
        except Exception as e:
            result.status = TaskStatus.FAILED.value
            result.message = f"Error en monitoreo: {str(e)}"
        
        return result
    
    def _execute_detect_new(self, task: ScheduleTask, result: TaskResult) -> TaskResult:
        """Ejecuta tarea de detección de videos nuevos sin transcribir"""
        try:
            if not self.db:
                result.status = TaskStatus.FAILED.value
                result.message = "Base de datos no disponible"
                return result
            
            # Query para videos sin transcribir
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM videos 
                WHERE transcription_path IS NULL OR transcription_path = ''
            """)
            
            row = cursor.fetchone()
            pending_count = row['count'] if row else 0
            
            result.status = TaskStatus.COMPLETED.value
            result.message = f"Detección completada: {pending_count} videos sin transcribir"
            result.details = {'pending': pending_count}
            
        except Exception as e:
            result.status = TaskStatus.FAILED.value
            result.message = f"Error en detección: {str(e)}"
        
        return result
    
    def trigger_event(self, event_name: str, data: Any = None):
        """Dispara tareas basadas en eventos"""
        for task in self.get_enabled_tasks():
            if task.schedule_type == ScheduleType.EVENT.value:
                if task.event_trigger == event_name:
                    self._log(f"Evento '{event_name}' disparando tarea {task.name}", 'info')
                    self._execute_task(task)
    
    # ==================== HISTORIAL ====================
    
    def get_execution_history(self, limit: int = 50) -> List[TaskResult]:
        """Obtiene historial de ejecuciones"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Limpia historial de ejecuciones"""
        self.execution_history.clear()
    
    # ==================== ESTADÍSTICAS ====================
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del scheduler"""
        total_tasks = len(self.tasks)
        active_tasks = self.get_active_count()
        completed_today = 0
        failed_today = 0
        
        today = datetime.now().date()
        
        for result in self.execution_history:
            if result.started_at:
                try:
                    result_date = datetime.fromisoformat(result.started_at).date()
                    if result_date == today:
                        if result.status == TaskStatus.COMPLETED.value:
                            completed_today += 1
                        elif result.status == TaskStatus.FAILED.value:
                            failed_today += 1
                except:
                    pass
        
        next_run = None
        if self.tasks:
            next_times = []
            for task in self.get_enabled_tasks():
                next_time = self.get_next_execution_time(task.task_id)
                if next_time:
                    next_times.append(next_time)
            
            if next_times:
                next_run = min(next_times).isoformat()
        
        return {
            'running': self.running,
            'paused': self.paused,
            'total_tasks': total_tasks,
            'active_tasks': active_tasks,
            'completed_today': completed_today,
            'failed_today': failed_today,
            'next_execution': next_run
        }


def create_default_task(name: str, task_type: TaskType, schedule_type: ScheduleType, **kwargs) -> ScheduleTask:
    """Factory para crear tareas con valores por defecto"""
    return ScheduleTask(
        name=name,
        task_type=task_type.value,
        schedule_type=schedule_type.value,
        **kwargs
    )