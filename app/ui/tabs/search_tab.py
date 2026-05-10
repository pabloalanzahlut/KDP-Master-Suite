"""
GUI Tab for Advanced Search - KDP Master
========================================
Pestaña de búsqueda avanzada con sidebar de filtros y TreeView paginado.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import time
import threading
import csv
from datetime import datetime

try:
    from app.database.knowledge_db import KnowledgeDBManager
except ImportError:
    class KnowledgeDBManager:
        def __init__(self, db_path=None):
            self.db_path = db_path
        def search_advanced(self, **kwargs):
            return {'results': [], 'total': 0, 'page': 1, 'pages': 1, 'elapsed_ms': 0}
        def get_tipos(self):
            return []
        def rebuild_fts_index(self):
            return 0, 0


def setup_search_tab(self):
    """
    ================================================================
    MÓDULO: BÚSQUEDA AVANZADA KB - DISEÑO MODERNO
    ================================================================
    Interfaz de búsqueda con filtros laterales y resultados paginados.
    """
    for widget in self.tab_search.winfo_children():
        widget.destroy()
    
    self.kb_search_db = KnowledgeDBManager()
    self.search_page = 1
    self.search_total_pages = 1
    self.search_results_cache = []
    
    search_main = ttk.Frame(self.tab_search)
    search_main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    header_frame = ttk.Frame(search_main)
    header_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(header_frame, text="🔍 Búsqueda en Base de Conocimiento KDP", 
             font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=(0, 20))
    
    self.search_query_var = tk.StringVar()
    search_entry = ttk.Entry(header_frame, textvariable=self.search_query_var, 
                            width=50, font=("Segoe UI", 11))
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    search_entry.bind('<Return>', lambda e: self._search_execute())
    
    btn_frame = ttk.Frame(header_frame)
    btn_frame.pack(side=tk.LEFT, padx=(20, 0))
    
    ttk.Button(btn_frame, text="BUSCAR", command=self._search_execute,
              bootstyle="primary", width=10).pack(side=tk.LEFT, padx=3)
    
    ttk.Button(btn_frame, text="LIMPIAR", command=self._search_clear,
              bootstyle="secondary-outline", width=10).pack(side=tk.LEFT, padx=3)
    
    ttk.Button(btn_frame, text="EXPORTAR CSV", command=self._search_export_csv,
              bootstyle="success-outline", width=14).pack(side=tk.LEFT, padx=3)
    
    main_container = ttk.Frame(search_main)
    main_container.pack(fill=tk.BOTH, expand=True)
    
    sidebar = ttk.Frame(main_container, width=320)
    sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
    sidebar.pack_propagate(False)
    
    date_frame = ttk.LabelFrame(sidebar, text="📅 FILTRO DE FECHA", padding=10)
    date_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(date_frame, text="Desde — Hasta", 
             foreground="#64748b").pack(anchor=tk.W)
    
    date_inputs = ttk.Frame(date_frame)
    date_inputs.pack(fill=tk.X, pady=(5, 0))
    
    self.search_date_from_var = tk.StringVar()
    self.search_date_to_var = tk.StringVar()
    
    ttk.Entry(date_inputs, textvariable=self.search_date_from_var, 
             width=12).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Label(date_inputs, text="—").pack(side=tk.LEFT, padx=5)
    ttk.Entry(date_inputs, textvariable=self.search_date_to_var, 
             width=12).pack(side=tk.LEFT)
    
    ttk.Label(date_frame, text="Formato: YYYY-MM", 
             font=("Segoe UI", 8), foreground="#94a3b8").pack(anchor=tk.W, pady=(5, 0))
    
    type_frame = ttk.LabelFrame(sidebar, text="📋 TIPO DE CONTENIDO", padding=10)
    type_frame.pack(fill=tk.X, pady=(0, 15))
    
    self.search_tipo_var = tk.StringVar(value="Todos")
    tipo_combo = ttk.Combobox(type_frame, textvariable=self.search_tipo_var,
                values=["Todos", "Tutorial", "Artículo", "Investigación", 
                       "Lista", "Legal", "Fórmulas"],
                state="readonly", width=28)
    tipo_combo.pack(fill=tk.X)
    
    status_frame = ttk.LabelFrame(sidebar, text="⚙️ ESTADO DE PROCESADO", padding=10)
    status_frame.pack(fill=tk.X, pady=(0, 15))
    
    self.search_status_var = tk.StringVar(value="Todos")
    status_combo = ttk.Combobox(status_frame, textvariable=self.search_status_var,
                values=["Todos", "Procesado", "Pendiente", "Error"],
                state="readonly", width=28)
    status_combo.pack(fill=tk.X)
    
    fields_frame = ttk.LabelFrame(sidebar, text="✓ CAMPOS A INCLUIR", padding=10)
    fields_frame.pack(fill=tk.X, pady=(0, 15))
    
    self.search_check_all = tk.BooleanVar(value=True)
    self.search_check_structure = tk.BooleanVar(value=True)
    self.search_check_format = tk.BooleanVar(value=False)
    self.search_check_status = tk.BooleanVar(value=False)
    
    checks_grid = ttk.Frame(fields_frame)
    checks_grid.pack(fill=tk.X)
    
    ttk.Checkbutton(checks_grid, text="Todos", 
                   variable=self.search_check_all).grid(row=0, column=0, sticky=tk.W, pady=2)
    ttk.Checkbutton(checks_grid, text="Estructura", 
                   variable=self.search_check_structure).grid(row=0, column=1, sticky=tk.W, pady=2, padx=(15, 0))
    ttk.Checkbutton(checks_grid, text="Formato", 
                   variable=self.search_check_format).grid(row=1, column=0, sticky=tk.W, pady=2)
    ttk.Checkbutton(checks_grid, text="Estado", 
                   variable=self.search_check_status).grid(row=1, column=1, sticky=tk.W, pady=2, padx=(15, 0))
    
    order_frame = ttk.LabelFrame(sidebar, text="↕️ ORDEN CRONOLÓGICO", padding=10)
    order_frame.pack(fill=tk.X)
    
    self.search_order_var = tk.StringVar(value="Nuevo primero")
    ttk.Combobox(order_frame, textvariable=self.search_order_var,
                values=["Nuevo primero", "Antiguo primero"],
                state="readonly", width=28).pack(fill=tk.X)
    
    ttk.Button(sidebar, text="✅ Aplicar Filtros", 
              command=self._search_execute,
              bootstyle="success", width=28).pack(pady=(20, 0))
    
    results_panel = ttk.Frame(main_container)
    results_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    results_header = ttk.Frame(results_panel)
    results_header.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(results_header, text="📄 Resultados:", 
             font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
    
    self.search_count_label = ttk.Label(results_header, text="0", 
                                         foreground="#3b82f6", 
                                         font=("Segoe UI", 10, "bold"))
    self.search_count_label.pack(side=tk.LEFT, padx=(5, 0))
    
    ttk.Label(results_header, text="entradas").pack(side=tk.LEFT, padx=(0, 20))
    
    self.search_fts_label = ttk.Label(results_header, text="FTS5 — 0ms", 
                                    foreground="#64748b", font=("Consolas", 8))
    self.search_fts_label.pack(side=tk.LEFT)
    
    tree_frame = ttk.Frame(results_panel)
    tree_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("id", "category", "tipo", "status", "date", "words", "conf")
    self.search_tree = ttk.Treeview(tree_frame, columns=columns, 
                                   show="headings", height=18)
    
    self.search_tree.heading("id", text="ID")
    self.search_tree.column("id", width=50, anchor=tk.CENTER)
    
    self.search_tree.heading("category", text="CATEGORÍA")
    self.search_tree.column("category", width=180)
    
    self.search_tree.heading("tipo", text="TIPO")
    self.search_tree.column("tipo", width=100, anchor=tk.CENTER)
    
    self.search_tree.heading("status", text="ESTADO")
    self.search_tree.column("status", width=90, anchor=tk.CENTER)
    
    self.search_tree.heading("date", text="FECHA")
    self.search_tree.column("date", width=120, anchor=tk.CENTER)
    
    self.search_tree.heading("words", text="PALABRAS")
    self.search_tree.column("words", width=80, anchor=tk.CENTER)
    
    self.search_tree.heading("conf", text="CONFIANZA")
    self.search_tree.column("conf", width=80, anchor=tk.CENTER)
    
    self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                             command=self.search_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.search_tree.configure(yscrollcommand=scrollbar.set)
    
    self.search_tree.tag_configure("tutorial", background="#1e3a5f", foreground="#60a5fa")
    self.search_tree.tag_configure("articulo", background="#1a3a2f", foreground="#34d399")
    self.search_tree.tag_configure("investigacion", background="#2d1f4a", foreground="#a78bfa")
    self.search_tree.tag_configure("lista", background="#3d3020", foreground="#fbbf24")
    self.search_tree.tag_configure("legal", background="#3d1a1a", foreground="#f87171")
    self.search_tree.tag_configure("formulas", background="#1a3d3d", foreground="#22d3ee")
    self.search_tree.tag_configure("pending", foreground="#f59e0b")
    self.search_tree.tag_configure("error", foreground="#ef4444")
    self.search_tree.tag_configure("oddrow", background="#1e293b")
    self.search_tree.tag_configure("evenrow", background="#0f172a")
    
    self.search_tree.bind('<Double-Button-1>', self._search_view_entry)
    
    pagination_frame = ttk.Frame(results_panel, padding=(0, 15))
    pagination_frame.pack(fill=tk.X)
    
    self.search_page_info = ttk.Label(pagination_frame, 
                                     text="Mostrando 0-0 de 0 resultados · Página 0/0",
                                     foreground="#64748b")
    self.search_page_info.pack(side=tk.LEFT)
    
    self.search_page_buttons_frame = ttk.Frame(pagination_frame)
    self.search_page_buttons_frame.pack(side=tk.RIGHT)
    
    self._search_update_pagination()
    
    search_entry.focus_set()


def _search_execute(self):
    """Ejecuta la búsqueda con filtros."""
    query = self.search_query_var.get().strip()
    
    self.search_page = 1
    
    def do_search():
        start_time = time.time()
        
        try:
            tipo = self.search_tipo_var.get() if hasattr(self, 'search_tipo_var') else "Todos"
            status = self.search_status_var.get() if hasattr(self, 'search_status_var') else "Todos"
            order_val = self.search_order_var.get() if hasattr(self, 'search_order_var') else "Nuevo primero"
            
            order = "newest" if order_val == "Nuevo primero" else "oldest"
            
            result = self.kb_search_db.search_advanced(
                query=query,
                tipo=tipo,
                status=status,
                date_from=self.search_date_from_var.get().strip(),
                date_to=self.search_date_to_var.get().strip(),
                order=order,
                page=self.search_page,
                page_size=50
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self.search_results_cache = result['results']
            self.search_total_pages = result['pages']
            
            def update_ui():
                for item in self.search_tree.get_children():
                    self.search_tree.delete(item)
                
                for idx, row in enumerate(result['results']):
                    tipo_val = row.get('tipo', 'Artículo') or 'Artículo'
                    status_val = row.get('status', 'Procesado') or 'Procesado'
                    conf_val = row.get('confidence_score', 0) or 0
                    words_val = row.get('palabras', 0) or 0
                    timestamp_val = row.get('timestamp', '') or ''
                    category_val = row.get('category', '') or ''
                    
                    tag = tipo_val.lower()
                    if status_val == 'Pendiente':
                        tag += ' pending'
                    elif status_val == 'Error':
                        tag += ' error'
                    
                    self.search_tree.insert('', tk.END, values=(
                        row.get('id', ''),
                        category_val,
                        tipo_val,
                        status_val,
                        timestamp_val[:10] if timestamp_val else '',
                        words_val,
                        f"{conf_val:.1f}%"
                    ), tags=(tag,))
                
                self.search_count_label.config(text=str(result['total']))
                self.search_fts_label.config(text=f"FTS5 — {elapsed_ms:.0f}ms")
                self._search_update_pagination()
            
            self.root.after(0, update_ui)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Búsqueda falló:\n{e}"))
    
    threading.Thread(target=do_search, daemon=True).start()


def _search_clear(self):
    """Limpia todos los filtros y resultados."""
    if hasattr(self, 'search_query_var'):
        self.search_query_var.set("")
    if hasattr(self, 'search_date_from_var'):
        self.search_date_from_var.set("")
    if hasattr(self, 'search_date_to_var'):
        self.search_date_to_var.set("")
    if hasattr(self, 'search_tipo_var'):
        self.search_tipo_var.set("Todos")
    if hasattr(self, 'search_status_var'):
        self.search_status_var.set("Todos")
    if hasattr(self, 'search_order_var'):
        self.search_order_var.set("Nuevo primero")
    
    for item in self.search_tree.get_children():
        self.search_tree.delete(item)
    
    self.search_count_label.config(text="0")
    self.search_fts_label.config(text="FTS5 — 0ms")
    self.search_page = 1
    self.search_total_pages = 1
    self.search_results_cache = []
    self._search_update_pagination()


def _search_update_pagination(self):
    """Actualiza los botones de paginación."""
    for widget in self.search_page_buttons_frame.winfo_children():
        widget.destroy()
    
    total = len(self.search_results_cache)
    start = (self.search_page - 1) * 50 + 1
    end = min(self.search_page * 50, self.search_page * 50 - 1 + total)
    
    if total == 0:
        start = 0
        end = 0
    
    self.search_page_info.config(text=f"Mostrando {start}-{end} de {self.search_total_pages * 50} resultados · Página {self.search_page}/{max(self.search_total_pages, 1)}")
    
    if self.search_page > 1:
        ttk.Button(self.search_page_buttons_frame, text="◀ Anterior",
                  command=lambda: self._search_go_page(self.search_page - 1),
                  bootstyle="secondary-outline", width=12).pack(side=tk.LEFT, padx=2)
    
    ttk.Button(self.search_page_buttons_frame, text=f"Pág. {self.search_page}/{max(self.search_total_pages, 1)}",
              state="disabled", width=12).pack(side=tk.LEFT, padx=2)
    
    if self.search_page < self.search_total_pages:
        ttk.Button(self.search_page_buttons_frame, text="Siguiente ▶",
                  command=lambda: self._search_go_page(self.search_page + 1),
                  bootstyle="secondary-outline", width=12).pack(side=tk.LEFT, padx=2)


def _search_go_page(self, page):
    """Navega a una página específica."""
    self.search_page = page
    self._search_execute()


def _search_export_csv(self):
    """Exporta resultados a CSV."""
    if not self.search_results_cache:
        messagebox.showwarning("Sin resultados", "No hay resultados para exportar")
        return
    
    filepath = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        initialfile=f"busqueda_kdp_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    )
    
    if not filepath:
        return
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "Categoría", "Tipo", "Estado", "Fecha", "Palabras", "Confianza"])
            
            for row in self.search_results_cache:
                writer.writerow([
                    row.get('id', ''),
                    row.get('category', ''),
                    row.get('tipo', ''),
                    row.get('status', ''),
                    row.get('timestamp', ''),
                    row.get('palabras', ''),
                    row.get('confidence_score', '')
                ])
        
        messagebox.showinfo("Éxito", f"Resultados exportados a:\n{filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar:\n{e}")


def _search_view_entry(self, event):
    """Muestra detalles de una entrada seleccionada."""
    selection = self.search_tree.selection()
    if not selection:
        return
    
    item = selection[0]
    values = self.search_tree.item(item)['values']
    
    if values and values[0]:
        entry_id = values[0]
        
        conn = self.kb_search_db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM knowledge_entries WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            if row:
                detail_win = tk.Toplevel(self.root)
                detail_win.title(f"Detalle: ID {entry_id}")
                detail_win.geometry("800x600")
                
                text_area = tk.Text(detail_win, wrap=tk.WORD, padx=20, pady=20)
                text_area.pack(fill=tk.BOTH, expand=True)
                
                content = f"""ID: {row['id']}
Categoría: {row['category']}
Tipo: {row.get('tipo', 'N/A')}
Estado: {row.get('status', 'N/A')}
Fecha: {row['timestamp']}
Palabras: {row.get('palabras', 0)}
Confianza: {row.get('confidence_score', 0):.1f}%

---
{row['content']}
"""
                text_area.insert(1.0, content)
        finally:
            conn.close()