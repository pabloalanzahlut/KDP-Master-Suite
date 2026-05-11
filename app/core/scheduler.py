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


@dataclass
class SchedulerConfig:
    """Configuración del scheduler"""
    default_interval_minutes: int = 60
    default_daily_time: str = "03:00"
    default_enabled: bool = True
    notifications_enabled: bool = True
    auto_start_on_launch: bool = False
    check_interval_seconds: int = 60
    max_concurrent_per_type: int = 1
    default_timezone: str = "local"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SchedulerConfig':
        if data is None:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


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


DAYS_OF_WEEK = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
DAYS_OF_WEEK_DISPLAY = {
    'mon': 'Lunes', 'tue': 'Martes', 'wed': 'Miércoles',
    'thu': 'Jueves', 'fri': 'Viernes', 'sat': 'Sábado', 'sun': 'Domingo'
}

CONDITION_TYPES = {
    'has_pending_videos': 'has_pending_videos:N',
    'disk_space': 'disk_space:N',
    'time_window': 'time_window:HH:MM-HH:MM',
    'queue_empty': 'queue_empty'
}

CONDITION_DESCRIPTIONS = {
    'has_pending_videos': 'Solo ejecutar si hay N+ videos pendientes',
    'disk_space': 'Solo ejecutar si hay al menos N MB libres',
    'time_window': 'Solo ejecutar entre HH:MM y HH:MM',
    'queue_empty': 'Solo ejecutar si la cola de procesamiento está vacía'
}

COMMON_TIMEZONES = {
    'local': 'Hora local',
    'America/New_York': 'Nueva York (UTC-5)',
    'America/Chicago': 'Chicago (UTC-6)',
    'America/Denver': 'Denver (UTC-7)',
    'America/Los_Angeles': 'Los Angeles (UTC-8)',
    'America/Mexico_City': 'Ciudad de México (UTC-6)',
    'Europe/London': 'Londres (UTC+0)',
    'Europe/Paris': 'París (UTC+1)',
    'Europe/Berlin': 'Berlín (UTC+1)',
    'Asia/Tokyo': 'Tokio (UTC+9)',
    'Asia/Shanghai': 'Shanghái (UTC+8)',
    'Asia/Singapore': 'Singapur (UTC+8)',
    'Australia/Sydney': 'Sídney (UTC+11)'
}


def get_timezone_offset(tz_name: str) -> int:
    """Obtiene el offset de timezone en horas"""
    if tz_name == 'local':
        return 0

    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        return now.utcoffset().total_seconds() // 3600
    except Exception:
        return 0


def convert_to_timezone(dt: datetime, tz_name: str) -> datetime:
    """Convierte un datetime a la zona horaria especificada"""
    if tz_name == 'local':
        return dt

    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
        return dt.astimezone(tz)
    except Exception:
        return dt


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
    allowed_days: Optional[List[str]] = None
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    event_trigger: Optional[str] = None
    max_retries: int = 3
    retry_count: int = 0
    auto_integrate_kb: bool = True
    max_active_tasks: int = 10
    condition: Optional[str] = None
    timezone: str = "local"

    def __post_init__(self):
        if self.allowed_days is None or not self.allowed_days:
            self.allowed_days = DAYS_OF_WEEK.copy()

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

        # Sistema de cola (Mutex)
        self._task_lock = threading.Lock()
        self._running_tasks: Dict[str, str] = {}
        self._task_type_locks: Dict[str, threading.Lock] = {
            TaskType.DOWNLOAD.value: threading.Lock(),
            TaskType.PROCESS.value: threading.Lock(),
            TaskType.MONITOR.value: threading.Lock(),
            TaskType.DETECT_NEW.value: threading.Lock()
        }
        self.max_concurrent_per_type = 1

        # Callbacks
        self.on_task_start: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_task_error: Optional[Callable] = None
        self.on_log: Optional[Callable] = None
        self.on_notification: Optional[Callable] = None
        self.on_progress: Optional[Callable[[str, int, str], None]] = None

        # Progress tracking
        self._task_progress: Dict[str, int] = {}
        
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

        # Cargar configuración
        self._load_config()
    
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

    def _load_config(self):
        """Carga configuración del scheduler desde archivo"""
        config_file = self.config_dir / "scheduler_config.json"

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config_obj = SchedulerConfig.from_dict(data.get('config', {}))
                    self._log("Configuración del scheduler cargada", 'info')
            except Exception as e:
                self._log(f"Error al cargar configuración: {e}", 'error')
                self.config_obj = SchedulerConfig()
        else:
            self.config_obj = SchedulerConfig()

    def _save_config(self):
        """Guarda configuración del scheduler en archivo"""
        config_file = self.config_dir / "scheduler_config.json"

        try:
            data = {
                'version': '1.0',
                'last_modified': datetime.now().isoformat(),
                'config': self.config_obj.to_dict()
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self._log(f"Error al guardar configuración: {e}", 'error')

    def get_config(self) -> SchedulerConfig:
        """Obtiene la configuración actual"""
        return self.config_obj

    def update_config(self, **kwargs) -> bool:
        """Actualiza la configuración"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config_obj, key):
                    setattr(self.config_obj, key, value)

                if key == 'max_concurrent_per_type':
                    self.max_concurrent_per_type = value

            self._save_config()
            self._log("Configuración actualizada", 'info')
            return True
        except Exception as e:
            self._log(f"Error al actualizar configuración: {e}", 'error')
            return False

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
                     on_notification: Callable = None,
                     on_progress: Callable = None):
        """Configura callbacks para eventos"""
        self.on_task_start = on_task_start
        self.on_task_complete = on_task_complete
        self.on_task_error = on_task_error
        self.on_log = on_log
        self.on_notification = on_notification
        self.on_progress = on_progress

    def report_progress(self, task_id: str, percent: int, message: str = ""):
        """Reporta el progreso de una tarea"""
        self._task_progress[task_id] = percent

        if self.on_progress:
            try:
                self.on_progress(task_id, percent, message)
            except Exception as e:
                logger.error(f"Error en callback on_progress: {e}")

    def get_task_progress(self, task_id: str) -> Optional[int]:
        """Obtiene el progreso de una tarea"""
        return self._task_progress.get(task_id)
    
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
    
    def _is_day_allowed(self, task: ScheduleTask, target_date: datetime) -> bool:
        """Verifica si el día de la semana está permitido para la tarea"""
        if not task.allowed_days:
            return True

        day_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
        current_day = day_map[target_date.weekday()]
        return current_day in task.allowed_days

    def _find_next_allowed_day(self, task: ScheduleTask, start_date: datetime) -> datetime:
        """Encuentra el próximo día permitido para la tarea"""
        check_date = start_date
        for _ in range(8):
            if self._is_day_allowed(task, check_date):
                return check_date
            check_date += timedelta(days=1)
        return start_date + timedelta(days=1)

    def _calculate_next_run(self, task: ScheduleTask) -> Optional[str]:
        """Calcula la próxima fecha/hora de ejecución"""
        now = datetime.now()
        schedule_type = ScheduleType(task.schedule_type)

        base_calc = None

        if schedule_type == ScheduleType.INTERVAL:
            interval = timedelta(minutes=task.interval_minutes)
            base_calc = now + interval

        elif schedule_type == ScheduleType.DAILY:
            try:
                hour, minute = map(int, task.daily_time.split(':'))
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                if target <= now:
                    target += timedelta(days=1)

                base_calc = target
            except:
                base_calc = now + timedelta(days=1)

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
                try:
                    hour, minute = map(int, times[0].split(':'))
                    base_calc = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                except:
                    base_calc = now + timedelta(days=1)
            else:
                base_calc = next_time

        elif schedule_type == ScheduleType.EVENT:
            return now.isoformat()

        else:
            base_calc = now + timedelta(hours=1)

        if base_calc and not self._is_day_allowed(task, base_calc):
            base_calc = self._find_next_allowed_day(task, base_calc)
            if schedule_type in [ScheduleType.DAILY, ScheduleType.MULTIPLE]:
                try:
                    if schedule_type == ScheduleType.DAILY:
                        hour, minute = map(int, task.daily_time.split(':'))
                    else:
                        hour, minute = map(int, times[0].split(':'))
                    base_calc = base_calc.replace(hour=hour, minute=minute, second=0, microsecond=0)
                except:
                    pass

        return base_calc.isoformat() if base_calc else None
    
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
    
    def _can_execute_task(self, task: ScheduleTask) -> tuple[bool, str]:
        """Verifica si la tarea puede ejecutarse (Mutex check)

        Returns:
            (can_execute, reason)
        """
        task_type_lock = self._task_type_locks.get(task.task_type)
        if task_type_lock is None:
            return True, ""

        if not task_type_lock.acquire(blocking=False):
            return False, f"Otra tarea de tipo '{task.task_type}' está en ejecución"

        self._running_tasks[task.task_id] = task.task_id
        return True, ""

    def _evaluate_condition(self, condition: str) -> tuple[bool, str]:
        """Evalúa una condición de ejecución

        Args:
            condition: Condición en formato "tipo:parametro"

        Returns:
            (can_execute, reason)
        """
        if not condition:
            return True, ""

        try:
            if ':' in condition:
                cond_type, param = condition.split(':', 1)
            else:
                cond_type = condition
                param = None

            if cond_type == 'has_pending_videos':
                return self._check_pending_videos(param)
            elif cond_type == 'disk_space':
                return self._check_disk_space(param)
            elif cond_type == 'time_window':
                return self._check_time_window(param)
            elif cond_type == 'queue_empty':
                return self._check_queue_empty()
            else:
                return True, ""

        except Exception as e:
            self._log(f"Error evaluando condición '{condition}': {e}", 'error')
            return True, ""

    def _check_pending_videos(self, threshold: str) -> tuple[bool, str]:
        """Verifica si hay videos pendientes"""
        try:
            threshold_num = int(threshold) if threshold else 5

            if not self.db:
                return True, ""

            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as count FROM videos
                WHERE transcription_path IS NULL OR transcription_path = ''
            """)
            row = cursor.fetchone()
            pending = row['count'] if row else 0
            conn.close()

            if pending >= threshold_num:
                return True, f"Hay {pending} videos pendientes (umbral: {threshold_num})"
            else:
                return False, f"Solo hay {pending} videos pendientes (requiere: {threshold_num})"

        except Exception as e:
            return True, ""

    def _check_disk_space(self, threshold_mb: str) -> tuple[bool, str]:
        """Verifica espacio en disco"""
        try:
            threshold = int(threshold_mb) if threshold_mb else 500
            import shutil
            stats = shutil.disk_usage(".")
            free_mb = stats.free / (1024 * 1024)

            if free_mb >= threshold:
                return True, f"Espacio disponible: {free_mb:.0f} MB"
            else:
                return False, f"Espacio insuficiente: {free_mb:.0f} MB (requiere: {threshold} MB)"

        except Exception as e:
            return True, ""

    def _check_time_window(self, time_range: str) -> tuple[bool, str]:
        """Verifica si estamos dentro del rango horario"""
        try:
            if not time_range or '-' not in time_range:
                return True, ""

            start_time, end_time = time_range.split('-')
            start_hour, start_min = map(int, start_time.strip().split(':'))
            end_hour, end_min = map(int, end_time.strip().split(':'))

            now = datetime.now()
            current_minutes = now.hour * 60 + now.minute
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            if start_minutes <= current_minutes <= end_minutes:
                return True, f"Dentro del rango {time_range}"
            else:
                return False, f"Fuera del horario {time_range} (ahora: {now.strftime('%H:%M')})"

        except Exception as e:
            return True, ""

    def _check_queue_empty(self) -> tuple[bool, str]:
        """Verifica si la cola de procesamiento está vacía"""
        try:
            if not self.db:
                return True, ""

            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as count FROM processing_history
                WHERE status = 'running'
            """)
            row = cursor.fetchone()
            running = row['count'] if row else 0
            conn.close()

            if running == 0:
                return True, "Cola vacía"
            else:
                return False, f"Hay {running} procesos en ejecución"

        except Exception as e:
            return True, ""

    def get_available_conditions(self) -> dict:
        """Retorna las condiciones disponibles"""
        return {
            'types': CONDITION_TYPES,
            'descriptions': CONDITION_DESCRIPTIONS
        }

    def _release_task_lock(self, task: ScheduleTask):
        """Libera el lock de la tarea"""
        task_type_lock = self._task_type_locks.get(task.task_type)
        if task_type_lock:
            try:
                task_type_lock.release()
            except RuntimeError:
                pass

        if task.task_id in self._running_tasks:
            del self._running_tasks[task.task_id]

    def _execute_task(self, task: ScheduleTask):
        """Ejecuta una tarea con control de exclusión mutua y condiciones"""
        can_execute, reason = self._can_execute_task(task)
        if not can_execute:
            self._log(f"Tarea '{task.name}' omitida: {reason}", 'warning')
            task.next_run = self._calculate_next_run(task)
            return

        if task.condition:
            condition_met, condition_reason = self._evaluate_condition(task.condition)
            if not condition_met:
                self._log(f"Tarea '{task.name}' omitida por condición: {condition_reason}", 'info')
                task.next_run = self._calculate_next_run(task)
                return
            else:
                self._log(f"Condición '{task.condition}' cumplida: {condition_reason}", 'info')

        try:
            self._execute_task_internal(task)
        finally:
            self._release_task_lock(task)

    def _execute_task_internal(self, task: ScheduleTask):
        """Lógica interna de ejecución de tarea (sin mutex)"""
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

        # Persistir en base de datos
        if self.db:
            try:
                self.db.save_scheduler_history(
                    task_id=task.task_id,
                    task_name=task.name,
                    task_type=task.task_type,
                    status=result.status,
                    message=result.message,
                    details=result.details,
                    started_at=result.started_at,
                    finished_at=result.finished_at,
                    duration_seconds=result.duration_seconds
                )
            except Exception as e:
                logger.error(f"Error guardando historial en BD: {e}")

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

    def get_history_from_db(self, limit: int = 100, task_id: str = None,
                            status: str = None) -> List[dict]:
        """Obtiene historial de ejecuciones desde la base de datos"""
        if not self.db:
            return []

        try:
            return self.db.get_scheduler_history(limit, task_id, status)
        except Exception as e:
            logger.error(f"Error obteniendo historial desde BD: {e}")
            return []

    def get_history_stats_today(self) -> dict:
        """Obtiene estadísticas del historial de hoy"""
        if not self.db:
            return {'completed': 0, 'failed': 0, 'running': 0}

        try:
            return self.db.get_scheduler_history_today()
        except Exception as e:
            logger.error(f"Error en estadísticas de hoy: {e}")
            return {'completed': 0, 'failed': 0, 'running': 0}

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
            'next_execution': next_run,
            'running_tasks': dict(self._running_tasks),
            'max_concurrent_per_type': self.max_concurrent_per_type
        }

    def get_running_tasks_info(self) -> dict:
        """Obtiene información de tareas en ejecución"""
        return {
            'count': len(self._running_tasks),
            'tasks': dict(self._running_tasks)
        }

    def is_task_type_running(self, task_type: str) -> bool:
        """Verifica si hay una tarea de cierto tipo en ejecución"""
        return task_type in self._running_tasks.values()

    def force_stop_task(self, task_id: str) -> bool:
        """Fuerza la detención de una tarea en ejecución"""
        if task_id in self._running_tasks:
            self._log(f"Tarea {task_id} marcada para parada forzada", 'warning')
            return True
        return False


def create_default_task(name: str, task_type: TaskType, schedule_type: ScheduleType, **kwargs) -> ScheduleTask:
    """Factory para crear tareas con valores por defecto"""
    return ScheduleTask(
        name=name,
        task_type=task_type.value,
        schedule_type=schedule_type.value,
        **kwargs
    )


TASK_TEMPLATES = {
    'daily_download_3am': {
        'name': 'Descarga Diaria 3AM',
        'task_type': TaskType.DOWNLOAD,
        'schedule_type': ScheduleType.DAILY,
        'daily_time': '03:00',
        'allowed_days': DAYS_OF_WEEK.copy(),
        'description': 'Descarga videos de canales monitoreados a las 3 AM'
    },
    'daily_download_6am': {
        'name': 'Descarga Diaria 6AM',
        'task_type': TaskType.DOWNLOAD,
        'schedule_type': ScheduleType.DAILY,
        'daily_time': '06:00',
        'allowed_days': DAYS_OF_WEEK.copy(),
        'description': 'Descarga videos de canales monitoreados a las 6 AM'
    },
    'hourly_monitor': {
        'name': 'Monitor Cada Hora',
        'task_type': TaskType.MONITOR,
        'schedule_type': ScheduleType.INTERVAL,
        'interval_minutes': 60,
        'allowed_days': DAYS_OF_WEEK.copy(),
        'description': 'Verifica canales cada hora para nuevos videos'
    },
    'half_hourly_monitor': {
        'name': 'Monitor Cada 30 Minutos',
        'task_type': TaskType.MONITOR,
        'schedule_type': ScheduleType.INTERVAL,
        'interval_minutes': 30,
        'allowed_days': DAYS_OF_WEEK.copy(),
        'description': 'Verifica canales cada 30 minutos para nuevos videos'
    },
    'daily_process_2am': {
        'name': 'Procesamiento Nocturno',
        'task_type': TaskType.PROCESS,
        'schedule_type': ScheduleType.DAILY,
        'daily_time': '02:00',
        'allowed_days': DAYS_OF_WEEK.copy(),
        'description': 'Procesa archivos de transcripción a las 2 AM'
    },
    'weekday_monitor': {
        'name': 'Monitor Días Hábiles',
        'task_type': TaskType.MONITOR,
        'schedule_type': ScheduleType.INTERVAL,
        'interval_minutes': 120,
        'allowed_days': ['mon', 'tue', 'wed', 'thu', 'fri'],
        'description': 'Verifica canales cada 2 horas en días laborales'
    },
    'weekend_download': {
        'name': 'Descarga Fines de Semana',
        'task_type': TaskType.DOWNLOAD,
        'schedule_type': ScheduleType.DAILY,
        'daily_time': '08:00',
        'allowed_days': ['sat', 'sun'],
        'description': 'Descarga videos solo los fines de semana a las 8 AM'
    },
    'detect_new_videos': {
        'name': 'Detectar Videos Nuevos',
        'task_type': TaskType.DETECT_NEW,
        'schedule_type': ScheduleType.INTERVAL,
        'interval_minutes': 15,
        'allowed_days': DAYS_OF_WEEK.copy(),
        'description': 'Verifica videos sin transcribir cada 15 minutos'
    }
}


def create_task_from_template(template_id: str, **overrides) -> Optional[ScheduleTask]:
    """Crea una tarea desde una plantilla pre-configurada

    Args:
        template_id: Identificador de la plantilla (key en TASK_TEMPLATES)
        **overrides: Valores que sobrescriben los de la plantilla

    Returns:
        ScheduleTask instanciada o None si la plantilla no existe
    """
    if template_id not in TASK_TEMPLATES:
        logger.warning(f"Plantilla '{template_id}' no encontrada")
        return None

    template = TASK_TEMPLATES[template_id]

    task = ScheduleTask(
        name=template['name'],
        task_type=template['task_type'].value,
        schedule_type=template['schedule_type'].value,
        interval_minutes=template.get('interval_minutes', 60),
        daily_time=template.get('daily_time', '03:00'),
        allowed_days=template.get('allowed_days', DAYS_OF_WEEK.copy()),
        auto_integrate_kb=True,
        enabled=True
    )

    for key, value in overrides.items():
        if hasattr(task, key):
            setattr(task, key, value)

    return task


def get_available_templates() -> dict:
    """Retorna el diccionario de plantillas disponibles"""
    return {
        tid: {
            'name': tpl['name'],
            'description': tpl['description'],
            'task_type': tpl['task_type'].value,
            'schedule_type': tpl['schedule_type'].value
        }
        for tid, tpl in TASK_TEMPLATES.items()
    }