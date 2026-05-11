"""
GUI Tab for Channel Monitoring
===============================
Pestaña de monitoreo de canales para gui_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json

# Importar servicios de monitoreo e UI
from app.database.db_manager import DatabaseManager
from app.services.monitor_service import ChannelMonitorService
from app.core.keyword_filter import KeywordFilter
from app.ui.components.notifications import ToastNotification
from app.ui.components.tooltips import ToolTip


def setup_monitor_tab(self):
    """Configura la pestaña de Monitor de Canales."""
    # Inicializar servicios
    try:
        if not hasattr(self, 'db_manager') or self.db_manager is None:
            self.db_manager = DatabaseManager()
        if not hasattr(self, 'monitor_service') or self.monitor_service is None:
            self.monitor_service = ChannelMonitorService(db_manager=self.db_manager)
        
        # Configurar callbacks
        self.monitor_service.set_callbacks(
            on_new_video=self.on_monitor_new_video,
            on_processing_complete=self.on_monitor_processing_complete,
            on_error=self.on_monitor_error,
            on_log=self.on_monitor_log,
            on_duplicate_detected=self.on_monitor_duplicate_detected
        )
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo inicializar el monitor: {e}")
        return
    
    # Frame principal con dos columnas
    main_container = ttk.Frame(self.tab_monitor)
    main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # ========== COLUMNA IZQUIERDA: Gestión de Canales ==========
    left_frame = ttk.LabelFrame(main_container, text=" 📺 Canales Monitoreados ", padding=10)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    # Botones de acción
    btn_frame = ttk.Frame(left_frame)
    btn_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(btn_frame, text="➕ Añadir Canal", style="Success.TButton",
               command=self.add_channel_dialog).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="🗑️ Eliminar", style="Danger.TButton",
               command=self.remove_selected_channel).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="🔄 Refrescar", 
               command=self.refresh_channels_list).pack(side=tk.LEFT, padx=2)
    
    # TreeView de canales
    channels_container = ttk.Frame(left_frame)
    channels_container.pack(fill=tk.BOTH, expand=True)
    
    # Scrollbars
    channels_scroll_y = ttk.Scrollbar(channels_container, orient=tk.VERTICAL)
    channels_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    channels_scroll_x = ttk.Scrollbar(channels_container, orient=tk.HORIZONTAL)
    channels_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    # TreeView
    self.channels_tree = ttk.Treeview(
        channels_container,
        columns=("id", "nombre", "url", "estado", "ultima_verificacion", "videos"),
        show="headings",
        yscrollcommand=channels_scroll_y.set,
        xscrollcommand=channels_scroll_x.set,
        height=10
    )
    
    channels_scroll_y.config(command=self.channels_tree.yview)
    channels_scroll_x.config(command=self.channels_tree.xview)
    
    # Configurar columnas
    self.channels_tree.heading("id", text="ID")
    self.channels_tree.heading("nombre", text="Nombre del Canal")
    self.channels_tree.heading("url", text="URL / Handle")
    self.channels_tree.heading("estado", text="Estado")
    self.channels_tree.heading("ultima_verificacion", text="Última Verif.")
    self.channels_tree.heading("videos", text="Videos")
    
    self.channels_tree.column("id", width=40, anchor=tk.CENTER)
    self.channels_tree.column("nombre", width=200)
    self.channels_tree.column("url", width=150)
    self.channels_tree.column("estado", width=70, anchor=tk.CENTER)
    self.channels_tree.column("ultima_verificacion", width=120, anchor=tk.CENTER)
    self.channels_tree.column("videos", width=60, anchor=tk.CENTER)
    
    self.channels_tree.pack(fill=tk.BOTH, expand=True)
    
    # Bind doble click para ver videos
    self.channels_tree.bind("<Double-1>", self.show_channel_videos)
    # Bind clic derecho para menú contextual
    self.channels_tree.bind("<Button-3>", self.show_context_menu)
    # Bind Ctrl+A para seleccionar todo
    self.channels_tree.bind("<Control-a>", self.select_all_channels)
    
    # Crear Menú Contextual
    self.context_menu = tk.Menu(self.root, tearoff=0)
    self.context_menu.add_command(label="🔍 Verificar Ahora", command=self.check_selected_channel)
    self.context_menu.add_command(label="✏️ Editar Canal", command=self.edit_selected_channel)
    self.context_menu.add_command(label="📋 Copiar URL", command=self.copy_channel_url)
    self.context_menu.add_separator()
    self.context_menu.add_command(label="🗑️ Eliminar", command=self.remove_selected_channel)
    self.context_menu.add_separator()
    self.context_menu.add_command(label="✅ Seleccionar Todo", command=self.select_all_channels)

    # ========== COLUMNA DERECHA: Control y Estadísticas ==========
    right_frame = ttk.Frame(main_container)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
    
    # Panel de Control
    control_frame = ttk.LabelFrame(right_frame, text=" 🎮 Control del Monitor ", padding=10)
    control_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Estado del monitor
    status_frame = ttk.Frame(control_frame)
    status_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(status_frame, text="Estado:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
    self.monitor_status_label = ttk.Label(status_frame, text="⚫ Detenido", 
                                         font=("Segoe UI", 10))
    self.monitor_status_label.pack(side=tk.LEFT, padx=10)
    
    # Botones de control
    control_buttons = ttk.Frame(control_frame)
    control_buttons.pack(fill=tk.X)
    
    self.start_monitor_btn = ttk.Button(control_buttons, text="▶️ Iniciar Monitor",
                                       style="Success.TButton",
                                       command=self.start_monitor)
    self.start_monitor_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    self.stop_monitor_btn = ttk.Button(control_buttons, text="⏹️ Detener",
                                      style="Danger.TButton",
                                      command=self.stop_monitor,
                                      state=tk.DISABLED)
    self.stop_monitor_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    ttk.Button(control_buttons, text="🔍 Verificar Ahora",
              command=self.check_now).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    # ========== PANEL DE PERFILES DE FILTROS ==========
    profiles_frame = ttk.LabelFrame(right_frame, text=" 📁 Perfiles de Filtros ", padding=10)
    profiles_frame.pack(fill=tk.X, pady=(0, 10))
    
    profiles_inner = ttk.Frame(profiles_frame)
    profiles_inner.pack(fill=tk.X)
    
    # Selector de perfil activo
    ttk.Label(profiles_inner, text="Perfil activo:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
    
    profile_select_frame = ttk.Frame(profiles_inner)
    profile_select_frame.grid(row=0, column=1, sticky=tk.EW, pady=2)
    
    self.profile_combo = ttk.Combobox(profile_select_frame, state="readonly", width=20)
    self.profile_combo.pack(side=tk.LEFT, padx=(0, 5))
    self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_selected)
    
    ttk.Button(profile_select_frame, text="🔄", width=3, command=self.reload_filter_profiles).pack(side=tk.LEFT)
    
    # Botones de gestión de perfiles
    profile_btns = ttk.Frame(profiles_frame)
    profile_btns.pack(fill=tk.X, pady=(5, 0))
    
    ttk.Button(profile_btns, text="➕ Nuevo", width=8, command=self.create_new_filter_profile).pack(side=tk.LEFT, padx=2)
    ttk.Button(profile_btns, text="📋 Duplicar", width=8, command=self.duplicate_filter_profile).pack(side=tk.LEFT, padx=2)
    ttk.Button(profile_btns, text="🗑️ Eliminar", width=8, style="Danger.TButton", command=self.delete_filter_profile).pack(side=tk.LEFT, padx=2)
    ttk.Button(profile_btns, text="⭐ Activar", width=8, style="Success.TButton", command=self.activate_filter_profile).pack(side=tk.LEFT, padx=2)
    
    # Indicador de perfil activo
    self.active_profile_label = ttk.Label(profiles_frame, text="", font=("Segoe UI", 8), foreground="#10b981")
    self.active_profile_label.pack(anchor=tk.W, pady=(5, 0))
    
    profiles_inner.columnconfigure(1, weight=1)
    
    # Panel de Filtros de Palabras Clave
    filter_frame = ttk.LabelFrame(right_frame, text=" 🔤 Filtros de Palabras ", padding=10)
    filter_frame.pack(fill=tk.X, pady=(0, 10))
    
    filter_inner = ttk.Frame(filter_frame)
    filter_inner.pack(fill=tk.X)
    
    self.filter_enabled_var = tk.BooleanVar(value=False)
    self.filter_enabled_check = ttk.Checkbutton(
        filter_inner,
        text="Habilitar Filtro",
        variable=self.filter_enabled_var,
        command=self.on_filter_toggle
    )
    self.filter_enabled_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
    
    ttk.Label(filter_inner, text="Incluir (blanco):", font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
    self.include_keywords_var = tk.StringVar()
    include_entry = ttk.Entry(filter_inner, textvariable=self.include_keywords_var, font=("Segoe UI", 9))
    include_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)
    
    ttk.Label(filter_inner, text="Excluir (negro):", font=("Segoe UI", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
    self.exclude_keywords_var = tk.StringVar()
    exclude_entry = ttk.Entry(filter_inner, textvariable=self.exclude_keywords_var, font=("Segoe UI", 9))
    exclude_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)
    
    ttk.Label(filter_inner, text="Modo:", font=("Segoe UI", 9)).grid(row=3, column=0, sticky=tk.W, pady=2)
    mode_frame = ttk.Frame(filter_inner)
    mode_frame.grid(row=3, column=1, sticky=tk.W)
    self.filter_mode_var = tk.StringVar(value="OR")
    ttk.Radiobutton(mode_frame, text="Cualquiera (OR)", variable=self.filter_mode_var, value="OR").pack(side=tk.LEFT, padx=2)
    ttk.Radiobutton(mode_frame, text="Todas (AND)", variable=self.filter_mode_var, value="AND").pack(side=tk.LEFT, padx=2)
    
    filter_inner.columnconfigure(1, weight=1)
    
    filter_btn_frame = ttk.Frame(filter_frame)
    filter_btn_frame.pack(fill=tk.X, pady=(10, 0))
    ttk.Button(filter_btn_frame, text="💾 Guardar", command=self.save_keyword_filter_config).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    ttk.Button(filter_btn_frame, text="🧪 Probar", command=self.test_keyword_filter).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    ttk.Button(filter_btn_frame, text="🔄 Reset", command=self.reset_keyword_filter).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    self.filter_test_entry = ttk.Entry(filter_btn_frame, width=20)
    self.filter_test_entry.pack(side=tk.LEFT, padx=5)
    self.filter_test_entry.insert(0, "Título de prueba...")
    self.filter_test_entry.bind("<FocusIn>", lambda e: self.filter_test_entry.delete(0, tk.END) if self.filter_test_entry.get() == "Título de prueba..." else None)
    
    self.filter_result_label = ttk.Label(filter_frame, text="", font=("Segoe UI", 9))
    self.filter_result_label.pack(anchor=tk.W, pady=(5, 0))
    
    load_keyword_filter_config()
    
    # Cargar perfiles de filtros
    self.reload_filter_profiles()
    
    # Panel de Estadísticas
    stats_frame = ttk.LabelFrame(right_frame, text=" 📊 Estadísticas ", padding=10)
    stats_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Grid de estadísticas
    stats_grid = ttk.Frame(stats_frame)
    stats_grid.pack(fill=tk.X)
    
    # Fila 1
    ttk.Label(stats_grid, text="Canales activos:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
    self.stat_channels = ttk.Label(stats_grid, text="0", font=("Segoe UI", 9, "bold"), foreground="#3b82f6")
    self.stat_channels.grid(row=0, column=1, sticky=tk.E, pady=2)
    
    # Fila 2
    ttk.Label(stats_grid, text="Videos detectados:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
    self.stat_total_videos = ttk.Label(stats_grid, text="0", font=("Segoe UI", 9, "bold"), foreground="#3b82f6")
    self.stat_total_videos.grid(row=1, column=1, sticky=tk.E, pady=2)
    
    # Fila 3
    ttk.Label(stats_grid, text="Pendientes:", font=("Segoe UI", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
    self.stat_pending = ttk.Label(stats_grid, text="0", font=("Segoe UI", 9, "bold"), foreground="#f59e0b")
    self.stat_pending.grid(row=2, column=1, sticky=tk.E, pady=2)
    
    # Fila 4
    ttk.Label(stats_grid, text="Completados:", font=("Segoe UI", 9)).grid(row=3, column=0, sticky=tk.W, pady=2)
    self.stat_completed = ttk.Label(stats_grid, text="0", font=("Segoe UI", 9, "bold"), foreground="#10b981")
    self.stat_completed.grid(row=3, column=1, sticky=tk.E, pady=2)
    
    # Fila 5
    ttk.Label(stats_grid, text="Fallidos:", font=("Segoe UI", 9)).grid(row=4, column=0, sticky=tk.W, pady=2)
    self.stat_failed = ttk.Label(stats_grid, text="0", font=("Segoe UI", 9, "bold"), foreground="#ef4444")
    self.stat_failed.grid(row=4, column=1, sticky=tk.E, pady=2)
    
    # Fila 6 - Duplicados detectados
    ttk.Label(stats_grid, text="Duplicados:", font=("Segoe UI", 9)).grid(row=5, column=0, sticky=tk.W, pady=2)
    self.stat_duplicates = ttk.Label(stats_grid, text="0", font=("Segoe UI", 9, "bold"), foreground="#8b5cf6")
    self.stat_duplicates.grid(row=5, column=1, sticky=tk.E, pady=2)
    
    # Fila 7 - Tasa de duplicados
    ttk.Label(stats_grid, text="Tasa duplicados:", font=("Segoe UI", 9)).grid(row=6, column=0, sticky=tk.W, pady=2)
    self.stat_duplicate_rate = ttk.Label(stats_grid, text="0%", font=("Segoe UI", 9, "bold"), foreground="#8b5cf6")
    self.stat_duplicate_rate.grid(row=6, column=1, sticky=tk.E, pady=2)
    
    stats_grid.columnconfigure(0, weight=1)
    stats_grid.columnconfigure(1, weight=1)
    
    # Filtros de Duplicados
    filter_frame = ttk.LabelFrame(right_frame, text=" 🔍 Filtros de Duplicados ", padding=8)
    filter_frame.pack(fill=tk.X, pady=(0, 10))
    
    self.duplicate_filters = {
        'exact': tk.BooleanVar(value=True),
        'repost': tk.BooleanVar(value=True),
        'duration': tk.BooleanVar(value=True),
        'tags': tk.BooleanVar(value=True),
        'semantic': tk.BooleanVar(value=True)
    }
    
    filter_grid = ttk.Frame(filter_frame)
    filter_grid.pack(fill=tk.X)
    
    ttk.Checkbutton(filter_grid, text="Exactos", variable=self.duplicate_filters['exact'],
                    command=self._apply_duplicate_filters).pack(side=tk.LEFT, padx=5)
    ttk.Checkbutton(filter_grid, text="Reposts", variable=self.duplicate_filters['repost'],
                    command=self._apply_duplicate_filters).pack(side=tk.LEFT, padx=5)
    ttk.Checkbutton(filter_grid, text="Duración", variable=self.duplicate_filters['duration'],
                    command=self._apply_duplicate_filters).pack(side=tk.LEFT, padx=5)
    ttk.Checkbutton(filter_grid, text="Tags", variable=self.duplicate_filters['tags'],
                    command=self._apply_duplicate_filters).pack(side=tk.LEFT, padx=5)
    ttk.Checkbutton(filter_grid, text="Semántico", variable=self.duplicate_filters['semantic'],
                    command=self._apply_duplicate_filters).pack(side=tk.LEFT, padx=5)
    
    self.duplicate_list = tk.Listbox(filter_frame, height=4, font=("Segoe UI", 9))
    self.duplicate_list.pack(fill=tk.X, pady=(5, 0))
    self.duplicate_list.bind('<<ListboxSelect>>', self._on_duplicate_select)
    
    dup_btn_frame = ttk.Frame(filter_frame)
    dup_btn_frame.pack(fill=tk.X, pady=(5, 0))
    ttk.Button(dup_btn_frame, text="📊 Ver Relaciones", 
               command=self._show_duplicate_relations).pack(side=tk.LEFT, padx=2)
    ttk.Button(dup_btn_frame, text="🔄 Actualizar", 
               command=self._apply_duplicate_filters).pack(side=tk.LEFT, padx=2)
    
    # Botones de Exportación
    export_frame = ttk.Frame(right_frame)
    export_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(export_frame, text="📊 Exportar CSV", 
               command=lambda: self.export_monitor_data('csv')).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    ttk.Button(export_frame, text="💾 Exportar JSON",
               command=lambda: self.export_monitor_data('json')).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    # Log de Actividad
    log_frame = ttk.LabelFrame(right_frame, text=" 📝 Log de Actividad ", padding=10)
    log_frame.pack(fill=tk.BOTH, expand=True)
    
    # ScrolledText para logs
    from tkinter import scrolledtext
    self.monitor_log = scrolledtext.ScrolledText(
        log_frame,
        height=15,
        font=("Consolas", 9),
        bg="#0a0e1a" if self.current_theme == "dark" else "#f8fafc",
        fg="#10b981" if self.current_theme == "dark" else "#1e293b",
        wrap=tk.WORD
    )
    self.monitor_log.pack(fill=tk.BOTH, expand=True)
    
    # Botón para limpiar log
    ttk.Button(log_frame, text="🗑️ Limpiar Log",
              command=lambda: self.monitor_log.delete(1.0, tk.END)).pack(pady=(5, 0))
    
    # Cargar datos iniciales
    self.refresh_channels_list()
    self.update_monitor_stats()
    
    # Actualizar estado cada 5 segundos
    self.update_monitor_ui()


# ========== MÉTODOS DE CALLBACK ==========

def on_monitor_new_video(self, video):
    """Callback cuando se detecta un nuevo video."""
    self.log_monitor(f"✨ Nuevo video: {video.get('title', 'Sin título')}")
    self.update_monitor_stats()
    
    # Enviar notificación usando NotificationRouter
    if hasattr(self, 'notifier') and self.notifier:
        self.notifier.notify(
            title="Nuevo Video Detectado",
            message=video.get('title', 'Sin título')[:60],
            type="info",
            action=lambda: self.root.after(0, lambda: self.notebook.select(self.tab_monitor))
        )


def on_monitor_processing_complete(self, video):
    """Callback cuando se completa el procesamiento de un video."""
    self.log_monitor(f"✅ Procesado: {video.get('title', 'Sin título')}")
    self.update_monitor_stats()
    
    # Enviar notificación usando NotificationRouter
    if hasattr(self, 'notifier') and self.notifier:
        self.notifier.notify(
            title="Video Procesado",
            message=video.get('title', 'Sin título')[:60],
            type="success"
        )


def on_monitor_error(self, error):
    """Callback cuando ocurre un error."""
    self.log_monitor(f"❌ Error: {error}", level="error")
    
    # Enviar notificación de error usando NotificationRouter
    if hasattr(self, 'notifier') and self.notifier:
        self.notifier.notify(
            title="Error en Monitor",
            message=str(error)[:80],
            type="error"
        )


def on_monitor_log(self, message, level="info"):
    """Callback para logs generales."""
    self.log_monitor(message, level)


def on_monitor_duplicate_detected(self, duplicate_info):
    """Callback cuando se detecta contenido duplicado."""
    video_title = duplicate_info.get('title', 'Sin título')
    dup_type = duplicate_info.get('duplicate_info', {}).get('type', 'unknown')
    channel = duplicate_info.get('channel', 'Unknown')
    
    self.log_monitor(f"⚠️ Duplicado en {channel}: {video_title} ({dup_type})", level="warning")
    
    # Actualizar contador de duplicados
    if hasattr(self, 'stat_duplicates'):
        current = int(self.stat_duplicates.cget("text") or "0")
        self.stat_duplicates.config(text=str(current + 1))
    
    # Mostrar notificación toast
    try:
        from app.ui.components.notifications import ToastNotification
        ToastNotification.show(
            self.root,
            f"Duplicado detectado: {video_title[:40]}...",
            type="warning",
            duration=5000
        )
    except Exception as e:
        self.logger.error(f"Error mostrando notificación de duplicado: {e}")
    
    # Agregar a la lista de duplicados filtrados
    if hasattr(self, 'duplicate_list'):
        dup_type_key = dup_type.lower().replace('_', '').replace('exactcontent', 'exact').replace('similarduration', 'duration').replace('similartags', 'tags').replace('semanticsimilar', 'semantic')
        if dup_type_key in self.duplicate_filters and self.duplicate_filters[dup_type_key].get():
            self.duplicate_list.insert(tk.END, f"[{dup_type}] {video_title[:60]}")


def _apply_duplicate_filters(self):
    """Aplica los filtros de duplicados y actualiza la lista."""
    if not hasattr(self, 'duplicate_list'):
        return
    
    self.duplicate_list.delete(0, tk.END)
    
    try:
        if hasattr(self, 'db_manager'):
            duplicates = self.db_manager.get_duplicate_relations()
            type_map = {
                'EXACT_CONTENT': 'exact', 'exact_content': 'exact',
                'REPOST': 'repost', 'repost': 'repost',
                'SIMILAR_DURATION': 'duration', 'similar_duration': 'duration',
                'SIMILAR_TAGS': 'tags', 'similar_tags': 'tags',
                'SEMANTIC_SIMILAR': 'semantic', 'semantic_similar': 'semantic'
            }
            
            for dup in duplicates:
                dup_type = dup.get('relation_type', 'unknown')
                type_key = type_map.get(dup_type, dup_type)
                if type_key in self.duplicate_filters and self.duplicate_filters[type_key].get():
                    title = dup.get('video1_title', 'Unknown')[:60]
                    self.duplicate_list.insert(tk.END, f"[{dup_type}] {title}")
    except Exception as e:
        self.logger.error(f"Error aplicando filtros de duplicados: {e}")


def _on_duplicate_select(self, event):
    """Maneja la selección de un duplicado en la lista."""
    selection = self.duplicate_list.curselection()
    if not selection:
        return
    
    item = self.duplicate_list.get(selection[0])
    self.log_monitor(f"Duplicado seleccionado: {item}", level="info")

def _show_duplicate_relations(self):
    """Muestra un panel con las relaciones de duplicados."""
    if not hasattr(self, 'db_manager'):
        self.log_monitor("DB no disponible", level="error")
        return
    
    relations = self.db_manager.get_duplicate_relations(limit=50)
    
    if not relations:
        self.log_monitor("No hay relaciones de duplicados registradas", level="info")
        return
    
    top = tk.Toplevel(self.root)
    top.title("🔗 Relaciones de Duplicados")
    top.geometry("700x400")
    
    frame = ttk.Frame(top, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("ID", "Video 1", "Tipo", "Confianza", "Fecha")
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    tree.column("Video 1", width=180)
    
    for rel in relations:
        tree.insert("", tk.END, values=(
            rel.get('id', ''),
            rel.get('video1_title', 'Unknown')[:30],
            rel.get('relation_type', ''),
            f"{rel.get('confidence', 0)*100:.0f}%",
            str(rel.get('created_at', ''))[:19]
        ))
    
    tree.pack(fill=tk.BOTH, expand=True)
    
    ttk.Button(frame, text="Cerrar", command=top.destroy).pack(pady=10)


def export_monitor_data(self, format_type='csv'):
    """Exporta los datos del monitor a CSV o JSON."""
    from tkinter import filedialog
    import json
    import csv
    
    # Obtener datos
    try:
        channels = self.monitor_service.get_all_channels()
        # Enriquecer con conteos
        data = []
        for ch in channels:
            videos = self.db_manager.get_videos_by_channel(ch['id'])
            row = dict(ch)
            row['video_count'] = len(videos)
            row['videos'] = videos
            data.append(row)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'json':
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile=f"monitor_export_{timestamp}.json",
                filetypes=[("JSON Files", "*.json")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, default=str)
                ToastNotification.show(self.root, "Exportación JSON exitosa", "success")
                
        elif format_type == 'csv':
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=f"monitor_export_{timestamp}.csv",
                filetypes=[("CSV Files", "*.csv")]
            )
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Nombre", "URL", "Estado", "Última Verificación", "Total Videos"])
                    for item in data:
                        writer.writerow([
                            item['id'],
                            item['channel_name'],
                            item['channel_url'],
                            "Activo" if item['active'] else "Inactivo",
                            item.get('last_checked', 'Nunca'),
                            item['video_count']
                        ])
                ToastNotification.show(self.root, "Exportación CSV exitosa", "success")
                
    except Exception as e:
        messagebox.showerror("Error de Exportación", f"No se pudo exportar: {e}")


# ========== MÉTODOS DE GESTIÓN ==========

def add_channel_dialog(self):
    """Muestra diálogo para añadir un nuevo canal."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Añadir Canal")
    dialog.geometry("500x200")
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Centrar diálogo
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Frame principal
    main_frame = ttk.Frame(dialog, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # URL
    ttk.Label(main_frame, text="URL del Canal:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
    url_var = tk.StringVar()
    url_entry = ttk.Entry(main_frame, textvariable=url_var, width=50)
    url_entry.pack(fill=tk.X, pady=(0, 15))
    url_entry.focus()
    
    # Nombre
    ttk.Label(main_frame, text="Nombre del Canal:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
    name_var = tk.StringVar()
    name_entry = ttk.Entry(main_frame, textvariable=name_var, width=50)
    name_entry.pack(fill=tk.X, pady=(0, 20))
    
    # Botones
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X)
    
    def add_channel():
        url = url_var.get().strip()
        name = name_var.get().strip()
        
        if not url or not name:
            messagebox.showwarning("Campos Vacíos", "Por favor completa todos los campos.")
            return
        
        try:
            channel_id = self.monitor_service.add_channel(url, name)
            if channel_id:
                self.log_monitor(f"✅ Canal añadido: {name}")
                self.refresh_channels_list()
                self.update_monitor_stats()
                dialog.destroy()
                ToastNotification.show(self.root, f"Canal '{name}' añadido exitosamente", "success")
            else:
                messagebox.showwarning("Canal Existente", "Este canal ya está en la lista.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo añadir el canal: {e}")
    
    ttk.Button(btn_frame, text="✅ Añadir", style="Success.TButton",
              command=add_channel).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="❌ Cancelar",
              command=dialog.destroy).pack(side=tk.LEFT, padx=5)


def remove_selected_channel(self):
    """Elimina el canal seleccionado."""
    selection = self.channels_tree.selection()
    if not selection:
        messagebox.showwarning("Sin Selección", "Por favor selecciona un canal para eliminar.")
        return
    
    item = self.channels_tree.item(selection[0])
    channel_id = item['values'][0]
    channel_name = item['values'][1]
    
    if messagebox.askyesno("Confirmar Eliminación", 
                          f"¿Estás seguro de eliminar el canal '{channel_name}'?\n\n"
                          "Esto también eliminará todos los videos asociados."):
        try:
            self.monitor_service.remove_channel(channel_id)
            self.log_monitor(f"🗑️ Canal eliminado: {channel_name}")
            self.refresh_channels_list()
            self.update_monitor_stats()
            ToastNotification.show(self.root, f"Canal '{channel_name}' eliminado", "success")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el canal: {e}")


def refresh_channels_list(self):
    """Refresca la lista de canales."""
    # Limpiar TreeView
    for item in self.channels_tree.get_children():
        self.channels_tree.delete(item)
    
    # Obtener canales
    channels = self.monitor_service.get_all_channels()
    
    for channel in channels:
        # Obtener número de videos
        videos = self.db_manager.get_videos_by_channel(channel['id'])
        video_count = len(videos)
        
        # Estado
        estado = "🟢 Activo" if channel['active'] else "🔴 Inactivo"
        
        # Última verificación
        last_checked = channel.get('last_checked', 'Nunca')
        if last_checked and last_checked != 'Nunca':
            try:
                dt = datetime.fromisoformat(last_checked)
                last_checked = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        self.channels_tree.insert("", tk.END, values=(
            channel['id'],
            channel['channel_name'],
            channel['channel_url'].replace("https://www.youtube.com/", "").replace("@", "@"), # Simple clean
            estado,
            last_checked,
            video_count
        ))


def show_channel_videos(self, event):
    """Muestra los videos de un canal en un diálogo."""
    selection = self.channels_tree.selection()
    if not selection:
        return
    
    item = self.channels_tree.item(selection[0])
    channel_id = item['values'][0]
    channel_name = item['values'][1]
    
    # Crear diálogo
    dialog = tk.Toplevel(self.root)
    dialog.title(f"Videos de {channel_name}")
    dialog.geometry("800x500")
    dialog.transient(self.root)
    
    # Frame principal
    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # TreeView de videos
    videos_tree = ttk.Treeview(
        main_frame,
        columns=("id", "titulo", "estado", "fecha"),
        show="headings",
        height=20
    )
    
    videos_tree.heading("id", text="ID")
    videos_tree.heading("titulo", text="Título")
    videos_tree.heading("estado", text="Estado")
    videos_tree.heading("fecha", text="Descubierto")
    
    videos_tree.column("id", width=50, anchor=tk.CENTER)
    videos_tree.column("titulo", width=450)
    videos_tree.column("estado", width=100, anchor=tk.CENTER)
    videos_tree.column("fecha", width=150, anchor=tk.CENTER)
    
    videos_tree.pack(fill=tk.BOTH, expand=True)
    
    # Cargar videos
    videos = self.db_manager.get_videos_by_channel(channel_id)
    
    for video in videos:
        estado_map = {
            'pending': '⏳ Pendiente',
            'processing': '🔄 Procesando',
            'completed': '✅ Completado',
            'failed': '❌ Fallido'
        }
        estado = estado_map.get(video.get('status', 'pending'), 'Desconocido')
        
        fecha = video.get('discovered_at', '')
        if fecha:
            try:
                dt = datetime.fromisoformat(fecha)
                fecha = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        videos_tree.insert("", tk.END, values=(
            video['id'],
            video.get('title', 'Sin título'),
            estado,
            fecha
        ))
    
    # Botón cerrar
    ttk.Button(main_frame, text="Cerrar", command=dialog.destroy).pack(pady=(10, 0))


def start_monitor(self):
    """Inicia el monitoreo automático."""
    try:
        self.monitor_service.start_monitoring()
        self.monitor_status_label.config(text="🟢 Activo", foreground="#10b981")
        self.start_monitor_btn.config(state=tk.DISABLED)
        self.stop_monitor_btn.config(state=tk.NORMAL)
        self.log_monitor("▶️ Monitor iniciado")
        ToastNotification.show(self.root, "Monitor iniciado exitosamente", "success")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar el monitor: {e}")


def stop_monitor(self):
    """Detiene el monitoreo automático."""
    try:
        self.monitor_service.stop_monitoring()
        self.monitor_status_label.config(text="⚫ Detenido", foreground="#64748b")
        self.start_monitor_btn.config(state=tk.NORMAL)
        self.stop_monitor_btn.config(state=tk.DISABLED)
        self.log_monitor("⏹️ Monitor detenido")
        ToastNotification.show(self.root, "Monitor detenido", "info")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo detener el monitor: {e}")


def check_now(self):
    """Verifica nuevos videos manualmente."""
    self.log_monitor("🔍 Verificando nuevos videos...")
    try:
        new_count = self.monitor_service.check_for_new_videos()
        self.log_monitor(f"✅ Verificación completada. {new_count} videos nuevos detectados.")
        self.refresh_channels_list()
        self.update_monitor_stats()
        ToastNotification.show(self.root, f"{new_count} videos nuevos detectados", "info")
    except Exception as e:
        self.log_monitor(f"❌ Error en verificación: {e}", "error")
        messagebox.showerror("Error", f"No se pudo verificar: {e}")


def update_monitor_stats(self):
    """Actualiza las estadísticas del monitor."""
    try:
        stats = self.monitor_service.get_statistics()
        
        self.stat_channels.config(text=str(stats.get('active_channels', 0)))
        self.stat_total_videos.config(text=str(stats.get('total_videos', 0)))
        self.stat_pending.config(text=str(stats.get('pending', 0)))
        self.stat_completed.config(text=str(stats.get('completed', 0)))
        self.stat_failed.config(text=str(stats.get('failed', 0)))
        
        # Actualizar estadísticas de duplicados
        if hasattr(self, 'stat_duplicates'):
            self.stat_duplicates.config(text=str(stats.get('total_reposts', 0)))
        if hasattr(self, 'stat_duplicate_rate'):
            rate = stats.get('duplicate_rate', 0)
            self.stat_duplicate_rate.config(text=f"{rate}%")
    except Exception as e:
        self.logger.error(f"Error actualizando estadísticas: {e}")


def update_monitor_ui(self):
    """Actualiza la UI del monitor periódicamente."""
    try:
        # Actualizar estado del monitor
        if self.monitor_service.is_monitoring():
            self.monitor_status_label.config(text="🟢 Activo", foreground="#10b981")
            self.start_monitor_btn.config(state=tk.DISABLED)
            self.stop_monitor_btn.config(state=tk.NORMAL)
        else:
            self.monitor_status_label.config(text="⚫ Detenido", foreground="#64748b")
            self.start_monitor_btn.config(state=tk.NORMAL)
            self.stop_monitor_btn.config(state=tk.DISABLED)
        
        # Actualizar estadísticas
        self.update_monitor_stats()
        
    except Exception as e:
        self.logger.error(f"Error actualizando UI del monitor: {e}")
    
    # Programar próxima actualización
    self.root.after(5000, self.update_monitor_ui)


def log_monitor(self, message, level="info"):
    """Añade un mensaje al log del monitor."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Color según nivel
    color_map = {
        "info": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444"
    }
    
    formatted_message = f"[{timestamp}] {message}\n"
    
    self.monitor_log.insert(tk.END, formatted_message)
    self.monitor_log.see(tk.END)
    
    lines = int(self.monitor_log.index('end-1c').split('.')[0])
    if lines > 1000:
        self.monitor_log.delete("1.0", f"{lines - 1000}.0")


# ========== NUEVOS MÉTODOS DE MENÚ CONTEXTUAL ==========

def show_context_menu(self, event):
    """Muestra el menú contextual en la fila seleccionada."""
    item = self.channels_tree.identify_row(event.y)
    if item:
        # Si el clic es sobre un ítem no seleccionado, limpiamos y seleccionamos ese único ítem
        if item not in self.channels_tree.selection():
            self.channels_tree.selection_set(item)
        self.context_menu.post(event.x_root, event.y_root)

def select_all_channels(self, event=None):
    """Selecciona todos los canales de la lista."""
    self.channels_tree.selection_set(self.channels_tree.get_children())
    return "break" # Previene propagación del evento

def check_selected_channel(self):
    """Fuerza verificación del canal seleccionado."""
    # Por ahora reutilizamos la verificación global, idealmente sería individual
    self.check_now()

def edit_selected_channel(self):
    """Permite editar el nombre del canal seleccionado."""
    selection = self.channels_tree.selection()
    if not selection: return
    
    item = self.channels_tree.item(selection[0])
    current_name = item['values'][1]
    channel_id = item['values'][0]
    
    new_name = tk.simpledialog.askstring("Editar Canal", "Nuevo nombre del canal:", initialvalue=current_name, parent=self.root)
    if new_name and new_name != current_name:
        try:
            self.monitor_service.update_channel(channel_id, name=new_name)
            self.refresh_channels_list()
            ToastNotification.show(self.root, "Nombre actualizado correctamente", "success")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo editar: {e}")

def copy_channel_url(self):
    """Copia la URL al portapapeles."""
    selection = self.channels_tree.selection()
    if not selection: return
    
    item = self.channels_tree.item(selection[0])
    url = item['values'][2] # Columna URL
    self.root.clipboard_clear()
    self.root.clipboard_append(url)
    ToastNotification.show(self.root, "URL copiada al portapapeles", "info")


def on_filter_toggle(self):
    """Maneja el toggle de habilitación del filtro."""
    enabled = self.filter_enabled_var.get()
    self.log_monitor(f"Filtro {'habilitado' if enabled else 'deshabilitado'}")
    
    # Deshabilitar inputs mientras el monitor corre
    is_running = self.monitor_service.is_monitoring() if hasattr(self, 'monitor_service') and self.monitor_service else False
    state = tk.DISABLED if is_running else tk.NORMAL
    
    # Si está corriendo y el filtro está habilitado, deshabilitar edición
    if is_running and enabled:
        messagebox.showwarning("Monitor Activo", "Detén el monitor para editar los filtros.")


def load_keyword_filter_config(self):
    """Carga la configuración del filtro desde la base de datos."""
    if hasattr(self, 'monitor_service') and self.monitor_service:
        try:
            config = self.monitor_service.get_keyword_filter_config()
            if config:
                self.filter_enabled_var.set(config.get('enabled', False))
                self.include_keywords_var.set(", ".join(config.get('include_keywords', [])))
                self.exclude_keywords_var.set(", ".join(config.get('exclude_keywords', [])))
                self.filter_mode_var.set(config.get('mode', 'OR'))
                update_filter_status()
        except Exception as e:
            self.log_monitor(f"Error cargando filtro: {e}", "error")


def save_keyword_filter_config(self):
    """Guarda la configuración del filtro en la base de datos."""
    include_str = self.include_keywords_var.get()
    exclude_str = self.exclude_keywords_var.get()
    
    include_keywords = [k.strip() for k in include_str.split(",") if k.strip()]
    exclude_keywords = [k.strip() for k in exclude_str.split(",") if k.strip()]
    mode = self.filter_mode_var.get()
    enabled = self.filter_enabled_var.get()
    
    if hasattr(self, 'monitor_service') and self.monitor_service:
        try:
            # Verificar si el monitor está corriendo
            if self.monitor_service.is_monitoring():
                messagebox.showwarning("Monitor Activo", "Detén el monitor antes de guardar cambios.")
                return
            
            success = self.monitor_service.set_keyword_filter(
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
                mode=mode,
                enabled=enabled
            )
            
            if success:
                self.monitor_service.reload_keyword_filter()
                ToastNotification.show(self.root, "Filtro guardado correctamente", "success")
                self.log_monitor(f"Filtro guardado: enabled={enabled}, mode={mode}, include={include_keywords}, exclude={exclude_keywords}")
            else:
                messagebox.showerror("Error", "No se pudo guardar el filtro en la base de datos.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar filtro: {e}")
    
    update_filter_status()


def test_keyword_filter(self):
    """Prueba el filtro con un título de ejemplo."""
    test_title = self.filter_test_entry.get().strip()
    if not test_title:
        test_title = "KDP Tutorial Amazon"
    
    include = [k.strip() for k in self.include_keywords_var.get().split(",") if k.strip()]
    exclude = [k.strip() for k in self.exclude_keywords_var.get().split(",") if k.strip()]
    mode = self.filter_mode_var.get()
    enabled = self.filter_enabled_var.get()
    
    # Crear filtro temporal para prueba
    from app.core.keyword_filter import KeywordFilter
    temp_filter = KeywordFilter(include, exclude, mode)
    temp_filter.enabled = enabled
    
    should_process, reason = temp_filter.should_process(test_title)
    
    if should_process:
        status_text = f"✅ PROCESARÍA: '{test_title}' ({reason})"
        status_color = "#10b981"
    else:
        status_text = f"❌ RECHAZARÍA: '{test_title}' ({reason})"
        status_color = "#ef4444"
    
    self.filter_result_label.config(text=status_text, foreground=status_color)
    self.log_monitor(f"Prueba filtro: {status_text}")


def reset_keyword_filter(self):
    """Resetea la configuración del filtro a valores predeterminados."""
    if messagebox.askyesno("Confirmar Reset", "¿Estás seguro de resetsear los filtros?"):
        self.filter_enabled_var.set(False)
        self.include_keywords_var.set("")
        self.exclude_keywords_var.set("")
        self.filter_mode_var.set("OR")
        self.filter_result_label.config(text="")
        self.log_monitor("Filtro reseteado")


def update_filter_status(self):
    """Actualiza el label de estado del filtro."""
    if hasattr(self, 'filter_result_label'):
        enabled = self.filter_enabled_var.get()
        include = self.include_keywords_var.get()
        exclude = self.exclude_keywords_var.get()
        
        if enabled:
            count_i = len([k for k in include.split(",") if k.strip()])
            count_e = len([k for k in exclude.split(",") if k.strip()])
            self.log_monitor(f"Filtro activo: {count_i} incluir, {count_e} excluir, modo {self.filter_mode_var.get()}")


# ========== MÉTODOS DE GESTIÓN DE PERFILES DE FILTROS ==========

def reload_filter_profiles(self):
    """Recarga la lista de perfiles en el combo box."""
    try:
        profiles = self.db_manager.get_all_filter_profiles()
        profile_names = []
        active_idx = 0
        
        for i, p in enumerate(profiles):
            name = p['name']
            if p.get('is_active'):
                name = f"⭐ {name}"
                active_idx = i
            profile_names.append(name)
        
        if hasattr(self, 'profile_combo'):
            self.profile_combo['values'] = profile_names
            if profile_names:
                self.profile_combo.current(active_idx)
        
        self.log_monitor(f"Perfiles recargados: {len(profiles)} perfiles")
    except Exception as e:
        self.log_monitor(f"Error recargando perfiles: {e}", "error")


def on_profile_selected(self, event=None):
    """Maneja la selección de un perfil del combo."""
    try:
        idx = self.profile_combo.current()
        if idx < 0:
            return
        
        profiles = self.db_manager.get_all_filter_profiles()
        if idx < len(profiles):
            profile = profiles[idx]
            self.load_filter_profile_to_ui(profile)
            self.log_monitor(f"Perfil cargado: {profile['name']}")
    except Exception as e:
        self.log_monitor(f"Error seleccionando perfil: {e}", "error")


def load_filter_profile_to_ui(self, profile: dict):
    """Carga los datos de un perfil en la UI."""
    try:
        # Cargar include keywords
        include_kws = profile.get('include_keywords', [])
        if isinstance(include_kws, str):
            include_kws = json.loads(include_kws) if include_kws else []
        self.include_keywords_var.set(", ".join(include_kws) if include_kws else "")
        
        # Cargar exclude keywords
        exclude_kws = profile.get('exclude_keywords', [])
        if isinstance(exclude_kws, str):
            exclude_kws = json.loads(exclude_kws) if exclude_kws else []
        self.exclude_keywords_var.set(", ".join(exclude_kws) if exclude_kws else "")
        
        # Cargar modo
        mode = profile.get('mode', 'OR')
        self.filter_mode_var.set(mode)
        
        # Cargar enabled
        enabled = bool(profile.get('enabled', 0))
        self.filter_enabled_var.set(enabled)
        
        # Actualizar indicador de perfil activo
        if hasattr(self, 'active_profile_label'):
            is_active = bool(profile.get('is_active', 0))
            if is_active:
                self.active_profile_label.config(text=f"⭐ Perfil activo: {profile['name']}", foreground="#10b981")
            else:
                self.active_profile_label.config(text=f"Perfil: {profile['name']} (inactivo)", foreground="#64748b")
        
        self.log_monitor(f"Datos del perfil '{profile['name']}' cargados en UI")
    except Exception as e:
        self.log_monitor(f"Error cargando perfil en UI: {e}", "error")


def create_new_filter_profile(self):
    """Crea un nuevo perfil de filtro."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Crear Perfil de Filtro")
    dialog.geometry("400x180")
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Centrar diálogo
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    main_frame = ttk.Frame(dialog, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="Nombre del perfil:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
    name_var = tk.StringVar()
    name_entry = ttk.Entry(main_frame, textvariable=name_var, width=40)
    name_entry.pack(fill=tk.X, pady=(0, 15))
    name_entry.focus()
    
    ttk.Label(main_frame, text="Copiar configuración del perfil actual:", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(0, 5))
    copy_from_current = tk.BooleanVar(value=True)
    ttk.Checkbutton(main_frame, text="Usar configuración actual como base", variable=copy_from_current).pack(anchor=tk.W, pady=(0, 15))
    
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X)
    
    def save():
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning("Nombre requerido", "Por favor ingresa un nombre para el perfil.")
            return
        
        try:
            if copy_from_current.get():
                include_kws = [k.strip() for k in self.include_keywords_var.get().split(",") if k.strip()]
                exclude_kws = [k.strip() for k in self.exclude_keywords_var.get().split(",") if k.strip()]
                mode = self.filter_mode_var.get()
                enabled = self.filter_enabled_var.get()
            else:
                include_kws = []
                exclude_kws = []
                mode = "OR"
                enabled = False
            
            profile_id = self.db_manager.create_filter_profile(name, include_kws, exclude_kws, mode, enabled)
            
            if profile_id:
                self.log_monitor(f"Perfil '{name}' creado exitosamente")
                self.reload_filter_profiles()
                dialog.destroy()
                ToastNotification.show(self.root, f"Perfil '{name}' creado", "success")
            else:
                messagebox.showerror("Error", "Ya existe un perfil con ese nombre.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el perfil: {e}")
    
    ttk.Button(btn_frame, text="✅ Crear", style="Success.TButton", command=save).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)


def duplicate_filter_profile(self):
    """Duplica el perfil actualmente seleccionado."""
    idx = self.profile_combo.current() if hasattr(self, 'profile_combo') else -1
    if idx < 0:
        messagebox.showwarning("Sin selección", "Selecciona un perfil para duplicar.")
        return
    
    profiles = self.db_manager.get_all_filter_profiles()
    if idx >= len(profiles):
        return
    
    source_profile = profiles[idx]
    
    dialog = tk.Toplevel(self.root)
    dialog.title("Duplicar Perfil")
    dialog.geometry("400x150")
    dialog.transient(self.root)
    dialog.grab_set()
    
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    main_frame = ttk.Frame(dialog, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text=f"Duplicando: {source_profile['name']}", font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(0, 10))
    
    ttk.Label(main_frame, text="Nombre para la copia:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
    name_var = tk.StringVar(value=f"{source_profile['name']} (copia)")
    name_entry = ttk.Entry(main_frame, textvariable=name_var, width=40)
    name_entry.pack(fill=tk.X, pady=(0, 15))
    name_entry.select_range(0, tk.END)
    name_entry.focus()
    
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X)
    
    def save():
        new_name = name_var.get().strip()
        if not new_name:
            messagebox.showwarning("Nombre requerido", "Por favor ingresa un nombre.")
            return
        
        new_id = self.db_manager.duplicate_filter_profile(source_profile['id'], new_name)
        if new_id:
            self.log_monitor(f"Perfil duplicado: '{source_profile['name']}' -> '{new_name}'")
            self.reload_filter_profiles()
            dialog.destroy()
            ToastNotification.show(self.root, f"Perfil duplicado como '{new_name}'", "success")
        else:
            messagebox.showerror("Error", "No se pudo duplicar el perfil.")
    
    ttk.Button(btn_frame, text="✅ Duplicar", style="Success.TButton", command=save).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)


def delete_filter_profile(self):
    """Elimina el perfil actualmente seleccionado."""
    idx = self.profile_combo.current() if hasattr(self, 'profile_combo') else -1
    if idx < 0:
        messagebox.showwarning("Sin selección", "Selecciona un perfil para eliminar.")
        return
    
    profiles = self.db_manager.get_all_filter_profiles()
    if idx >= len(profiles):
        return
    
    profile = profiles[idx]
    
    if profile.get('is_active'):
        messagebox.showwarning("Perfil Activo", "No puedes eliminar el perfil activo. Activa otro primero.")
        return
    
    if len(profiles) <= 1:
        messagebox.showwarning("Último Perfil", "No puedes eliminar el último perfil existente.")
        return
    
    if messagebox.askyesno("Confirmar Eliminación", f"¿Eliminar el perfil '{profile['name']}'?"):
        if self.db_manager.delete_filter_profile(profile['id']):
            self.log_monitor(f"Perfil eliminado: {profile['name']}")
            self.reload_filter_profiles()
            ToastNotification.show(self.root, f"Perfil '{profile['name']}' eliminado", "success")
        else:
            messagebox.showerror("Error", "No se pudo eliminar el perfil.")


def activate_filter_profile(self):
    """Activa el perfil seleccionado."""
    idx = self.profile_combo.current() if hasattr(self, 'profile_combo') else -1
    if idx < 0:
        messagebox.showwarning("Sin selección", "Selecciona un perfil para activar.")
        return
    
    profiles = self.db_manager.get_all_filter_profiles()
    if idx >= len(profiles):
        return
    
    profile = profiles[idx]
    
    if self.db_manager.set_active_filter_profile(profile['id']):
        # Cargar el perfil en la UI
        self.load_filter_profile_to_ui(profile)
        self.reload_filter_profiles()
        self.log_monitor(f"Perfil activado: {profile['name']}")
        ToastNotification.show(self.root, f"Perfil '{profile['name']}' activado", "success")
    else:
        messagebox.showerror("Error", "No se pudo activar el perfil.")


def save_current_as_new_profile(self):
    """Guarda la configuración actual como un nuevo perfil."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Guardar como Nuevo Perfil")
    dialog.geometry("400x150")
    dialog.transient(self.root)
    dialog.grab_set()
    
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    main_frame = ttk.Frame(dialog, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="Guardar configuración actual como:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
    name_var = tk.StringVar()
    name_entry = ttk.Entry(main_frame, textvariable=name_var, width=40)
    name_entry.pack(fill=tk.X, pady=(0, 15))
    name_entry.focus()
    
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X)
    
    def save():
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning("Nombre requerido", "Ingresa un nombre para el perfil.")
            return
        
        include_kws = [k.strip() for k in self.include_keywords_var.get().split(",") if k.strip()]
        exclude_kws = [k.strip() for k in self.exclude_keywords_var.get().split(",") if k.strip()]
        mode = self.filter_mode_var.get()
        enabled = self.filter_enabled_var.get()
        
        profile_id = self.db_manager.create_filter_profile(name, include_kws, exclude_kws, mode, enabled)
        if profile_id:
            self.log_monitor(f"Configuración guardada como perfil: {name}")
            self.reload_filter_profiles()
            dialog.destroy()
            ToastNotification.show(self.root, f"Perfil '{name}' creado", "success")
        else:
            messagebox.showerror("Error", "Ya existe un perfil con ese nombre.")
    
    ttk.Button(btn_frame, text="💾 Guardar", style="Success.TButton", command=save).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
