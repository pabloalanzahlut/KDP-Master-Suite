"""
GUI Tab for Remote Dashboard
=============================
Pestaña para controlar el Dashboard Web Remoto
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import time
from pathlib import Path

from app.ui.components.notifications import ToastNotification
from app.core.app_state import AppState


def setup_dashboard_tab(self):
    """Configura la pestaña de Dashboard Web."""
    frame = ttk.Frame(self.tab_dashboard, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="📊 Dashboard Web Remoto", font=("Segoe UI", 18, "bold")).pack(pady=(0, 10))
    ttk.Label(frame, text="Monitorea el sistema desde cualquier dispositivo en localhost.", font=("Segoe UI", 11), foreground="gray").pack(pady=(0, 30))
    
    info_frame = ttk.LabelFrame(frame, text=" Estado del Servidor ", padding=20)
    info_frame.pack(fill=tk.X, pady=(0, 20))
    
    self.dashboard_link = ttk.Label(info_frame, text="http://localhost:8000", font=("Consolas", 14, "bold"), foreground="#3b82f6", cursor="hand2")
    self.dashboard_link.pack(pady=10)
    self.dashboard_link.bind("<Button-1>", lambda e: open_url("http://localhost:8000"))
    
    self.dashboard_status_lbl = ttk.Label(info_frame, text="⚫ Servidor Detenido", font=("Segoe UI", 10))
    self.dashboard_status_lbl.pack(pady=5)
    
    self.dashboard_port_lbl = ttk.Label(info_frame, text="", font=("Segoe UI", 9), foreground="#94a3b8")
    self.dashboard_port_lbl.pack()
    
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=20)
    
    self.dashboard_btn = ttk.Button(btn_frame, text="▶️ Iniciar Servidor Web", command=lambda: toggle_server(self), style="Success.TButton", width=25)
    self.dashboard_btn.pack(pady=5)
    
    if is_port_in_use(8000):
        self.dashboard_process = None
        self.dashboard_btn.config(text="⏹️ Detener Servidor Web", style="Danger.TButton")
        self.dashboard_status_lbl.config(text="🟢 Puerto 8000 en uso (posiblemente activo)", foreground="#10b981")


def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def toggle_server(self):
    if not hasattr(self, 'dashboard_process') or self.dashboard_process is None:
        if is_port_in_use(8000):
            self.dashboard_process = None
            self.dashboard_btn.config(text="⏹️ Detener Servidor Web", style="Danger.TButton")
            self.dashboard_status_lbl.config(text="🟢 Servidor Detectado en puerto 8000", foreground="#10b981")
            ToastNotification.show(self.root, "Dashboard ya está corriendo en puerto 8000", "info")
            return
        
        try:
            server_script = os.path.join(self.base_dir, "dashboard_server.py")
            self.dashboard_process = subprocess.Popen(
                [sys.executable, server_script],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                cwd=self.base_dir
            )
            time.sleep(1)
            
            if self.dashboard_process.poll() is not None:
                ToastNotification.show(self.root, "Error al iniciar el servidor. Revisa la consola.", "error")
                self.dashboard_process = None
                return
            
            self.dashboard_btn.config(text="⏹️ Detener Servidor Web", style="Danger.TButton")
            self.dashboard_status_lbl.config(text="🟢 Servidor Ejecutándose", foreground="#10b981")
            self.dashboard_port_lbl.config(text="Puerto 8000 · Auto-refresh cada 30s")
            ToastNotification.show(self.root, "Dashboard Web Iniciado en http://localhost:8000", "success")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar: {e}")
    else:
        try:
            self.dashboard_process.terminate()
            self.dashboard_process.wait(timeout=5)
        except Exception:
            self.dashboard_process.kill()
        
        self.dashboard_process = None
        self.dashboard_btn.config(text="▶️ Iniciar Servidor Web", style="Success.TButton")
        self.dashboard_status_lbl.config(text="⚫ Servidor Detenido", foreground="gray")
        self.dashboard_port_lbl.config(text="")
        ToastNotification.show(self.root, "Dashboard Web Detenido", "info")


def open_url(url):
    import webbrowser
    webbrowser.open(url)


def set_monitor_running(running: bool):
    """Actualiza el estado del monitor en AppState (thread-safe)."""
    AppState.set("monitor_running", running)


def get_monitor_running() -> bool:
    """Obtiene el estado del monitor desde AppState."""
    return AppState.get("monitor_running", False)
