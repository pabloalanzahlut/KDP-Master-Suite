"""
Processing Mixin
Gestión de procesamiento de archivos y transcripciones.
"""

import logging
import os
import tkinter as tk
from tkinter import messagebox, filedialog


class ProcessingMixin:
    """Mixin para funcionalidades de procesamiento de archivos."""

    def refresh_file_list(self):
        """Actualiza la lista de archivos en la pestaña de procesamiento."""
        if hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.refresh_file_list(self)
            except Exception as e:
                self.log(f"[ERROR] Error al actualizar lista: {e}", "error")

    def start_processing(self):
        """Inicia el procesamiento de los archivos seleccionados."""
        if hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.start_processing(self)
            except Exception as e:
                self.log(f"[ERROR] Error al iniciar procesamiento: {e}", "error")

    def display_metadata(self, event):
        """Muestra los metadatos del archivo seleccionado."""
        if hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.display_metadata(self, event)
            except Exception as e:
                self.log(f"[WARN] Error mostrando metadatos: {e}")

    def browse_input(self):
        """Abre diálogo para seleccionar directorio de entrada."""
        if hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.browse_input(self)
            except Exception as e:
                self.log(f"[ERROR] Error al seleccionar directorio: {e}")
        else:
            directory = filedialog.askdirectory(title="Seleccionar Directorio de Entrada")
            if directory and hasattr(self, 'input_dir'):
                self.input_dir.set(directory)

    def browse_output(self):
        """Abre diálogo para seleccionar directorio de salida."""
        if hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.browse_output(self)
            except Exception as e:
                self.log(f"[ERROR] Error al seleccionar directorio: {e}")
        else:
            directory = filedialog.askdirectory(title="Seleccionar Directorio de Salida")
            if directory and hasattr(self, 'output_dir'):
                self.output_dir.set(directory)

    def select_all_files(self):
        """Selecciona todos los archivos en la lista."""
        if hasattr(self, 'tree'):
            for item in self.tree.get_children():
                self.tree.selection_add(item)
        elif hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.select_all_files(self)
            except Exception as e:
                self.log(f"[WARN] Error al seleccionar archivos: {e}")

    def delete_selected_file(self):
        """Elimina el archivo seleccionado."""
        if hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.delete_selected_file(self)
            except Exception as e:
                self.log(f"[ERROR] Error al eliminar archivo: {e}")

    def open_file_location(self):
        """Abre la ubicación del archivo seleccionado."""
        if hasattr(self, 'process_tab') and self.process_tab:
            try:
                self.process_tab.open_file_location(self)
            except Exception as e:
                self.log(f"[ERROR] Error al abrir ubicación: {e}")

    def setup_process_tab(self):
        """Configura la pestaña de procesamiento."""
        if hasattr(self, 'process_tab') and self.process_tab:
            self.process_tab.setup_process_tab(self)

    def validate_directories(self):
        """Valida que los directorios necesarios existan."""
        dirs_to_check = []
        if hasattr(self, 'input_dir'):
            dirs_to_check.append(self.input_dir.get())
        if hasattr(self, 'output_dir'):
            dirs_to_check.append(self.output_dir.get())
        
        for d in dirs_to_check:
            if d and not os.path.exists(d):
                try:
                    os.makedirs(d, exist_ok=True)
                except Exception as e:
                    self.log(f"[WARN] No se pudo crear directorio {d}: {e}")