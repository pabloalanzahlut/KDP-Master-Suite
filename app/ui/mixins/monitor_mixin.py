"""
Monitor Mixin
Gestión del monitor de canales y seguimiento de videos.
"""

import logging
import tkinter as tk
from tkinter import messagebox


class MonitorMixin:
    """Mixin para funcionalidades de monitoreo de canales."""

    def start_monitor(self):
        """Inicia el servicio de monitoreo de canales."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.start_monitor(self)
            except Exception as e:
                self.log(f"[ERROR] Error al iniciar monitor: {e}", "error")

    def stop_monitor(self):
        """Detiene el servicio de monitoreo."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.stop_monitor(self)
            except Exception as e:
                self.log(f"[ERROR] Error al detener monitor: {e}", "error")

    def check_now(self):
        """Fuerza una verificación inmediata de canales."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.check_now(self)
            except Exception as e:
                self.log(f"[ERROR] Error al verificar canales: {e}", "error")

    def toggle_monitor(self):
        """Alterna el estado del monitor (legacy)."""
        return self.toggle_monitor_service()

    def toggle_monitor_service(self):
        """Alterna el estado del servicio de monitoreo."""
        if hasattr(self, 'monitor_service') and self.monitor_service:
            try:
                if getattr(self, 'monitor_var', False):
                    self.monitor_service.stop()
                    self.monitor_var.set(False)
                    self.log("[MONITOR] Monitoreo detenido.")
                else:
                    self.monitor_service.start()
                    self.monitor_var.set(True)
                    self.log("[MONITOR] Monitoreo iniciado.")
            except Exception as e:
                self.log(f"[ERROR] Error al cambiar estado del monitor: {e}", "error")

    def add_channel_quick(self):
        """Añade un canal rápidamente (diálogo rápido)."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.add_channel_quick(self)
            except Exception as e:
                self.log(f"[ERROR] Error al añadir canal: {e}", "error")

    def add_channel_dialog(self):
        """Abre el diálogo completo para añadir canal."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.add_channel_dialog(self)
            except Exception as e:
                self.log(f"[ERROR] Error al abrir diálogo de canal: {e}", "error")

    def remove_selected_channel(self):
        """Elimina el canal seleccionado."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.remove_selected_channel(self)
            except Exception as e:
                self.log(f"[ERROR] Error al eliminar canal: {e}", "error")

    def refresh_channel_list(self):
        """Actualiza la lista de canales monitoreados."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.refresh_channel_list(self)
            except Exception as e:
                self.log(f"[WARN] Error al actualizar lista de canales: {e}")

    def update_monitor_stats(self):
        """Actualiza las estadísticas del monitor."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.update_monitor_stats(self)
            except Exception as e:
                self.log(f"[WARN] Error actualizando estadísticas: {e}")

    def update_monitor_ui(self):
        """Actualiza la interfaz del monitor."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.update_monitor_ui(self)
            except Exception as e:
                self.log(f"[WARN] Error actualizando UI del monitor: {e}")

    def show_channel_videos(self, event):
        """Muestra los videos del canal seleccionado."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.show_channel_videos(self, event)
            except Exception as e:
                self.log(f"[WARN] Error mostrando videos del canal: {e}")

    def on_monitor_new_video(self, video):
        """Callback cuando se detecta un nuevo video."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.on_monitor_new_video(self, video)
            except Exception as e:
                self.log(f"[WARN] Error en callback de nuevo video: {e}")

    def on_monitor_processing_complete(self, video):
        """Callback cuando termina el procesamiento de un video."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.on_monitor_processing_complete(self, video)
            except Exception as e:
                self.log(f"[WARN] Error en callback de procesamiento: {e}")

    def on_monitor_error(self, error):
        """Callback cuando ocurre un error en el monitor."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.on_monitor_error(self, error)
            except Exception as e:
                self.log(f"[WARN] Error en callback de error: {e}")

    def check_selected_channel(self):
        """Verifica el canal seleccionado."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.check_selected_channel(self)
            except Exception as e:
                self.log(f"[WARN] Error al verificar canal: {e}")

    def edit_selected_channel(self):
        """Edita el canal seleccionado."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.edit_selected_channel(self)
            except Exception as e:
                self.log(f"[ERROR] Error al editar canal: {e}")

    def copy_channel_url(self):
        """Copia la URL del canal al portapapeles."""
        if hasattr(self, 'monitor_tab') and self.monitor_tab:
            try:
                self.monitor_tab.copy_channel_url(self)
            except Exception as e:
                self.log(f"[WARN] Error al copiar URL: {e}")