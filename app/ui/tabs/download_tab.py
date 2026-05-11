"""
GUI Tab for Downloads
=====================
Pestaña de descargas para gui_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, Menu
import os
import shutil
import threading
import time
import re
import json
from datetime import datetime
from pathlib import Path

# Importar componentes de UI y servicios
from app.ui.components.notifications import ToastNotification
from app.ui.components.tooltips import ToolTip
from app.services.download_service import DownloadService


def setup_download_tab(self):
    """Configura la pestaña de descargas."""
    main_container = ttk.Frame(self.tab_download)
    main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    # ===== ZONA DE DRAG & DROP =====
    drop_zone_frame = ttk.LabelFrame(main_container, text=" 📥 Zona de Descarga Rápida ", padding=20)
    drop_zone_frame.pack(fill=tk.X, pady=(0, 15))
    
    # Usar Frame en lugar de Canvas para evitar error de DND
    self.drop_frame = tk.Frame(
        drop_zone_frame,
        bg="#1e293b" if self.current_theme == "dark" else "#f8fafc",
        relief="solid",
        bd=2,
        highlightthickness=2,
        highlightbackground="#3b82f6",
        highlightcolor="#60a5fa",
        cursor="hand2"
    )
    self.drop_frame.pack(fill=tk.X, pady=(0, 15), ipady=40)
    
    # Texto dentro del frame
    label_container = tk.Frame(self.drop_frame, bg="#1e293b" if self.current_theme == "dark" else "#f8fafc")
    label_container.pack(expand=True)
    
    tk.Label(
        label_container,
        text="☁️ ARRASTRA URLs AQUÍ",
        font=("Segoe UI", 14, "bold"),
        bg="#1e293b" if self.current_theme == "dark" else "#f8fafc",
        fg="#60a5fa" if self.current_theme == "dark" else "#3b82f6"
    ).pack()
    
    tk.Label(
        label_container,
        text="o pega/escribe abajo",
        font=("Segoe UI", 10),
        bg="#1e293b" if self.current_theme == "dark" else "#f8fafc",
        fg="#94a3b8"
    ).pack()
    
    # Efectos visuales al pasar el mouse
    self.drop_frame.bind("<Enter>", lambda e: self.drop_frame.config(bg="#334155" if self.current_theme == "dark" else "#e0f2fe"))
    self.drop_frame.bind("<Leave>", lambda e: self.drop_frame.config(bg="#1e293b" if self.current_theme == "dark" else "#f8fafc"))
    
    # DND no disponible (tkinterdnd2 no está en requirements)
    # El drop funciona solo pegando en el campo de texto
    pass
    
    url_input_frame = ttk.Frame(drop_zone_frame)
    url_input_frame.pack(fill=tk.X)
    
    ttk.Label(url_input_frame, text="🔗 URL:", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(0, 10))
    
    self.url_combo = ttk.Combobox(url_input_frame, textvariable=self.url_var, 
                                 width=55, font=("Segoe UI", 11))
    self.url_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=6)
    self.update_channel_combo()
    ToolTip(self.url_combo, "Escribe una URL de Video, @Canal o selecciona uno de tus favoritos")
    
    btn_container = ttk.Frame(url_input_frame)
    btn_container.pack(side=tk.LEFT, padx=(10, 0))
    
    ttk.Button(btn_container, text="📋", command=self.paste_from_clipboard, width=4).pack(side=tk.LEFT, padx=2)
    ToolTip(btn_container.winfo_children()[-1], "Pegar desde portapapeles")
    
    ttk.Button(btn_container, text="⭐", command=self.manage_channels, width=4).pack(side=tk.LEFT, padx=2)
    ToolTip(btn_container.winfo_children()[-1], "Gestionar canales favoritos")
    
    action_frame = ttk.Frame(drop_zone_frame)
    action_frame.pack(fill=tk.X, pady=(15, 0))
    
    self.btn_direct_download = ttk.Button(action_frame, text="⚡ DESCARGA INMEDIATA", 
                                         command=self.start_download, style="Success.TButton")
    self.btn_direct_download.pack(side=tk.LEFT, padx=(0, 10), ipadx=10)
    ToolTip(self.btn_direct_download, "Descargar inmediatamente sin añadir a la cola")
    
    ttk.Button(action_frame, text="➕ Añadir a Cola", command=self.add_to_queue, style="Primary.TButton").pack(side=tk.LEFT)
    
    # ===== SECCIÓN DE COLA Y PARÁMETROS =====
    bottom_container = ttk.Frame(main_container)
    bottom_container.pack(fill=tk.BOTH, expand=True)
    
    queue_frame = ttk.LabelFrame(bottom_container, text=" 📝 Cola de Procesamiento por Lotes ", padding=15)
    queue_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    
    queue_controls = ttk.Frame(queue_frame)
    queue_controls.pack(fill=tk.X, pady=(0, 10))
    
    self.btn_start_queue = ttk.Button(queue_controls, text="▶️ INICIAR COLA", 
                                     command=self.start_queue_download, style="Primary.TButton")
    self.btn_start_queue.pack(side=tk.LEFT, padx=(0, 5))
    
    self.btn_pause_queue = ttk.Button(queue_controls, text="⏸️ Pausar", 
                                     command=self.toggle_pause_queue, state='disabled')
    self.btn_pause_queue.pack(side=tk.LEFT, padx=2)
    
    self.btn_remove_queue = ttk.Button(queue_controls, text="🗑️ Quitar", 
                                      command=self.remove_from_queue, style="Warning.TButton")
    self.btn_remove_queue.pack(side=tk.LEFT, padx=2)
    
    self.btn_clear_queue = ttk.Button(queue_controls, text="🔥 Vaciar", 
                                     command=self.clear_queue, style="Danger.TButton")
    self.btn_clear_queue.pack(side=tk.LEFT, padx=2)
    
    ttk.Separator(queue_controls, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
    
    ttk.Button(queue_controls, text="✅ Todo", width=6,
              command=lambda: self.queue_listbox.selection_set(0, tk.END)).pack(side=tk.LEFT, padx=2)
    ttk.Button(queue_controls, text="❌ Ninguno", width=8,
              command=lambda: self.queue_listbox.selection_clear(0, tk.END)).pack(side=tk.LEFT, padx=2)

    # MÓDULO: Seleccionar Solo No Procesados
    ttk.Button(queue_controls, text="📋 No Procesados", width=12,
              command=self.select_unprocessed_in_queue).pack(side=tk.LEFT, padx=2)
    ToolTip(queue_controls.winfo_children()[-1], "Seleccionar solo videos no procesados")

    # MÓDULO: Configuración de Límite y Paginación
    ttk.Button(queue_controls, text="📊 Límite", width=6,
              command=self.show_batch_limit_dialog).pack(side=tk.LEFT, padx=2)
    ToolTip(queue_controls.winfo_children()[-1], "Configurar límite de videos y paginación")

    self.queue_count_label = ttk.Label(queue_controls, text="0 items",
                                      font=("Segoe UI", 9), foreground="#94a3b8")
    self.queue_count_label.pack(side=tk.RIGHT, padx=10)
    
    list_container = ttk.Frame(queue_frame)
    list_container.pack(fill=tk.BOTH, expand=True)
    
    self.queue_listbox = tk.Listbox(list_container, height=8, 
                                   font=("Segoe UI", 10),
                                   bg="#1e293b" if self.current_theme == "dark" else "#ffffff",
                                   fg="#f1f5f9" if self.current_theme == "dark" else "#0f172a",
                                   selectbackground="#3b82f6",
                                   selectforeground="white",
                                   borderwidth=0, 
                                   highlightthickness=1,
                                   highlightbackground="#334155" if self.current_theme == "dark" else "#e2e8f0",
                                   relief="flat")
    self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    queue_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.queue_listbox.yview)
    queue_scrollbar.pack(side=tk.RIGHT, fill="y")
    self.queue_listbox.config(yscrollcommand=queue_scrollbar.set)
    
    # === MODULO: PROGRESO_LOTES (INICIO) - WIDGET DE PROGRESO ===
    self.batch_progress_frame = ttk.Frame(queue_frame)
    self.batch_progress_frame.pack(fill=tk.X, pady=(10, 0))
    
    self.batch_progress_bar = ttk.Progressbar(
        self.batch_progress_frame, 
        mode='determinate',
        length=200,
        maximum=100
    )
    self.batch_progress_bar.pack(fill=tk.X, pady=(0, 5))
    
    self.batch_status_label = ttk.Label(
        self.batch_progress_frame,
        text="Sin actividad",
        font=("Segoe UI", 9)
    )
    self.batch_status_label.pack(anchor=tk.W)
    # === MODULO: PROGRESO_LOTES (FIN) - WIDGET DE PROGRESO ===
    
    params_frame = ttk.LabelFrame(bottom_container, text=" ⚙️ Configuración de Descarga ", padding=15)
    params_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
    
    ttk.Label(params_frame, text="Opciones de Red:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
    
    self.monitor_var = tk.BooleanVar(value=False)
    cb1 = ttk.Checkbutton(params_frame, text="🔄 Modo Vigilancia (24h)", 
                         variable=self.monitor_var, command=self.toggle_monitor)
    cb1.pack(anchor=tk.W, pady=5)
    ToolTip(cb1, "Monitorear cambios en canales cada 24 horas")
    
    self.optimize_var = tk.BooleanVar(value=False)
    cb2 = ttk.Checkbutton(params_frame, text="⚡ Solo Verificar URL", 
                         variable=self.optimize_var)
    cb2.pack(anchor=tk.W, pady=5)
    ToolTip(cb2, "Si está marcado, SOLO verifica que los canales existen sin descargar subtítulos")
    
    self.secure_mode_var = tk.BooleanVar(value=False)
    cb3 = ttk.Checkbutton(params_frame, text="🛡️ No Sobrescribir Existentes", 
                         variable=self.secure_mode_var)
    cb3.pack(anchor=tk.W, pady=5)
    ToolTip(cb3, "Si un archivo .vtt ya existe, lo omite y no lo re-descarga")
    
    ttk.Separator(params_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
    
    ttk.Label(params_frame, text="Acciones Rápidas:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
    
    ttk.Button(params_frame, text="📂 Ver Descargas", 
              command=lambda: self.open_folder(self.input_dir.get())).pack(fill=tk.X, pady=5)
    
    ttk.Button(params_frame, text="🧹 Limpiar Caché", 
              command=self.clear_ytdlp_cache, style="Warning.TButton").pack(fill=tk.X, pady=5)


def on_drop_urls(self, event):
    """Procesa URLs arrastradas y soltadas en la zona de drop."""
    raw = event.data.strip()
    urls = []
    
    if raw.startswith('{') and raw.endswith('}'):
        raw = raw[1:-1]
    
    for part in raw.split():
        part = part.strip('{}').strip()
        if part and ('youtube.com' in part.lower() or 'youtu.be' in part.lower() or part.startswith('@')):
            urls.append(part)
    
    if not urls:
        if raw.startswith('@') or 'youtube' in raw.lower():
            urls = [raw]
    
    if urls:
        self.url_var.set(urls[0])
        for u in urls[1:]:
            if u not in self.download_queue:
                self.download_queue.append(u)
        self.update_queue_ui()
        self.save_config()
        ToastNotification.show(self.root, f"📥 {len(urls)} URL(s) recibida(s)", "success")
    else:
        ToastNotification.show(self.root, "⚠️ No se detectaron URLs de YouTube", "warning")


def update_channel_combo(self):
    """Actualiza la lista desplegable con los canales guardados."""
    if hasattr(self, 'db_manager') and self.db_manager:
        channels = self.db_manager.get_all_channels(active_only=False)
        names = [c.get('channel_name') or c.get('channel_url', '') for c in channels]
    else:
        names = [c.get('name') or c.get('url', '') for c in getattr(self, 'channels', [])]
    if hasattr(self, 'url_combo'):
        self.url_combo['values'] = names


def add_to_queue(self):
    """Añade URL a la cola con validación inteligente del Pre-Ing Gateway."""
    url = self.url_var.get().strip()
    if not url or url == "Sin canales guardados" or url.startswith(" ✨"):
        return
    
    from app.core.utils import normalize_youtube_url
    norm_url = normalize_youtube_url(url)
    queue_normalized = [normalize_youtube_url(q) for q in self.download_queue]
    
    if norm_url in queue_normalized:
        messagebox.showwarning("Advertencia", "URL ya existente en la cola.")
        return
    
    gateway_result = None
    use_smart_gateway = getattr(self, 'enable_smart_gateway', False)
    
    if use_smart_gateway:
        try:
            from app.pre_ingesta.gateway import get_gateway, IngestaResult
            gateway = get_gateway()
            gateway_result = gateway.process(url, source="gui", use_ai=True)
            
            if not gateway_result.success:
                if gateway_result.item and gateway_result.item.state.value == "duplicado":
                    messagebox.showwarning("Duplicado", gateway_result.message)
                    return
                elif gateway_result.item and gateway_result.item.state.value == "bloqueado":
                    messagebox.showwarning("Bloqueado", f"Contenido no aprobado: {gateway_result.message}")
                    return
                else:
                    messagebox.showwarning("Validación", gateway_result.message)
        except Exception as e:
            self.log(f"[WARN] Gateway no disponible: {e}", "warning")
    
    self.download_queue.append(url)
    self.update_queue_ui()
    self.save_config()
    self.url_var.set("")
    self.log(f"[+] Añadido a la cola: {url}")
    
    if gateway_result and gateway_result.item:
        score_info = f" | Relevancia: {gateway_result.item.relevance_score:.1f}/10"
        category_info = f" | Categoría: {gateway_result.item.category or 'N/A'}"
        self.log(f"[AI] Score: {score_info}{category_info}")


def remove_from_queue(self):
    selection = self.queue_listbox.curselection()
    if selection:
        idx = selection[0]
        val = self.queue_listbox.get(idx)
        if " ✨" in val: return
        url = self.download_queue.pop(idx)
        self.update_queue_ui()
        self.save_config()
        self.log(f"[-] Eliminado de la cola: {url}")


def clear_queue(self):
    if not self.download_queue: return
    if messagebox.askyesno("Confirmar", "¿Vaciar toda la cola de descargas?"):
        self.download_queue = []
        self.update_queue_ui()
        self.save_config()
        self.log("[!] Cola vaciada.")


def update_queue_ui(self):
    """Actualiza la lista visual de la cola de descargas de forma segura."""
    def update():
        self.queue_listbox.delete(0, tk.END)
        if not self.download_queue:
            self.queue_listbox.insert(tk.END, " ✨ La cola está vacía. ¡Añade algo arriba!")
            if hasattr(self, 'queue_count_label'):
                self.queue_count_label.config(text="0 items")
        else:
            for i, url in enumerate(self.download_queue, 1):
                self.queue_listbox.insert(tk.END, f" {i}. {url}")
            if hasattr(self, 'queue_count_label'):
                count = len(self.download_queue)
                self.queue_count_label.config(text=f"{count} item{'s' if count != 1 else ''}")
    self.root.after(0, update)


def start_download(self):
    raw_input = self.url_var.get().strip()
    
    if raw_input.startswith("@"):
        url = f"https://www.youtube.com/{raw_input}"
    else:
        url = raw_input

    if not url or not hasattr(self, 'validate_url_regex') or not self.validate_url_regex(url):
        messagebox.showwarning("Error", "Por favor ingresa una URL válida de YouTube (Video, Playlist o @Canal).")
        return
        
    try:
        _, _, free = shutil.disk_usage(self.input_dir.get())
        if free < 200 * 1024 * 1024:
            messagebox.showerror("Error de Espacio", "Espacio en disco insuficiente (<200MB).")
            return
    except:
        pass

    self.status_var.set("Descargando...")
    self.progress_var.set(10)
    
    self.save_session_state(url, "downloading")

    def log_to_gui(message, level='info'):
        if level == 'error': self.logger.error(message)
        else: self.logger.info(message)

    def update_progress(value):
        self.root.after(0, lambda: self.progress_var.set(value))

    download_service = DownloadService(
        input_dir=self.input_dir.get(),
        optimize=self.optimize_var.get(),
        secure_mode=self.secure_mode_var.get(),
        ffmpeg_location=os.path.join(self.base_dir, 'bin'),
        progress_callback=update_progress,
        log_callback=log_to_gui
    )

    def run_dl():
        success, msg = download_service.perform_download(url)
        self.root.after(0, lambda: self.clear_session_state())
        self.root.after(0, lambda: self.status_var.set("Listo"))
        self.root.after(0, lambda: self.progress_var.set(0))
        
        if success:
            self.root.after(0, self.refresh_file_list)
            if self.monitor_var.get():
                if hasattr(self, '_monitor_timer_id'):
                    self.root.after_cancel(self._monitor_timer_id)
                self._monitor_timer_id = self.root.after(86400000, self.start_download)
            else:
                self.root.after(0, lambda: messagebox.showinfo("Éxito", "Descarga completada."))
        else:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Hubo un error en la descarga:\n{msg}"))

    threading.Thread(target=run_dl, daemon=True).start()


def toggle_pause_queue(self):
    if not self.queue_running: return
    self.queue_paused = not self.queue_paused
    if self.queue_paused:
        self.btn_pause_queue.config(text="▶️ Reanudar")
        self.status_var.set("Cola PAUSADA (esperando fin de descarga actual...)")
    else:
        self.btn_pause_queue.config(text="⏸️ Pausar")
        self.status_var.set("Reanudando cola...")


def start_queue_download(self):
    if not self.download_queue:
        messagebox.showinfo("Cola vacía", "La cola está vacía.")
        return
    
    if self.queue_running: return

    urls = list(self.download_queue)
    for i, u in enumerate(urls):
        if u.startswith("@"):
            urls[i] = f"https://www.youtube.com/{u}"

    self.queue_running = True
    self.queue_paused = False
    self.status_var.set("Procesando cola inteligente...")
    
    self.btn_start_queue.config(state='disabled')
    self.btn_pause_queue.config(state='normal', text="⏸️ Pausar")
    self.btn_remove_queue.config(state='disabled')
    self.btn_clear_queue.config(state='disabled')
    
    def log_to_gui(message, level='info'):
        if level == 'error': self.logger.error(message)
        else: self.logger.info(message)

    def update_progress(value):
        self.root.after(0, lambda: self.progress_var.set(value))

    # === MODULO: PROGRESO_LOTES (INICIO) - CALLBACK ===
    def on_batch_progress(stats):
        """Callback para actualizar progreso del lote en la UI."""
        current = stats.get("current", 0)
        total = stats.get("total", 1)
        new_count = stats.get("new", 0)
        existing = stats.get("existing", 0)
        no_subs = stats.get("no_subs", 0)
        errors = stats.get("errors", 0)
        status = stats.get("status", "")
        detail = stats.get("detail", "")
        
        pct = (current / total * 100) if total > 0 else 0
        
        status_text = f"Videos: {current}/{total} | Nuevos: {new_count} | Existentes: {existing}"
        if status == "discovering":
            status_text = f"🔍 {detail}"
        elif status == "downloading":
            status_text = f"⏳ {detail} - {status_text}"
        elif status == "completed":
            status_text = f"✅ Completado: {new_count} nuevos, {existing} existentes, {no_subs} sin subs, {errors} errores"
        
        def update_ui():
            self.batch_progress_bar['value'] = pct
            self.batch_status_label.config(text=status_text)
        
        self.root.after(0, update_ui)
    # === MODULO: PROGRESO_LOTES (FIN) - CALLBACK ===
    
    download_service = DownloadService(
        input_dir=self.input_dir.get(),
        optimize=self.optimize_var.get(),
        secure_mode=self.secure_mode_var.get(),
        ffmpeg_location=os.path.join(self.base_dir, 'bin'),
        progress_callback=update_progress,
        log_callback=log_to_gui,
        batch_progress_callback=on_batch_progress
    )

    # === MODULO: PROGRESO_LOTES (INICIO) - RUN_QUEUE ===
    def run_queue():
        total = len(urls)
        success_count = 0
        failed_urls = []
        
        for i, url in enumerate(urls):
            while self.queue_paused and self.queue_running:
                time.sleep(0.5)
            
            if not self.queue_running:
                failed_urls.extend(urls[i:])
                break
            
            self.root.after(0, lambda idx=i: self.status_var.set(f"Descargando {idx+1}/{total}..."))
            self.root.after(0, lambda idx=i: self.queue_listbox.selection_clear(0, tk.END))
            self.root.after(0, lambda idx=i: self.queue_listbox.selection_set(idx))
            self.root.after(0, lambda idx=i: self.queue_listbox.see(idx))
            
            if download_service.perform_download(url)[0]:
                success_count += 1
            else:
                failed_urls.append(url)
        
        def finish():
            self.status_var.set("Cola finalizada")
            self.progress_var.set(0)
            self.batch_progress_bar['value'] = 0
            self.batch_status_label.config(text="Cola finalizada")
            self.queue_running = False
            self.download_queue = list(failed_urls)
            self.update_queue_ui()
            self.save_config()
            self.btn_start_queue.config(state='normal')
            self.btn_pause_queue.config(state='disabled', text="⏸️ Pausar")
            self.btn_remove_queue.config(state='normal')
            self.btn_clear_queue.config(state='normal')
            messagebox.showinfo("Cola Finalizada", f"Se procesaron {total} enlaces.\nExitosos: {success_count}\nFallidos: {len(failed_urls)}")
        
        self.root.after(0, finish)

    threading.Thread(target=run_queue, daemon=True).start()
    # === MODULO: PROGRESO_LOTES (FIN) - RUN_QUEUE ===


def paste_from_clipboard(self):
    """Pega el contenido del portapapeles en el campo de URL."""
    try:
        content = self.root.clipboard_get()
        if content and isinstance(content, str):
            self.url_var.set(content.strip())
            ToastNotification.show(self.root, "📋 URL pegada con éxito", "success")
    except Exception:
        pass


def manage_channels(self):
    """Ventana para gestionar canales guardados."""
    win = tk.Toplevel(self.root)
    win.title("Gestor de Canales Pro")
    win.geometry("800x600")
    
    toolbar = ttk.Frame(win, padding=5)
    toolbar.pack(fill=tk.X)
    
    search_var = tk.StringVar()
    ttk.Entry(toolbar, textvariable=search_var).pack(side=tk.LEFT, padx=5)
    
    if hasattr(self, 'db_manager') and self.db_manager:
        channels = self.db_manager.get_all_channels(active_only=False)
        categories = sorted(list(set(c.get("category", "General") for c in channels)))
    else:
        categories = sorted(list(set(c.get("category", "General") for c in getattr(self, 'channels', []))))
    
    cat_filter_var = tk.StringVar(value="Todas")
    cat_combo = ttk.Combobox(toolbar, textvariable=cat_filter_var, values=["Todas"] + categories, state="readonly", width=15)
    cat_combo.pack(side=tk.LEFT, padx=5)

    list_frame = ttk.Frame(win, padding=5)
    list_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("name", "url", "category", "active", "last_checked")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
    for col in columns: tree.heading(col, text=col.replace("_", " ").title())
    tree.column("name", width=200)
    tree.column("url", width=250)
    tree.column("category", width=100)
    tree.column("active", width=80)
    tree.column("last_checked", width=120)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def refresh_list():
        tree.delete(*tree.get_children())
        if hasattr(self, 'db_manager') and self.db_manager:
            channels = self.db_manager.get_all_channels(active_only=False)
        else:
            channels = getattr(self, 'channels', [])
        
        for c in channels:
            name = c.get('channel_name') or c.get('name', '')
            url = c.get('channel_url') or c.get('url', '')
            active = c.get('active', True)
            if search_var.get().lower() in name.lower() or search_var.get().lower() in url.lower():
                if cat_filter_var.get() == "Todas" or c.get("category", "General") == cat_filter_var.get():
                    tree.insert("", tk.END, values=(name, url, c.get("category", "General"), "✅" if active else "❌", c.get("last_checked", "-")))

    search_var.trace("w", lambda *args: refresh_list())
    cat_combo.bind("<<ComboboxSelected>>", lambda e: refresh_list())
    refresh_list()
    
    btn_frame = ttk.Frame(win, padding=10)
    btn_frame.pack(fill=tk.X)
    
    ttk.Button(btn_frame, text="Cerrar", command=win.destroy).pack(side=tk.RIGHT)


# ==================== MÓDULOS DESCARGA MASIVA ====================

def select_unprocessed_in_queue(self):
    """Selecciona solo los items no procesados en la cola."""
    if not hasattr(self, 'queue_listbox'):
        return

    # Limpiar selección actual
    self.queue_listbox.selection_clear(0, tk.END)

    # Obtener estado de cada item en la cola
    # Los items no procesados son los que no tienen marca de check
    unprocessed = []
    for i in range(self.queue_listbox.size()):
        item = self.queue_listbox.get(i)
        # Verificar si ya fue procesado (heurística: buscar marca)
        # Esto es un placeholder - la lógica real dependería de cómo se marquen los items
        if "✅" not in str(item) and "❌" not in str(item):
            unprocessed.append(i)

    # Seleccionar items no procesados
    for idx in unprocessed:
        self.queue_listbox.selection_set(idx)

    if unprocessed:
        ToastNotification.show(self.root, f"{len(unprocessed)} items no procesados seleccionados", "info")
    else:
        ToastNotification.show(self.root, "Todos los items parecen estar procesados", "info")


def show_batch_limit_dialog(self):
    """Muestra diálogo para configurar límite de videos y paginación."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Configurar Límite de Descarga Masiva")
    dialog.geometry("450x350")
    dialog.transient(self.root)
    dialog.grab_set()

    # Centrar diálogo
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")

    main_frame = ttk.Frame(dialog, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Título
    ttk.Label(main_frame, text="Configuración de Descarga Masiva",
              font=("Segoe UI", 12, "bold")).pack(pady=(0, 15))

    # === Límite de Videos ===
    limit_frame = ttk.LabelFrame(main_frame, text=" 📊 Límite de Videos ", padding=10)
    limit_frame.pack(fill=tk.X, pady=(0, 10))

    limit_var = tk.IntVar(value=50)
    ttk.Label(limit_frame, text="Videos máximo por canal:").pack(anchor=tk.W)
    ttk.Spinbox(limit_frame, from_=0, to=500, textvariable=limit_var, width=10,
                increment=10).pack(anchor=tk.W, pady=5)
    ttk.Label(limit_frame, text="0 = sin límite (usa con precaución)", 
             font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W)

    # === Paginación ===
    page_frame = ttk.LabelFrame(main_frame, text=" 📄 Paginación ", padding=10)
    page_frame.pack(fill=tk.X, pady=(0, 10))

    offset_var = tk.IntVar(value=0)
    ttk.Label(page_frame, text="Saltar primeros videos (offset):").pack(anchor=tk.W)
    ttk.Spinbox(page_frame, from_=0, to=1000, textvariable=offset_var, width=10,
                increment=50).pack(anchor=tk.W, pady=5)
    ttk.Label(page_frame, text="Ej: 0 = desde inicio, 50 = omitir 50 primeros", 
             font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W)

    # === Filtro de Duración ===
    dur_frame = ttk.LabelFrame(main_frame, text=" ⏱️ Filtro de Duración ", padding=10)
    dur_frame.pack(fill=tk.X, pady=(0, 10))

    min_var = tk.StringVar(value="0")
    max_var = tk.StringVar(value="0")

    min_frame = ttk.Frame(dur_frame)
    min_frame.pack(fill=tk.X, pady=2)
    ttk.Label(min_frame, text="Min (minutos):").pack(side=tk.LEFT)
    ttk.Entry(min_frame, textvariable=min_var, width=8).pack(side=tk.LEFT, padx=5)

    max_frame = ttk.Frame(dur_frame)
    max_frame.pack(fill=tk.X, pady=2)
    ttk.Label(max_frame, text="Max (minutos):").pack(side=tk.LEFT)
    ttk.Entry(max_frame, textvariable=max_var, width=8).pack(side=tk.LEFT, padx=5)

    ttk.Label(dur_frame, text="0 = sin límite | Filtra Shorts (<1min) y Videos Largos", 
             font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W)

    # === Botones ===
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))

    def apply_config():
        limit = limit_var.get()
        offset = offset_var.get()
        try:
            min_min = int(min_var.get()) * 60 if min_var.get() else 0
            max_min = int(max_var.get()) * 60 if max_var.get() else 0
        except ValueError:
            min_min = 0
            max_min = 0

        # Guardar configuración
        self._batch_limit = limit
        self._batch_offset = offset
        self._batch_min_duration = min_min
        self._batch_max_duration = max_min

        # Resetear DownloadService para que use la nueva config
        if hasattr(self, '_download_service') and self._download_service:
            self._download_service = None

        msg = f"Limite: {limit or 'sin limite'}, Offset: {offset}, Duracion: {min_var.get()}-{max_var.get()} min"
        ToastNotification.show(self.root, f"Config aplicada: {msg}", "success")
        dialog.destroy()

    ttk.Button(btn_frame, text="✅ Aplicar", style="Success.TButton",
               command=apply_config).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="❌ Cancelar",
              command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="🔄 Resetear",
               command=lambda: [limit_var.set(50), offset_var.set(0), 
                               min_var.set("0"), max_var.set("0")]).pack(side=tk.LEFT, padx=5)
