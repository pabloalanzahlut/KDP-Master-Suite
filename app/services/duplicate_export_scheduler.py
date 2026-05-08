"""
KDP_MASTER - Duplicate Export Scheduler
=======================================
Scheduler para exportación automática de duplicados.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)


class DuplicateExportScheduler:
    """
    Scheduler para exportación automática de duplicados.

    Frecuencias disponibles:
    - daily: Todos los días a la hora especificada
    - weekly: Una vez por semana
    - monthly: Una vez al mes
    """

    def __init__(self, db_manager, export_callback: Callable):
        self.db = db_manager
        self.export_callback = export_callback
        self._running = False
        self._thread = None
        self._schedule_config: Dict = {
            'enabled': False,
            'frequency': 'daily',
            'hour': 2,
            'minute': 0,
            'export_dir': None,
            'last_export': None,
            'next_export': None
        }

    def configure(self, enabled: bool, frequency: str = 'daily',
                  hour: int = 2, minute: int = 0, export_dir: str = None):
        """Configura el scheduler."""
        self._schedule_config = {
            'enabled': enabled,
            'frequency': frequency,
            'hour': hour,
            'minute': minute,
            'export_dir': export_dir,
            'last_export': self._schedule_config.get('last_export'),
            'next_export': self._calculate_next_run(hour, minute, frequency)
        }
        self._save_config()

        if enabled and not self._running:
            self.start()
        elif not enabled and self._running:
            self.stop()

        logger.info(f"Scheduler configurado: enabled={enabled}, freq={frequency}, {hour}:{minute:02d}")

    def _calculate_next_run(self, hour: int, minute: int, frequency: str) -> Optional[datetime]:
        """Calcula la próxima ejecución."""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            if frequency == 'daily':
                next_run += timedelta(days=1)
            elif frequency == 'weekly':
                next_run += timedelta(days=7)
            elif frequency == 'monthly':
                next_run += timedelta(days=30)

        return next_run

    def _save_config(self):
        """Guarda configuración en settings."""
        try:
            if hasattr(self, '_app_settings'):
                self._app_settings['duplicate_export_schedule'] = self._schedule_config
        except Exception as e:
            logger.error(f"Error guardando config scheduler: {e}")

    def load_config(self, settings: Dict):
        """Carga configuración desde settings."""
        config = settings.get('duplicate_export_schedule', {})
        if config:
            self._schedule_config.update(config)
            if self._schedule_config.get('enabled'):
                self.start()

    def start(self):
        """Inicia el scheduler."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduler de exportación iniciado")

    def stop(self):
        """Detiene el scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Scheduler de exportación detenido")

    def _run_loop(self):
        """Loop principal del scheduler."""
        while self._running:
            try:
                now = datetime.now()
                next_run = self._schedule_config.get('next_export')

                if next_run and now >= next_run:
                    self._execute_export()
                    freq = self._schedule_config.get('frequency', 'daily')
                    hour = self._schedule_config.get('hour', 2)
                    minute = self._schedule_config.get('minute', 0)
                    self._schedule_config['next_export'] = self._calculate_next_run(hour, minute, freq)

                time.sleep(60)
            except Exception as e:
                logger.error(f"Error en loop del scheduler: {e}")
                time.sleep(60)

    def _execute_export(self):
        """Ejecuta la exportación."""
        try:
            export_dir = self._schedule_config.get('export_dir')
            if not export_dir:
                logger.warning("Scheduler: export_dir no configurado")
                return

            filename = f"duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = self.export_callback(export_dir=export_dir, filename=filename)

            self._schedule_config['last_export'] = datetime.now().isoformat()
            self._save_config()
            logger.info(f"Exportación automática completada: {filepath}")

        except Exception as e:
            logger.error(f"Error en exportación automática: {e}")

    def get_status(self) -> Dict:
        """Retorna estado del scheduler."""
        return {
            'running': self._running,
            **self._schedule_config
        }

    def force_export(self):
        """Fuerza una exportación inmediata."""
        self._execute_export()
