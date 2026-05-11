"""
KDP MASTER - Export Settings Tab
================================
Pestaña de configuración de exportación de Base de Conocimiento.
Panel UI para configurar exportaciones (formato, plantilla, filtros, scheduler).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import simpledialog
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import json

try:
    import customtkinter as ctk
except ImportError:
    ctk = None


class ExportSettingsTab:
    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.config_file = getattr(app_instance, 'config_file', None)
        self.export_service = None
        self.scheduler = None

        self._init_export_service()
        self._create_ui()
        self._load_settings()

    def _init_export_service(self):
        try:
            from app.services.kb_export_service import KBExportService
            from app.services.kb_export_scheduler import KBExportScheduler

            self.export_service = KBExportService()
            self.scheduler = KBExportScheduler(export_service=self.export_service)
        except ImportError as e:
            self.app.logger.warning(f"KBExportService no disponible: {e}")

    def _create_ui(self):
        container = ttk.Frame(self.parent)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title = ttk.Label(container, text="📤 Configuración de Exportación KB",
                         font=("Inter", 14, "bold"))
        title.pack(anchor=tk.W, pady=(0, 15))

        options_frame = ttk.LabelFrame(container, text="⚙️ Opciones de Exportación", padding=15)
        options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        scheduler_frame = ttk.LabelFrame(container, text="📊 Programación Automática", padding=15)
        scheduler_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self._build_export_options(options_frame)
        self._build_scheduler_options(scheduler_frame)
        self._build_action_buttons(container)

    def _build_export_options(self, parent):
        format_frame = ttk.LabelFrame(parent, text="📋 Formato de Salida", padding=10)
        format_frame.pack(fill=tk.X, pady=(0, 15))

        self.format_var = tk.StringVar(value="html")
        formats = [
            ("HTML", "html", "Archivo HTML con estilos"),
            ("PDF", "pdf", "Archivo PDF (requiere WeasyPrint)"),
            ("ZIP", "zip", "Comprimir en archivo ZIP"),
            ("BOTH", "both", "HTML + PDF")
        ]

        for text, value, desc in formats:
            ttk.Radiobutton(format_frame, text=f"{text} - {desc}",
                           variable=self.format_var, value=value).pack(anchor=tk.W, pady=2)

        template_frame = ttk.LabelFrame(parent, text="📄 Plantilla", padding=10)
        template_frame.pack(fill=tk.X, pady=(0, 15))

        self.template_var = tk.StringVar(value="complete")
        templates = [
            ("Completo", "complete", "Índice, búsqueda y estilos completos"),
            ("Minimal", "minimal", "Solo contenido sin estilos"),
            ("Solo Índice", "index_only", "Solo índice navegable")
        ]

        for text, value, desc in templates:
            ttk.Radiobutton(template_frame, text=f"{text} - {desc}",
                           variable=self.template_var, value=value).pack(anchor=tk.W, pady=2)

        filters_frame = ttk.LabelFrame(parent, text="🔍 Filtros Pre-Export", padding=10)
        filters_frame.pack(fill=tk.X, pady=(0, 15))

        self.enable_filters_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters_frame, text="Habilitar filtros",
                       variable=self.enable_filters_var,
                       command=self._toggle_filters).pack(anchor=tk.W)

        filter_options = ttk.Frame(filters_frame)
        filter_options.pack(fill=tk.X, pady=(10, 0))

        self.categories_var = tk.StringVar(value="")
        ttk.Label(filter_options, text="Categorías:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.categories_entry = ttk.Entry(filter_options, textvariable=self.categories_var, width=25)
        self.categories_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(filter_options, text="(separadas por coma)").grid(row=1, column=1, sticky=tk.W, padx=5)

        self.days_filter_var = tk.IntVar(value=0)
        ttk.Label(filter_options, text="Últimos días:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.days_entry = ttk.Entry(filter_options, textvariable=self.days_filter_var, width=10)
        self.days_entry.grid(row=2, column=1, sticky=tk.W, padx=5)

        self.incremental_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filters_frame, text="Exportación incremental (solo entradas nuevas)",
                       variable=self.incremental_var).pack(anchor=tk.W, pady=(10, 0))

        limits_frame = ttk.LabelFrame(parent, text="📏 Límites", padding=10)
        limits_frame.pack(fill=tk.X)

        ttk.Label(limits_frame, text="Máx. entradas por archivo:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.max_entries_var = tk.IntVar(value=500)
        ttk.Entry(limits_frame, textvariable=self.max_entries_var, width=10).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(limits_frame, text="Umbral split (KB):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.split_threshold_var = tk.IntVar(value=2000)
        ttk.Entry(limits_frame, textvariable=self.split_threshold_var, width=10).grid(row=1, column=1, sticky=tk.W)

        self._toggle_filters()

    def _build_scheduler_options(self, parent):
        self.scheduler_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Habilitar exportación automática",
                       variable=self.scheduler_enabled_var,
                       command=self._toggle_scheduler).pack(anchor=tk.W, pady=(0, 10))

        self.frequency_var = tk.StringVar(value="daily")
        ttk.Label(parent, text="Frecuencia:").pack(anchor=tk.W, pady=(5, 0))
        frequencies = [
            ("Cada Hora", "hourly"),
            ("Diario", "daily"),
            ("Semanal", "weekly"),
            ("Mensual", "monthly")
        ]
        for text, value in frequencies:
            ttk.Radiobutton(parent, text=text, variable=self.frequency_var,
                           value=value).pack(anchor=tk.W, padx=20)

        time_frame = ttk.Frame(parent)
        time_frame.pack(fill=tk.X, pady=10)
        ttk.Label(time_frame, text="Hora de ejecución:").pack(anchor=tk.W)

        time_inner = ttk.Frame(time_frame)
        time_inner.pack(anchor=tk.W, pady=5)

        self.hour_var = tk.IntVar(value=2)
        self.minute_var = tk.IntVar(value=0)

        hour_spin = ttk.Spinbox(time_inner, from_=0, to=23, textvariable=self.hour_var, width=5)
        hour_spin.pack(side=tk.LEFT)
        ttk.Label(time_inner, text=":").pack(side=tk.LEFT)
        minute_spin = ttk.Spinbox(time_inner, from_=0, to=59, textvariable=self.minute_var, width=5)
        minute_spin.pack(side=tk.LEFT)

        self.scheduler_compression_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Comprimir en ZIP automáticamente",
                       variable=self.scheduler_compression_var).pack(anchor=tk.W, pady=(10, 0))

        status_frame = ttk.LabelFrame(parent, text="📊 Estado del Scheduler", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        self.scheduler_status_var = tk.StringVar(value="⏸️ Detenido")
        ttk.Label(status_frame, textvariable=self.scheduler_status_var,
                  font=("Inter", 10, "bold")).pack(pady=5)

        ttk.Button(status_frame, text="🔄 Actualizar",
                  command=self._refresh_scheduler_status).pack(pady=5)

    def _build_action_buttons(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(btn_frame, text="👁️ Vista Previa",
                   command=self._show_preview).pack(side=tk.LEFT, padx=2)

        ttk.Button(btn_frame, text="📤 Exportar Ahora",
                   command=self._run_export, style="Primary.TButton").pack(side=tk.LEFT, padx=2)

        ttk.Button(btn_frame, text="💾 Guardar Config",
                   command=self._save_settings).pack(side=tk.LEFT, padx=2)

        ttk.Button(btn_frame, text="🗑️ Limpiar Historial",
                   command=self._clear_history).pack(side=tk.RIGHT, padx=2)

    def _toggle_filters(self):
        state = 'normal' if self.enable_filters_var.get() else 'disabled'
        for child in self.parent.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                for item in child.winfo_children():
                    if hasattr(item, 'winfo_children'):
                        for child_item in item.winfo_children():
                            try:
                                child_item.configure(state=state)
                            except:
                                pass

    def _toggle_scheduler(self):
        state = 'normal' if self.scheduler_enabled_var.get() else 'disabled'
        for child in self.parent.winfo_children():
            if isinstance(child, ttk.PanedWindow):
                for panel in child.winfo_children():
                    if hasattr(panel, 'winfo_children'):
                        for item in panel.winfo_children():
                            try:
                                item.configure(state=state)
                            except:
                                pass

    def _show_preview(self):
        try:
            from app.services.kb_export_service import ExportFilters

            filters = None
            if self.enable_filters_var.get():
                categories = self.categories_var.get().split(',') if self.categories_var.get() else []
                categories = [c.strip() for c in categories if c.strip()]

                filters = ExportFilters(
                    categories=categories,
                    days_back=self.days_filter_var.get() if self.days_filter_var.get() > 0 else None,
                    last_export_id=0 if self.incremental_var.get() else None
                )

            preview_data = self.export_service.preview_export(filters=filters, max_entries=10)

            self._display_preview_dialog(preview_data)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar preview: {e}")

    def _display_preview_dialog(self, preview_data: Dict):
        dialog = tk.Toplevel(self.parent)
        dialog.title("👁️ Vista Previa de Exportación")
        dialog.geometry("700x500")
        dialog.transient(self.parent)
        dialog.grab_set()

        header = ttk.Label(dialog, text="📋 Vista Previa - Exportación KB",
                          font=("Inter", 12, "bold"))
        header.pack(pady=10)

        info_frame = ttk.LabelFrame(dialog, text="📊 Estadísticas", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        total_entries = preview_data.get('total_count', 0)
        preview_count = preview_data.get('preview_count', 0)
        estimated_size = preview_data.get('estimated_size_kb', 0)
        categories = preview_data.get('categories', [])

        ttk.Label(info_frame, text=f"Total entradas: {total_entries}").grid(row=0, column=0, sticky=tk.W, padx=10)
        ttk.Label(info_frame, text=f"Tamaño estimado: ~{estimated_size:.1f} KB").grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Label(info_frame, text=f"Categorías: {len(categories)}").grid(row=1, column=0, sticky=tk.W, padx=10)

        list_frame = ttk.LabelFrame(dialog, text="📝 Primeras Entradas", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        tree = ttk.Treeview(list_frame, columns=('titulo', 'categoria', 'fecha'), show='headings', height=10)
        tree.heading('titulo', text='Título')
        tree.heading('categoria', text='Categoría')
        tree.heading('fecha', text='Fecha')
        tree.column('titulo', width=300)
        tree.column('categoria', width=150)
        tree.column('fecha', width=150)
        tree.pack(fill=tk.BOTH, expand=True)

        for entry in preview_data.get('entries', []):
            tree.insert('', tk.END, values=(
                entry.get('title', 'N/A')[:50],
                entry.get('category', 'N/A'),
                entry.get('timestamp', 'N/A')
            ))

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Cerrar", command=dialog.destroy).pack()

    def _run_export(self):
        try:
            from app.services.kb_export_service import ExportFilters, ExportConfig

            filters = None
            if self.enable_filters_var.get():
                categories = self.categories_var.get().split(',') if self.categories_var.get() else []
                categories = [c.strip() for c in categories if c.strip()]

                filters = ExportFilters(
                    categories=categories,
                    days_back=self.days_filter_var.get() if self.days_filter_var.get() > 0 else None,
                    last_export_id=0 if self.incremental_var.get() else None
                )

            format_type = self.format_var.get()
            compression = format_type == 'zip' or self.format_var.get() == 'both'

            result = self.export_service.export(
                filters=filters,
                format=format_type,
                template=self.template_var.get(),
                compression=compression
            )

            if result.success:
                messagebox.showinfo("Éxito", f"Exportación completada:\n"
                               f"Archivo: {result.output_path}\n"
                               f"Entradas: {result.entries_count}")
            else:
                messagebox.showerror("Error", f"Exportación fallida: {result.error}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo ejecutar exportación: {e}")

    def _save_settings(self):
        settings = {
            "export": {
                "format": self.format_var.get(),
                "template": self.template_var.get(),
                "enable_filters": self.enable_filters_var.get(),
                "categories": self.categories_var.get(),
                "days_filter": self.days_filter_var.get(),
                "incremental": self.incremental_var.get(),
                "max_entries": self.max_entries_var.get(),
                "split_threshold": self.split_threshold_var.get()
            },
            "export_scheduler": {
                "enabled": self.scheduler_enabled_var.get(),
                "frequency": self.frequency_var.get(),
                "hour": self.hour_var.get(),
                "minute": self.minute_var.get(),
                "compression": self.scheduler_compression_var.get()
            }
        }

        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                existing.update(settings)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, indent=2)
                messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
        else:
            config_path = Path("settings.json")
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)
                messagebox.showinfo("Éxito", f"Configuración guardada en {config_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def _load_settings(self):
        settings = {}
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except:
                pass

        export_settings = settings.get("export", {})
        self.format_var.set(export_settings.get("format", "html"))
        self.template_var.set(export_settings.get("template", "complete"))
        self.enable_filters_var.set(export_settings.get("enable_filters", False))
        self.categories_var.set(export_settings.get("categories", ""))
        self.days_filter_var.set(export_settings.get("days_filter", 0))
        self.incremental_var.set(export_settings.get("incremental", True))
        self.max_entries_var.set(export_settings.get("max_entries", 500))
        self.split_threshold_var.set(export_settings.get("split_threshold", 2000))

        sched_settings = settings.get("export_scheduler", {})
        self.scheduler_enabled_var.set(sched_settings.get("enabled", False))
        self.frequency_var.set(sched_settings.get("frequency", "daily"))
        self.hour_var.set(sched_settings.get("hour", 2))
        self.minute_var.set(sched_settings.get("minute", 0))
        self.scheduler_compression_var.set(sched_settings.get("compression", False))

        self._toggle_filters()
        self._toggle_scheduler()
        self._refresh_scheduler_status()

    def _clear_history(self):
        if messagebox.askyesno("Confirmar", "¿Limpiar historial de exportaciones?"):
            try:
                history = self.export_service.get_export_history(limit=1000)
                if hasattr(self.export_service, 'init_export_history'):
                    messagebox.showinfo("Info", f"Historial actual: {len(history)} entradas")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo limpiar: {e}")

    def _refresh_scheduler_status(self):
        if self.scheduler:
            status = self.scheduler.get_status()
            running = status.get("running", False)
            self.scheduler_status_var.set("✅ Activo" if running else "⏸️ Detenido")
        else:
            self.scheduler_status_var.set("⏸️ No disponible")


def setup_export_settings_tab(parent, app_instance):
    """Factory para crear la pestaña de configuración de exportación."""
    return ExportSettingsTab(parent, app_instance)
