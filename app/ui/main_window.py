"""
KDP Master Suite - Main Window Orchestrator
===========================================
Módulo central de la interfaz de usuario que coordina todas las pestañas y servicios.
"""

import tkinter as tk
from tkinter import ttk, messagebox, Menu, scrolledtext, filedialog
import os
import sys
import json
import logging
import threading
import shutil
import subprocess
from datetime import datetime
import os
import sys
from pathlib import Path
import urllib.request
import re

# --- Importaciones de Core ---
from app.core.config import Config
from app.core.security import SecurityManager
from app.core.logger import setup_app_logging
from app.core.ui_framework import (
    ThemeManager, AnimationEngine, ResponsiveManager, 
    BindingManager, ui_context
)
from app.core.plugin_manager import PluginManager

# --- Importaciones de Servicios ---
from app.database.db_manager import DatabaseManager
from app.database.knowledge_db import KnowledgeDBManager
from app.services.download_service import DownloadService
from app.services.processing_service import ProcessingService
from app.services.monitor_service import ChannelMonitorService
from app.services.knowledge_integrator import KnowledgeIntegrator

# --- Importaciones de Componentes UI ---
from app.ui.components.notifications import ToastNotification
from app.ui.components.tooltips import ToolTip

# --- Importaciones de Pestañas (Modularización Mixin) ---
import app.ui.tabs.download_tab as download_tab
import app.ui.tabs.process_tab as process_tab
import app.ui.tabs.analyze_tab as analyze_tab
import app.ui.tabs.search_tab as search_tab
import app.ui.tabs.monitor_tab as monitor_tab
import app.ui.tabs.dashboard_tab as dashboard_tab

class TranscriptionProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KDP Master Suite v2.5 SOMD Edition")
        
        # Configuración de base y rutas
        self.base_dir = Path(__file__).parent.parent.parent
        self.lock_file = self.base_dir / ".app.lock"
        self.config_file = self.base_dir / "settings.json"
        
        # Inicializar Logging
        self.logger, self.audit_logger = setup_app_logging(self.base_dir)
        
        # Variables de estado y opciones
        self.queue_running = False
        self.queue_paused = False
        self.current_theme = "dark"
        self.blacklist = []
        self.channels = []
        self.files_to_process = []
        self.download_queue = []
        
        # Variables de UI vinculadas
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Sistema listo")
        self.disk_status_var = tk.StringVar(value="Calculando espacio...")
        self.progress_var = tk.DoubleVar(value=0)
        
        # Inicializar Managers de Core
        self.security = SecurityManager(key_file=self.base_dir / ".master.key")
        self.theme_manager = ThemeManager(self.root)
        self.anim_engine = AnimationEngine()
        self.responsive_manager = ResponsiveManager(self.root)
        self.binding_manager = BindingManager(self.root)
        self.plugin_manager = PluginManager(self.root)
        
        # Inicializar Servicios
        self.db_manager = DatabaseManager(db_path=self.base_dir / "data" / "channel_monitor.db")
        self.monitor_service = ChannelMonitorService(db_manager=self.db_manager)
        
        # Registrar UI Context
        ui_context["theme"] = self.theme_manager
        ui_context["anim"] = self.anim_engine
        ui_context["responsive"] = self.responsive_manager
        ui_context["bindings"] = self.binding_manager
        ui_context["plugins"] = self.plugin_manager
        
        # Cargar Configuración
        self.load_config()
        
        # Integrador de conocimiento (depende de blacklist cargada)
        self.knowledge_db = KnowledgeDBManager()
        self.integrator = KnowledgeIntegrator(self.blacklist, db_manager=self.knowledge_db)
        self.integrator.ai_provider = getattr(self, 'ai_provider', 'none')
        self.integrator.api_key = getattr(self, 'api_key', '')
        self.integrator.system_prompt = getattr(self, 'ai_system_prompt', '')
        
        self.html_gen = None # Placeholder para el generador HTML si existe
        
        # Construcción de la Interfaz
        self.create_ui()
        
        # Inicialización de datos
        self.refresh_file_list()
        self.update_disk_space_status()
        
        # Guardar configuración al salir
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Carga de Plugins
        self.plugin_manager.load_plugins(self)

    def load_config(self):
        """Carga la configuración desde el archivo settings.json."""
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = self.base_dir
        
        defaults = {
            "input_dir": str(base_dir / "data" / "transcriptions"),
            "output_dir": str(base_dir / "outputs" / "transcriptions_processed"),
            "blacklist": [],
            "channels": [],
            "ai_provider": "none",
            "ai_api_key": "",
            "ai_system_prompt": "Clasifica el texto..."
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    defaults.update(data)
            except: pass
            
        self.input_dir = tk.StringVar(value=defaults["input_dir"])
        self.output_dir = tk.StringVar(value=defaults["output_dir"])
        self.blacklist = defaults["blacklist"]
        self.channels = defaults["channels"]
        self.ai_provider = defaults["ai_provider"]
        
        # Desencriptar API Key
        raw_key = defaults["ai_api_key"]
        if raw_key and self.security:
            try: self.api_key = self.security.decrypt(raw_key)
            except: self.api_key = raw_key
        else: self.api_key = raw_key
        
        self.ai_system_prompt = defaults["ai_system_prompt"]

    def save_config(self):
        """Guarda la configuración actual."""
        encrypted_key = self.api_key
        if self.api_key and self.security:
            encrypted_key = self.security.encrypt(self.api_key)
            
        config = {
            "input_dir": self.input_dir.get(),
            "output_dir": self.output_dir.get(),
            "blacklist": self.blacklist,
            "channels": self.channels,
            "ai_provider": self.ai_provider,
            "ai_api_key": encrypted_key,
            "ai_system_prompt": self.ai_system_prompt
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def create_ui(self):
        """Crea la estructura modular de la interfaz."""
        # 1. Menú
        self.setup_menu()
        
        # 2. Main Container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # 3. Notebook (Tabs)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear Frames para Pestañas
        self.tab_download = ttk.Frame(self.notebook)
        self.tab_process = ttk.Frame(self.notebook)
        self.tab_analyze = ttk.Frame(self.notebook)
        self.tab_search = ttk.Frame(self.notebook)
        self.tab_monitor = ttk.Frame(self.notebook)
        self.tab_dashboard = ttk.Frame(self.notebook)
        
        # Añadir al Notebook
        self.notebook.add(self.tab_download, text=" 📥 Descargas ")
        self.notebook.add(self.tab_process, text=" ⚙️ Procesamiento ")
        self.notebook.add(self.tab_analyze, text=" 🧠 Inteligencia ")
        self.notebook.add(self.tab_search, text=" 🔍 Búsqueda ")
        self.notebook.add(self.tab_monitor, text=" 📺 Monitor ")
        self.notebook.add(self.tab_dashboard, text=" 📊 Dashboard ")
        
        # 4. Inicializar Pestañas desde módulos
        download_tab.setup_download_tab(self)
        process_tab.setup_process_tab(self)
        analyze_tab.setup_analyze_tab(self)
        search_tab.setup_search_tab(self)
        monitor_tab.setup_monitor_tab(self)
        dashboard_tab.setup_dashboard_tab(self)
        
        # 5. Status Bar
        self.setup_status_bar()

    def setup_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="🚪 Salir", command=self.on_closing)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        
        maint_menu = Menu(menubar, tearoff=0)
        maint_menu.add_command(label="🧹 Limpiar Caché yt-dlp", command=self.clear_ytdlp_cache)
        menubar.add_cascade(label="Mantenimiento", menu=maint_menu)

    def setup_status_bar(self):
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Label(status_bar, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)
        ttk.Label(status_bar, textvariable=self.disk_status_var).pack(side=tk.RIGHT, padx=10)
        
        self.progress_bar = ttk.Progressbar(status_bar, variable=self.progress_var, maximum=100, length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=20, pady=2)

    # --- Delegación de métodos de pestañas (Monkey Patching o Mixins) ---
    # Esto permite que los callbacks definidos en los módulos de pestañas funcionen
    
    # Download Tab Methods
    def start_download(self): download_tab.start_download(self)
    def add_to_queue(self): download_tab.add_to_queue(self)
    def start_queue_download(self): download_tab.start_queue_download(self)
    def update_queue_ui(self): download_tab.update_queue_ui(self)
    def toggle_pause_queue(self): download_tab.toggle_pause_queue(self)
    def remove_from_queue(self): download_tab.remove_from_queue(self)
    def clear_queue(self): download_tab.clear_queue(self)
    def update_channel_combo(self): download_tab.update_channel_combo(self)
    def paste_from_clipboard(self): download_tab.paste_from_clipboard(self)
    def manage_channels(self): download_tab.manage_channels(self)
    def toggle_monitor(self): pass

    # Processing Tab Methods
    def refresh_file_list(self): process_tab.refresh_file_list(self)
    def start_processing(self): process_tab.start_processing(self)
    def display_metadata(self, e): process_tab.display_metadata(self, e)
    def browse_input(self): process_tab.browse_input(self)
    def browse_output(self): process_tab.browse_output(self)
    def select_all_files(self): 
        for item in self.tree.get_children(): self.tree.selection_add(item)
    def delete_selected_file(self): process_tab.delete_selected_file(self)
    def open_file_location(self): process_tab.open_file_location(self)

    # Analyze Tab Methods
    def run_analysis(self): analyze_tab.run_analysis(self)
    def generate_html(self): analyze_tab.generate_html(self)

    # Search Tab Methods
    def run_search(self): search_tab.run_search(self)

    # Monitor Tab Methods
    def start_monitor(self): monitor_tab.start_monitor(self)
    def stop_monitor(self): monitor_tab.stop_monitor(self)
    def check_now(self): monitor_tab.check_now(self)
    def update_monitor_stats(self): monitor_tab.update_monitor_stats(self)
    def update_monitor_ui(self): monitor_tab.update_monitor_ui(self)
    def log_monitor(self, msg, level='info'): monitor_tab.log_monitor(self, msg, level)
    def refresh_channels_list(self): monitor_tab.refresh_channels_list(self)
    def on_monitor_new_video(self, v): monitor_tab.on_monitor_new_video(self, v)
    def on_monitor_processing_complete(self, v): monitor_tab.on_monitor_processing_complete(self, v)
    def on_monitor_error(self, e): monitor_tab.on_monitor_error(self, e)
    def on_monitor_log(self, m, l='info'): monitor_tab.on_monitor_log(self, m, l)
    def add_channel_dialog(self): monitor_tab.add_channel_dialog(self)
    def remove_selected_channel(self): monitor_tab.remove_selected_channel(self)
    def show_channel_videos(self, e): monitor_tab.show_channel_videos(self, e)
    def export_monitor_data(self, f): monitor_tab.export_monitor_data(self, f)
    def show_context_menu(self, e): monitor_tab.show_context_menu(self, e)
    def select_all_channels(self, e=None): monitor_tab.select_all_channels(self, e)
    def check_selected_channel(self): monitor_tab.check_selected_channel(self)
    def edit_selected_channel(self): monitor_tab.edit_selected_channel(self)
    def copy_channel_url(self): monitor_tab.copy_channel_url(self)
    def load_keyword_filter_config(self): monitor_tab.load_keyword_filter_config(self)
    def save_keyword_filter_config(self): monitor_tab.save_keyword_filter_config(self)
    def test_keyword_filter(self): monitor_tab.test_keyword_filter(self)
    def reset_keyword_filter(self): monitor_tab.reset_keyword_filter(self)
    def on_filter_toggle(self): monitor_tab.on_filter_toggle(self)
    
    # Common Helper Methods
    def open_folder(self, path):
        abs_path = os.path.abspath(os.path.join(self.base_dir, path))
        if os.path.exists(abs_path):
            if sys.platform == 'win32': os.startfile(abs_path)
            else: subprocess.Popen(['xdg-open', abs_path])
        else: messagebox.showerror("Error", f"Carpeta no existe: {abs_path}")

    def clear_ytdlp_cache(self):
        try:
            subprocess.run(["yt-dlp", "--rm-cache-dir"], check=True)
            messagebox.showinfo("Caché Limpia", "La caché de yt-dlp ha sido eliminada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo limpiar la caché: {e}")

    def update_disk_space_status(self):
        try:
            path = self.input_dir.get()
            _, _, free = shutil.disk_usage(path if os.path.exists(path) else self.base_dir)
            free_gb = free / (1024**3)
            self.disk_status_var.set(f"💾 Disco: {free_gb:.1f} GB Libres")
            if free_gb < 1.0: self.status_var.set("⚠️ ADVERTENCIA: Poco espacio")
        except: pass
        self.root.after(5000, self.update_disk_space_status)

    def on_closing(self):
        if self.queue_running:
            if not messagebox.askyesno("Saliendo", "Descarga en curso. ¿Seguro que desea salir?"): return
        self.backup_data()
        self.save_config()
        self.root.destroy()

    def backup_data(self):
        src = self.base_dir / "knowledge"
        if not src.exists(): return
        dest = self.base_dir / "backups"
        dest.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        try: shutil.make_archive(str(dest / f"backup_{ts}"), 'zip', str(src))
        except: pass

    def on_compact_mode_change(self, is_compact):
        # Lógica para ajustar UI en pantallas pequeñas
        pass

    def validate_directories(self):
        """Asegura que los directorios necesarios existan."""
        for d in [self.input_dir.get(), self.output_dir.get()]:
            if not os.path.exists(d):
                try: os.makedirs(d)
                except: pass

    def save_session_state(self, url, status): pass # Implement later
    def clear_session_state(self): pass # Implement later
    def validate_url_regex(self, url):
        return re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$', url) is not None
