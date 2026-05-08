# -*- coding: utf-8 -*-
"""
Theme Editor Component for KDP Master Suite
Provides visual JSON editor with real-time validation and preview.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from pathlib import Path


class ThemeEditorWindow:
    """
    Editor visual para temas JSON con validación en tiempo real.
    """
    
    # =========================================================================
    # [INI MÓDULO 2] Constructor e Inicialización
    # =========================================================================
    
    def __init__(self, parent, theme_manager, current_theme_name="dark"):
        """
        Inicializa el editor de temas.
        
        Args:
            parent: Ventana padre (root de Tk)
            theme_manager: Instancia de ThemeManager
            current_theme_name: Tema actualmente activo
        """
        self.parent = parent
        self.theme_manager = theme_manager
        self.current_active_theme = current_theme_name
        
        self.window = tk.Toplevel(parent)
        self.window.title("Gestor de Temas Personalizados")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.current_editing_theme = None
        self.is_modified = False
        
        self._setup_styles()
        self._create_ui()
        self._load_themes_list()
        
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self):
        """Configura estilos visuales del editor."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        is_dark = True
        bg_color = "#1e1e1e" if is_dark else "#f5f5f5"
        fg_color = "#ffffff" if is_dark else "#1e1e1e"
        accent = "#3b82f6"
        
        self.style.configure("Editor.TFrame", background=bg_color)
        self.style.configure("Editor.TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("EditorHeader.TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 14, "bold"))
        
        self.editor_bg = "#1e1e1e"
        self.editor_fg = "#d4d4d4"
        self.editor_error_fg = "#ff6b6b"
        self.editor_valid_fg = "#10b981"
    
    # =========================================================================
    # [INI MÓDULO 2] Interfaz de Usuario
    # =========================================================================
    
    def _create_ui(self):
        """Crea la interfaz del editor."""
        main_container = ttk.Frame(self.window, style="Editor.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        self._create_header(main_container)
        self._create_main_content(main_container)
        self._create_footer(main_container)
    
    def _create_header(self, parent):
        """Crea el header con título y botones principales."""
        header_frame = ttk.Frame(parent, style="Editor.TFrame")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        title_label = ttk.Label(
            header_frame,
            text="Gestor de Temas JSON",
            style="EditorHeader.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        btn_frame = ttk.Frame(header_frame, style="Editor.TFrame")
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="+ Nuevo", command=self._create_new_theme).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Importar", command=self._import_theme).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Exportar", command=self._export_theme).pack(side=tk.LEFT, padx=3)
    
    def _create_main_content(self, parent):
        """Crea el contenido principal con panels izquierdo y derecho."""
        content_frame = ttk.Frame(parent, style="Editor.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        left_panel = self._create_theme_list_panel(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        right_panel = self._create_json_editor_panel(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def _create_theme_list_panel(self, parent):
        """Crea el panel de lista de temas."""
        list_frame = ttk.LabelFrame(parent, text="Temas Disponibles", padding=10)
        
        self.theme_listbox = tk.Listbox(
            list_frame,
            width=28,
            height=25,
            font=("Consolas", 10),
            bg="#252526",
            fg="#cccccc",
            selectbackground="#3c3c3c",
            selectforeground="#ffffff",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.theme_listbox.pack(fill=tk.BOTH, expand=True)
        self.theme_listbox.bind('<<ListboxSelect>>', self._on_theme_selected)
        
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Button(list_btn_frame, text="Eliminar", command=self._delete_theme).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_btn_frame, text="Actualizar", command=self._load_themes_list).pack(side=tk.LEFT, padx=2)
        
        return list_frame
    
    def _create_json_editor_panel(self, parent):
        """Crea el panel del editor JSON."""
        editor_frame = ttk.LabelFrame(parent, text="Editor JSON", padding=10)
        
        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        text_frame = ttk.Frame(editor_container)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.json_text = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=("Consolas", 11),
            bg=self.editor_bg,
            fg=self.editor_fg,
            insertbackground="#ffffff",
            selectbackground="#264f78",
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.json_text.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = ttk.Scrollbar(editor_container, orient=tk.HORIZONTAL, command=self.json_text.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.json_text.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.json_text.bind('<KeyRelease>', self._on_text_changed)
        
        status_frame = ttk.Frame(editor_container)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.validation_label = ttk.Label(
            status_frame,
            text="Sin cambios",
            font=("Segoe UI", 9)
        )
        self.validation_label.pack(side=tk.LEFT)
        
        btn_frame = ttk.Frame(status_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="Validar", command=self._validate_json).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Previsualizar", command=self._preview_theme).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Guardar", command=self._save_theme).pack(side=tk.LEFT, padx=3)
        
        return editor_frame
    
    def _create_footer(self, parent):
        """Crea el footer con información adicional."""
        footer_frame = ttk.Frame(parent, style="Editor.TFrame")
        footer_frame.pack(fill=tk.X, padx=20, pady=(10, 15))
        
        help_text = ttk.Label(
            footer_frame,
            text="Usa 'base': 'dark' o 'light' y sobrescribe solo los colores que quieras cambiar en 'overrides'",
            font=("Segoe UI", 8),
            foreground="#666666"
        )
        help_text.pack(side=tk.LEFT)
        
        close_btn = ttk.Button(footer_frame, text="Cerrar", command=self._on_close)
        close_btn.pack(side=tk.RIGHT)
    
    # =========================================================================
    # [FIN MÓDULO 2] Funciones de Datos
    # =========================================================================
    
    def _get_template(self, template_type="dark"):
        """Retorna una plantilla de tema base."""
        templates = {
            "dark": {
                "name": "Mi Tema Oscuro",
                "base": "dark",
                "colors": {"accent": "#8b5cf6", "bg_secondary": "#1e1e3f"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "bold"}}
            },
            "light": {
                "name": "Mi Tema Claro",
                "base": "light",
                "colors": {"accent": "#6366f1", "bg_secondary": "#f0f4ff"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "bold"}}
            },
            "purple": {
                "name": "Purple Dream",
                "base": "dark",
                "colors": {"accent": "#a855f7", "bg_secondary": "#1e1b4b", "info": "#c084fc"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "bold"}}
            },
            "ocean": {
                "name": "Ocean Blue",
                "base": "dark",
                "colors": {"accent": "#0ea5e9", "bg_secondary": "#0c4a6e", "info": "#38bdf8"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "bold"}}
            },
            "forest": {
                "name": "Forest Green",
                "base": "dark",
                "colors": {"accent": "#22c55e", "bg_secondary": "#14532d", "success": "#4ade80"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "bold"}}
            },
            "sunset": {
                "name": "Sunset Orange",
                "base": "dark",
                "colors": {"accent": "#f97316", "bg_secondary": "#7c2d12", "warning": "#fb923c"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "bold"}}
            },
            "rose": {
                "name": "Rose Pink",
                "base": "dark",
                "colors": {"accent": "#f43f5e", "bg_secondary": "#881337", "danger": "#fb7185"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "bold"}}
            },
            "minimal_light": {
                "name": "Minimal Light",
                "base": "light",
                "colors": {"accent": "#18181b", "bg_secondary": "#ffffff"},
                "fonts": {"header": {"family": "Segoe UI", "size": 22, "weight": "normal"}}
            },
            "corporate": {
                "name": "Corporate Blue",
                "base": "light",
                "colors": {"accent": "#1e40af", "bg_secondary": "#eff6ff", "info": "#3b82f6"},
                "fonts": {"header": {"family": "Arial", "size": 20, "weight": "bold"}}
            }
        }
        
        if template_type in templates:
            return templates[template_type]
        
        return templates.get("dark", {"name": "Nuevo Tema", "base": "dark", "colors": {}, "fonts": {}})
    
    # =========================================================================
    # [INI MÓDULO 2] Handlers de Eventos
    # =========================================================================
    
    def _load_themes_list(self):
        """Carga la lista de temas disponibles."""
        self.theme_listbox.delete(0, tk.END)
        
        available_themes = self.theme_manager.list_available_themes()
        
        for name, info in available_themes.items():
            theme_type = info["type"]
            if theme_type == "built-in":
                display = f"• {name} (Incorporado)"
            elif theme_type == "custom":
                display = f"◦ {name} (Personalizado)"
            else:
                display = f"✗ {name} (Corrupto)"
            
            self.theme_listbox.insert(tk.END, display)
    
    def _on_theme_selected(self, event=None):
        """Maneja selección de tema de la lista."""
        selection = self.theme_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.theme_listbox.get(selection[0])
        
        if "(Incorporado)" in selected_text:
            name = selected_text.split("•")[1].split("(")[0].strip()
            theme = self.theme_manager.DEFAULT_THEMES.get(name, {})
            json_content = json.dumps(theme, indent=2)
        else:
            name = selected_text.split("◦")[1].split("(")[0].strip()
            success, colors, fonts, msg = self.theme_manager.load_custom_theme(name)
            if success:
                json_content = json.dumps({
                    "name": name,
                    "base": self.theme_manager.DEFAULT_THEMES.get("dark", {}).get("base"),
                    "colors": colors,
                    "fonts": fonts
                }, indent=2)
            else:
                messagebox.showerror("Error", f"No se pudo cargar el tema: {msg}")
                return
        
        self.json_text.delete('1.0', tk.END)
        self.json_text.insert('1.0', json_content)
        self.current_editing_theme = name
        self.is_modified = False
        self._update_validation_status("Cargado", True)
    
    def _on_text_changed(self, event=None):
        """Maneja cambios en el texto del editor."""
        self.is_modified = True
        self._validate_json(show_message=False)
    
    def _on_close(self):
        """Maneja cierre de la ventana."""
        if self.is_modified:
            if messagebox.askyesno("Confirmar", "Hay cambios sin guardar. ¿Salir sin guardar?"):
                self.window.destroy()
        else:
            self.window.destroy()
    
    # =========================================================================
    # [INI MÓDULO 2] Acciones del Usuario
    # =========================================================================
    
    def _create_new_theme(self):
        """Crea un nuevo tema desde plantilla."""
        template = self._get_template("dark")
        self.json_text.delete('1.0', tk.END)
        self.json_text.insert('1.0', json.dumps(template, indent=2))
        self.current_editing_theme = None
        self.is_modified = True
        self._update_validation_status("Nuevo tema (sin guardar)", False)
    
    def _delete_theme(self):
        """Elimina el tema seleccionado."""
        selection = self.theme_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un tema para eliminar")
            return
        
        selected_text = self.theme_listbox.get(selection[0])
        
        if "(Incorporado)" in selected_text:
            messagebox.showerror("Error", "No puedes eliminar temas incorporados")
            return
        
        if not messagebox.askyesno("Confirmar", f"¿Eliminas el tema '{selected_text}'?"):
            return
        
        name = selected_text.split("◦")[1].split("(")[0].strip()
        
        themes_dir = self.theme_manager.themes_dir
        if themes_dir:
            file_path = Path(themes_dir) / f"{name}.json"
            if file_path.exists():
                try:
                    file_path.unlink()
                    messagebox.showinfo("Éxito", f"Tema '{name}' eliminado")
                    self._load_themes_list()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar: {str(e)}")
    
    def _validate_json(self, show_message=True):
        """Valida el JSON actual."""
        try:
            json_content = self.json_text.get('1.0', tk.END).strip()
            if not json_content:
                self._update_validation_status("Vacío", False)
                if show_message:
                    messagebox.showwarning("Advertencia", "El editor está vacío")
                return False
            
            theme_data = json.loads(json_content)
            
            is_valid, error = self.theme_manager.validate_theme_strict(theme_data)
            
            if is_valid:
                self._update_validation_status("✓ JSON válido", True)
                if show_message:
                    messagebox.showinfo("Validación", "El tema es válido")
                return True
            else:
                self._update_validation_status(f"✗ {error}", False)
                if show_message:
                    messagebox.showerror("Error de Validación", error)
                return False
                
        except json.JSONDecodeError as e:
            error_msg = f"Error en línea {e.lineno}: {e.msg}"
            self._update_validation_status(f"✗ {error_msg}", False)
            if show_message:
                messagebox.showerror("Error de JSON", error_msg)
            return False
    
    def _preview_theme(self):
        """Previsualiza el tema actual."""
        if not self._validate_json(show_message=False):
            messagebox.showwarning("Advertencia", "El JSON tiene errores. La previsualización puede no funcionar correctamente.")
        
        try:
            json_content = self.json_text.get('1.0', tk.END).strip()
            theme_data = json.loads(json_content)
            
            merged = self.theme_manager.merge_with_base(theme_data)
            self.theme_manager.colors = merged["colors"]
            self.theme_manager.fonts = merged["fonts"]
            self.theme_manager.current_theme_name = merged["name"]
            self.theme_manager.apply_theme()
            
            if messagebox.askyesno("Previsualización", 
                                f"Tema '{merged['name']}' aplicado temporalmente.\n\n"
                                "¿Deseas mantener este tema?"):
                self._save_theme()
            else:
                self.theme_manager.load_theme(self.current_active_theme)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo previsualizar: {str(e)}")
    
    def _save_theme(self):
        """Guarda el tema actual."""
        if not self._validate_json(show_message=False):
            messagebox.showerror("Error", "El JSON tiene errores. Corrígelos antes de guardar.")
            return
        
        try:
            json_content = self.json_text.get('1.0', tk.END).strip()
            theme_data = json.loads(json_content)
            
            success, msg, file_path = self.theme_manager.save_theme(theme_data)
            
            if success:
                messagebox.showinfo("Éxito", msg)
                self.is_modified = False
                self.current_editing_theme = theme_data["name"]
                self._load_themes_list()
            else:
                messagebox.showerror("Error", msg)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
    
    def _import_theme(self):
        """Importa un tema desde archivo."""
        file_path = filedialog.askopenfilename(
            title="Importar Tema",
            filetypes=[("JSON Theme", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            is_valid, error = self.theme_manager.validate_theme_strict(theme_data)
            if not is_valid:
                messagebox.showerror("Error", f"El tema importado es inválido: {error}")
                return
            
            self.json_text.delete('1.0', tk.END)
            self.json_text.insert('1.0', json.dumps(theme_data, indent=2))
            self.is_modified = True
            messagebox.showinfo("Éxito", "Tema importado correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar: {str(e)}")
    
    def _export_theme(self):
        """Exporta el tema actual a archivo."""
        if not self._validate_json(show_message=False):
            messagebox.showwarning("Advertencia", "El JSON tiene errores. ¿Exportar de todos modos?")
            if not messagebox.askyesno("Confirmar", "¿Exportar tema con errores?"):
                return
        
        try:
            json_content = self.json_text.get('1.0', tk.END).strip()
            theme_data = json.loads(json_content)
            
            default_name = theme_data.get("name", "tema_personalizado")
            file_path = filedialog.asksaveasfilename(
                title="Exportar Tema",
                defaultextension=".json",
                initialfile=f"{default_name}.json",
                filetypes=[("JSON Theme", "*.json")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(theme_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Éxito", f"Tema exportado a:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
    
    def _update_validation_status(self, text, is_valid):
        """Actualiza el label de estado de validación."""
        if is_valid is None:
            color = "#888888"
        elif is_valid:
            color = self.editor_valid_fg
        else:
            color = self.editor_error_fg
        
        self.validation_label.config(text=text, foreground=color)


def open_theme_editor(parent, theme_manager, current_theme_name="dark"):
    """
    Abre el editor de temas.
    Función de conveniencia para instanciar el editor.
    """
    editor = ThemeEditorWindow(parent, theme_manager, current_theme_name)
    return editor