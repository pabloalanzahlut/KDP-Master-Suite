"""
Módulo P3-27: Pausa Automática Nocturna
Detiene operaciones durante horario nocturno configurable (default 2AM-6AM).
"""
import time
import threading
import logging
from datetime import datetime, time as dt_time
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class NightModeConfig:
    """Configuración del modo nocturno."""
    enabled: bool = True
    start_hour: int = 2
    start_minute: int = 0
    end_hour: int = 6
    end_minute: int = 0
    timezone: str = "local"
    pause_downloads: bool = True
    pause_monitoring: bool = False
    pause_processing: bool = True


class NightModeScheduler:
    """
    Scheduler para pausa automática durante horario nocturno.
    Implementa el patrón Observer para notificar a servicios.
    """

    DEFAULT_CONFIG = NightModeConfig()

    def __init__(
        self,
        config: Optional[NightModeConfig] = None,
        on_pause: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None
    ):
        self.config = config or self.DEFAULT_CONFIG
        self.on_pause_callback = on_pause
        self.on_resume_callback = on_resume
        self._is_paused = False
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._pause_reason = ""
        self._observers: list = []

    def start(self):
        """Inicia el scheduler de modo nocturno."""
        if self._running:
            logger.warning("NightModeScheduler ya está en ejecución")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="NightModeScheduler")
        self._thread.start()
        logger.info(f"NightModeScheduler iniciado: {self._get_config_str()}")

    def stop(self):
        """Detiene el scheduler."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("NightModeScheduler detenido")

    def _run_loop(self):
        """Loop principal del scheduler."""
        while self._running:
            try:
                self._check_and_toggle()
            except Exception as e:
                logger.error(f"Error en NightModeScheduler loop: {e}")
            time.sleep(60)

    def _check_and_toggle(self):
        """Verifica si debe pausar o reanudar basado en la hora actual."""
        if not self.config.enabled:
            return

        now = datetime.now()
        current_time = now.time()

        start_time = dt_time(self.config.start_hour, self.config.start_minute)
        end_time = dt_time(self.config.end_hour, self.config.end_minute)

        is_night_hours = self._is_time_in_range(current_time, start_time, end_time)

        if is_night_hours and not self._is_paused:
            self._pause()
        elif not is_night_hours and self._is_paused:
            self._resume()

    def _is_time_in_range(self, current: dt_time, start: dt_time, end: dt_time) -> bool:
        """Determina si la hora actual está en el rango nocturno."""
        if start <= end:
            return start <= current <= end
        else:
            return current >= start or current <= end

    def _pause(self):
        """Pausa todos los servicios controlados."""
        self._is_paused = True
        self._pause_reason = f"Noche ({self.config.start_hour:02d}:00 - {self.config.end_hour:02d}:00)"

        logger.info(f"⏸️ Modo nocturno activado: {self._pause_reason}")

        if self.on_pause_callback:
            try:
                self.on_pause_callback()
            except Exception as e:
                logger.error(f"Error en on_pause_callback: {e}")

        for observer in self._observers:
            try:
                observer.on_night_mode_start()
            except Exception as e:
                logger.error(f"Error notificando observer: {e}")

    def _resume(self):
        """Reanuda todos los servicios controlados."""
        was_paused = self._is_paused
        self._is_paused = False

        logger.info("▶️ Modo nocturno finalizado - Reanudando operaciones")

        if self.on_resume_callback:
            try:
                self.on_resume_callback()
            except Exception as e:
                logger.error(f"Error en on_resume_callback: {e}")

        for observer in self._observers:
            try:
                observer.on_night_mode_end()
            except Exception as e:
                logger.error(f"Error notificando observer: {e}")

    def _get_config_str(self) -> str:
        """Retorna representación string de la configuración."""
        return f"{self.config.start_hour:02d}:{self.config.start_minute:02d} - {self.config.end_hour:02d}:{self.config.end_minute:02d}"

    def is_paused(self) -> bool:
        """Retorna True si está actualmente en pausa por modo nocturno."""
        return self._is_paused

    def should_skip_operation(self, operation_type: str) -> bool:
        """
        Determina si una operación debe ser saltada basándose en el tipo.
        Args:
            operation_type: Tipo de operación ('download', 'monitor', 'process')
        Returns:
            True si la operación debe ser saltada
        """
        if not self._is_paused:
            return False

        if operation_type == "download" and self.config.pause_downloads:
            return True
        if operation_type == "monitor" and self.config.pause_monitoring:
            return True
        if operation_type == "process" and self.config.pause_processing:
            return True

        return False

    def add_observer(self, observer):
        """Agrega un observador para notificaciones de pause/resume."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """Remueve un observador."""
        if observer in self._observers:
            self._observers.remove(observer)

    def update_config(self, config: NightModeConfig):
        """Actualiza la configuración del scheduler."""
        self.config = config
        logger.info(f"Configuración actualizada: {self._get_config_str()}")

    def get_status(self) -> Dict:
        """Retorna el estado actual del scheduler."""
        return {
            "enabled": self.config.enabled,
            "is_paused": self._is_paused,
            "pause_reason": self._pause_reason,
            "schedule": self._get_config_str(),
            "pause_downloads": self.config.pause_downloads,
            "pause_monitoring": self.config.pause_monitoring,
            "pause_processing": self.config.pause_processing
        }

    def get_next_change(self) -> Optional[datetime]:
        """Retorna la próxima hora de cambio de estado."""
        now = datetime.now()
        current_time = now.time()

        start_time = dt_time(self.config.start_hour, self.config.start_minute)
        end_time = dt_time(self.config.end_hour, self.config.end_minute)

        if self._is_paused:
            next_change = datetime.combine(now.date(), end_time)
            if current_time > end_time:
                next_change = datetime.combine((now + timedelta(days=1)).date(), end_time)
        else:
            next_change = datetime.combine(now.date(), start_time)
            if current_time > start_time:
                next_change = datetime.combine((now + timedelta(days=1)).date(), start_time)

        return next_change


from datetime import timedelta


def create_night_mode_scheduler(
    start_hour: int = 2,
    end_hour: int = 6,
    enabled: bool = True
) -> NightModeScheduler:
    """
    Crea y retorna una instancia de NightModeScheduler.
    Args:
        start_hour: Hora de inicio de pausa (default: 2 AM)
        end_hour: Hora de fin de pausa (default: 6 AM)
        enabled: Si el scheduler está habilitado inicialmente
    """
    config = NightModeConfig(
        enabled=enabled,
        start_hour=start_hour,
        end_hour=end_hour
    )
    return NightModeScheduler(config=config)


_global_scheduler: Optional[NightModeScheduler] = None


def get_night_mode_scheduler() -> NightModeScheduler:
    """Obtiene la instancia global del scheduler de modo nocturno."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = create_night_mode_scheduler()
    return _global_scheduler