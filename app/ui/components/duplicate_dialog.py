"""
KDP_MASTER - Duplicate Decision Dialog
=========================================
Diálogo modal para que el usuario decida qué hacer con contenido duplicado detectado.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, List


class DuplicateDecisionDialog:
    """
    Diálogo modal para decisión del usuario ante contenido duplicado.
    
    Muestra:
    - Información del video nuevo
    - Información del/los video(s) duplicado(s)
    - Opciones de acción
    """
    
    def __init__(self, parent, duplicate_info: Dict, callback: Callable = None):
        """
        Args:
            parent: Ventana padre
            duplicate_info: Diccionario con información del duplicado
                - new_video: Información del video nuevo
                - duplicate_type: Tipo de duplicado (EXACT, REPOST, etc)
                - similar_videos: Lista de videos similares
            callback: Función a llamar con la decisión del usuario
        """
        self.parent = parent
        self.duplicate_info = duplicate_info
        self.callback = callback
        self.result = None
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Crea el diálogo modal."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Contenido Duplicado Detectado")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Configurar tamaño y posición
        self.dialog.geometry("600x450")
        self.dialog.resizable(False, False)
        
        # Centrar en pantalla
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(self.dialog, bg='#1e1e2e', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header con icono de advertencia
        header_frame = tk.Frame(main_frame, bg='#1e1e2e')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        icon_label = tk.Label(header_frame, text="⚠️", font=("Segoe UI", 24), 
                            bg='#1e1e2e', fg='#f59e0b')
        icon_label.pack(side=tk.LEFT)
        
        title_label = tk.Label(header_frame, 
                              text="Se ha detectado contenido duplicado",
                              font=("Segoe UI", 14, "bold"), 
                              bg='#1e1e2e', fg='white')
        title_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Frame de información del video nuevo
        new_video_frame = self._create_info_card(main_frame, "Video Nuevo", 
                                                 self.duplicate_info.get('new_video', {}),
                                                 '#3b82f6')
        new_video_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Frame de información del duplicado
        similar_videos = self.duplicate_info.get('similar_videos', [])
        if similar_videos:
            dup_frame = self._create_info_card(main_frame, "Video Existente Similar",
                                               similar_videos[0], '#f59e0b')
            dup_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Tipo de detección
        type_frame = tk.Frame(main_frame, bg='#1e1e2e')
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        type_label = tk.Label(type_frame, text="Tipo de detección:",
                            font=("Segoe UI", 10), bg='#1e1e2e', fg='#a0a0a0')
        type_label.pack(side=tk.LEFT)
        
        dup_type = self.duplicate_info.get('duplicate_type', 'unknown')
        type_value = tk.Label(type_frame, text=self._format_duplicate_type(dup_type),
                            font=("Segoe UI", 10, "bold"), bg='#1e1e2e', fg='#f59e0b')
        type_value.pack(side=tk.LEFT, padx=(5, 0))
        
        # Opciones de acción
        action_label = tk.Label(main_frame, text="¿Qué desea hacer?",
                               font=("Segoe UI", 11, "bold"), bg='#1e1e2e', fg='white')
        action_label.pack(pady=(0, 10))
        
        # Botones de acción
        button_frame = tk.Frame(main_frame, bg='#1e1e2e')
        button_frame.pack(fill=tk.X)
        
        # Estilo de botones de alto contraste
        btn_style = {
            'font': ("Segoe UI", 10, "bold"),
            'padx': 15,
            'pady': 8,
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }
        
        # Botón 1: Procesar ambos
        btn_process_both = tk.Button(button_frame, text="Procesar Ambos",
                                     bg='#10b981', fg='white', **btn_style,
                                     command=lambda: self._on_decision('process_both'))
        btn_process_both.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        # Botón 2: Omitir nuevo
        btn_omit = tk.Button(button_frame, text="Omitir Nuevo",
                            bg='#ef4444', fg='white', **btn_style,
                            command=lambda: self._on_decision('omit_new'))
        btn_omit.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        # Botón 3: Agrupar
        btn_group = tk.Button(button_frame, text="Agrupar",
                             bg='#8b5cf6', fg='white', **btn_style,
                             command=lambda: self._on_decision('group'))
        btn_group.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        # Botón 4: Ignorar siempre
        btn_ignore = tk.Button(button_frame, text="Ignorar Siempre",
                              bg='#6b7280', fg='white', **btn_style,
                              command=lambda: self._on_decision('ignore_always'))
        btn_ignore.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Checkbox para recordar decisión
        remember_var = tk.BooleanVar(value=False)
        remember_check = tk.Checkbutton(main_frame, text="Recordar esta decisión para futuros casos similares",
                                        variable=remember_var, bg='#1e1e2e', fg='#a0a0a0',
                                        selectcolor='#1e1e2e', activebackground='#1e1e2e')
        remember_check.pack(pady=(15, 0))
        
        # Guardar variable
        self.remember_var = remember_var
    
    def _create_info_card(self, parent, title: str, info: Dict, color: str) -> tk.Frame:
        """Crea un card de información."""
        frame = tk.Frame(parent, bg='#2d2d3d', padx=12, pady=10, relief=tk.FLAT)
        
        title_label = tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"),
                              bg='#2d2d3d', fg=color)
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        if info:
            for key, value in info.items():
                row = tk.Frame(frame, bg='#2d2d3d')
                row.pack(fill=tk.X, pady=2)
                
                key_label = tk.Label(row, text=f"{key}:", font=("Segoe UI", 9),
                                    bg='#2d2d3d', fg='#a0a0a0')
                key_label.pack(side=tk.LEFT)
                
                value_label = tk.Label(row, text=str(value)[:50], font=("Segoe UI", 9),
                                      bg='#2d2d3d', fg='white')
                value_label.pack(side=tk.LEFT, padx=(5, 0))
        
        return frame
    
    def _format_duplicate_type(self, dup_type: str) -> str:
        """Formatea el tipo de duplicado para mostrar."""
        type_map = {
            'exact_content': 'Contenido Exacto (mismo hash)',
            'repost': 'Repost (título similar)',
            'similar_duration': 'Duración Similar',
            'similar_tags': 'Tags en Común',
            'semantic_similar': 'Similitud Semántica (IA)'
        }
        return type_map.get(dup_type, dup_type)
    
    def _on_decision(self, decision: str):
        """Maneja la decisión del usuario."""
        self.result = {
            'decision': decision,
            'remember': self.remember_var.get()
        }
        
        if self.callback:
            self.callback(self.result)
        
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict]:
        """Muestra el diálogo y retorna el resultado."""
        self.parent.wait_window(self.dialog)
        return self.result


class DuplicateNotification:
    """
    Notificación simplificada para cuando no se requiere decisión del usuario.
    Muestra un toast con información del duplicado.
    """
    
    @staticmethod
    def show(parent, duplicate_info: Dict, duration: int = 5000):
        """
        Muestra una notificación de duplicado.
        
        Args:
            parent: Widget padre
            duplicate_info: Info del duplicado
            duration: Duración en ms
        """
        notification = tk.Toplevel(parent)
        notification.wm_overrideredirect(True)
        notification.attributes('-topmost', True)
        
        # Frame principal
        frame = tk.Frame(notification, bg='#f59e0b', padx=15, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono y mensaje
        icon_label = tk.Label(frame, text="🔄", font=("Segoe UI", 14),
                             bg='#f59e0b', fg='white')
        icon_label.pack(side=tk.LEFT, padx=(0, 8))
        
        title = duplicate_info.get('new_video', {}).get('title', 'Video')
        if len(title) > 40:
            title = title[:40] + "..."
        
        msg_label = tk.Label(frame, text=f"Duplicado: {title}",
                            bg='#f59e0b', fg='white', font=("Segoe UI", 9),
                            wraplength=250)
        msg_label.pack(side=tk.LEFT)
        
        # Posicionar
        notification.update_idletasks()
        width = notification.winfo_width()
        height = notification.winfo_height()
        screen_width = parent.winfo_screenwidth()
        x = screen_width - width - 20
        y = 80
        notification.geometry(f"+{x}+{y}")
        
        # Auto-cerrar
        def close():
            try:
                notification.destroy()
            except:
                pass
        
        notification.after(duration, close)
        
        return notification