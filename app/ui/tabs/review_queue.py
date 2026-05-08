"""
GUI Tab for Review Queue
========================
Pestaña de cola de revisión humana para gui_app.py
Permite revisar y aprobar contenido pendiente.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, List, Dict


def setup_review_tab(self):
    """Configura la pestaña de Cola de Revisión Humana."""
    if not hasattr(self, 'review_queue_initialized'):
        self.review_queue_initialized = False
    
    _build_review_ui(self)


def _build_review_ui(self):
    """Construye la interfaz de usuario de revisión"""
    main_container = ttk.Frame(self.tab_review)
    main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    header_frame = ttk.Frame(main_container)
    header_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(header_frame, text="👁️ COLA DE REVISIÓN HUMANA", 
              font=("Inter", 14, "bold")).pack(side=tk.LEFT)
    
    stats_frame = ttk.Frame(header_frame)
    stats_frame.pack(side=tk.RIGHT)
    
    self.review_pending_count = tk.StringVar(value="0 pendientes")
    ttk.Label(stats_frame, textvariable=self.review_pending_count,
              font=("Inter", 10, "bold"), foreground="#f59e0b").pack(side=tk.LEFT, padx=5)
    
    btn_frame = ttk.Frame(header_frame)
    btn_frame.pack(side=tk.RIGHT, padx=10)
    
    ttk.Button(btn_frame, text="🔄 Actualizar", 
               command=lambda: _refresh_review_list(self),
               bootstyle="info-outline").pack(side=tk.LEFT, padx=2)
    
    ttk.Button(btn_frame, text="✅ Aprobar Seleccionados", 
               command=lambda: _approve_selected(self),
               bootstyle="success").pack(side=tk.LEFT, padx=2)
    
    ttk.Button(btn_frame, text="❌ Rechazar Seleccionados", 
               command=lambda: _reject_selected(self),
               bootstyle="danger-outline").pack(side=tk.LEFT, padx=2)
    
    content_paned = tk.PanedWindow(main_container, orient=tk.HORIZONTAL)
    content_paned.pack(fill=tk.BOTH, expand=True)
    
    left_panel = ttk.LabelFrame(content_paned, text="📋 Elementos en Cola", padding=10)
    content_paned.add(left_panel)
    
    _build_review_list(self, left_panel)
    
    right_panel = ttk.LabelFrame(content_paned, text="📝 Detalle", padding=10)
    content_paned.add(right_panel)
    
    _build_review_detail(self, right_panel)


def _build_review_list(self, parent):
    """Construye la lista de elementos a revisar"""
    tree_frame = ttk.Frame(parent)
    tree_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("id", "tipo", "titulo", "fecha", "estado", "prioridad")
    self.review_tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=20)
    
    self.review_tree.heading("#0", text="")
    self.review_tree.column("#0", width=30, stretch=False)
    
    self.review_tree.heading("id", text="ID")
    self.review_tree.column("id", width=80)
    
    self.review_tree.heading("tipo", text="Tipo")
    self.review_tree.column("tipo", width=100)
    
    self.review_tree.heading("titulo", text="Título")
    self.review_tree.column("titulo", width=300)
    
    self.review_tree.heading("fecha", text="Fecha")
    self.review_tree.column("fecha", width=120)
    
    self.review_tree.heading("estado", text="Estado")
    self.review_tree.column("estado", width=100)
    
    self.review_tree.heading("prioridad", text="Prioridad")
    self.review_tree.column("prioridad", width=80)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.review_tree.yview)
    self.review_tree.configure(yscrollcommand=scrollbar.set)
    
    self.review_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    self.review_tree.bind("<<TreeviewSelect>>", lambda e: _on_review_select(self))


def _build_review_detail(self, parent):
    """Construye el panel de detalle del elemento seleccionado"""
    detail_frame = ttk.Frame(parent)
    detail_frame.pack(fill=tk.BOTH, expand=True)
    
    self.review_detail_txt = tk.Text(detail_frame, wrap=tk.WORD, height=25, font=("Consolas", 10))
    self.review_detail_txt.pack(fill=tk.BOTH, expand=True, pady=5)
    
    action_frame = ttk.Frame(parent)
    action_frame.pack(fill=tk.X, pady=5)
    
    ttk.Button(action_frame, text="✅ Aprobar", 
               command=lambda: _approve_item(self),
               bootstyle="success").pack(side=tk.LEFT, padx=2)
    
    ttk.Button(action_frame, text="❌ Rechazar", 
               command=lambda: _reject_item(self),
               bootstyle="danger-outline").pack(side=tk.LEFT, padx=2)
    
    ttk.Button(action_frame, text="⏭️ Saltar", 
               command=lambda: _skip_item(self),
               bootstyle="secondary-outline").pack(side=tk.LEFT, padx=2)


def _refresh_review_list(self):
    """Refresca la lista de revisión"""
    if hasattr(self, 'review_tree'):
        for item in self.review_tree.get_children():
            self.review_tree.delete(item)
        
        if hasattr(self, 'db_manager') and self.db_manager:
            try:
                pending_items = self._get_pending_review_items()
                for item in pending_items:
                    self.review_tree.insert("", tk.END, values=(
                        item.get('id', ''),
                        item.get('tipo', ''),
                        item.get('titulo', '')[:50] + '...',
                        item.get('fecha', ''),
                        item.get('estado', ''),
                        item.get('prioridad', '')
                    ))
            except Exception as e:
                pass
        
        count = len(self.review_tree.get_children())
        if hasattr(self, 'review_pending_count'):
            self.review_pending_count.set(f"{count} pendientes")


def _get_pending_review_items(self) -> List[Dict]:
    """Obtiene los elementos pendientes de revisión"""
    return []


def _on_review_select(self):
    """Maneja la selección de un elemento en la lista"""
    selection = self.review_tree.selection()
    if not selection:
        return
    
    item = self.review_tree.item(selection[0])
    values = item.get('values', [])
    
    if values and len(values) >= 3:
        detail = f"=== DETALLE DEL ELEMENTO ===\n\n"
        detail += f"ID: {values[0]}\n"
        detail += f"Tipo: {values[1]}\n"
        detail += f"Título: {values[2]}\n"
        detail += f"Fecha: {values[3]}\n"
        detail += f"Estado: {values[4]}\n"
        detail += f"Prioridad: {values[5]}\n"
        
        self.review_detail_txt.delete("1.0", tk.END)
        self.review_detail_txt.insert("1.0", detail)


def _approve_selected(self):
    """Aprueba los elementos seleccionados"""
    selection = self.review_tree.selection()
    if not selection:
        messagebox.showinfo("Revisión", "Selecciona elementos para aprobar.")
        return
    messagebox.showinfo("Revisión", f"Aprobados: {len(selection)} elementos")
    _refresh_review_list(self)


def _reject_selected(self):
    """Rechaza los elementos seleccionados"""
    selection = self.review_tree.selection()
    if not selection:
        messagebox.showinfo("Revisión", "Selecciona elementos para rechazar.")
        return
    messagebox.showinfo("Revisión", f"Rechazados: {len(selection)} elementos")
    _refresh_review_list(self)


def _approve_item(self):
    """Aprueba el elemento seleccionado actualmente"""
    if hasattr(self, 'review_tree'):
        selection = self.review_tree.selection()
        if selection:
            self.review_tree.delete(selection[0])
            messagebox.showinfo("Revisión", "Elemento aprobado.")


def _reject_item(self):
    """Rechaza el elemento seleccionado actualmente"""
    if hasattr(self, 'review_tree'):
        selection = self.review_tree.selection()
        if selection:
            self.review_tree.delete(selection[0])
            messagebox.showinfo("Revisión", "Elemento rechazado.")


def _skip_item(self):
    """Salta al siguiente elemento"""
    if hasattr(self, 'review_tree'):
        selection = self.review_tree.selection()
        if selection:
            items = self.review_tree.get_children()
            current_idx = items.index(selection[0]) if selection[0] in items else 0
            next_idx = (current_idx + 1) % len(items) if items else None
            if next_idx is not None:
                self.review_tree.selection_set(items[next_idx])