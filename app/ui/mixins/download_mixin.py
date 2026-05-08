"""
Download Mixin
Gestión de descargas y cola de procesamiento.
"""

import logging
import tkinter as tk
from tkinter import messagebox


class DownloadMixin:
    """Mixin para funcionalidades de descarga y cola de procesamiento."""

    def add_to_queue(self):
        """Añade la URL actual a la cola de descargas."""
        if hasattr(self, 'download_tab_module') and self.download_tab_module:
            try:
                self.download_tab_module.add_to_queue(self)
            except Exception as e:
                self.log(f"[ERROR] No se pudo añadir a la cola: {e}", "error")
        elif hasattr(self, 'download_tab') and self.download_tab:
            try:
                self.download_tab.add_to_queue(self)
            except Exception as e:
                self.log(f"[ERROR] No se pudo añadir a la cola: {e}", "error")
        else:
            messagebox.showerror("Error", "Módulo de pestañas de descarga no cargado.")

    def remove_from_queue(self):
        """Elimina los elementos seleccionados de la cola."""
        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                self.download_tab.remove_from_queue(self)
            except Exception as e:
                self.log(f"[ERROR] Error al eliminar de la cola: {e}", "error")

    def clear_queue(self):
        """Limpia todos los elementos de la cola de procesamiento."""
        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                if messagebox.askyesno("Confirmar", "¿Vaciar toda la cola de descargas?"):
                    self.download_tab.clear_queue(self)
                    self.log("[🗑️] Cola de descargas vaciada.")
            except Exception as e:
                self.log(f"[ERROR] Error al limpiar la cola: {e}", "error")

    def start_download(self):
        """Inicia la descarga individual del campo de URL."""
        if hasattr(self, 'download_service') and self.download_service:
            self.download_service.is_background_mode = False

        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                self.download_tab.start_download(self)
            except Exception as e:
                self.log(f"[ERROR] Fallo al iniciar descarga: {e}", "error")
        else:
            messagebox.showerror("Error", "Servicio de descarga no disponible.")

    def toggle_pause_queue(self):
        """Pausa o reanuda la ejecución de la cola de lotes."""
        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                self.download_tab.toggle_pause_queue(self)
                status = "PAUSADA" if getattr(self, 'queue_paused', False) else "REANUDADA"
                self.log(f"[⏸️] Cola de descargas {status}.")
            except Exception as e:
                self.log(f"[ERROR] Error al cambiar estado de la cola: {e}", "error")

    def start_queue_download(self):
        """Inicia el procesamiento por lotes de toda la cola."""
        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                if not getattr(self, 'download_queue', []):
                    messagebox.showinfo("Info", "La cola está vacía.")
                    return
                self.log(f"[🚀] Iniciando procesamiento por lotes de {len(self.download_queue)} videos...")
                self.download_tab.start_queue_download(self)
            except Exception as e:
                self.log(f"[ERROR] Error crítico en cola de lotes: {e}", "error")
                self.queue_running = False
        else:
            messagebox.showerror("Error", "Servicio de procesamiento por lotes no disponible.")

    def paste_from_clipboard(self):
        """Pega contenido del portapapeles en el campo de URL."""
        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                self.download_tab.paste_from_clipboard(self)
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.debug(f"Error al pegar desde portapapeles: {e}")

    def update_queue_ui(self):
        """Actualiza la interfaz de la cola de descargas."""
        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                self.download_tab.update_queue_ui(self)
            except Exception as e:
                self.log(f"[WARN] Error actualizando UI de cola: {e}")

    def update_channel_combo(self):
        """Actualiza el combobox de canales."""
        if hasattr(self, 'download_tab') and self.download_tab:
            try:
                self.download_tab.update_channel_combo(self)
            except Exception as e:
                self.log(f"[WARN] Error actualizando canal: {e}")