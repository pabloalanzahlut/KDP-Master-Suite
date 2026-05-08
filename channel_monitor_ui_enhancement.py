# -*- coding: utf-8 -*-
"""
Enhanced Channel Monitor Tab for KDP Knowledge Integrator
Implements Canva/Figma UI/UX principles: Clarity, Drag & Drop, Feedback, Consistency
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
from datetime import datetime

# Este código debe ser integrado en la clase TranscriptionProcessorApp de gui_app.py

def setup_channel_monitor_tab(self):
    """
    Configura la pestaña de Monitor de Canales con principios UI/UX de Canva/Figma
    """
    # Contenedor principal
    main_container = ttk.Frame(self.tab_channel_monitor)
    main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    # ===== HEADER CON ESTADÍSTICAS =====
    stats_frame = ttk.Frame(main_container)
    stats_frame.pack(fill=tk.X, pady=(0, 15))
    
    # Cards de estadísticas
    def create_stat_card(parent, title, value_var, icon, color):
        card = ttk.Frame(parent, relief="raised", borderwidth=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Icono y título
        header = ttk.Frame(card)
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        ttk.Label(header, text=icon, font=("Segoe UI", 16)).pack(side=tk.LEFT)
        ttk.Label(header, text=title, font=("Segoe UI", 9), foreground="#94a3b8").pack(side=tk.LEFT, padx=5)
        
        # Valor
        ttk.Label(card, textvariable=value_var, font=("Segoe UI", 20, "bold"), 
                 foreground=color).pack(padx=10, pady=(0, 10))
        
        return card
    
    # Variables de estadísticas
    self.stat_total_channels = tk.StringVar(value="0")
    self.stat_active_channels = tk.StringVar(value="0")
    self.stat_pending_videos = tk.StringVar(value="0")
    self.stat_last_check = tk.StringVar(value="Nunca")
    
    create_stat_card(stats_frame, "Total Canales", self.stat_total_channels, "📺", "#3b82f6")
    create_stat_card(stats_frame, "Activos", self.stat_active_channels, "✅", "#10b981")
    create_stat_card(stats_frame, "Videos Pendientes", self.stat_pending_videos, "⏳", "#f59e0b")
    
    # Última verificación
    last_check_frame = ttk.Frame(stats_frame, relief="raised", borderwidth=1)
    last_check_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    ttk.Label(last_check_frame, text="🕐 Última Verificación", 
             font=("Segoe UI", 9), foreground="#94a3b8").pack(padx=10, pady=(10, 5))
    ttk.Label(last_check_frame, textvariable=self.stat_last_check, 
             font=("Segoe UI", 11, "bold"), foreground="#06b6d4").pack(padx=10, pady=(0, 10))
    
    # ===== ZONA DE DRAG & DROP PARA CANALES =====
    drop_zone_frame = ttk.LabelFrame(main_container, text=" ☁️ Añadir Canal Rápido ", padding=15)
    drop_zone_frame.pack(fill=tk.X, pady=(0, 15))
    
    # Canvas para drag & drop
    self.channel_drop_canvas = tk.Canvas(drop_zone_frame, height=80,
                                         bg="#1e293b" if self.current_theme == "dark" else "#f8fafc",
                                         highlightthickness=2,
                                         highlightbackground="#a855f7",
                                         highlightcolor="#c084fc",
                                         relief="flat")
    self.channel_drop_canvas.pack(fill=tk.X, pady=(0, 10))
    
    # Dibujar borde punteado
    self.draw_channel_dashed_border()
    
    # Texto central
    canvas_width = 800
    self.channel_drop_canvas.create_text(canvas_width//2, 25,
                                         text="🎯 ARRASTRA URL DE CANAL AQUÍ",
                                         font=("Segoe UI", 14, "bold"),
                                         fill="#a855f7" if self.current_theme == "dark" else "#9333ea",
                                         tags="drop_text")
    self.channel_drop_canvas.create_text(canvas_width//2, 50,
                                         text="o ingresa manualmente abajo",
                                         font=("Segoe UI", 9),
                                         fill="#94a3b8",
                                         tags="drop_subtext")
    
    # Eventos hover
    self.channel_drop_canvas.bind("<Enter>", self.on_channel_drop_enter)
    self.channel_drop_canvas.bind("<Leave>", self.on_channel_drop_leave)
    
    # Input manual
    input_frame = ttk.Frame(drop_zone_frame)
    input_frame.pack(fill=tk.X)
    
    ttk.Label(input_frame, text="🔗 URL del Canal:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
    
    self.channel_url_var = tk.StringVar()
    channel_entry = ttk.Entry(input_frame, textvariable=self.channel_url_var, 
                             font=("Segoe UI", 10), width=40)
    channel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=4)
    
    ttk.Label(input_frame, text="📝 Nombre:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(15, 10))
    
    self.channel_name_var = tk.StringVar()
    name_entry = ttk.Entry(input_frame, textvariable=self.channel_name_var, 
                          font=("Segoe UI", 10), width=25)
    name_entry.pack(side=tk.LEFT, padx=5, ipady=4)
    
    ttk.Button(input_frame, text="➕ Añadir", command=self.add_channel_quick, 
              style="Success.TButton").pack(side=tk.LEFT, padx=(10, 0))
    
    # ===== PANEL DIVIDIDO: LISTA + CONTROLES =====
    paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True)
    
    # Panel izquierdo: Lista de canales
    left_panel = ttk.Frame(paned)
    paned.add(left_panel, weight=3)
    
    list_frame = ttk.LabelFrame(left_panel, text=" 📋 Canales Monitoreados ", padding=10)
    list_frame.pack(fill=tk.BOTH, expand=True)
    
    # Toolbar de lista
    toolbar = ttk.Frame(list_frame)
    toolbar.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(toolbar, text="🔄 Actualizar", command=self.refresh_channel_list, 
              style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(toolbar, text="⚙️ Gestionar", command=self.manage_channels).pack(side=tk.LEFT, padx=5)
    ttk.Button(toolbar, text="🗑️ Eliminar", command=self.delete_selected_channel, 
              style="Danger.TButton").pack(side=tk.LEFT, padx=5)
    
    # Contador
    self.channel_count_label = ttk.Label(toolbar, text="0 canales", 
                                        font=("Segoe UI", 9), foreground="#94a3b8")
    self.channel_count_label.pack(side=tk.RIGHT, padx=10)
    
    # TreeView de canales
    tree_container = ttk.Frame(list_frame)
    tree_container.pack(fill=tk.BOTH, expand=True)
    
    columns = ("name", "url", "status", "videos")
    self.channel_tree = ttk.Treeview(tree_container, columns=columns, show="headings", 
                                     selectmode="extended", height=12)
    
    self.channel_tree.heading("name", text="📺 Nombre")
    self.channel_tree.heading("url", text="🔗 URL")
    self.channel_tree.heading("status", text="⚡ Estado")
    self.channel_tree.heading("videos", text="📊 Videos")
    
    self.channel_tree.column("name", width=200)
    self.channel_tree.column("url", width=150)
    self.channel_tree.column("status", width=100, anchor="center")
    self.channel_tree.column("videos", width=80, anchor="center")
    
    self.channel_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.channel_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    self.channel_tree.config(yscrollcommand=scrollbar.set)
    
    # Panel derecho: Controles y logs
    right_panel = ttk.Frame(paned, padding=(10, 0, 0, 0))
    paned.add(right_panel, weight=1)
    
    # Controles de monitoreo
    control_frame = ttk.LabelFrame(right_panel, text=" ⚙️ Control de Monitoreo ", padding=15)
    control_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Button(control_frame, text="▶️ Verificar Ahora", command=self.check_channels_now, 
              style="Success.TButton").pack(fill=tk.X, pady=5, ipady=10)
    ttk.Button(control_frame, text="⏸️ Pausar Monitor", command=self.toggle_monitor_service).pack(fill=tk.X, pady=5)
    ttk.Button(control_frame, text="📊 Ver Estadísticas", command=self.show_monitor_stats).pack(fill=tk.X, pady=5)
    
    ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
    
    # Configuración de intervalo
    ttk.Label(control_frame, text="Intervalo de verificación:", 
             font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))
    
    self.monitor_interval_var = tk.IntVar(value=60)
    interval_frame = ttk.Frame(control_frame)
    interval_frame.pack(fill=tk.X, pady=5)
    
    ttk.Scale(interval_frame, from_=15, to=180, variable=self.monitor_interval_var, 
             orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
    ttk.Label(interval_frame, textvariable=self.monitor_interval_var, 
             font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
    ttk.Label(interval_frame, text="min").pack(side=tk.LEFT)
    
    # Log de actividad
    log_frame = ttk.LabelFrame(right_panel, text=" 📜 Actividad del Monitor ", padding=10)
    log_frame.pack(fill=tk.BOTH, expand=True)
    
    self.monitor_log = scrolledtext.ScrolledText(log_frame, height=15, 
                                                 font=("Consolas", 9),
                                                 bg="#020617" if self.current_theme == "dark" else "#f8fafc",
                                                 fg="#10b981" if self.current_theme == "dark" else "#1e293b",
                                                 state='disabled')
    self.monitor_log.pack(fill=tk.BOTH, expand=True)
    
    # Inicializar lista
    self.refresh_channel_list()
    self.update_channel_stats()


def draw_channel_dashed_border(self):
    """Dibuja borde punteado en el canvas de drag & drop de canales"""
    width = self.channel_drop_canvas.winfo_reqwidth() or 800
    height = self.channel_drop_canvas.winfo_reqheight() or 80
    
    dash_pattern = (8, 4)
    color = "#a855f7" if self.current_theme == "dark" else "#9333ea"
    
    self.channel_drop_canvas.create_line(10, 10, width-10, 10, fill=color, dash=dash_pattern, width=2, tags="border")
    self.channel_drop_canvas.create_line(width-10, 10, width-10, height-10, fill=color, dash=dash_pattern, width=2, tags="border")
    self.channel_drop_canvas.create_line(width-10, height-10, 10, height-10, fill=color, dash=dash_pattern, width=2, tags="border")
    self.channel_drop_canvas.create_line(10, height-10, 10, 10, fill=color, dash=dash_pattern, width=2, tags="border")


def on_channel_drop_enter(self, event):
    """Efecto visual al pasar mouse sobre zona de drop de canales"""
    self.channel_drop_canvas.config(bg="#4c1d95" if self.current_theme == "dark" else "#f3e8ff")
    self.channel_drop_canvas.config(cursor="hand2")


def on_channel_drop_leave(self, event):
    """Restaurar apariencia normal"""
    self.channel_drop_canvas.config(bg="#1e293b" if self.current_theme == "dark" else "#f8fafc")
    self.channel_drop_canvas.config(cursor="")


def add_channel_quick(self):
    """Añade un canal rápidamente con feedback toast"""
    url = self.channel_url_var.get().strip()
    name = self.channel_name_var.get().strip()
    
    if not url:
        ToastNotification.show(self.root, "Por favor ingresa una URL de canal", "warning")
        return
    
    if not name:
        name = url.split("/")[-1] or "Canal sin nombre"
    
    # Verificar duplicados
    if any(c['url'] == url for c in self.channels):
        ToastNotification.show(self.root, "Este canal ya está en la lista", "warning")
        return
    
    # Añadir canal
    new_channel = {
        "name": name,
        "url": url,
        "category": "General",
        "active": True,
        "date_added": datetime.now().strftime("%Y-%m-%d")
    }
    
    self.channels.append(new_channel)
    self.save_config()
    self.update_channel_combo()
    self.refresh_channel_list()
    self.update_channel_stats()
    
    # Limpiar campos
    self.channel_url_var.set("")
    self.channel_name_var.set("")
    
    # Toast de éxito
    ToastNotification.show(self.root, f"✅ Canal '{name}' añadido correctamente", "success")
    
    # Log
    self.log_monitor_activity(f"Canal añadido: {name} ({url})")


def refresh_channel_list(self):
    """Actualiza la lista visual de canales"""
    self.channel_tree.delete(*self.channel_tree.get_children())
    
    for channel in self.channels:
        status = "✅ Activo" if channel.get("active", True) else "❌ Inactivo"
        videos = "0"  # TODO: Integrar con channel_monitor_service para obtener count real
        
        self.channel_tree.insert("", tk.END, values=(
            channel['name'],
            channel['url'],
            status,
            videos
        ))
    
    # Actualizar contador
    count = len(self.channels)
    self.channel_count_label.config(text=f"{count} canal{'es' if count != 1 else ''}")


def update_channel_stats(self):
    """Actualiza las estadísticas del header"""
    total = len(self.channels)
    active = sum(1 for c in self.channels if c.get("active", True))
    
    self.stat_total_channels.set(str(total))
    self.stat_active_channels.set(str(active))
    # TODO: Integrar con DB para obtener videos pendientes reales
    self.stat_pending_videos.set("0")
    self.stat_last_check.set("Hace 5 min")  # TODO: Obtener de monitor service


def delete_selected_channel(self):
    """Elimina canales seleccionados con confirmación"""
    selected = self.channel_tree.selection()
    if not selected:
        ToastNotification.show(self.root, "Selecciona al menos un canal", "warning")
        return
    
    count = len(selected)
    if not messagebox.askyesno("Confirmar", f"¿Eliminar {count} canal(es) seleccionado(s)?"):
        return
    
    # Obtener URLs de canales seleccionados
    urls_to_delete = set()
    for item in selected:
        values = self.channel_tree.item(item)['values']
        urls_to_delete.add(values[1])  # URL está en columna 1
    
    # Eliminar de la lista
    self.channels = [c for c in self.channels if c['url'] not in urls_to_delete]
    
    self.save_config()
    self.update_channel_combo()
    self.refresh_channel_list()
    self.update_channel_stats()
    
    ToastNotification.show(self.root, f"🗑️ {count} canal(es) eliminado(s)", "success")
    self.log_monitor_activity(f"{count} canales eliminados")


def check_channels_now(self):
    """Fuerza verificación inmediata de canales"""
    ToastNotification.show(self.root, "🔄 Verificando canales...", "info")
    self.log_monitor_activity("Verificación manual iniciada...")
    
    # TODO: Integrar con channel_monitor_service.check_channels()
    # Por ahora solo simulamos
    self.root.after(2000, lambda: ToastNotification.show(
        self.root, "✅ Verificación completada", "success"))


def toggle_monitor_service(self):
    """Activa/desactiva el servicio de monitoreo automático"""
    # TODO: Implementar toggle real del servicio
    ToastNotification.show(self.root, "⏸️ Monitor pausado", "info")
    self.log_monitor_activity("Monitor pausado manualmente")


def show_monitor_stats(self):
    """Muestra ventana con estadísticas detalladas"""
    # TODO: Implementar ventana de estadísticas completa
    messagebox.showinfo("Estadísticas", "Función en desarrollo")


def log_monitor_activity(self, message):
    """Añade mensaje al log de actividad del monitor"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    
    self.monitor_log.configure(state='normal')
    self.monitor_log.insert(tk.END, log_msg)
    self.monitor_log.see(tk.END)
    self.monitor_log.configure(state='disabled')


# NOTA: Estas funciones deben ser añadidas como métodos de la clase TranscriptionProcessorApp
# en gui_app.py. Copiar el contenido de cada función y añadirlo a la clase con la indentación correcta.
