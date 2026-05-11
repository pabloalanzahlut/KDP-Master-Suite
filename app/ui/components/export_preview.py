"""
KDP MASTER - Export Preview Component
=====================================
Componente UI para preview de exportación KB.
Muestra vista previa del contenido antes de generar archivos.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, List, Optional, Callable
import re


class ExportPreviewComponent:
    """Componente de preview para exportaciones KB.

    Características:
    - Preview de entradas con contenido truncado
    - Filtrado visual por categoría
    - Indicadores de tamaño estimado
    - Botón de exportar con configuración
    """

    def __init__(self, parent, on_export_callback: Callable = None):
        self.parent = parent
        self.on_export_callback = on_export_callback
        self.preview_data: Optional[Dict] = None
        self._create_ui()

    def _create_ui(self):
        main_frame = ttk.Frame(self.parent)

        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 10))

        title = ttk.Label(header, text="📋 Vista Previa de Exportación",
                         font=("Inter", 11, "bold"))
        title.pack(side=tk.LEFT)

        self.stats_label = ttk.Label(header, text="", foreground="#666")
        self.stats_label.pack(side=tk.RIGHT)

        filter_bar = ttk.Frame(main_frame)
        filter_bar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_bar, text="Filtrar por categoría:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_filter_var = tk.StringVar(value="")
        self.category_combo = ttk.Combobox(filter_bar, textvariable=self.category_filter_var,
                                          state='readonly', width=20)
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', self._on_filter_change)

        ttk.Button(filter_bar, text="🔄 Limpiar", width=10,
                  command=self._clear_filter).pack(side=tk.LEFT, padx=5)

        list_container = ttk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        columns = ('titulo', 'categoria', 'tamano', 'fecha')
        self.tree = ttk.Treeview(list_container, columns=columns, show='tree headings',
                                height=8, selectmode='extended')

        self.tree.heading('#0', text='')
        self.tree.heading('titulo', text='Título')
        self.tree.heading('categoria', text='Categoría')
        self.tree.heading('tamano', text='Tamaño')
        self.tree.heading('fecha', text='Fecha')

        self.tree.column('#0', width=30, stretch=False)
        self.tree.column('titulo', width=350)
        self.tree.column('categoria', width=120)
        self.tree.column('tamano', width=80, anchor='e')
        self.tree.column('fecha', width=130)

        scroll_y = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(list_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=scroll_x.set)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind('<Double-1>', self._on_entry_double_click)

        self.detail_frame = ttk.LabelFrame(main_frame, text="📄 Detalle de Entrada", padding=10)
        self.detail_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.detail_text = scrolledtext.ScrolledText(self.detail_frame, height=6,
                                                    font=('Consolas', 9), wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_text.configure(state='disabled')

        btn_bar = ttk.Frame(main_frame)
        btn_bar.pack(fill=tk.X, pady=(10, 0))

        self.select_all_btn = ttk.Button(btn_bar, text="☑️ Seleccionar Todo",
                                        command=self._select_all)
        self.select_all_btn.pack(side=tk.LEFT, padx=2)

        self.deselect_all_btn = ttk.Button(btn_bar, text="⬜ Deseleccionar Todo",
                                           command=self._deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=2)

        ttk.Label(btn_bar, text="|").pack(side=tk.LEFT, padx=10)

        self.selected_count_var = tk.StringVar(value="0 seleccionados")
        ttk.Label(btn_bar, textvariable=self.selected_count_var).pack(side=tk.LEFT, padx=5)

        self.export_btn = ttk.Button(btn_bar, text="📤 Exportar Selección",
                                     style="Primary.TButton",
                                     command=self._export_selected)
        self.export_btn.pack(side=tk.RIGHT, padx=2)

        self.export_all_btn = ttk.Button(btn_bar, text="📤 Exportar Todo",
                                        style="Success.TButton",
                                        command=self._export_all)
        self.export_all_btn.pack(side=tk.RIGHT, padx=2)

        return main_frame

    def load_preview(self, preview_data: Dict):
        """Carga datos de preview y los muestra en el componente."""
        self.preview_data = preview_data

        entries = preview_data.get('entries', [])
        categories = preview_data.get('categories', [])
        total = preview_data.get('total_count', 0)
        estimated = preview_data.get('estimated_size_kb', 0)

        self.stats_label.configure(text=f"Total: {total} | ~{estimated:.1f} KB")

        self.category_combo['values'] = ['Todos'] + list(categories)
        self.category_filter_var.set('Todos')

        self._populate_tree(entries)

    def _populate_tree(self, entries: List[Dict], category_filter: str = None):
        self.tree.delete(*self.tree.get_children())

        for entry in entries:
            cat = entry.get('category', 'General')
            if category_filter and category_filter != 'Todos' and cat != category_filter:
                continue

            title = entry.get('title', 'Sin título')[:60]
            content = entry.get('content_preview', '')
            size = len(content.encode('utf-8')) if content else 0
            size_str = self._format_size(size)
            timestamp = entry.get('timestamp', 'N/A')
            source = entry.get('source', '')

            self.tree.insert('', tk.END, iid=entry.get('title', ''),
                           values=(title, cat, size_str, timestamp[:16] if timestamp else 'N/A'),
                           tags=('entry',))

            if content:
                content_short = content[:200] + '...' if len(content) > 200 else content
                self.tree.insert(entry.get('title', ''), tk.END, text=content_short)

        self._update_selection_count()

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _on_filter_change(self, event=None):
        category = self.category_filter_var.get()
        if self.preview_data:
            self._populate_tree(self.preview_data.get('entries', []), category)

    def _clear_filter(self):
        self.category_filter_var.set('Todos')
        if self.preview_data:
            self._populate_tree(self.preview_data.get('entries', []))

    def _on_entry_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, 'values')
        if values:
            title = values[0]
            for entry in self.preview_data.get('entries', []):
                if entry.get('title', '').startswith(title[:30]):
                    self._show_detail(entry)
                    break

    def _show_detail(self, entry: Dict):
        self.detail_text.configure(state='normal')
        self.detail_text.delete('1.0', tk.END)

        content = entry.get('content_preview', entry.get('content', ''))
        detail = f"""Título: {entry.get('title', 'N/A')}
Categoría: {entry.get('category', 'N/A')}
Fuente: {entry.get('source', 'N/A')}
Fecha: {entry.get('timestamp', 'N/A')}

--- Contenido ---
{content}"""

        self.detail_text.insert('1.0', detail)
        self.detail_text.configure(state='disabled')

    def _select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)
        self._update_selection_count()

    def _deselect_all(self):
        self.tree.selection_remove(*self.tree.selection())
        self._update_selection_count()

    def _update_selection_count(self):
        count = len(self.tree.selection())
        self.selected_count_var.set(f"{count} seleccionados")

    def _export_selected(self):
        selection = self.tree.selection()
        if not selection:
            return

        selected_titles = [self.tree.item(item, 'values')[0] for item in selection
                          if self.tree.item(item, 'values')]

        if self.on_export_callback:
            self.on_export_callback(selected_titles)

    def _export_all(self):
        if self.on_export_callback:
            self.on_export_callback(None)

    def get_widget(self) -> ttk.Frame:
        return self.parent


class ExportPreviewDialog:
    """Diálogo modal para preview de exportación."""

    def __init__(self, parent, preview_data: Dict, on_export_callback: Callable = None):
        self.parent = parent
        self.preview_data = preview_data
        self.on_export_callback = on_export_callback
        self.dialog = None
        self.component = None

    def show(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("👁️ Vista Previa - Exportación KB")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        header = ttk.Frame(self.dialog)
        header.pack(fill=tk.X, padx=15, pady=10)

        ttk.Label(header, text="📋 Vista Previa de Exportación",
                 font=("Inter", 14, "bold")).pack(side=tk.LEFT)

        ttk.Button(header, text="✕", width=3,
                  command=self.dialog.destroy).pack(side=tk.RIGHT)

        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.component = ExportPreviewComponent(container, on_export_callback=self.on_export_callback)
        self.component.load_preview(self.preview_data)

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        ttk.Button(btn_frame, text="Cancelar",
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

        ttk.Button(btn_frame, text="📤 Exportar",
                  style="Primary.TButton",
                  command=self._on_export).pack(side=tk.RIGHT, padx=5)

        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())

    def _on_export(self):
        if self.on_export_callback:
            self.on_export_callback(None)
        self.dialog.destroy()


def show_export_preview(parent, preview_data: Dict, on_export_callback: Callable = None):
    """Función helper para mostrar diálogo de preview."""
    dialog = ExportPreviewDialog(parent, preview_data, on_export_callback)
    dialog.show()
    return dialog
