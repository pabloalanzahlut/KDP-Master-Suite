"""
Componente de logging para redirigir logs a la GUI.
Manejo de TextHandler con autolimpieza de memoria.
"""

import logging
import tkinter as tk


class TextHandler(logging.Handler):
    """Handler que redirige logs a un widget ScrolledText."""
    
    def __init__(self, text_widget, max_lines=1000):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        self.max_lines = max_lines

    def emit(self, record):
        """Emite el registro de log al widget."""
        msg = self.format(record)
        
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            
            current_lines = int(self.text_widget.index('end-1c').split('.')[0])
            if current_lines > self.max_lines:
                self.text_widget.delete("1.0", f"{current_lines - self.max_lines}.0")
            
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        
        self.text_widget.after(0, append)


class LogViewer:
    """Widget de visualización de logs con autolimpieza."""
    
    def __init__(self, parent, max_lines=1000):
        self.max_lines = max_lines
        self.text_widget = tk.Text(parent, wrap=tk.WORD, height=10, state='disabled')
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.handler = TextHandler(self.text_widget, max_lines)
    
    @property
    def handler(self):
        return self._handler
    
    @handler.setter
    def handler(self, value):
        self._handler = value
    
    def get_handler(self):
        return self._handler