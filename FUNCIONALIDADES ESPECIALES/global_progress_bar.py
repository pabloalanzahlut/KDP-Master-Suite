import tkinter as tk
from tkinter import ttk

class GlobalStatusBar(ttk.Frame):
    """
    Componente de UI para mostrar el progreso global del sistema (US-008).
    Ubicado típicamente en la parte inferior de la ventana principal.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()

    def _create_widgets(self):
        # --- INICIO CONFIGURACIÓN ESTÉTICA (Sugerencias v2.0) ---
        self.status_label = ttk.Label(self, text="Sistema Listo", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress.pack(side=tk.RIGHT, padx=10, pady=2)
        
        self.percentage_label = ttk.Label(self, text="0%", font=("Segoe UI", 9, "bold"))
        self.percentage_label.pack(side=tk.RIGHT, padx=5)
        # --- FIN CONFIGURACIÓN ESTÉTICA ---

    def update_progress(self, current: float, total: float, message: str = None):
        """
        Actualiza la barra de progreso global desde cualquier hilo de forma segura.
        """
        if total <= 0: return
        
        percent = (current / total) * 100
        self.progress['value'] = percent
        self.percentage_label.config(text=f"{int(percent)}%")
        
        if message:
            self.status_label.config(text=message)
            
    def set_error(self, message: str):
        """Muestra un estado de error visual en la barra global."""
        self.status_label.config(text=f"❌ Error: {message}", foreground="red")

    def reset(self):
        """Reinicia la barra a su estado inicial."""
        self.progress['value'] = 0
        self.percentage_label.config(text="0%")
        self.status_label.config(text="Listo", foreground="black")