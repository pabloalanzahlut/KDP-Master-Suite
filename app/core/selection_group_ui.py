"""
P4-37: UI para Guardar/Cargar Grupos de Selección
Interfaz para gestionar grupos de videos seleccionados.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class SelectionGroupUI:
    """UI para gestionar grupos de selección."""

    def __init__(
        self,
        parent,
        on_group_load: Optional[Callable] = None,
        on_group_save: Optional[Callable] = None
    ):
        self.parent = parent
        self.on_group_load = on_group_load
        self.on_group_save = on_group_save
        self._groups: Dict[str, List[str]] = {}

    def create_selection_dialog(
        self,
        title: str = "Guardar Grupo de Selección",
        current_selection: List[str] = None
    ) -> Optional[str]:
        """
        Crea diálogo para guardar un grupo.
        Args:
            current_selection: Lista de IDs seleccionados
        Returns:
            Nombre del grupo o None si cancelado
        """
        dialog = tk.Toplevel(self.parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(self.parent)

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Nombre del grupo:").pack(anchor=tk.W)

        name_var = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
        name_entry.pack(pady=(5, 10))

        ttk.Label(frame, text="Descripción (opcional):").pack(anchor=tk.W)

        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(frame, textvariable=desc_var, width=40)
        desc_entry.pack(pady=(5, 15))

        if current_selection:
            ttk.Label(
                frame,
                text=f"Videos seleccionados: {len(current_selection)}"
            ).pack(anchor=tk.W)

        result = {'name': None, 'description': ''}

        def on_save():
            if not name_var.get().strip():
                messagebox.showwarning("Aviso", "Ingresa un nombre para el grupo")
                return
            result['name'] = name_var.get().strip()
            result['description'] = desc_var.get().strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Guardar", command=on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=on_cancel).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return result['name']

    def create_load_dialog(
        self,
        available_groups: Dict[str, Dict]
    ) -> Optional[str]:
        """
        Crea diálogo para cargar un grupo.
        Args:
            available_groups: Dict de grupos disponibles {name: {description, count}}
        Returns:
            Nombre del grupo seleccionado o None
        """
        dialog = tk.Toplevel(self.parent)
        dialog.title("Cargar Grupo de Selección")
        dialog.geometry("500x300")
        dialog.transient(self.parent)

        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Selecciona un grupo:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        listbox = tk.Listbox(frame, height=10)
        listbox.pack(fill=tk.BOTH, expand=True)

        for group_name, info in available_groups.items():
            desc = info.get('description', '')
            count = info.get('count', 0)
            listbox.insert(tk.END, f"{group_name} ({count} videos) - {desc}")

        if not available_groups:
            listbox.insert(tk.END, "No hay grupos guardados")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=scrollbar.set)

        result = {'selection': None}

        def on_load():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                group_names = list(available_groups.keys())
                if idx < len(group_names):
                    result['selection'] = group_names[idx]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Cargar", command=on_load).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=on_cancel).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return result['selection']


def create_selection_group_ui(parent) -> SelectionGroupUI:
    return SelectionGroupUI(parent)