import tkinter as tk

class ToastNotification:
    """Sistema de notificaciones toast modernas"""
    
    @staticmethod
    def show(parent, message, type="info", duration=3000):
        """
        Muestra una notificación toast
        
        Args:
            parent: Widget padre (normalmente root)
            message: Mensaje a mostrar
            type: Tipo de notificación ('success', 'error', 'warning', 'info')
            duration: Duración en milisegundos (0 para no auto-cerrar)
        """
        # Crear ventana toplevel
        toast = tk.Toplevel(parent)
        toast.wm_overrideredirect(True)
        toast.attributes('-topmost', True)
        
        # Colores según tipo
        colors = {
            'success': {'bg': '#10b981', 'fg': 'white', 'icon': '✓'},
            'error': {'bg': '#ef4444', 'fg': 'white', 'icon': '✕'},
            'warning': {'bg': '#f59e0b', 'fg': 'white', 'icon': '⚠'},
            'info': {'bg': '#3b82f6', 'fg': 'white', 'icon': 'ℹ'}
        }
        
        color_scheme = colors.get(type, colors['info'])
        
        # Frame principal con padding
        frame = tk.Frame(toast, bg=color_scheme['bg'], padx=20, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono
        icon_label = tk.Label(frame, text=color_scheme['icon'], 
                             bg=color_scheme['bg'], fg=color_scheme['fg'],
                             font=("Segoe UI", 14, "bold"))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Mensaje
        msg_label = tk.Label(frame, text=message, 
                            bg=color_scheme['bg'], fg=color_scheme['fg'],
                            font=("Segoe UI", 10), wraplength=300)
        msg_label.pack(side=tk.LEFT)
        
        # Posicionar en esquina superior derecha
        toast.update_idletasks()
        width = toast.winfo_width()
        height = toast.winfo_height()
        screen_width = parent.winfo_screenwidth()
        x = screen_width - width - 20
        y = 20
        toast.geometry(f"+{x}+{y}")
        
        # Auto-cerrar después de duration
        if duration > 0:
            def fade_out():
                try:
                    toast.destroy()
                except:
                    pass
            toast.after(duration, fade_out)
        
        # Permitir cerrar con click
        frame.bind("<Button-1>", lambda e: toast.destroy())
        icon_label.bind("<Button-1>", lambda e: toast.destroy())
        msg_label.bind("<Button-1>", lambda e: toast.destroy())
        
        return toast
