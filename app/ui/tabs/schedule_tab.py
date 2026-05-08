"""
GUI Tab for Schedule Management
================================
Pestaña de programación horaria para gui_app.py
Permite crear, editar, eliminar y monitorear tareas programadas.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional

from app.core.scheduler import ScheduleManager, ScheduleTask, TaskType, ScheduleType, TaskStatus


def setup_schedule_tab(self):
    """Configura la pestaña de Programación Horaria."""
    if not hasattr(self, 'schedule_manager') or self.schedule_manager is None:
        from app.core.scheduler import ScheduleManager
        self.schedule_manager = ScheduleManager(
            config=getattr(self, 'config', None),
            db_manager=getattr(self, 'db_manager', None)
        )
        
        self.schedule_manager.set_services(
            download_service=getattr(self, 'download_service', None),
            processing_service=getattr(self, 'processing_service', None),
            monitor_service=getattr(self, 'monitor_service', None),
            knowledge_integrator=getattr(self, 'knowledge_integrator', None)
        )
        
        self.schedule_manager.set_callbacks(
            on_task_start=self.on_schedule_task_start,
            on_task_complete=self.on_schedule_task_complete,
            on_task_error=self.on_schedule_task_error,
            on_log=self.on_schedule_log,
            on_notification=self.show_schedule_notification
        )
    
    _build_schedule_ui(self)


def _build_schedule_ui(self):
    """Construye la interfaz de usuario de programación"""
    main_container = ttk.Frame(self.tab_schedule)
    main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    top_frame = ttk.Frame(main_container)
    top_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(top_frame, text="📅 PROGRAMACIÓN HORARIA", 
              font=("Inter", 14, "bold")).pack(side=tk.LEFT)
    
    status_frame = ttk.Frame(top_frame)
    status_frame.pack(side=tk.RIGHT)
    
    self.schedule_status_var = tk.StringVar(value="⏸️ Detenido")
    ttk.Label(status_frame, textvariable=self.schedule_status_var,
              font=("Inter", 10, "bold")).pack(side=tk.LEFT, padx=5)
    
    self.schedule_btn = ttk.Button(status_frame, text="▶️ Iniciar",
                                    style="Success.TButton",
                                    command=self.toggle_scheduler)
    self.schedule_btn.pack(side=tk.LEFT, padx=2)
    
    content_paned = tk.PanedWindow(main_container, orient=tk.HORIZONTAL)
    content_paned.pack(fill=tk.BOTH, expand=True)
    
    left_panel = ttk.LabelFrame(content_paned, text="🎯 Tareas Programadas", padding=10)
    content_paned.add(left_panel)
    
    _build_task_list(self, left_panel)
    
    right_panel = tk.PanedWindow(content_paned, orient=tk.VERTICAL)
    content_paned.add(right_panel)
    
    stats_frame = ttk.LabelFrame(right_panel, text="📊 Estadísticas", padding=10)
    right_panel.add(stats_frame)
    _build_stats_panel(self, stats_frame)
    
    log_frame = ttk.LabelFrame(right_panel, text="🕐 Log de Ejecuciones", padding=10)
    right_panel.add(log_frame)
    _build_log_panel(self, log_frame)


def _build_task_list(self, parent):
    """Construye la lista de tareas"""
    btn_frame = ttk.Frame(parent)
    btn_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(btn_frame, text="➕ Nueva Tarea", style="Primary.TButton",
               command=self.create_new_schedule_task).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="🗑️ Eliminar", style="Danger.TButton",
               command=self.delete_selected_task).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="▶️ Ejecutar Ahora", 
               command=self.run_task_now).pack(side=tk.LEFT, padx=2)
    
    tree_container = ttk.Frame(parent)
    tree_container.pack(fill=tk.BOTH, expand=True)
    
    scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    scroll_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    columns = ("nombre", "tipo", "programacion", "proxima", "estado")
    self.schedule_tree = ttk.Treeview(tree_container, columns=columns, show="headings",
                                       yscrollcommand=scroll_y.set,
                                       xscrollcommand=scroll_x.set,
                                       height=8)
    
    scroll_y.config(command=self.schedule_tree.yview)
    scroll_x.config(command=self.schedule_tree.xview)
    
    self.schedule_tree.heading("nombre", text="Nombre")
    self.schedule_tree.heading("tipo", text="Tipo")
    self.schedule_tree.heading("programacion", text="Programación")
    self.schedule_tree.heading("proxima", text="Próxima Ejecución")
    self.schedule_tree.heading("estado", text="Estado")
    
    self.schedule_tree.column("nombre", width=150)
    self.schedule_tree.column("tipo", width=100)
    self.schedule_tree.column("programacion", width=120)
    self.schedule_tree.column("proxima", width=150)
    self.schedule_tree.column("estado", width=80)
    
    self.schedule_tree.pack(fill=tk.BOTH, expand=True)
    
    self.schedule_tree.bind("<Double-1>", self.on_schedule_task_double_click)
    
    self.refresh_schedule_tree()


def _build_stats_panel(self, parent):
    """Construye el panel de estadísticas"""
    stats_container = ttk.Frame(parent)
    stats_container.pack(fill=tk.BOTH, expand=True)
    
    self.schedule_stats_var = tk.StringVar(value="Cargando...")
    stats_text = ttk.Label(stats_container, textvariable=self.schedule_stats_var,
                           font=("Inter", 10), justify=tk.LEFT)
    stats_text.pack(fill=tk.BOTH, expand=True)
    
    ttk.Button(parent, text="🔄 Actualizar", 
               command=self.refresh_schedule_stats).pack(pady=5)


def _build_log_panel(self, parent):
    """Construye el panel de log de ejecuciones"""
    log_container = ttk.Frame(parent)
    log_container.pack(fill=tk.BOTH, expand=True)
    
    scroll_y = ttk.Scrollbar(log_container, orient=tk.VERTICAL)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    self.schedule_log_text = tk.Text(log_container, height=6, state='disabled',
                                      font=("Consolas", 9))
    scroll_y.config(command=self.schedule_log_text.yview)
    self.schedule_log_text.pack(fill=tk.BOTH, expand=True)
    
    btn_frame = ttk.Frame(parent)
    btn_frame.pack(fill=tk.X, pady=5)
    ttk.Button(btn_frame, text="🗑️ Limpiar Log", 
               command=self.clear_schedule_log).pack(side=tk.LEFT)


def refresh_schedule_tree(self):
    """Actualiza la lista de tareas"""
    for item in self.schedule_tree.get_children():
        self.schedule_tree.delete(item)
    
    if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
        return
    
    for task in self.schedule_manager.get_all_tasks():
        tipo_display = {
            'download': '📥 Descarga',
            'process': '⚙️ Procesar',
            'monitor': '📺 Monitor',
            'detect_new': '🔔 Detectar Nuevos'
        }.get(task.task_type, task.task_type)
        
        schedule_display = ""
        if task.schedule_type == 'interval':
            schedule_display = f"Cada {task.interval_minutes} min"
        elif task.schedule_type == 'daily':
            schedule_display = f"Diaria {task.daily_time}"
        elif task.schedule_type == 'multiple':
            schedule_display = f"Múltiple: {', '.join(task.multiple_times[:2])}"
        elif task.schedule_type == 'event':
            schedule_display = f"Evento: {task.event_trigger or 'N/A'}"
        
        next_run = task.next_run[:16] if task.next_run else "N/A"
        
        estado = "✅ Activa" if task.enabled else "⏸️ Pausada"
        
        self.schedule_tree.insert('', tk.END, values=(
            task.name, tipo_display, schedule_display, next_run, estado
        ), tags=(task.task_id,))


def refresh_schedule_stats(self):
    """Actualiza las estadísticas del scheduler"""
    if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
        return
    
    stats = self.schedule_manager.get_stats()
    
    next_exec = "N/A"
    if stats.get('next_execution'):
        try:
            dt = datetime.fromisoformat(stats['next_execution'])
            next_exec = dt.strftime("%H:%M:%S")
        except:
            next_exec = stats['next_execution'][:8]
    
    status_text = f"""Tareas Totales: {stats['total_tasks']}
Tareas Activas: {stats['active_tasks']}
Ejecuciones Hoy: {stats['completed_today']}
Fallos Hoy: {stats['failed_today']}
Próxima Ejecución: {next_exec}"""
    
    self.schedule_stats_var.set(status_text)
    
    if stats['running']:
        if stats['paused']:
            self.schedule_status_var.set("⏸️ Pausado")
        else:
            self.schedule_status_var.set("✅ Activo")
    else:
        self.schedule_status_var.set("⏸️ Detenido")


def toggle_scheduler(self):
    """Inicia o detiene el scheduler"""
    if not hasattr(self, 'schedule_manager'):
        return
    
    if self.schedule_manager.running:
        self.schedule_manager.stop()
        self.schedule_btn.config(text="▶️ Iniciar")
    else:
        self.schedule_manager.start()
        self.schedule_btn.config(text="⏹️ Detener")
    
    self.refresh_schedule_stats()


def create_new_schedule_task(self):
    """Abre diálogo para crear nueva tarea"""
    dialog = tk.Toplevel(self.root)
    dialog.title("✨ Nueva Tarea Programada")
    dialog.geometry("450x500")
    dialog.transient(self.root)
    dialog.grab_set()
    
    task_name_var = tk.StringVar()
    task_type_var = tk.StringVar(value="download")
    schedule_type_var = tk.StringVar(value="interval")
    interval_var = tk.IntVar(value=60)
    daily_time_var = tk.StringVar(value="03:00")
    enabled_var = tk.BooleanVar(value=True)
    auto_kb_var = tk.BooleanVar(value=True)
    
    ttk.Label(dialog, text="Nombre de la Tarea:").pack(pady=(10, 0))
    ttk.Entry(dialog, textvariable=task_name_var, width=40).pack(pady=5)
    
    ttk.Label(dialog, text="Tipo de Tarea:").pack(pady=(10, 0))
    type_frame = ttk.Frame(dialog)
    type_frame.pack()
    for val, text in [('download', '📥 Descarga'), ('process', '⚙️ Procesar'),
                      ('monitor', '📺 Monitor'), ('detect_new', '🔔 Detectar Nuevos')]:
        ttk.Radiobutton(type_frame, text=text, variable=task_type_var, 
                        value=val).pack(side=tk.LEFT, padx=5)
    
    ttk.Label(dialog, text="Tipo de Programación:").pack(pady=(10, 0))
    sched_frame = ttk.Frame(dialog)
    sched_frame.pack()
    for val, text in [('interval', 'Intervalo'), ('daily', 'Diaria'), 
                      ('multiple', 'Múltiple'), ('event', 'Por Evento')]:
        ttk.Radiobutton(sched_frame, text=text, variable=schedule_type_var,
                        value=val).pack(side=tk.LEFT, padx=3)
    
    ttk.Label(dialog, text="Intervalo (minutos):").pack(pady=(10, 0))
    ttk.Entry(dialog, textvariable=interval_var, width=15).pack()
    
    ttk.Label(dialog, text="Hora diaria (HH:MM):").pack(pady=(10, 0))
    ttk.Entry(dialog, textvariable=daily_time_var, width=15).pack()
    
    options_frame = ttk.LabelFrame(dialog, text="Opciones", padding=10)
    options_frame.pack(pady=10, fill=tk.X, padx=20)
    ttk.Checkbutton(options_frame, text="Habilitada", variable=enabled_var).pack(anchor=tk.W)
    ttk.Checkbutton(options_frame, text="Auto-integrar a KB después de procesar", 
                    variable=auto_kb_var).pack(anchor=tk.W)
    
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=10)
    
    def save_task():
        if not task_name_var.get():
            messagebox.showwarning("Advertencia", "Ingrese un nombre para la tarea")
            return
        
        task = ScheduleTask(
            name=task_name_var.get(),
            task_type=task_type_var.get(),
            schedule_type=schedule_type_var.get(),
            interval_minutes=interval_var.get(),
            daily_time=daily_time_var.get(),
            enabled=enabled_var.get(),
            auto_integrate_kb=auto_kb_var.get()
        )
        
        if self.schedule_manager.add_task(task):
            messagebox.showinfo("Éxito", "Tarea creada correctamente")
            dialog.destroy()
            refresh_schedule_tree(self)
            refresh_schedule_stats(self)
        else:
            messagebox.showerror("Error", "No se pudo crear la tarea")
    
    ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="💾 Guardar", style="Primary.TButton",
               command=save_task).pack(side=tk.LEFT, padx=5)


def delete_selected_task(self):
    """Elimina la tarea seleccionada"""
    selection = self.schedule_tree.selection()
    if not selection:
        messagebox.showwarning("Advertencia", "Seleccione una tarea para eliminar")
        return
    
    item = selection[0]
    task_id = self.schedule_tree.item(item, 'tags')[0]
    
    if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta tarea?"):
        if self.schedule_manager.remove_task(task_id):
            messagebox.showinfo("Éxito", "Tarea eliminada")
            refresh_schedule_tree(self)
            refresh_schedule_stats(self)
        else:
            messagebox.showerror("Error", "No se pudo eliminar la tarea")


def run_task_now(self):
    """Ejecuta la tarea seleccionada inmediatamente"""
    selection = self.schedule_tree.selection()
    if not selection:
        messagebox.showwarning("Advertencia", "Seleccione una tarea para ejecutar")
        return
    
    item = selection[0]
    task_id = self.schedule_tree.item(item, 'tags')[0]
    
    task = self.schedule_manager.get_task(task_id)
    if task:
        self.schedule_manager._execute_task(task)
        messagebox.showinfo("Ejecutando", f"Tarea '{task.name}' iniciada")
        refresh_schedule_stats(self)


def on_schedule_task_double_click(self, event):
    """Maneja doble clic en tarea para editar"""
    selection = self.schedule_tree.selection()
    if not selection:
        return
    
    item = selection[0]
    task_id = self.schedule_tree.item(item, 'tags')[0]
    
    task = self.schedule_manager.get_task(task_id)
    if task:
        _show_edit_task_dialog(self, task)


def _show_edit_task_dialog(self, task):
    """Muestra diálogo para editar tarea"""
    dialog = tk.Toplevel(self.root)
    dialog.title(f"✏️ Editar: {task.name}")
    dialog.geometry("400x350")
    dialog.transient(self.root)
    dialog.grab_set()
    
    name_var = tk.StringVar(value=task.name)
    enabled_var = tk.BooleanVar(value=task.enabled)
    interval_var = tk.IntVar(value=task.interval_minutes)
    daily_time_var = tk.StringVar(value=task.daily_time or "03:00")
    
    ttk.Label(dialog, text="Nombre:").pack(pady=(10, 0))
    ttk.Entry(dialog, textvariable=name_var, width=35).pack(pady=5)
    
    ttk.Label(dialog, text="Intervalo (minutos):").pack(pady=(10, 0))
    ttk.Entry(dialog, textvariable=interval_var, width=15).pack()
    
    ttk.Label(dialog, text="Hora diaria (HH:MM):").pack(pady=(10, 0))
    ttk.Entry(dialog, textvariable=daily_time_var, width=15).pack()
    
    ttk.Checkbutton(dialog, text="Habilitada", variable=enabled_var).pack(pady=10)
    
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=10)
    
    def save_changes():
        self.schedule_manager.update_task(
            task.task_id,
            name=name_var.get(),
            enabled=enabled_var.get(),
            interval_minutes=interval_var.get(),
            daily_time=daily_time_var.get()
        )
        messagebox.showinfo("Éxito", "Tarea actualizada")
        dialog.destroy()
        refresh_schedule_tree(self)
        refresh_schedule_stats(self)
    
    ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="💾 Guardar", style="Primary.TButton",
               command=save_changes).pack(side=tk.LEFT, padx=5)


def clear_schedule_log(self):
    """Limpia el log de ejecuciones"""
    if hasattr(self, 'schedule_manager') and self.schedule_manager:
        self.schedule_manager.clear_history()
    
    self.schedule_log_text.config(state='normal')
    self.schedule_log_text.delete(1.0, tk.END)
    self.schedule_log_text.config(state='disabled')


def on_schedule_task_start(self, task):
    """Callback cuando inicia una tarea"""
    self.schedule_log_text.config(state='normal')
    self.schedule_log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ▶️ Iniciando: {task.name}\n")
    self.schedule_log_text.see(tk.END)
    self.schedule_log_text.config(state='disabled')
    self.root.after(100, refresh_schedule_stats, self)


def on_schedule_task_complete(self, task, result):
    """Callback cuando completa una tarea"""
    self.schedule_log_text.config(state='normal')
    self.schedule_log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Completado: {task.name} - {result.message}\n")
    self.schedule_log_text.see(tk.END)
    self.schedule_log_text.config(state='disabled')
    self.root.after(100, refresh_schedule_stats, self)


def on_schedule_task_error(self, task, result):
    """Callback cuando falla una tarea"""
    self.schedule_log_text.config(state='normal')
    self.schedule_log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {task.name} - {result.message}\n")
    self.schedule_log_text.see(tk.END)
    self.schedule_log_text.config(state='disabled')
    self.root.after(100, refresh_schedule_stats, self)


def on_schedule_log(self, message, level):
    """Callback para logs del scheduler"""
    pass


def show_schedule_notification(self, title, message, type="info"):
    """Muestra notificación toast para eventos del scheduler"""
    try:
        from app.ui.components.notifications import ToastNotification
        ToastNotification.show(self.root, f"{title}\n{message}", type=type, duration=5000)
    except Exception as e:
        print(f"Error mostrando notificación: {e}")


TranscriptionProcessorApp_schedule_tab = setup_schedule_tab
TranscriptionProcessorApp_refresh_schedule_tree = refresh_schedule_tree
TranscriptionProcessorApp_refresh_schedule_stats = refresh_schedule_stats
TranscriptionProcessorApp_toggle_scheduler = toggle_scheduler
TranscriptionProcessorApp_create_new_schedule_task = create_new_schedule_task
TranscriptionProcessorApp_delete_selected_task = delete_selected_task
TranscriptionProcessorApp_run_task_now = run_task_now
TranscriptionProcessorApp_on_schedule_task_double_click = on_schedule_task_double_click
TranscriptionProcessorApp_clear_schedule_log = clear_schedule_log
TranscriptionProcessorApp_on_schedule_task_start = on_schedule_task_start
TranscriptionProcessorApp_on_schedule_task_complete = on_schedule_task_complete
TranscriptionProcessorApp_on_schedule_task_error = on_schedule_task_error
TranscriptionProcessorApp_on_schedule_log = on_schedule_log