"""
GUI Extensions for Multi-Selection with Checkboxes
==================================================
Extensiones para TreeView con soporte de checkboxes.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Dict


class CheckboxTreeview(ttk.Treeview):
    """
    TreeView extendido con soporte para checkboxes.
    Permite selección múltiple visual con checkboxes.
    """
    
    def __init__(self, master, selection_manager, item_type='video', **kwargs):
        """
        Inicializa TreeView con checkboxes.
        
        Args:
            master: Widget padre
            selection_manager: Instancia de SelectionManager
            item_type: Tipo de items ('video', 'channel', 'file')
            **kwargs: Argumentos para ttk.Treeview
        """
        # Guardar item_type antes de pasar kwargs a super()
        self.item_type = item_type
        
        # Inicializar TreeView base
        super().__init__(master, **kwargs)
        
        self.selection_manager = selection_manager
        
        # Callbacks
        self.on_selection_changed: Optional[Callable] = None
        
        # Bind eventos
        self.bind('<Button-1>', self._on_click)
        self.bind('<space>', self._on_space)
        
        # Tags para checkboxes
        self.tag_configure('checked', foreground='#10b981')
        self.tag_configure('unchecked', foreground='#64748b')
    
    def _on_click(self, event):
        """Maneja click en el TreeView."""
        region = self.identify_region(event.x, event.y)
        
        if region == "tree":
            # Click en el checkbox (primera columna)
            item = self.identify_row(event.y)
            if item:
                self.toggle_item(item)
                return "break"  # Prevenir selección normal
    
    def _on_space(self, event):
        """Maneja tecla espacio para toggle."""
        selection = self.selection()
        if selection:
            for item in selection:
                self.toggle_item(item)
            return "break"
    
    def toggle_item(self, item):
        """Toggle checkbox de un item."""
        values = self.item(item, 'values')
        if not values:
            return
        
        item_id = values[0]  # Asumimos que el ID está en la primera columna
        
        # Toggle en el manager según tipo
        if self.item_type == 'video':
            is_selected = self.selection_manager.toggle_video(int(item_id))
        elif self.item_type == 'channel':
            is_selected = self.selection_manager.toggle_channel(int(item_id))
        elif self.item_type == 'file':
            is_selected = self.selection_manager.toggle_file(str(item_id))
        else:
            return
        
        # Actualizar visual
        self.update_item_checkbox(item, is_selected)
        
        # Callback
        if self.on_selection_changed:
            self.on_selection_changed()
    
    def update_item_checkbox(self, item, is_selected: bool):
        """Actualiza el visual del checkbox."""
        checkbox = "☑" if is_selected else "☐"
        tag = 'checked' if is_selected else 'unchecked'
        
        # Obtener valores actuales
        values = list(self.item(item, 'values'))
        
        # Actualizar checkbox en la primera columna visible
        # (asumiendo que hay una columna dedicada para checkbox)
        if len(values) > 1:
            values[1] = checkbox  # Segunda columna es el checkbox
            self.item(item, values=values, tags=(tag,))
    
    def refresh_all_checkboxes(self):
        """Refresca todos los checkboxes según el estado del manager."""
        for item in self.get_children():
            values = self.item(item, 'values')
            if not values:
                continue
            
            item_id = values[0]
            
            # Verificar estado en el manager
            if self.item_type == 'video':
                is_selected = self.selection_manager.is_video_selected(int(item_id))
            elif self.item_type == 'channel':
                is_selected = self.selection_manager.is_channel_selected(int(item_id))
            elif self.item_type == 'file':
                is_selected = self.selection_manager.is_file_selected(str(item_id))
            else:
                continue
            
            self.update_item_checkbox(item, is_selected)
    
    def select_all(self):
        """Selecciona todos los items."""
        item_ids = []
        for item in self.get_children():
            values = self.item(item, 'values')
            if values:
                item_ids.append(values[0])
        
        if self.item_type == 'video':
            self.selection_manager.select_all_videos([int(id) for id in item_ids])
        elif self.item_type == 'channel':
            self.selection_manager.select_all_channels([int(id) for id in item_ids])
        elif self.item_type == 'file':
            self.selection_manager.select_all_files([str(id) for id in item_ids])
        
        self.refresh_all_checkboxes()
        
        if self.on_selection_changed:
            self.on_selection_changed()
    
    def deselect_all(self):
        """Deselecciona todos los items."""
        if self.item_type == 'video':
            self.selection_manager.deselect_all_videos()
        elif self.item_type == 'channel':
            self.selection_manager.deselect_all_channels()
        elif self.item_type == 'file':
            self.selection_manager.deselect_all_files()
        
        self.refresh_all_checkboxes()
        
        if self.on_selection_changed:
            self.on_selection_changed()
    
    def invert_selection(self):
        """Invierte la selección."""
        item_ids = []
        for item in self.get_children():
            values = self.item(item, 'values')
            if values:
                item_ids.append(values[0])
        
        if self.item_type == 'video':
            self.selection_manager.invert_video_selection([int(id) for id in item_ids])
        elif self.item_type == 'channel':
            self.selection_manager.invert_channel_selection([int(id) for id in item_ids])
        elif self.item_type == 'file':
            self.selection_manager.invert_file_selection([str(id) for id in item_ids])
        
        self.refresh_all_checkboxes()
        
        if self.on_selection_changed:
            self.on_selection_changed()
    
    def get_selected_items(self) -> List:
        """Retorna lista de items seleccionados."""
        if self.item_type == 'video':
            return self.selection_manager.get_selected_videos()
        elif self.item_type == 'channel':
            return self.selection_manager.get_selected_channels()
        elif self.item_type == 'file':
            return self.selection_manager.get_selected_files()
        return []
    
    def get_selection_count(self) -> int:
        """Retorna el número de items seleccionados."""
        if self.item_type == 'video':
            return self.selection_manager.get_video_selection_count()
        elif self.item_type == 'channel':
            return self.selection_manager.get_channel_selection_count()
        elif self.item_type == 'file':
            return self.selection_manager.get_file_selection_count()
        return 0


class SelectionToolbar(ttk.Frame):
    """
    Barra de herramientas para operaciones de selección.
    Incluye botones para Seleccionar Todo, Deseleccionar, Invertir, etc.
    """
    
    def __init__(self, master, checkbox_treeview: CheckboxTreeview, **kwargs):
        """
        Inicializa la barra de herramientas.
        
        Args:
            master: Widget padre
            checkbox_treeview: Instancia de CheckboxTreeview
        """
        super().__init__(master, **kwargs)
        
        self.treeview = checkbox_treeview
        
        # Label de contador
        self.count_label = ttk.Label(self, text="0 seleccionados", 
                                     font=("Segoe UI", 9, "bold"))
        self.count_label.pack(side=tk.LEFT, padx=5)
        
        # Botones
        ttk.Button(self, text="✓ Todos", width=10,
                  command=self.treeview.select_all).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(self, text="✗ Ninguno", width=10,
                  command=self.treeview.deselect_all).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(self, text="⇄ Invertir", width=10,
                  command=self.treeview.invert_selection).pack(side=tk.LEFT, padx=2)
        
        # Configurar callback para actualizar contador
        self.treeview.on_selection_changed = self.update_count
        
        # Actualizar contador inicial
        self.update_count()
    
    def update_count(self):
        """Actualiza el contador de selección."""
        count = self.treeview.get_selection_count()
        self.count_label.config(text=f"{count} seleccionado{'s' if count != 1 else ''}")


# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    from app.services.selection_manager import SelectionManager
    
    root = tk.Tk()
    root.title("Demo: CheckboxTreeview")
    root.geometry("600x400")
    
    # Crear selection manager
    manager = SelectionManager()
    
    # Frame principal
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Toolbar
    toolbar_frame = ttk.Frame(main_frame)
    toolbar_frame.pack(fill=tk.X, pady=(0, 10))
    
    # TreeView con checkboxes
    tree = CheckboxTreeview(
        main_frame,
        selection_manager=manager,
        item_type='video',
        columns=("id", "checkbox", "title", "status"),
        show="headings",
        height=15
    )
    
    tree.heading("id", text="ID")
    tree.heading("checkbox", text="☐")
    tree.heading("title", text="Título")
    tree.heading("status", text="Estado")
    
    tree.column("id", width=50, anchor=tk.CENTER)
    tree.column("checkbox", width=40, anchor=tk.CENTER)
    tree.column("title", width=350)
    tree.column("status", width=100, anchor=tk.CENTER)
    
    tree.pack(fill=tk.BOTH, expand=True)
    
    # Toolbar de selección
    toolbar = SelectionToolbar(toolbar_frame, tree)
    toolbar.pack(side=tk.LEFT)
    
    # Añadir datos de ejemplo
    for i in range(1, 11):
        tree.insert("", tk.END, values=(
            i,
            "☐",
            f"Video de Ejemplo {i}",
            "Pendiente" if i % 2 == 0 else "Completado"
        ))
    
    # Botón para mostrar selección
    def show_selection():
        selected = tree.get_selected_items()
        print(f"Videos seleccionados: {selected}")
        print(f"Resumen: {manager.get_selection_summary()}")
    
    ttk.Button(toolbar_frame, text="Mostrar Selección",
              command=show_selection).pack(side=tk.RIGHT, padx=5)
    
    root.mainloop()
