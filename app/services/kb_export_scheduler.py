"""
KDP MASTER - KB Export Scheduler
=============================
Scheduler para exportaciones automáticas de Base de Conocimiento.
Extiende DuplicateExportScheduler con características específicas para KB.

Características:
- Frecuencias: hourly, daily, weekly, monthly
- Ejecución automática según schedule
- Notificaciones al completar/fallar
- Historial de ejecuciones
- Integración con KBExportService
"""

# ============================================================
# IMPORTS
# ============================================================

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable

from app.services.kb_export_service import (
    KBExportService,
    ExportFilters,
    ExportResult
)

logger = logging.getLogger(__name__)

# ============================================================
# CLASE: KBExportScheduler
# ============================================================

class KBExportScheduler:
    """Scheduler para exportaciones automáticas de KB.

    Características:
    - Frecuencias configurables: hourly, daily, weekly, monthly
    - Callback para notificaciones (on_complete, on_error)
    - Logging de ejecuciones
    - Ejecución manual forzada
    """

    def __init__(self, export_service: KBExportService = None,
                 on_complete: Callable = None, on_error: Callable = None):
        """Inicializa el scheduler.

        Args:
            export_service: Instancia de KBExportService
            on_complete: Callback al completar exportación
            on_error: Callback al fallar exportación
        """
        self.export_service = export_service or KBExportService()

        # Callbacks
        self.on_complete = on_complete
        self.on_error = on_error

        # Estado
        self._running = False
        self._thread = None

        # Configuración
        self._config: Dict = {
            "enabled": False,
            "frequency": "daily",
            "hour": 2,
            "minute": 0,
            "last_export": None,
            "next_export": None,
            "template": "full",
            "compression": False,
            "incremental": False
        }

        # Cargar configuración guardada
        self._load_config()

    def configure(self, enabled: bool, frequency: str = "daily",
                  hour: int = 2, minute: int = 0,
                  template: str = "full", compression: bool = False,
                  incremental: bool = False):
        """Configura el scheduler.

        Args:
            enabled: Si está habilitado
            frequency: Frecuencia (hourly/daily/weekly/monthly)
            hour: Hora de ejecución
            minute: Minuto de ejecución
            template: Plantilla a usar
            compression: Si comprimir en ZIP
            incremental: Si usar exportación incremental
        """
        next_run = self._calculate_next_run(hour, minute, frequency)

        self._config = {
            "enabled": enabled,
            "frequency": frequency,
            "hour": hour,
            "minute": minute,
            "last_export": self._config.get("last_export"),
            "next_export": next_run.isoformat() if next_run else None,
            "template": template,
            "compression": compression,
            "incremental": incremental
        }

        self._save_config()

        # Iniciar/detener según enabled
        if enabled and not self._running:
            self.start()
        elif not enabled and self._running:
            self.stop()

        logger.info(f"KB Scheduler configurado: enabled={enabled}, freq={frequency}, {hour:02d}:{minute:02d}")

    def _calculate_next_run(self, hour: int, minute: int, frequency: str) -> datetime:
        """Calcula la próxima ejecución según frecuencia."""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            if frequency == "hourly":
                next_run = now + timedelta(hours=1)
            elif frequency == "daily":
                next_run += timedelta(days=1)
            elif frequency == "weekly":
                next_run += timedelta(days=7)
            elif frequency == "monthly":
                next_run += timedelta(days=30)

        return next_run

    def _save_config(self):
        """Guarda configuración a archivo."""
        try:
            config_path = self.export_service.output_dir / "kb_export_scheduler.json"
            config_path.write_text(
                datetime.now().isoformat() + "\n" +
                str(self._config),
                encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Error guardando scheduler config: {e}")

    def _load_config(self):
        """Carga configuración desde archivo."""
        try:
            config_path = self.export_service.output_dir / "kb_export_scheduler.json"
            if config_path.exists():
                content = config_path.read_text(encoding="utf-8")
                # Cargar desde JSON en el servicio ya existente
                loaded = self.export_service.load_scheduler_config()
                if loaded:
                    self._config.update(loaded)
        except Exception as e:
            logger.warning(f"Error cargando scheduler config: {e}")

    def start(self):
        """Inicia el scheduler en hilo separado."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("KB Scheduler iniciado")

    def stop(self):
        """Detiene el scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("KB Scheduler detenido")

    def _run_loop(self):
        """Loop principal del scheduler."""
        while self._running:
            try:
                now = datetime.now()
                frequency = self._config.get("frequency", "daily")
                hour = self._config.get("hour", 2)
                minute = self._config.get("minute", 0)

                # Calcular próxima ejecución
                next_run = self._calculate_next_run(hour, minute, frequency)
                next_run_str = self._config.get("next_export")

                if next_run_str:
                    try:
                        next_run = datetime.fromisoformat(next_run_str)
                    except:
                        pass

                # Verificar si es hora de ejecutar
                if now >= next_run:
                    logger.info(f"Ejecutando scheduled export: {now}")
                    self._execute_export()

                    # Calcular siguiente ejecución
                    next_run = self._calculate_next_run(hour, minute, frequency)
                    self._config["next_export"] = next_run.isoformat()
                    self._save_config()

                # Dormir 60 segundos antes de volver a verificar
                time.sleep(60)

            except Exception as e:
                logger.error(f"Error en scheduler loop: {e}")
                time.sleep(60)

    def _execute_export(self):
        """Ejecuta la exportación programada."""
        template = self._config.get("template", "full")
        compression = self._config.get("compression", False)
        incremental = self._config.get("incremental", False)

        try:
            if incremental:
                result = self.export_service.export_incremental(
                    format="html",
                    template=template
                )
            else:
                result = self.export_service.export(
                    format="html",
                    template=template,
                    compression=compression
                )

            # Actualizar última ejecución
            self._config["last_export"] = datetime.now().isoformat()
            self._save_config()

            # Notificar según resultado
            if result.success:
                logger.info(f"Scheduled export completado: {result.entries_count} entradas")
                if self.on_complete:
                    self.on_complete(result)
            else:
                logger.error(f"Scheduled export falló: {result.error}")
                if self.on_error:
                    self.on_error(result.error)

        except Exception as e:
            logger.error(f"Error en scheduled export: {e}")
            if self.on_error:
                self.on_error(str(e))

    def force_export(self):
        """Fuerza una exportación inmediata."""
        self._execute_export()

    def get_status(self) -> Dict:
        """Retorna estado del scheduler."""
        return {
            "running": self._running,
            **self._config
        }

    def get_last_export_info(self) -> Dict:
        """Retorna información de la última exportación."""
        return self.export_service.get_last_export_info() or {}


# ============================================================
# FUNCIÓN DE CONVENIENCIA
# ============================================================

def create_kb_scheduler(
    frequency: str = "daily",
    hour: int = 2,
    minute: int = 0,
    template: str = "full",
    compression: bool = False,
    incremental: bool = False,
    on_complete: Callable = None,
    on_error: Callable = None
) -> KBExportScheduler:
    """Crea y configura un KBExportScheduler.

    Uso:
        def on_complete(result):
            print(f"Export completado: {result.output_path}")

        scheduler = create_kb_scheduler(
            frequency="daily",
            hour=2,
            on_complete=on_complete
        )
        scheduler.start()
    """
    service = KBExportService()
    scheduler = KBExportScheduler(
        export_service=service,
        on_complete=on_complete,
        on_error=on_error
    )
    scheduler.configure(
        enabled=True,
        frequency=frequency,
        hour=hour,
        minute=minute,
        template=template,
        compression=compression,
        incremental=incremental
    )
    return scheduler


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "start":
            scheduler = create_kb_scheduler(
                frequency="daily",
                hour=2,
                minute=0
            )
            scheduler.start()
            print("Scheduler iniciado. Presiona Ctrl+C para detener.")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                scheduler.stop()
                print("Scheduler detenido.")

        elif command == "run":
            service = KBExportService()
            result = service.export_incremental()
            print(f"Export: {result.output_path}")

        else:
            print(f"Comando desconocido: {command}")
            sys.exit(1)
    else:
        service = KBExportService()
        history = service.get_export_history(limit=5)
        print(f"Últimas {len(history)} exportaciones:")
        for h in history:
            print(f"  [{h.id}] {h.export_date} - {h.entries_count} entradas - {h.status}")