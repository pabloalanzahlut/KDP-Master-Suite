import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, Menu
import tkinter.font as tkfont
import time
from logging.handlers import RotatingFileHandler
import csv
import shutil
import zipfile
import json
import sqlite3
import os
import sys
import subprocess
import logging
import threading
import re
import urllib.request
import urllib.error
import atexit
import time
from pathlib import Path
from datetime import datetime

# --- Importación de Servicios de Lógica de Negocio ---
try:
    from app.services.download_service import DownloadService
    from app.services.processing_service import ProcessingService
except ImportError:
    try:
        from services import DownloadService, ProcessingService
    except ImportError:
        DownloadService, ProcessingService = None, None

# Importar Servicios Pro
try:
    from app.database.db_manager import DatabaseManager
    from app.database.knowledge_db import KnowledgeDBManager
    from app.services.monitor_service import ChannelMonitorService
    from app.services.processed_videos_tracker import ProcessedVideosTracker
    from app.services.manual_content_merger import ManualContentMerger
except ImportError as e:
    print(f"Error importando servicios pro: {e}")
    try:
        from db_manager import DatabaseManager
        from knowledge_db import KnowledgeDBManager
        from monitor_service import ChannelMonitorService
        from processed_videos_tracker import ProcessedVideosTracker
        from manual_content_merger import ManualContentMerger
    except ImportError:
        DatabaseManager, ChannelMonitorService = None, None, None, None
        KnowledgeDBManager = None
        ProcessedVideosTracker, ManualContentMerger = None, None

# Intentar importar el chequeo de salud
try:
    from modules import check_kb_health
except ImportError:
    try:
        import check_kb_health
    except ImportError:
        check_kb_health = None

# Intentar importar el generador de grafos
try:
    from modules import generate_role_graph
except ImportError:
    try:
        import generate_role_graph
    except ImportError:
        generate_role_graph = None

# Intentar importar el módulo de conocimiento
try:
    from modules.integrate_knowledge import KnowledgeIntegrator
except ImportError:
    try:
        from integrate_knowledge import KnowledgeIntegrator
    except ImportError:
        KnowledgeIntegrator = None

# Intentar importar el conversor PDF (requiere WeasyPrint/GTK)
try:
    from convert_to_pdf import convert_md_to_pdf
except ImportError:
    try:
        from modules.convert_to_pdf import convert_md_to_pdf
    except ImportError:
        convert_md_to_pdf = None

try:
    from export_kb import KBExporter
except ImportError:
    try:
        from modules.export_kb import KBExporter
    except ImportError:
        KBExporter = None

# Intentar importar el generador de reportes
try:
    from modules import generate_category_report
except ImportError:
    try:
        import generate_category_report
    except ImportError:
        generate_category_report = None

# Intentar importar el validador de configuración
try:
    import sv_ttk
except ImportError:
    sv_ttk = None

# Intentar importar el validador de configuración
try:
    from modules import validate_config
except ImportError:
    try:
        import validate_config
    except ImportError:
        validate_config = None

# Intentar importar el instalador de ffmpeg
try:
    from modules import install_ffmpeg
except ImportError:
    try:
        import install_ffmpeg
    except ImportError:
        install_ffmpeg = None

# Intentar cargar configuración del entorno si existe
# Intentar importar el administrador de seguridad
try:
    from modules.security import SecurityManager
except ImportError:
    try:
        from security import SecurityManager
    except ImportError:
        SecurityManager = None


# --- Importación de UI Framework Avanzado (NUEVO) ---
try:
    from app.core.ui_framework import ThemeManager, AnimationEngine, IconManager, ResponsiveManager, BindingManager, ui_context
    from app.core.plugin_manager import PluginManager
    from modules.dashboard import DashboardView
except ImportError as e:
    print(f"Error importando UI Framework: {e}")
    ThemeManager, AnimationEngine, IconManager, ResponsiveManager, BindingManager, PluginManager, ui_context, DashboardView = None, None, None, None, None, None, {}, None

# Importar utilidad de normalización
try:
    from app.core.utils import normalize_youtube_url
except ImportError:
    def normalize_youtube_url(url): return url # Fallback

# Importar configuración centralizada
try:
    from app.config import config
    import logging
    logging.basicConfig(level=getattr(logging, config.general.log_level))
except ImportError as e:
    print(f"Advertencia: No se pudo cargar config.py: {e}")

# Función para limpiar directorios temporales de PyInstaller de forma segura

# ── Imports consolidados desde métodos (movidos aquí) ──────────────
import webbrowser
import sys as sys_module
import traceback
import subprocess as _sp
import tkinter.messagebox
try:
    from app.core.notification_router import NotificationRouter
except ImportError:
    NotificationRouter = None
try:
    from app.services.export_audit import ExportAuditLogger
except ImportError:
    ExportAuditLogger = None
try:
    from app.services.kb_exporter import KBExporter, export_kb
except ImportError:
    KBExporter = None
try:
    from app.ui.tabs import download_tab
except ImportError:
    download_tab = None
try:
    from app.ui.tabs import process_tab
except ImportError:
    process_tab = None
try:
    from app.ui.tabs import schedule_tab
except ImportError:
    schedule_tab = None
try:
    from app.ui.tabs import settings_tab
except ImportError:
    settings_tab = None
try:
    from app.ui.tabs.download_tab import update_queue_ui as _uq
except ImportError:
    _uq = None
try:
    from app.ui.tabs.process_tab import refresh_file_list
except ImportError:
    refresh_file_list = None
try:
    from modules.manual_analyzer import ManualAnalyzer
except ImportError:
    ManualAnalyzer = None
try:
    import manual_analyzer
except ImportError:
    manual_analyzer = None
try:
    from check_updates import check_for_updates
except ImportError:
    check_for_updates = None
try:
    from modules.check_updates import check_for_updates
except ImportError:
    check_for_updates = None
try:
    import pystray
except ImportError:
    pystray = None
try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

def cleanup_temp_dir():
    try:
        if getattr(sys, 'frozen', False):
            temp_dir = sys._MEIPASS
            for _ in range(3):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    break
                except Exception:
                    time.sleep(0.5)
    except Exception:
        pass

atexit.register(cleanup_temp_dir)

# Configuración de Logging para redirigir a la GUI
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            
            # Autolimpieza: Mantener solo las últimas 1000 líneas (Prevención de fuga de memoria)
            current_lines = int(self.text_widget.index('end-1c').split('.')[0])
            if current_lines > 1000:
                self.text_widget.delete("1.0", f"{current_lines - 1000}.0")
            
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        self.text_widget.after(0, append)

class ToolTip:
    """Clase para mostrar ayuda contextual (Tooltips)"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        tw = tk.Toplevel(self.widget)
        self.tip_window = tw
        tw.wm_overrideredirect(True)
        # Posicionar el tooltip cerca del cursor
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                       background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                       font=("Segoe UI", "9", "normal"), padx=5, pady=3)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

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

class TranscriptionProcessorApp:
    def __init__(self, root):
        self.root = root
        self.stat_channels = {}  # Inicializar canales del monitor
        self.monitor_service = None  # Inicializar monitor service
        self.scheduler_running = False  # Estado del scheduler
        self.scheduler_thread = None  # Referencia al hilo del scheduler
        self.root.title("KDP Master Suite v2.4.3 Enterprise Gold Edition")
        
        # Responsive window sizing basado en resolución de pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calcular tamaño óptimo (80% de la pantalla, pero no más de 1400x900)
        window_width = min(int(screen_width * 0.8), 1400)
        window_height = min(int(screen_height * 0.8), 900)
        
        # Centrar ventana
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(900, 650)  # Tamaño mínimo aumentado para mejor UX
        
        # Permitir maximizar
        self.root.state('normal')
        
        self.current_theme = "dark" # Default
        
        # Configuración de estilo UI/UX
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Base dir fix for dist
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Limpieza automática de carpetas basura en dist
        self.cleanup_dist_garbage()

        # Bloqueo de Instancia Única (Manejo Robusto)
        self.lock_file = os.path.join(self.base_dir, "app.lock")
        if os.path.exists(self.lock_file):
            try:
                # Intentar leer si el proceso sigue vivo es complejo en cross-platform sin psutil
                # Asumiremos que si el bloqueo existe y el usuario quiere, lo puede borrar.
                if messagebox.askyesno("Confirmación de Arranque", 
                                       "Se detectó un archivo de bloqueo ('app.lock') de una sesión anterior.\n"
                                       "Si la aplicación no está abierta, esto puede deberse a un cierre inesperado.\n\n"
                                       "¿Desea eliminar el bloqueo e iniciar KDP Master Suite?"):
                    try:
                        os.remove(self.lock_file)
                    except Exception as e:
                        messagebox.showerror("Error Crítico", f"No se pudo eliminar el bloqueo: {e}")
                        sys.exit()
                else:
                    sys.exit()
            except Exception:
                pass

        with open(self.lock_file, 'w') as f:
            f.write(str(os.getpid()))

        self.queue_running = False
        self.queue_paused = False

        # Variables de opciones
        self.secure_mode_var = tk.BooleanVar(value=False)

        # Variables de estado
        # Cargar configuración persistente o usar defaults
        self.config_file = os.path.join(self.base_dir, "settings.json")
        
        # Inicializar Administrador de Seguridad (Enterprise)
        self.security = SecurityManager() if SecurityManager else None
        
        # --- Inicializar UI Framework Avanzado ---
        if ThemeManager:
            self.theme_manager = ThemeManager(self.root)
            self.anim_engine = AnimationEngine()
            
            # Inicializar nuevos managers Enterprise
            self.responsive_manager = ResponsiveManager(self.root)
            self.binding_manager = BindingManager(self.root)
            self.plugin_manager = PluginManager(self.root)
            
            # Registrar contexto global
            ui_context["theme"] = self.theme_manager
            ui_context["anim"] = self.anim_engine
            ui_context["responsive"] = self.responsive_manager
            ui_context["bindings"] = self.binding_manager
            ui_context["plugins"] = self.plugin_manager
            
            # Registrar listener para modo compacto
            self.responsive_manager.register_listener(self.on_compact_mode_change)
            
            # Cargar Plugins
            self.plugin_manager.load_plugins(self)
        else:
            self.theme_manager, self.anim_engine = None, None
            self.responsive_manager, self.binding_manager = None, None
            self.plugin_manager = None
        
        self.validate_configuration()
        self.load_config()
        self._ensure_dashboard_config()
        self.load_theme_preference()
        
        # Inicializar Componentes Pro (Database & Monitor)
        self.db_manager = DatabaseManager() if DatabaseManager else None
        
        # Inicializar Trackers Enterprise (JSON indestructible + Manual Merger)
        self.video_tracker = ProcessedVideosTracker() if ProcessedVideosTracker else None
        self.manual_merger = ManualContentMerger() if ManualContentMerger else None
        
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Sistema listo")
        self.disk_status_var = tk.StringVar(value="Calculando espacio...")
        self.progress_var = tk.DoubleVar(value=0)
        self.new_videos_count_var = tk.StringVar(value="0 videos")
        self.search_var = tk.StringVar()
        self.channel_url_var = tk.StringVar()
        self.channel_name_var = tk.StringVar()
        self.monitor_interval_var = tk.StringVar(value="60")
        self.include_keywords_var = tk.StringVar()
        self.exclude_keywords_var = tk.StringVar()
        self.new_videos_var = tk.StringVar(value="")
        self.active_channels_var = tk.StringVar(value="Canales: 0")
        self.stat_total_channels = tk.StringVar(value="0")
        self.stat_active_channels = tk.StringVar(value="0")
        self.stat_pending_videos = tk.StringVar(value="0")
        self.stat_last_check = tk.StringVar(value="Nunca")
        self.filter_enabled_var = tk.BooleanVar(value=False)
        self.filter_mode_var = tk.StringVar(value="OR")
        self.total_fav_var = tk.StringVar(value="Total: 0")
        self.files_to_process = []
        self.download_queue = [] # Inicialización de cola Enterprise
        
        # Integrador de conocimiento con manejo de errores
        self.knowledge_db = KnowledgeDBManager() if KnowledgeDBManager else None
        try:
            self.integrator = KnowledgeIntegrator(self.blacklist, db_manager=self.knowledge_db) if KnowledgeIntegrator else None
        except Exception as e:
            print(f"⚠️ Error inicializando KnowledgeIntegrator: {e}")
            self.integrator = None
        
        # Pasar configuración de IA al integrador
        if self.integrator:
            self.integrator.ai_provider = self.ai_provider
            self.integrator.api_key = self.api_key
            self.integrator.system_prompt = self.ai_system_prompt

        # Verificación de Integridad
        if self.integrator:
            issues = self.integrator.verify_integrity()
            if issues:
                msg = "⚠️ Se detectaron problemas de integridad en la base de conocimiento:\n\n" + "\n".join(issues)
                messagebox.showwarning("Alerta de Seguridad", msg)
                # Log de auditoría
                if hasattr(self, 'audit_logger'):
                    for issue in issues:
                        self.audit_logger.warning(f"Fallo de integridad detectado al inicio: {issue}")

        self.html_gen = None

        # ── StringVars / IntVars / BoolVars — declaradas aquí para que
        # ── cualquier método pueda accederlas antes de que create_ui() corra.

        # ── StringVars / IntVars / BoolVars — declaradas aquí para que
        # ── cualquier método pueda accederlas antes de que create_ui() corra.

        # Construcción de la Interfaz
        self.create_ui()
        self.setup_logging()
        
        # Inicializar NotificationRouter con settings
        try:
            settings = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            self.notifier = NotificationRouter(self, settings=settings)
        except Exception as e:
            logging.warning(
                f"NotificationRouter no disponible — notificaciones desactivadas: {e}"
            )
            self.notifier = None
        
        # Inicializar Monitor (después de create_ui para que existan los tabs)
        if self.db_manager and ChannelMonitorService:
            self.monitor_service = ChannelMonitorService(db_manager=self.db_manager, notifier=self.notifier)
            self.monitor_service.set_callbacks(
                on_new_video=lambda v: self.root.after(0, lambda: self.on_monitor_new_video(v)),
                on_processing_complete=lambda v: self.root.after(0, lambda: self.on_monitor_processing_complete(v)),
                on_error=lambda e: self.root.after(0, lambda: self.on_monitor_error(e)),
                on_log=lambda msg, level='info': self.root.after(0, lambda: self.log_monitor_activity(msg))
            )
        if not self.notifier:
            logging.warning(
                "Monitor iniciado sin sistema de notificaciones. "
                "Los eventos no serán notificados al usuario."
            )
        if not self.notifier:
            logging.warning(
                "Monitor iniciado sin sistema de notificaciones. "
                "Los eventos no serán notificados al usuario."
            )
        else:
            self.monitor_service = None
        
        # Cargar Settings Tab
        self.setup_settings_tab()
        
        self.migrate_legacy_channels()
        
        # Auto-importar desde CSV si la DB está vacía
        self.auto_import_channels_from_csv()
        
        # Refrescar combo DESPUÉS de importar canales
        self.update_channel_combo()
        self.update_channel_stats()
        
        # Inicialización
        self.validate_directories()
        self.refresh_file_list()
        
        # Guardar configuración al salir
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configurar System Tray
        self._setup_system_tray()
        
        # Iniciar monitor de disco y verificar sesión previa
        self.update_disk_space_status()
        self.check_session_state()
        if not self.check_internet_connection():
            self.enter_offline_mode()
        # FFmpeg no es necesario para solo transcripciones
        # self.check_ffmpeg()
        self.check_ytdlp_updates()
        
        # Escaneo automático de videos nuevos al inicio (segundo plano)
        self.root.after(3000, self.auto_scan_new_videos)

    def validate_configuration(self):
        """Valida el archivo de configuración al inicio."""
        if validate_config and os.path.exists(self.config_file):
            valid, msg = validate_config.validate_settings(self.config_file)
            if not valid:
                response = messagebox.askyesno("Error de Configuración", f"El archivo de configuración tiene errores:\n\n{msg}\n\n¿Desea restablecer la configuración por defecto (se perderán sus ajustes)?")
                if response:
                    try:
                        os.remove(self.config_file)
                        messagebox.showinfo("Restablecido", "Configuración restablecida. Se iniciará el asistente.")
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo eliminar el archivo: {e}")
                else:
                    print("⚠️ Iniciando con configuración potencialmente inválida por decisión del usuario.")

    def load_config(self):
        try:
            from app.config import config
            defaults = {
                "input_dir": str(config.paths.download_dir),
                "output_dir": str(config.paths.processed_dir),
                "blacklist": [],
                "channels": [],
                "download_queue": [],
                "notifications": {
                    "enable_native": False,
                    "enable_internal": True,
                    "cooldown_minutes": 5,
                    "summary_mode": False
                }
            }
        except ImportError:
            defaults = {
                "input_dir": os.getenv("DOWNLOAD_DIR", "data/transcriptions"),
                "output_dir": os.getenv("PROCESSED_DIR", "outputs/transcriptions_processed"),
                "blacklist": [],
                "channels": [],
                "download_queue": [],
                "notifications": {
                    "enable_native": False,
                    "enable_internal": True,
                    "cooldown_minutes": 5,
                    "summary_mode": False
                }
            }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception:
                pass
        
        # Guardar configuración completa para acceso global (incluyendo NotificationRouter)
        self.settings = defaults
        
        self.input_dir = tk.StringVar(value=defaults["input_dir"])
        self.output_dir = tk.StringVar(value=defaults["output_dir"])
        self.blacklist = defaults.get("blacklist", [])
        self.channels = defaults.get("channels", [])
        self.download_queue = defaults.get("download_queue", [])

        # Cargar configuración de IA (Enterprise Encrypted)
        self.ai_provider = defaults.get("ai_provider", "none")
        raw_api_key = defaults.get("ai_api_key", "")
        
        if raw_api_key and self.security:
            self.api_key = self.security.decrypt(raw_api_key)
        else:
            self.api_key = raw_api_key
            
        self.ai_system_prompt = defaults.get("ai_system_prompt", "Clasifica el siguiente texto en una de estas categorías: 'Legalidad y Compliance', 'Matriz de Roles (GEM)', 'Matriz de Roles y Fases SOE', 'Fórmulas y Métricas', 'Investigación de Nichos', 'Amazon Ads y Marketing', 'Conocimiento General KDP'. Responde SOLO con el nombre de la categoría.")

    def _ensure_dashboard_config(self):
        """Asegura que la sección dashboard exista en settings."""
        defaults = {
            "port": 8000,
            "host": "127.0.0.1",
            "db_path": "data/channel_monitor.db"
        }
        self.settings.setdefault("dashboard", defaults)

    def migrate_legacy_channels(self):
        """Mueve canales de settings.json (self.channels) a SQLite (una sola vez)."""
        if not self.db_manager or not self.channels:
            return
            
        migrated_count = 0
        for ch in self.channels:
            # add_channel ya gestiona duplicados y normaliza URLs
            if self.db_manager.add_channel(ch['url'], ch['name']):
                migrated_count += 1
                
        if migrated_count > 0 or len(self.channels) > 0:
            self.logger.info(f"Finalizando migración: {migrated_count} nuevos canales movidos. Limpiando JSON.")
            # Limpiar lista en memoria para priorizar DB definitivamente
            self.channels = []
            self.save_config()
            # Actualizar stats globales
            self.update_channel_stats()

    def auto_import_channels_from_csv(self):
        """Importa canales desde CSV si la DB tiene menos de 10 canales."""
        if not self.db_manager:
            return
        
        csv_path = os.path.join(self.base_dir, "knowledge", "Libro1.csv")
        if not os.path.exists(csv_path):
            return
        
        current_count = len(self.db_manager.get_all_channels(active_only=False))
        if current_count >= 10:
            return
        
        self.logger.info(f"DB casi vacia ({current_count} canales). Importando desde CSV...")
        imported = 0
        skipped = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(' - ', 1)
                    if len(parts) == 2:
                        handle = parts[0].strip()
                        name = parts[1].strip()
                    else:
                        handle = line.strip()
                        name = line.strip()
                    
                    if not handle.startswith('@'):
                        handle = '@' + handle
                    
                    result = self.db_manager.add_channel(handle, name)
                    if result:
                        imported += 1
                    else:
                        skipped += 1
            
            self.logger.info(f"Auto-import CSV: {imported} nuevos, {skipped} duplicados")
            self.update_channel_combo()
            self.update_channel_stats()
        except Exception as e:
            self.logger.error(f"Error auto-importando CSV: {e}")

    def check_ytdlp_updates(self):
        """Verifica y actualiza yt-dlp automáticamente en segundo plano."""
        def update_task():
            try:
                self.logger.info("Verificando actualizaciones de yt-dlp...")
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                self.logger.info("yt-dlp verificado/actualizado correctamente.")
            except Exception as e:
                self.logger.warning(f"No se pudo actualizar yt-dlp: {e}")
        
        threading.Thread(target=update_task, daemon=True).start()

    def auto_scan_new_videos(self):
        """Escaneo automático de videos nuevos al iniciar la app (segundo plano)."""
        if not self.monitor_service or not self.db_manager:
            self.logger.info("Monitor no disponible, omitiendo escaneo automático.")
            return
        
        def scan_task():
            start_time = time.time()
            try:
                self.logger.info("=" * 60)
                self.logger.info("🔍 ESCANEO AUTOMÁTICO: Buscando videos nuevos en todos los canales favoritos...")
                self.logger.info("=" * 60)
                
                channels = self.db_manager.get_all_channels(active_only=True)
                total_channels = len(channels)
                self.logger.info(f"Canales activos a escanear: {total_channels}")
                
                if total_channels == 0:
                    self.logger.info("No hay canales activos. Agrega canales favoritos para activar el escaneo.")
                    return
                
                new_count = self.monitor_service.check_for_new_videos_parallel()
                
                if self.video_tracker:
                    for ch in channels:
                        ch_id = ch.get('channel_id') or str(ch['id'])
                        ch_name = ch.get('channel_name', 'Sin nombre')
                        videos = self.db_manager.get_videos_by_channel(ch['id'])
                        for v in videos:
                            self.video_tracker.register_video(
                                video_id=v['video_id'],
                                channel_id=ch_id,
                                channel_name=ch_name,
                                title=v.get('title', ''),
                                video_url=v.get('video_url', ''),
                                published_at=v.get('published_at', ''),
                                status=v.get('status', 'detected')
                            )
                    
                    elapsed = time.time() - start_time
                    self.video_tracker.record_scan(
                        channels_scanned=total_channels,
                        new_found=new_count,
                        duplicates=max(0, len(channels) * 30 - new_count),
                        duration_seconds=elapsed
                    )
                    
                    stats = self.video_tracker.get_stats()
                    self.logger.info(f"📊 Tracker JSON: {stats['total_videos_tracked']} videos rastreados en total")
                
                if new_count > 0:
                    self.logger.info(f"✅ Se detectaron {new_count} video(s) nuevo(s) sin descargar.")
                    pending = self.db_manager.get_pending_videos()
                    if pending:
                        self.logger.info(f"📥 {len(pending)} video(s) pendientes de descarga.")
                        ToastNotification.show(self.root, f"¡{new_count} video(s) nuevo(s) detectado(s)!", type="success", duration=5000)
                else:
                    self.logger.info("✅ No hay videos nuevos. Todos los canales están al día.")
                    ToastNotification.show(self.root, "Escaneo completado: Sin videos nuevos", type="info", duration=3000)
                
                self.logger.info("=" * 60)
                self.logger.info("Escaneo automático finalizado.")
                self.logger.info("=" * 60)
            except Exception as e:
                self.logger.error(f"Error en escaneo automático: {e}")
        
        threading.Thread(target=scan_task, daemon=True).start()
        self.new_videos_count_var.set("Escaneando...")
        self.root.after(5000, self.update_new_videos_display)

    def update_new_videos_display(self):
        """Actualiza el panel visual de videos nuevos en la UI."""
        if not self.db_manager:
            return
        
        pending = self.db_manager.get_pending_videos()
        pending_count = len(pending) if pending else 0
        
        if self.video_tracker:
            stats = self.video_tracker.get_stats()
            total_tracked = stats['total_videos_tracked']
            total_new = stats['statistics'].get('total_new', 0)
        else:
            total_tracked = 0
            total_new = 0
        
        channels = self.db_manager.get_all_channels(active_only=True)
        ch_count = len(channels)
        
        self.active_channels_var.set(f"📺 {ch_count} canales activos")
        
        if pending_count > 0:
            self.new_videos_var.set(f"🔔 {pending_count} video(s) pendiente(s)")
            self.new_videos_count_var.set(f"{pending_count} videos nuevos detectados")
            
            self.new_videos_info.configure(state=tk.NORMAL)
            self.new_videos_info.delete("1.0", tk.END)
            
            display_text = f"Videos nuevos detectados: {pending_count}\n"
            display_text += f"Videos rastreados en total: {total_tracked}\n"
            display_text += f"Canales activos: {ch_count}\n\n"
            
            for v in pending[:10]:
                display_text += f"  • {v.get('title', 'Sin título')[:80]}\n"
                display_text += f"    Canal: {v.get('channel_name', '')} | Publicado: {v.get('published_at', '')[:10]}\n"
            
            if pending_count > 10:
                display_text += f"\n  ... y {pending_count - 10} video(s) más."
            
            self.new_videos_info.insert("1.0", display_text)
            self.new_videos_info.configure(state=tk.DISABLED)
        else:
            self.new_videos_var.set("")
            self.new_videos_count_var.set("Sin videos nuevos")
            
            self.new_videos_info.configure(state=tk.NORMAL)
            self.new_videos_info.delete("1.0", tk.END)
            self.new_videos_info.insert("1.0", f"Todos los canales están al día.\n{ch_count} canales activos monitoreados.\nTotal de videos rastreados: {total_tracked}")
            self.new_videos_info.configure(state=tk.DISABLED)

    def manual_scan_new_videos(self):
        """Escaneo manual de videos nuevos desde el botón en la UI."""
        if not self.monitor_service or not self.db_manager:
            messagebox.showinfo("Info", "Monitor no disponible.")
            return
        
        self.log("[🔍] Iniciando escaneo manual de videos nuevos...")
        self.new_videos_count_var.set("Escaneando...")
        
        def scan_task():
            start_time = time.time()
            try:
                channels = self.db_manager.get_all_channels(active_only=True)
                total = len(channels)
                self.log(f"   Canales activos: {total}")
                
                if total == 0:
                    self.root.after(0, lambda: self.new_videos_count_var.set("Sin canales activos"))
                    return
                
                new_count = self.monitor_service.check_for_new_videos_parallel()
                elapsed = time.time() - start_time
                
                if self.video_tracker:
                    self.video_tracker.record_scan(
                        channels_scanned=total,
                        new_found=new_count,
                        duplicates=0,
                        duration_seconds=elapsed
                    )
                
                self.root.after(0, lambda: self.update_new_videos_display())
                
                if new_count > 0:
                    self.root.after(0, lambda: ToastNotification.show(
                        self.root, f"¡{new_count} video(s) nuevo(s) detectado(s)!", type="success", duration=5000
                    ))
                
                self.log(f"[✅] Escaneo manual completado: {new_count} video(s) nuevo(s) en {elapsed:.1f}s")
                
            except Exception as e:
                self.logger.error(f"Error en escaneo manual: {e}")
                self.root.after(0, lambda: self.new_videos_count_var.set("Error en escaneo"))
        
        threading.Thread(target=scan_task, daemon=True).start()

    def download_all_new_transcriptions(self):
        """Añade todos los videos pendientes a la cola de descarga de transcripciones."""
        if not self.db_manager:
            return
        
        pending = self.db_manager.get_pending_videos()
        if not pending:
            messagebox.showinfo("Info", "No hay videos nuevos pendientes de descarga.")
            return
        
        added = 0
        for v in pending:
            url = v.get('video_url', '')
            if url and url not in self.download_queue:
                self.download_queue.append(url)
                added += 1
        
        self.update_queue_ui()
        self.log(f"[📥] {added} video(s) nuevo(s) añadido(s) a la cola de transcripciones.")
        messagebox.showinfo("Cola Actualizada", f"Se añadieron {added} transcripciones a la cola.\nPresiona 'INICIAR COLA' para descargarlas.")

    def show_scan_stats(self):
        """Muestra estadísticas completas del escaneo."""
        if not self.db_manager:
            return
        
        stats = self.db_manager.get_statistics()
        pending = self.db_manager.get_pending_videos()
        channels = self.db_manager.get_all_channels(active_only=True)
        
        msg = f"📊 ESTADÍSTICAS DE ESCANEO\n\n"
        msg += f"Canales activos: {len(channels)}\n"
        msg += f"Videos totales en DB: {stats.get('total_videos', 0)}\n"
        msg += f"Videos nuevos pendientes: {len(pending) if pending else 0}\n"
        msg += f"Videos completados: {stats.get('completed', 0)}\n"
        msg += f"Videos fallidos: {stats.get('failed', 0)}\n"
        
        if self.video_tracker:
            vt_stats = self.video_tracker.get_stats()
            msg += f"\n📋 TRACKER JSON:\n"
            msg += f"Videos rastreados: {vt_stats['total_videos_tracked']}\n"
            msg += f"Escaneos realizados: {vt_stats['total_scans']}\n"
            msg += f"Tamaño archivo: {vt_stats['file_size_kb']} KB\n"
            s = vt_stats['statistics']
            msg += f"Total escaneados: {s.get('total_scanned', 0)}\n"
            msg += f"Nuevos detectados: {s.get('total_new', 0)}\n"
            msg += f"Duplicados omitidos: {s.get('total_duplicates', 0)}\n"
        
        if messagebox.askyesno("Estadísticas", msg + "\n\n¿Abrir archivo del tracker?"):
            if self.video_tracker:
                self.open_folder(str(self.video_tracker.tracker_file.parent))

    def check_first_run(self):
        if not os.path.exists(self.config_file):
            self.root.after(100, self.run_first_time_wizard)

    def check_internet_connection(self):
        """Verifica la conectividad a Internet al inicio."""
        try:
            urllib.request.urlopen('https://www.google.com', timeout=5)
            return True
        except urllib.error.URLError:
            self.logger.error("No se pudo conectar a Internet.")
            return False

    def _setup_system_tray(self):
        """Configura el icono de bandeja del sistema (System Tray)."""
        try:
            import pystray
        except ImportError:
            return
        
        def create_tray_icon(color="green"):
            """Crea una imagen simple para el icono de bandeja."""
            size = (64, 64)
            image = Image.new('RGB', size, color='white')
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill=color)
            draw.text((20, 25), "KDP", fill="white")
            return image
        
        def show_window(icon, item):
            self.root.after(0, self.root.deiconify)
        
        def quit_app(icon, item):
            self.on_closing()
        
        def toggle_scheduler_menu(icon, item):
            if hasattr(self, 'schedule_manager') and self.schedule_manager:
                if self.schedule_manager.running:
                    self.schedule_manager.stop()
                else:
                    self.schedule_manager.start()
                self.root.after(0, self._update_tray_icon)
        
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar Ventana", show_window),
            pystray.MenuItem("Iniciar/Pausar Scheduler", toggle_scheduler_menu),
            pystray.MenuItem("Salir", quit_app)
        )
        
        self.tray_icon = pystray.Icon("KDP Master", create_tray_icon("green"), "KDP Master Suite", menu)
        self.tray_icon.detached = True
        
        self._tray_update_thread = None
    
    def _update_tray_icon(self):
        """Actualiza el icono de la bandeja según el estado."""
        if not hasattr(self, 'tray_icon'):
            return
        
        try:
            
            color = "green" if (hasattr(self, 'schedule_manager') and 
                              self.schedule_manager and 
                              self.schedule_manager.running) else "red"
            
            size = (64, 64)
            image = Image.new('RGB', size, color='white')
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill=color)
            draw.text((20, 25), "KDP", fill="white")
            
            self.tray_icon.icon = image
        except:
            pass
    
    def _run_tray_icon(self):
        """Ejecuta el icono de bandeja en un hilo separado."""
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                self.tray_icon.run_detached()
            except Exception as e:
                print(f"Error al iniciar bandeja: {e}")

    def check_ffmpeg(self):
        """Verifica si FFmpeg está instalado y accesible."""
        # Desactivado: No es necesario para descargar solo subtítulos/metadatos.
        pass

    def offer_ffmpeg_install(self):
        """Ofrece descargar e instalar FFmpeg automáticamente."""
        if messagebox.askyesno("Falta Componente", "FFmpeg no fue encontrado. Es necesario para procesar videos correctamente.\n\n¿Desea descargarlo e instalarlo automáticamente ahora? (Puede tardar unos minutos)"):
            
            # Ventana de progreso
            popup = tk.Toplevel(self.root)
            popup.title("Instalando FFmpeg...")
            popup.geometry("300x100")
            popup.resizable(False, False)
            # Centrar
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 50
            popup.geometry(f"+{x}+{y}")
            
            lbl = ttk.Label(popup, text="Descargando componentes...", justify=tk.CENTER)
            lbl.pack(pady=10)
            pb = ttk.Progressbar(popup, mode='indeterminate')
            pb.pack(fill=tk.X, padx=20)
            pb.start()

            def run_install():
                success, msg = install_ffmpeg.install_ffmpeg()
                self.root.after(0, popup.destroy)
                if success:
                    self.logger.info(f"FFmpeg instalado en: {msg}")
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", "FFmpeg instalado correctamente."))
                else:
                    self.logger.error(f"Error instalando FFmpeg: {msg}")
                    self.root.after(0, lambda: messagebox.showerror("Error", f"No se pudo instalar FFmpeg:\n{msg}"))

            threading.Thread(target=run_install, daemon=True).start()

    def enter_offline_mode(self):
        """Deshabilita las funcionalidades de red y notifica al usuario."""
        self.root.title(f"{self.root.title()} - [MODO OFFLINE]")
        messagebox.showerror("Error de Red", "No se pudo conectar a Internet. Se iniciará en Modo Offline.")

        # Deshabilitar widgets de red
        self.notebook.tab(0, state="disabled") # Pestaña de descarga
        
        # Deshabilitar herramientas de red en el menú
        # (Esto requiere obtener el menú después de que se cree, lo haremos en create_ui)
        # Por ahora, la pestaña deshabilitada es la principal barrera.
        if hasattr(self, 'tools_menu'):
            self.tools_menu.entryconfig("🤖 Configurar IA", state="disabled")
            
        # Añadir botón de reintentar en la barra de estado o en un lugar visible
        self.retry_btn = ttk.Button(self.root, text="🔄 Reintentar Conexión", command=self.retry_connection)
        self.retry_btn.place(relx=0.5, rely=0.05, anchor="n")

    def retry_connection(self):
        """Intenta reconectar a internet y salir del modo offline."""
        if self.check_internet_connection():
            self.root.title(self.root.title().replace(" - [MODO OFFLINE]", ""))
            self.notebook.tab(0, state="normal")
            if hasattr(self, 'tools_menu'):
                self.tools_menu.entryconfig("🤖 Configurar IA", state="normal")
            self.retry_btn.destroy()
            messagebox.showinfo("Conexión Restablecida", "Se ha restablecido la conexión a Internet.")
        else:
            messagebox.showerror("Error de Conexión", "Aún no se detecta conexión a Internet.")

    def cleanup_dist_garbage(self):
        """Elimina carpetas basura generadas en dist si existen."""
        garbage_paths = [
            os.path.join(self.base_dir, "dist", "knowledge"),
            os.path.join(self.base_dir, "dist", "knowledge_base_OLD_MIGRATED")
        ]
        for p in garbage_paths:
            if os.path.exists(p) and os.path.isdir(p):
                try:
                    shutil.rmtree(p)
                except Exception:
                    pass

    def update_disk_space_status(self):
        """Actualiza el indicador de espacio en disco en la barra de estado."""
        try:
            path = self.input_dir.get()
            if not os.path.exists(path):
                path = self.base_dir
            
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (1024**3)
            
            self.disk_status_var.set(f"💾 Disco: {free_gb:.1f} GB Libres")
            
            # Alerta visual si queda poco espacio (< 1GB)
            # Nota: Cambiar color de fondo en ttk requiere estilos complejos, 
            # usamos texto para simplicidad y compatibilidad con temas.
            if free_gb < 1.0:
                self.status_var.set("⚠️ ADVERTENCIA: Poco espacio en disco")
        except Exception:
            self.disk_status_var.set("💾 Disco: N/A")
        
        self.root.after(5000, self.update_disk_space_status)

    def check_session_state(self):
        """Verifica si hubo un cierre inesperado durante una descarga."""
        session_file = os.path.join(self.base_dir, "session_state.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    state = json.load(f)
                if state.get("status") == "downloading" and state.get("url"):
                    if messagebox.askyesno("Sesión Restaurada", f"Se detectó una descarga interrumpida de:\n{state['url']}\n¿Desea reanudarla ahora?"):
                        self.url_var.set(state['url'])
                        self.root.after(500, self.start_download)
            except Exception as e:
                self.logger.error(f"Error leyendo sesión anterior: {e}")

    def save_session_state(self, url, status):
        """Guarda el estado actual para recuperación."""
        try:
            with open(os.path.join(self.base_dir, "session_state.json"), 'w') as f:
                json.dump({"url": url, "status": status, "timestamp": str(datetime.now())}, f)
        except:
            pass

    def log(self, message):
        """Atajo para loguear información tanto en consola como en la GUI de forma segura."""
        log_msg = f"{message}"
        if hasattr(self, 'logger'):
            self.logger.info(log_msg)
        else:
            print(log_msg)

    def update_queue_ui(self):
        self.save_config()
        _uq(self)

    def clear_session_state(self):
        """Limpia el estado de sesión al finalizar correctamente."""
        session_file = os.path.join(self.base_dir, "session_state.json")
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except:
                pass


    # === INICIO MODULO: check_for_app_updates ===
    def check_for_app_updates(self):
        """Verifica actualizaciones desde GitHub API en tiempo real."""
        self.log("[*] Verificando actualizaciones desde GitHub...")
        
        try:
            from modules.check_updates import check_for_updates
        except ImportError:
            try:
                from check_updates import check_for_updates
            except ImportError:
                self.log("[-] Modulo de actualizaciones no encontrado.")
                messagebox.showerror("Error", "Modulo de actualizaciones no encontrado.")
                return
        
        has_update, latest_v, changelog, download_url = check_for_updates()
        
        if has_update:
            #Dialogo detallado con changelog
            msg = f"Nueva version disponible: v{latest_v}\n\n"
            if changelog:
                # Limitar changelog a 500 caracteres
                msg += f"Cambios:\n{changelog[:500]}"
                if len(changelog) > 500:
                    msg += "\n\n[Ver cambios completos en GitHub]"
            
            if messagebox.askyesno("Actualizacion Disponible", msg):
                if download_url:
                    webbrowser.open(download_url)
                else:
                    webbrowser.open("https://github.com/pabloalanzahlut/KDP-Master-Suite/releases")
                self.log("[+] Navegando a descargas...")
        else:
            messagebox.showinfo("Actualizaciones", f"Tienes la version mas reciente: v{latest_v}")
    # === FIN MODULO ===

    def show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = (
            "KDP Master Suite v2.4.3 Enterprise Gold Edition\n\n"
            "Desarrollado para la gestión inteligente de conocimientos\n"
            "basados en transcripciones digitales.\n\n"
            "© 2026 KDP Master Solutions\n"
            "Todos los derechos reservados."
        )
        messagebox.showinfo("Acerca de", about_text)

    def run_health_check(self):
        """Diagnóstico completo: KB health check + verificación de sistema."""
        # --- Parte 1: KB Health Check (módulo externo) ---
        if check_kb_health:
            try:
                success, report = check_kb_health.check_health(self.base_dir)
                win = tk.Toplevel(self.root)
                win.title("Reporte de Salud KB")
                win.geometry("600x400")
                txt = scrolledtext.ScrolledText(win, font=("Consolas", 10))
                txt.pack(fill=tk.BOTH, expand=True)
                txt.insert(tk.END, "\n".join(report))
                return
            except Exception as e:
                self.logger.warning(f"check_kb_health falló: {e}") if hasattr(self, "logger") else None

        # --- Parte 2: Diagnóstico de sistema (fallback) ---
        self.log("[*] Iniciando diagnóstico de salud del sistema...")
        health_report = []
        try:
            _sp.run(["ffmpeg", "-version"], capture_output=True, check=True)
            health_report.append("✅ FFmpeg: Instalado y Funcional")
        except Exception:
            health_report.append("❌ FFmpeg: No encontrado o corrupto")
        if self.check_internet_connection():
            health_report.append("✅ Conexión: Online")
        else:
            health_report.append("⚠️ Conexión: Offline / Limitada")
        try:
            db_path = os.path.join(self.base_dir, "knowledge", "knowledge_base.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                health_report.append("✅ Base de Datos: Íntegra")
                conn.close()
            else:
                health_report.append("ℹ️ Base de Datos: Pendiente de creación")
        except Exception:
            health_report.append("❌ Base de Datos: Corrupta")
        try:
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (2**30)
            health_report.append(
                f"✅ Almacenamiento: {free_gb} GB Libres" if free_gb > 5
                else f"⚠️ Almacenamiento Crítico: {free_gb} GB Libres"
            )
        except Exception:
            pass
        report_str = "\n".join(health_report)
        self.log(f"[+] Diagnóstico completado.\n{report_str}")
        messagebox.showinfo("Diagnóstico de Salud", f"Estado del Sistema:\n\n{report_str}")

    def open_audit_log(self):
        audit_log_file = os.path.join("logs", "audit.log")
        if os.path.exists(audit_log_file):
            self.open_folder(audit_log_file)
        else:
            messagebox.showinfo("Info", "No hay archivo de log de auditoría aún.")

    def open_log_file(self):
        log_file = os.path.join("logs", "app.log")
        if os.path.exists(log_file):
            self.open_folder(log_file)
        else:
            messagebox.showinfo("Info", "No hay archivo de log aún.")

    def clear_console(self):
        self.log_area.configure(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.configure(state='disabled')

    def reset_session_state(self):
        self.clear_session_state()
        messagebox.showinfo("Éxito", "Estado de sesión limpiado.")

    def open_readme(self):
        # Intentar abrir el manual en docs/ o en la raíz
        readme_path = os.path.join(self.base_dir, "docs", "MANUAL_USUARIO.md")
        if not os.path.exists(readme_path):
            readme_path = os.path.join(self.base_dir, "MANUAL_USUARIO.md")
            
        if os.path.exists(readme_path):
            self.open_folder(readme_path)
        else:
            messagebox.showinfo("Info", "No se encontró el Manual de Usuario.")

    def configure_styles(self):
        # Paleta de colores Premium Enterprise Platinum - MEJORADA
        is_dark = self.current_theme == "dark"
        
        # Colores de fondo con más profundidad
        bg_color = "#0a0e1a" if is_dark else "#f8fafc"  # Más oscuro para dark mode
        bg_secondary = "#1e293b" if is_dark else "#ffffff"  # Fondos de cards/paneles
        bg_tertiary = "#334155" if is_dark else "#e2e8f0"  # Fondos alternativos
        
        # Colores de texto con mejor contraste
        fg_color = "#f1f5f9" if is_dark else "#0f172a"
        fg_secondary = "#cbd5e1" if is_dark else "#475569"
        fg_muted = "#94a3b8" if is_dark else "#64748b"
        
        # Colores de acento vibrantes
        accent_color = "#3b82f6"  # Blue 500 - Principal
        accent_hover = "#2563eb"  # Blue 600 - Hover
        accent_light = "#60a5fa"  # Blue 400 - Variante clara
        
        success_color = "#10b981"  # Emerald 500
        success_hover = "#059669"  # Emerald 600
        
        warning_color = "#f59e0b"  # Amber 500
        warning_hover = "#d97706"  # Amber 600
        
        danger_color = "#ef4444"  # Red 500
        danger_hover = "#dc2626"  # Red 600
        
        info_color = "#06b6d4"  # Cyan 500
        purple_color = "#a855f7"  # Purple 500
        
        self.root.configure(bg=bg_color)
        
        # Fuentes con jerarquía profesional mejorada
        # Intentar usar fuentes del sistema modernas, fallback a defaults
        try:
            self.header_font = tkfont.Font(family="Segoe UI", size=22, weight="bold")
            self.subhead_font = tkfont.Font(family="Segoe UI", size=14, weight="bold")
            self.normal_font = tkfont.Font(family="Segoe UI", size=10)
            self.small_font = tkfont.Font(family="Segoe UI", size=9)
            self.status_font = tkfont.Font(family="Segoe UI", size=9)
            self.mono_font = tkfont.Font(family="Consolas", size=10)
        except:
            # Fallback si Segoe UI no está disponible
            self.header_font = tkfont.Font(family="Arial", size=22, weight="bold")
            self.subhead_font = tkfont.Font(family="Arial", size=14, weight="bold")
            self.normal_font = tkfont.Font(family="Arial", size=10)
            self.small_font = tkfont.Font(family="Arial", size=9)
            self.status_font = tkfont.Font(family="Arial", size=9)
            self.mono_font = tkfont.Font(family="Courier", size=10)

        # Estilos base
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color, font=self.normal_font)
        
        # Botones Primarios - ALTO CONTRASTE
        self.style.configure("Primary.TButton", 
                           padding=(20, 12), 
                           font=('Segoe UI', 11, 'bold'), 
                           foreground="#FFFFFF", 
                           background=accent_color,
                           borderwidth=0,
                           relief="flat")
        self.style.map("Primary.TButton", 
                      background=[('active', accent_hover), 
                                ('pressed', '#1d4ed8'),
                                ('disabled', '#64748b')],
                      foreground=[('disabled', '#FFFFFF')],
                      relief=[('pressed', 'sunken')])
        
        # Botones de Éxito - VERDE BRILLANTE
        self.style.configure("Success.TButton", 
                           padding=(20, 12), 
                           font=('Segoe UI', 11, 'bold'), 
                           foreground="#FFFFFF", 
                           background=success_color,
                           borderwidth=0,
                           relief="flat")
        self.style.map("Success.TButton", 
                      background=[('active', success_hover),
                                ('pressed', '#047857')],
                      foreground=[('disabled', '#FFFFFF')])

        # Botones de Peligro - ROJO BRILLANTE
        self.style.configure("Danger.TButton", 
                           padding=(16, 10), 
                           font=('Segoe UI', 10, 'bold'), 
                           foreground="#FFFFFF", 
                           background=danger_color,
                           borderwidth=0,
                           relief="flat")
        self.style.map("Danger.TButton", 
                      background=[('active', danger_hover),
                                ('pressed', '#b91c1c')],
                      foreground=[('disabled', '#FFFFFF')])

        # Botones de Advertencia - NARANJA BRILLANTE
        self.style.configure("Warning.TButton", 
                           padding=(16, 10), 
                           font=('Segoe UI', 10, 'bold'), 
                           foreground="#FFFFFF", 
                           background=warning_color,
                           borderwidth=0,
                           relief="flat")
        self.style.map("Warning.TButton", 
                      background=[('active', warning_hover),
                                ('pressed', '#b45309')],
                      foreground=[('disabled', '#FFFFFF')])
        
        # Botones secundarios/normales
        self.style.configure("TButton",
                           padding=(12, 8),
                           font=('Segoe UI', 10),
                           background=bg_tertiary,
                           foreground=fg_color,
                           borderwidth=1,
                           relief="flat")
        self.style.map("TButton",
                      background=[('active', bg_secondary)],
                      relief=[('pressed', 'sunken')])
        
        # Headers y Labels
        self.style.configure("Header.TLabel", 
                           font=self.header_font, 
                           foreground=accent_light if is_dark else accent_color, 
                           background=bg_color)
        self.style.configure("SubHeader.TLabel", 
                           font=self.subhead_font, 
                           foreground=fg_color, 
                           background=bg_color)
        self.style.configure("Muted.TLabel",
                           font=self.small_font,
                           foreground=fg_muted,
                           background=bg_color)
        
        # Status bar con mejor diseño
        self.style.configure("Status.TLabel", 
                           font=self.status_font, 
                           foreground=fg_secondary, 
                           background=bg_secondary,
                           padding=(8, 4))
        self.style.configure("Status.TFrame",
                           background=bg_secondary,
                           relief="flat")
        
        # LabelFrames con mejor borde
        self.style.configure("TLabelframe", 
                           background=bg_color, 
                           borderwidth=2, 
                           relief="groove",
                           bordercolor=bg_tertiary)
        self.style.configure("TLabelframe.Label", 
                           font=self.subhead_font, 
                           foreground=accent_light if is_dark else accent_color, 
                           background=bg_color,
                           padding=(5, 2))
        
        # Notebook (pestañas) con diseño moderno
        self.style.configure("TNotebook", 
                           background=bg_color, 
                           borderwidth=0,
                           padding=0)
        self.style.configure("TNotebook.Tab", 
                           padding=[24, 10], 
                           font=('Segoe UI', 11, 'bold'),
                           borderwidth=0)
        self.style.map("TNotebook.Tab", 
                      background=[('selected', accent_color), 
                                ('!selected', bg_tertiary)],
                      foreground=[('selected', 'white'), 
                                ('!selected', fg_muted)],
                      expand=[('selected', [1, 1, 1, 0])])
        
        # Treeview moderno con mejor diseño
        self.style.configure("Treeview", 
                           background=bg_secondary,
                           foreground=fg_color,
                           fieldbackground=bg_secondary,
                           rowheight=35,
                           font=('Segoe UI', 10),
                           borderwidth=0)
        self.style.configure("Treeview.Heading", 
                           font=('Segoe UI', 10, 'bold'), 
                           background=bg_tertiary,
                           foreground=fg_color,
                           relief="flat",
                           borderwidth=1)
        self.style.map("Treeview", 
                      background=[('selected', accent_color)], 
                      foreground=[('selected', 'white')])
        self.style.map("Treeview.Heading",
                      background=[('active', bg_secondary)])

        # Entry fields mejorados
        self.style.configure("TEntry",
                           fieldbackground=bg_secondary,
                           foreground=fg_color,
                           borderwidth=2,
                           relief="flat")
        
        # Combobox
        self.style.configure("TCombobox",
                           fieldbackground=bg_secondary,
                           background=bg_secondary,
                           foreground=fg_color,
                           borderwidth=2,
                           arrowcolor=fg_color)
        
        self.style.map("TCombobox",
                      fieldbackground=[('readonly', bg_secondary), ('active', bg_tertiary)],
                      selectbackground=[('readonly', accent_color)],
                      selectforeground=[('readonly', 'white')])
        
        # Checkbuttons
        self.style.configure("TCheckbutton",
                           background=bg_color,
                           foreground=fg_color,
                           font=self.normal_font)
        
        # Scrollbars más sutiles
        self.style.configure("Vertical.TScrollbar", 
                           gripcount=0, 
                           background=bg_tertiary,
                           troughcolor=bg_secondary,
                           borderwidth=0,
                           arrowsize=13)
        self.style.map("Vertical.TScrollbar",
                      background=[('active', bg_tertiary)])
        
        # Progressbar con color de acento
        self.style.configure("TProgressbar",
                           background=accent_color,
                           troughcolor=bg_tertiary,
                           borderwidth=0,
                           thickness=8)
        
        # Separadores más sutiles
        self.style.configure("TSeparator",
                           background=bg_tertiary)


    def validate_directories(self):
        for path in [self.input_dir.get(), self.output_dir.get()]:
            if path:
                abs_path = path if os.path.isabs(path) else os.path.join(self.base_dir, path)
                if not os.path.exists(abs_path):
                    try:
                        os.makedirs(abs_path, exist_ok=True)
                        self.log(f"Directorio creado: {abs_path}")
                    except Exception as e:
                        self.log(f"Error creando directorio {abs_path}: {e}")
    
    def setup_logging(self):
        self.logger = logging.getLogger('KDP_GUI')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

        # Handler de Texto (GUI)
        handler = TextHandler(self.log_area)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Handler de Archivo con Rotación (Max 5MB, 3 backups)
        log_dir = os.path.join(self.base_dir, "logs")
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        log_file = os.path.join(log_dir, "app.log")
        
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # --- Logger de Auditoría ---
        self.audit_logger = logging.getLogger('KDP_AUDIT')
        self.audit_logger.setLevel(logging.INFO)
        audit_log_file = os.path.join(self.base_dir, "logs", "audit.log")
        audit_handler = RotatingFileHandler(audit_log_file, maxBytes=1*1024*1024, backupCount=5, encoding='utf-8')
        audit_handler.setFormatter(formatter)
        self.audit_logger.addHandler(audit_handler)

    def create_ui(self):
        # 1. Menú Superior Profesional
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="📂 Abrir Carpeta de Descargas", command=lambda: self.open_folder(self.input_dir.get()))
        file_menu.add_command(label="📤 Abrir Carpeta de Salida", command=lambda: self.open_folder(self.output_dir.get()))
        file_menu.add_command(label="🧠 Abrir Base de Conocimiento", command=lambda: self.open_folder(os.path.join("knowledge", "manuals")))
        file_menu.add_separator()
        
        # Submenú Exportar KB
        export_kb_menu = Menu(file_menu, tearoff=0)
        export_kb_menu.add_command(label="📄 Exportar KB a PDF", command=lambda: self.export_knowledge_base('pdf'))
        export_kb_menu.add_command(label="🌐 Exportar KB a HTML", command=lambda: self.export_knowledge_base('html'))
        export_kb_menu.add_command(label="📦 Exportar KB (PDF + HTML)", command=lambda: self.export_knowledge_base('both'))
        export_kb_menu.add_separator()
        export_kb_menu.add_command(label="⚙️ Configuración...", command=self._show_export_settings)
        file_menu.add_cascade(label="📚 Exportar Base de Conocimiento", menu=export_kb_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="📤 Exportar Configuración UI", command=self.export_ui_config)
        file_menu.add_command(label="📥 Importar Configuración UI", command=self.import_ui_config)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Ver (Temas y Logs)
        view_menu = Menu(menubar, tearoff=0)
        
        # Submenú de Temas Avanzado
        theme_menu = Menu(view_menu, tearoff=0)
        theme_menu.add_command(label="🌑 Oscuro (Default)", command=lambda: self.apply_specific_theme("dark"))
        theme_menu.add_command(label="☀️ Claro (Light)", command=lambda: self.apply_specific_theme("light"))
        theme_menu.add_separator()
        theme_menu.add_command(label="🎨 Gestionar Temas Personalizados...", command=lambda: messagebox.showinfo("Próximamente", "El gestor de temas JSON estará disponible en la próxima actualización."))
        view_menu.add_cascade(label="🎨 Temas e Interfaz", menu=theme_menu)
        
        view_menu.add_command(label="🔄 Refrescar Lista de Archivos [F5]", command=self.refresh_file_list)
        view_menu.add_separator()
        view_menu.add_command(label="📜 Ver Archivo de Log", command=self.open_log_file)
        view_menu.add_command(label="🛡️ Ver Log de Auditoría", command=self.open_audit_log)
        view_menu.add_command(label="📂 Abrir Carpeta de Logs", command=lambda: self.open_folder("logs"))
        view_menu.add_command(label="🧹 Limpiar Consola", command=self.clear_console)
        menubar.add_cascade(label="Ver", menu=view_menu)

        # Menú Mantenimiento (Enterprise+)
        maint_menu = Menu(menubar, tearoff=0)
        maint_menu.add_command(label="🧹 Limpiar Caché de yt-dlp", command=self.clear_ytdlp_cache)
        maint_menu.add_command(label="♻️ Reiniciar Estado de Sesión", command=self.reset_session_state)
        maint_menu.add_command(label="🔧 Reparar Integridad de Base de Datos", command=self.repair_integrity)
        maint_menu.add_separator()
        maint_menu.add_command(label="🏥 Ejecutar Diagnóstico de Salud", command=self.run_health_check)
        maint_menu.add_command(label="📈 Ver Reporte de Categorías", command=self.generate_category_report)
        maint_menu.add_separator()
        maint_menu.add_command(label="📊 Analizar Manuales (Duplicados/Banal)", command=self.analyze_manuals)
        maint_menu.add_command(label="🔄 Fusionar Contenido en Manuales", command=self.merge_manual_content)
        maint_menu.add_separator()
        maint_menu.add_command(label="📋 Historial de Importaciones", command=self.show_import_history)
        menubar.add_cascade(label="Mantenimiento", menu=maint_menu)

        # Menú Herramientas
        self.tools_menu = Menu(menubar, tearoff=0)
        self.tools_menu.add_command(label="⭐ Gestionar Canales Favoritos", command=self.manage_channels)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="📊 Ver Tracker de Videos (JSON)", command=self.show_video_tracker_stats)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="🤖 Configurar IA (Claves)", command=self.configure_ai)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="🛡️ Configurar Filtros (Blacklist)", command=self.edit_blacklist)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="⌨️ Configurar Atajos de Teclado", command=self.show_keybindings_editor)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="🚨 BOTÓN DE PÁNICO (Backup Atómico)", command=self.panic_backup)
        self.tools_menu.add_command(label="♻️ Restaurar desde Punto de Control", command=self.restore_backup)
        if generate_role_graph:
            self.tools_menu.add_command(label="📊 Generar Mapa de Roles", command=self.generate_role_graph)
        if convert_md_to_pdf:
            self.tools_menu.add_command(label="📄 Exportar Manual a PDF Premium", command=self.convert_legal_to_pdf)
        menubar.add_cascade(label="Herramientas", menu=self.tools_menu)

        # Menú Ayuda
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="🌐 Buscar Actualizaciones", command=self.check_for_app_updates)
        help_menu.add_command(label="📖 Ver Manual de Usuario", command=self.open_readme)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ Acerca de KDP Master Suite", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        # 2. Contenedor Principal con Gradiente Simulado
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Encabezado Premium
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Logo o Ícono de App con efecto visual
        logo_label = ttk.Label(header_frame, text="💎", font=("Segoe UI", 28))
        logo_label.pack(side=tk.LEFT, padx=(0, 12))
        ToolTip(logo_label, "KDP Master Suite - Sistema de Gestión de Conocimiento")
        
        # Título principal
        title_label = ttk.Label(header_frame, text="KDP Master Suite", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)
        
        # Versión con mejor estilo
        version_label = ttk.Label(header_frame, text="Enterprise Gold Edition v2.4.3", 
                                  font=("Segoe UI", 10, "italic"), foreground="#94a3b8")
        version_label.pack(side=tk.LEFT, padx=12, pady=(12, 0))
        ToolTip(version_label, "Versión 2.4.3 - Edición Auditada y Optimizada")
        
        # Botón de Salud Rápido en la esquina con tooltip mejorado
        self.health_btn = ttk.Button(header_frame, text="🟢 SISTEMA OK", width=16, command=self.run_health_check)
        self.health_btn.pack(side=tk.RIGHT, padx=5)
        ToolTip(self.health_btn, "Click para ejecutar diagnóstico completo del sistema")

        # 3. Pestañas (Notebook) con iconos mejorados
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=8)

        # Pestaña 1: Descargar con icono mejorado
        self.tab_download = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_download, text=" 📥 Descargas ")
        self.setup_download_tab()

        # Pestaña 2: Procesar con icono mejorado
        self.tab_process = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_process, text=" ⚙️ Procesamiento ")
        self.setup_process_tab()

        # Pestaña 3: Analizar (Integración) con icono mejorado
        self.tab_analyze = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_analyze, text=" 🧠 Inteligencia ")
        self.setup_analyze_tab()

        # Pestaña 4: Búsqueda con icono mejorado
        self.tab_search = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_search, text=" 🔍 Búsqueda ")
        self.setup_search_tab()

        # Pestaña 5: Monitor de Canales (NUEVO)
        self.tab_channel_monitor = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_channel_monitor, text=" 📺 Monitor de Canales ")
        self.setup_channel_monitor_tab()

        # Pestaña 6: Dashboard Inteligente (NUEVO)
        self.tab_dashboard = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_dashboard, text=" 📊 Dashboard ")
        self.setup_dashboard_tab()

        # Pestaña 7: Programación Horaria (NUEVO v2.6.0)
        self.tab_schedule = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_schedule, text=" 📅 Programación ")
        self.setup_schedule_tab()
        
        # Pestaña 8: Configuración
        try:
            self.tab_settings = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.tab_settings, text=" ⚙️ Configuración ")
            self.setup_settings_tab()
        except Exception as e:
            print(f"Settings tab no disponible: {e}")

        # 4. Área de Consola Enterprise
        log_frame = ttk.LabelFrame(main_frame, text=" Terminal de Operaciones en Tiempo Real ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=7, state='disabled', 
                                                  font=('Consolas', 10), 
                                                  bg="#020617" if self.current_theme == "dark" else "#f8fafc",
                                                  fg="#10b981" if self.current_theme == "dark" else "#1e293b",
                                                  insertbackground="white",
                                                  padx=10, pady=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # 5. Barra de Estado (Diseño Premium)
        status_container = ttk.Frame(self.root, padding=(5, 2))
        status_container.pack(fill=tk.X, side=tk.BOTTOM)
        
        status_bar = ttk.Frame(status_container, relief=tk.FLAT, padding=5, style="Status.TFrame")
        status_bar.pack(fill=tk.X)
        
        # Separador visual superior de la barra de estado
        sep = ttk.Separator(status_container, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, side=tk.TOP)
        
        self.status_icon_label = ttk.Label(status_bar, text="🛡️", font=('Segoe UI', 11))
        self.status_icon_label.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(status_bar, textvariable=self.status_var, font=("Inter", 9, "bold")).pack(side=tk.LEFT)
        
        # Indicador de videos nuevos detectados
        self.new_videos_label = ttk.Label(status_bar, textvariable=self.new_videos_var, 
                                          font=("Inter", 9, "bold"), foreground="#f59e0b")
        self.new_videos_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Indicador de canales activos
        self.active_channels_label = ttk.Label(status_bar, textvariable=self.active_channels_var, 
                                               font=("Inter", 9), foreground="#64748b")
        self.active_channels_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Indicadores a la derecha
        self.progress_percent_label = ttk.Label(status_bar, text="0%", font=("Inter", 9, "bold"), foreground="#3b82f6")
        self.progress_percent_label.pack(side=tk.RIGHT, padx=(0, 15))
        
        self.disk_label = ttk.Label(status_bar, textvariable=self.disk_status_var, font=("Inter", 9))
        self.disk_label.pack(side=tk.RIGHT, padx=15)
        
        self.version_label = ttk.Label(status_bar, text="v2.4.3-GOLD", font=("Inter", 8), foreground="#64748b")
        self.version_label.pack(side=tk.RIGHT, padx=10)
        
        # Barra de progreso global sutil (Permanente)
        self.progress_bar = ttk.Progressbar(status_bar, orient=tk.HORIZONTAL, length=200, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(side=tk.RIGHT, padx=15)
        
        # Inicializar UI de cola
        self.download_queue = []
        self.update_queue_ui()

        # Atajos de teclado globales
        self.root.bind('<F1>', lambda e: self.open_readme())
        self.root.bind('<F5>', lambda e: self.refresh_file_list())
        self.root.bind('<Control-q>', lambda e: self.on_closing())

    def setup_download_tab(self):
        download_tab.setup_download_tab(self)
        
        # Panel de Videos Nuevos Detectados (único de gui_app.py)
        self.new_videos_frame = ttk.LabelFrame(self.tab_download, text=" 🔔 Videos Nuevos Detectados ", padding=10)
        self.new_videos_frame.pack(fill=tk.X, pady=(10, 10))
        
        self.new_videos_info = tk.Text(self.new_videos_frame, height=5, wrap=tk.WORD, 
                                        state=tk.DISABLED,
                                        font=("Consolas", 9),
                                        bg="#1e293b" if self.current_theme == "dark" else "#f0fdf4",
                                        fg="#10b981" if self.current_theme == "dark" else "#166534",
                                        borderwidth=0, highlightthickness=1,
                                        highlightbackground="#10b981" if self.current_theme == "dark" else "#22c55e")
        self.new_videos_info.pack(fill=tk.X, padx=5)
        
        nv_btn_frame = ttk.Frame(self.new_videos_frame)
        nv_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(nv_btn_frame, text="🔄 Escanear Ahora", command=self.manual_scan_new_videos, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(nv_btn_frame, text="📥 Descargar Transcripciones", command=self.download_all_new_transcriptions, width=25, style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(nv_btn_frame, text="📊 Ver Estadísticas", command=self.show_scan_stats, width=18).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(nv_btn_frame, textvariable=self.new_videos_count_var, 
                  font=("Segoe UI", 9, "bold"), foreground="#f59e0b").pack(side=tk.RIGHT, padx=10)
    
    # --- drop zone now uses Frame, no canvas functions needed ---
    def draw_dashed_border(self):
        pass

    def on_drop_zone_enter(self, event):
        pass

    def on_drop_zone_leave(self, event):
        pass

    def add_to_queue(self):
        from app.ui.tabs.download_tab import add_to_queue
        add_to_queue(self)

    def remove_from_queue(self):
        from app.ui.tabs.download_tab import remove_from_queue
        remove_from_queue(self)

    def clear_queue(self):
        from app.ui.tabs.download_tab import clear_queue
        clear_queue(self)

    def start_download(self):
        from app.ui.tabs.download_tab import start_download
        start_download(self)

    def toggle_pause_queue(self):
        from app.ui.tabs.download_tab import toggle_pause_queue
        toggle_pause_queue(self)

    def start_queue_download(self):
        from app.ui.tabs.download_tab import start_queue_download
        start_queue_download(self)

    def paste_from_clipboard(self):
        from app.ui.tabs.download_tab import paste_from_clipboard
        paste_from_clipboard(self)

    # --- Funcionalidades ---

    def setup_process_tab(self):
        process_tab.setup_process_tab(self)

    def setup_analyze_tab(self):
        if not self.integrator:
            ttk.Label(self.tab_analyze, text="❌ Módulo 'integrate_knowledge' no encontrado.", foreground="#ef4444", font=("Inter", 12, "bold")).pack(pady=40)
            return

        # Encabezado de Pestaña
        header = ttk.Frame(self.tab_analyze)
        header.pack(fill=tk.X, pady=10)
        ttk.Label(header, text="🧠 Centro de Inteligencia SynthLearn", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Panel de Acciones
        btn_frame = ttk.Frame(self.tab_analyze)
        btn_frame.pack(fill=tk.X, pady=10)
        
        intel_btn = ttk.Button(btn_frame, text="🧠 Integrar Todo el Conocimiento", command=self.run_analysis, style="Primary.TButton")
        intel_btn.pack(side=tk.LEFT, padx=5, ipady=5)
        ToolTip(intel_btn, "Escanea archivos procesados y los categoriza en el Manual Maestro")
        
        if self.html_gen:
            html_btn = ttk.Button(btn_frame, text="🌐 Exportar Índice Web Navegable", command=self.generate_html, style="Success.TButton")
            html_btn.pack(side=tk.LEFT, padx=5, ipady=5)
            ToolTip(html_btn, "Genera una interfaz HTML para navegar por la base de conocimiento")

        # Área de Reporte con Estilo Terminal
        report_frame = ttk.LabelFrame(self.tab_analyze, text=" 📊 Reporte de Integración Atmosférica ", padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.analysis_text = scrolledtext.ScrolledText(report_frame, height=15, font=('Consolas', 10),
                                                       bg="#020617" if self.current_theme == "dark" else "white",
                                                       fg="#34d399" if self.current_theme == "dark" else "#1e293b")
        self.analysis_text.pack(fill=tk.BOTH, expand=True)

    def setup_search_tab(self):
        # Header y Herramientas de Búsqueda
        search_main = ttk.Frame(self.tab_search, padding=15)
        search_main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(search_main)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(control_frame, text="🔍 Búsqueda Semántica Global:", font=("Inter", 11, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        
        entry = ttk.Entry(control_frame, textvariable=self.search_var, width=60, font=("Inter", 11))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry.bind('<Return>', lambda e: self.run_search())
        
        search_btn = ttk.Button(control_frame, text="🔍 EJECUTAR BÚSQUEDA", command=self.run_search, style="Primary.TButton")
        search_btn.pack(side=tk.LEFT, padx=10)
        
        # Resultados con mejor presentación
        results_frame = ttk.LabelFrame(search_main, text=" 📄 Fragmentos de Conocimiento Encontrados ", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.search_results = scrolledtext.ScrolledText(results_frame, height=15, font=('Inter', 10),
                                                        bg="#1e293b" if self.current_theme == "dark" else "white",
                                                        fg="#f1f5f9" if self.current_theme == "dark" else "#1e293b",
                                                        padx=15, pady=15, spacing1=5)
        self.search_results.pack(fill=tk.BOTH, expand=True)
        
        # Pie de página de búsqueda
        footer_search = ttk.Frame(search_main)
        footer_search.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(footer_search, text="Tip: Usa palabras clave como 'seguridad', 'procedimiento' o 'error' para filtrar el conocimiento.", 
                  font=("Inter", 8, "italic"), foreground="#94a3b8").pack(side=tk.LEFT)

    # --- Funcionalidades ---

    def run_first_time_wizard(self):
        """Asistente de configuración inicial."""
        win = tk.Toplevel(self.root)
        win.title("Bienvenido - Configuración Inicial")
        win.geometry("500x400")
        win.transient(self.root)
        win.grab_set()
        
        ttk.Label(win, text="¡Bienvenido a KDP Master Suite!", font=("Segoe UI", 14, "bold")).pack(pady=20)
        ttk.Label(win, text="Configuremos tus carpetas de trabajo por primera vez.", font=("Segoe UI", 10)).pack(pady=10)
        
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Carpeta de Descargas (Entrada):").pack(anchor=tk.W)
        e1 = ttk.Entry(frame, textvariable=self.input_dir)
        e1.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(frame, text="Seleccionar", command=lambda: self.input_dir.set(filedialog.askdirectory() or self.input_dir.get())).pack(anchor=tk.E)
        
        ttk.Label(frame, text="Carpeta de Procesados (Salida):").pack(anchor=tk.W)
        e2 = ttk.Entry(frame, textvariable=self.output_dir)
        e2.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(frame, text="Seleccionar", command=lambda: self.output_dir.set(filedialog.askdirectory() or self.output_dir.get())).pack(anchor=tk.E)
        
        def finish():
            self.validate_directories()
            self.save_config()
            win.destroy()
            messagebox.showinfo("Configuración", "¡Todo listo! Puedes empezar a usar la aplicación.")
            
        ttk.Button(win, text="Guardar y Empezar", command=finish).pack(pady=20)

    def open_folder(self, path):
        if not os.path.isabs(path):
            abs_path = os.path.abspath(os.path.join(self.base_dir, path))
        else:
            abs_path = path
            
        if os.path.exists(abs_path):
            if sys.platform == 'win32':
                os.startfile(abs_path)
            else:
                subprocess.Popen(['xdg-open', abs_path])
        else:
            messagebox.showerror("Error", f"La carpeta no existe:\n{abs_path}")

    # --- Delegación a process_tab.py ---
    def refresh_file_list(self):
        refresh_file_list(self)

    def start_processing(self):
        try:
            from app.ui.tabs.process_tab import start_processing
            start_processing(self)
        except ImportError:
            # Módulo no disponible — ejecución inline
                if not ProcessingService:
                    messagebox.showerror("Error Crítico", "El servicio de procesamiento no está disponible.")
                    return

                selected_items = self.tree.selection()
                if not selected_items:
                    messagebox.showwarning("Atención", "No hay archivos seleccionados para procesar.")
                    return

                files_to_process = [self.tree.item(item)['values'][0] for item in selected_items]

                self.progress_var.set(0)

                # --- Lógica de Servicio ---
                processing_service = ProcessingService()

                def log_to_gui(message, level='info'):
                    if level == 'error': self.logger.error(message)
                    else: self.logger.info(message)

                def update_progress(value):
                    self.progress_var.set(value)
                    if hasattr(self, 'progress_percent_label'):
                        self.progress_percent_label.config(text=f"{int(value)}%")
                    self.root.update_idletasks()
                # -------------------------

                def run():
                    count = processing_service.process_files(
                        input_dir=self.input_dir.get(),
                        output_dir=self.output_dir.get(),
                        files_to_process=files_to_process,
                        progress_callback=update_progress,
                        log_callback=log_to_gui
                    )
                    self.root.after(0, lambda: [
                        self.status_var.set("Proceso completado"),
                        messagebox.showinfo("Éxito", f"Proceso completado.\n{count} archivos generados en: {self.output_dir.get()}")
                    ])

                threading.Thread(target=run, daemon=True).start()


    def display_metadata(self, event=None):
        from app.ui.tabs.process_tab import display_metadata
        display_metadata(self, event)

    def browse_input(self):
        from app.ui.tabs.process_tab import browse_input
        browse_input(self)

    def browse_output(self):
        from app.ui.tabs.process_tab import browse_output
        browse_output(self)

    def delete_selected_file(self):
        from app.ui.tabs.process_tab import delete_selected_file
        delete_selected_file(self)

    def open_file_location(self):
        from app.ui.tabs.process_tab import open_file_location
        open_file_location(self)

    def retry_process_file(self, filename):
        from app.ui.tabs.process_tab import retry_process_file
        retry_process_file(self, filename)

    def select_all_files(self):
        if not hasattr(self, 'tree') or not self.tree:
            return
        self.tree.unbind('<<TreeviewSelect>>')
        self.tree.selection_remove(self.tree.selection())
        for item in self.tree.get_children():
            self.tree.selection_add(item)
        self.tree.bind('<<TreeviewSelect>>', self.display_metadata)

    # --- Schedule Tab Delegation ---
    def on_schedule_task_start(self, task):
        from app.ui.tabs.schedule_tab import on_schedule_task_start
        on_schedule_task_start(self, task)

    def on_schedule_task_complete(self, task, result):
        from app.ui.tabs.schedule_tab import on_schedule_task_complete
        on_schedule_task_complete(self, task, result)

    def on_schedule_task_error(self, task, error):
        from app.ui.tabs.schedule_tab import on_schedule_task_error
        on_schedule_task_error(self, task, error)

    def on_schedule_log(self, message, level='info'):
        from app.ui.tabs.schedule_tab import on_schedule_log
        on_schedule_log(self, message, level)

    def show_schedule_notification(self, title, message, type="info"):
        from app.ui.tabs.schedule_tab import show_schedule_notification
        show_schedule_notification(self, title, message, type)

    def on_schedule_task_double_click(self, event=None):
        """Maneja el doble-click en una tarea de la lista del scheduler.

        Llamado por schedule_tab._build_task_list al bindear '<Double-1>'.
        Intenta delegar al módulo schedule_tab; si no está disponible,
        muestra la información básica de la tarea seleccionada.
        """
        try:
            from app.ui.tabs.schedule_tab import on_schedule_task_double_click
            on_schedule_task_double_click(self, event)
        except ImportError:
            # Fallback: mostrar info básica de la tarea seleccionada
            try:
                if not hasattr(self, 'schedule_tree') or self.schedule_tree is None:
                    return
                selection = self.schedule_tree.selection()
                if not selection:
                    return
                item = self.schedule_tree.item(selection[0])
                values = item.get('values', [])
                task_id   = values[0] if len(values) > 0 else "—"
                task_name = values[1] if len(values) > 1 else "Sin nombre"
                task_status = values[2] if len(values) > 2 else "—"
                messagebox.showinfo(
                    "Tarea Programada",
                    f"Nombre : {task_name}\n"
                    f"ID     : {task_id}\n"
                    f"Estado : {task_status}\n\n"
                    "(Módulo schedule_tab no disponible para edición completa)"
                )
            except Exception as inner_e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"on_schedule_task_double_click fallback error: {inner_e}")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error en on_schedule_task_double_click: {e}")

    def create_new_schedule_task(self):
        from app.ui.tabs.schedule_tab import create_new_schedule_task
        create_new_schedule_task(self)

    def delete_selected_task(self):
        from app.ui.tabs.schedule_tab import delete_selected_task
        delete_selected_task(self)

    def run_task_now(self):
        from app.ui.tabs.schedule_tab import run_task_now
        run_task_now(self)

    def refresh_schedule_tree(self):
        from app.ui.tabs.schedule_tab import refresh_schedule_tree
        refresh_schedule_tree(self)

    def refresh_schedule_stats(self):
        from app.ui.tabs.schedule_tab import refresh_schedule_stats
        refresh_schedule_stats(self)

    def clear_schedule_log(self):
        from app.ui.tabs.schedule_tab import clear_schedule_log
        clear_schedule_log(self)

    def backup_data(self):
        """Crea un backup de la carpeta knowledge al cerrar."""
        source = os.path.join(self.base_dir, "knowledge")
        if not os.path.exists(source):
            return

        backup_dir = os.path.join(self.base_dir, "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_name = os.path.join(backup_dir, f"knowledge_backup_{timestamp}")
        
        try:
            shutil.make_archive(archive_name, 'zip', source)
            msg = f"Backup automático creado: {archive_name}.zip"
            self.logger.info(msg)
            self.audit_logger.info(msg)
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")



    def repair_integrity(self):
        if not self.integrator: return
        
        if messagebox.askyesno("Confirmar Reparación", "Esto recalculará las firmas de todos los archivos en la base de conocimiento. Úsalo si has editado archivos manualmente.\n¿Continuar?"):
            try:
                count = self.integrator.recalculate_all_checksums()
                msg = f"Reparación de integridad completada. Se actualizaron {count} firmas de archivos."
                messagebox.showinfo("Éxito", msg)
                self.audit_logger.info(msg)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo reparar la integridad: {e}")

    def edit_blacklist(self):
        """Abre una ventana para editar la lista negra de palabras."""
        win = tk.Toplevel(self.root)
        win.title("Configurar Lista Negra")
        win.geometry("400x500")
        
        ttk.Label(win, text="Ingresa palabras o frases a ignorar (una por línea):").pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(win, width=40, height=20)
        text_area.pack(padx=10, pady=5)
        text_area.insert("1.0", "\n".join(self.blacklist))
        
        def save():
            content = text_area.get("1.0", tk.END).strip()
            self.blacklist = [line.strip() for line in content.splitlines() if line.strip()]
            if self.integrator:
                self.integrator.update_blacklist(self.blacklist)
            messagebox.showinfo("Guardado", "Lista negra actualizada.")
            win.destroy()
            
        ttk.Button(win, text="Guardar Cambios", command=save).pack(pady=10)

    def _show_export_settings(self):
        """Muestra configuración de exportación de KB."""
        win = Toplevel(self.root)
        win.title("Configurar Exportación KB")
        win.geometry("400x350")
        win.transient(self.root)
        
        ttk.Label(win, text="Configuración de Exportación", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        settings_frame = ttk.LabelFrame(win, text="Opciones", padding=15)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        var_pdf = BooleanVar(value=False)
        var_auto = BooleanVar(value=False)
        var_split = BooleanVar(value=True)
        
        ttk.Checkbutton(settings_frame, text="Habilitar exportación PDF (requiere WeasyPrint)",
                     variable=var_pdf).pack(anchor=tk.W, pady=5)
        ttk.Checkbutton(settings_frame, text="Auto-exportar al cerrar aplicación",
                     variable=var_auto).pack(anchor=tk.W, pady=5)
        ttk.Checkbutton(settings_frame, text="Dividir archivo si >10MB por categoría",
                     variable=var_split).pack(anchor=tk.W, pady=5)
        
        ttk.Label(settings_frame, text="Formato por defecto:").pack(anchor=tk.W, pady=(15, 5))
        format_combo = ttk.Combobox(settings_frame, values=['HTML', 'PDF'], state='readonly', width=10)
        format_combo.set('HTML')
        format_combo.pack(anchor=tk.W)
        
        def save_settings():
            try:
                settings_path = Path(self.base_dir) / "dist" / "settings.json"
                if settings_path.exists():
                    settings = json.loads(settings_path.read_text(encoding='utf-8'))
                else:
                    settings = {}
                
                if 'export' not in settings:
                    settings['export'] = {}
                
                settings['export']['pdf_enabled'] = var_pdf.get()
                settings['export']['auto_export_on_exit'] = var_auto.get()
                settings['export']['split_if_gt_mb'] = 10 if var_split.get() else 0
                settings['export']['default_format'] = format_combo.get().lower()
                
                settings_path.write_text(json.dumps(settings, indent=2), encoding='utf-8')
                messagebox.showinfo("Guardado", "Configuración de exportación guardada.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
        
        ttk.Button(win, text="Guardar", command=save_settings).pack(pady=15)
        ttk.Button(win, text="Cancelar", command=win.destroy).pack(pady=5)

    # ===== MÉTODOS DEL MONITOR DE CANALES =====
    
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
        
        channel_entry = ttk.Entry(input_frame, textvariable=self.channel_url_var, 
                                 font=("Segoe UI", 10), width=40)
        channel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=4)
        
        ttk.Label(input_frame, text="📝 Nombre:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(15, 10))
        
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
        
        # ===== PANEL DE FILTROS POR PALABRAS CLAVE =====
        filter_panel = ttk.LabelFrame(right_panel, text=" 🔍 Filtros por Palabras Clave ", padding=10)
        filter_panel.pack(fill=tk.X, pady=(15, 0))
        
        # Toggle para habilitar/deshabilitar filtros
        ttk.Checkbutton(filter_panel, text="Habilitar filtros", 
                       variable=self.filter_enabled_var,
                       command=self.on_filter_toggle).pack(anchor=tk.W, pady=(0, 10))
        
        # Frame para palabras a incluir
        ttk.Label(filter_panel, text="Incluir (blanco):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        include_entry = ttk.Entry(filter_panel, textvariable=self.include_keywords_var, font=("Segoe UI", 9))
        include_entry.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(filter_panel, text="(Separadas por coma)", font=("Segoe UI", 8), foreground="#94a3b8").pack(anchor=tk.W)
        
        # Frame para palabras a excluir (lista negra)
        ttk.Label(filter_panel, text="Excluir (negro):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10, 0))
        exclude_entry = ttk.Entry(filter_panel, textvariable=self.exclude_keywords_var, font=("Segoe UI", 9))
        exclude_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(filter_panel, text="(Palabras que descartar automáticamente)", font=("Segoe UI", 8), foreground="#94a3b8").pack(anchor=tk.W)
        
        # Modo de comparación
        mode_frame = ttk.Frame(filter_panel)
        mode_frame.pack(fill=tk.X, pady=10)
        ttk.Label(mode_frame, text="Modo:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Cualquiera (OR)", variable=self.filter_mode_var, 
                       value="OR").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Todas (AND)", variable=self.filter_mode_var, 
                       value="AND").pack(side=tk.LEFT)
        
        # Botones de acción
        btn_frame = ttk.Frame(filter_panel)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="💾 Guardar", command=self.save_keyword_filter_config,
                  style="Primary.TButton").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="🧪 Probar", command=self.test_keyword_filter,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="🔄 Reset", command=self.reset_keyword_filter,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Etiqueta de estadísticas del filtro
        self.filter_stats_label = ttk.Label(filter_panel, text="", 
                                           font=("Segoe UI", 8), foreground="#94a3b8")
        self.filter_stats_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Cargar configuración existente del filtro
        self.load_keyword_filter_config()
        
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
        
        # Normalizar URL para comparación
        norm_url = normalize_youtube_url(url)
        
        # Añadir canal a DB (gestiona duplicados internamente)
        if self.db_manager:
            db_id = self.db_manager.add_channel(url, name)
            if db_id:
                # Si es un canal nuevo (o re-activado)
                self.log_monitor_activity(f"Canal añadido a DB: {name} ({norm_url})")
            else:
                ToastNotification.show(self.root, "Este canal ya existe en el monitor", "warning")
                return
        else:
            # Fallback a lista antigua si no hay DB
            if any(normalize_youtube_url(c['url']) == norm_url for c in self.channels):
                ToastNotification.show(self.root, "Este canal ya está en la lista", "warning")
                return
            new_channel = {"name": name, "url": url, "category": "General", "active": True, "date_added": datetime.now().strftime("%Y-%m-%d")}
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
        """Actualiza la lista visual de canales desde la base de datos."""
        if not hasattr(self, 'channel_tree'):
            return
            
        self.channel_tree.delete(*self.channel_tree.get_children())
        
        if self.db_manager:
            channels = self.db_manager.get_all_channels(active_only=False)
            for ch in channels:
                status = "✅ Activo" if ch.get("active", True) else "❌ Inactivo"
                # Obtener count real de videos
                v_list = self.db_manager.get_videos_by_channel(ch['id'])
                videos = str(len(v_list))
                
                self.channel_tree.insert("", tk.END, values=(
                    ch['channel_name'],
                    ch['channel_url'],
                    status,
                    videos
                ))
            count = len(channels)
        else:
            for channel in self.channels:
                status = "✅ Activo" if channel.get("active", True) else "❌ Inactivo"
                self.channel_tree.insert("", tk.END, values=(
                    channel['name'],
                    channel['url'],
                    status,
                    "0"
                ))
            count = len(self.channels)
        
        # Actualizar contador
        if hasattr(self, 'channel_count_label'):
            self.channel_count_label.config(text=f"{count} canal{'es' if count != 1 else ''}")

    def update_channel_stats(self):
        """Actualiza las estadísticas del header usando la base de datos."""
        if self.db_manager:
            stats = self.db_manager.get_statistics()
            channels = self.db_manager.get_all_channels(active_only=False)
            total = len(channels)
            active = stats.get('active_channels', 0)
            pending = stats.get('pending', 0)
            
            # Formatear última verificación
            last_checks = [c['last_checked'] for c in channels if c['last_checked']]
            last_check_str = max(last_checks).split('.')[0] if last_checks else "Nunca"
        else:
            total = len(self.channels)
            active = sum(1 for c in self.channels if c.get("active", True))
            pending = 0
            last_check_str = "Nunca"

        if hasattr(self, 'stat_total_channels'):
            self.stat_total_channels.set(str(total))
            self.stat_active_channels.set(str(active))
            self.stat_pending_videos.set(str(pending))
            self.stat_last_check.set(last_check_str)
        
        # Sincronizar contador de la pestaña si existe
        if hasattr(self, 'channel_count_label'):
            self.channel_count_label.config(text=f"{total} canal{'es' if total != 1 else ''}")
        
        # Actualizar estadísticas del filtro
        self.update_filter_stats()
    
    def load_keyword_filter_config(self):
        """Carga la configuración del filtro desde la base de datos."""
        if self.monitor_service:
            try:
                config = self.monitor_service.get_keyword_filter_config()
                if config:
                    self.filter_enabled_var.set(config.get('enabled', False))
                    
                    include = config.get('include_keywords', [])
                    exclude = config.get('exclude_keywords', [])
                    mode = config.get('mode', 'OR')
                    
                    self.include_keywords_var.set(", ".join(include))
                    self.exclude_keywords_var.set(", ".join(exclude))
                    self.filter_mode_var.set(mode)
            except Exception as e:
                print(f"Error cargando filtro: {e}")
        
        self.update_filter_stats()
    
    def save_keyword_filter_config(self):
        """Guarda la configuración del filtro en la base de datos."""
        include_str = self.include_keywords_var.get()
        exclude_str = self.exclude_keywords_var.get()
        
        include_keywords = [k.strip() for k in include_str.split(",") if k.strip()]
        exclude_keywords = [k.strip() for k in exclude_str.split(",") if k.strip()]
        mode = self.filter_mode_var.get()
        enabled = self.filter_enabled_var.get()
        
        if self.monitor_service:
            success = self.monitor_service.set_keyword_filter(
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
                mode=mode,
                enabled=enabled
            )
            
            if success:
                ToastNotification.show(self.root, "Filtro guardado correctamente", "success")
                self.log_monitor_activity(f"Filtro actualizado: enabled={enabled}, mode={mode}, include={include_keywords}, exclude={exclude_keywords}")
            else:
                ToastNotification.show(self.root, "Error al guardar filtro", "error")
        else:
            ToastNotification.show(self.root, "Monitor no disponible", "error")
        
        self.update_filter_stats()
    
    def on_filter_toggle(self):
        """Maneja el toggle de habilitación del filtro."""
        enabled = self.filter_enabled_var.get()
        self.log_monitor_activity(f"Filtro {'habilitado' if enabled else 'deshabilitado'}")
    
    def test_keyword_filter(self):
        """Prueba el filtro con un título de ejemplo."""
        test_title = self.include_keywords_var.get().split(",")[0].strip() if self.include_keywords_var.get() else "KDP tutorial"
        
        if self.monitor_service:
            result = self.monitor_service.test_keyword_filter(test_title)
            
            status = "✓ PROCESARÍA" if result['should_process'] else "✗ IGNORARÍA"
            reason = result['reason']
            
            self.log_monitor_activity(f"Prueba: '{test_title}' -> {status} ({reason})")
            ToastNotification.show(self.root, f"Prueba: '{test_title}' -> {status}", "info" if result['should_process'] else "warning")
    
    def reset_keyword_filter(self):
        """Resetea la configuración del filtro."""
        self.filter_enabled_var.set(False)
        self.include_keywords_var.set("")
        self.exclude_keywords_var.set("")
        self.filter_mode_var.set("OR")
        
        if self.monitor_service:
            self.monitor_service.set_keyword_filter(
                include_keywords=[],
                exclude_keywords=[],
                mode="OR",
                enabled=False
            )
        
        self.log_monitor_activity("Filtro reseteado a valores por defecto")
        ToastNotification.show(self.root, "Filtro reseteado", "info")
        self.update_filter_stats()
    
    def update_filter_stats(self):
        """Actualiza las estadísticas mostradas del filtro."""
        if hasattr(self, 'filter_stats_label') and self.monitor_service:
            try:
                filter_config = self.monitor_service.get_keyword_filter_config()
                if filter_config and filter_config.get('enabled'):
                    stats = self.db_manager.get_filter_statistics() if self.db_manager else {}
                    ignored = stats.get('total_ignored_videos', 0)
                    total = stats.get('total_videos', 0)
                    rate = stats.get('filter_rate', 0)
                    
                    self.filter_stats_label.config(
                        text=f"📊 {ignored} videos ignorados ({rate}% del total)"
                    )
                else:
                    self.filter_stats_label.config(text="Filtro deshabilitado")
            except Exception as e:
                self.filter_stats_label.config(text="")
        elif hasattr(self, 'filter_stats_label'):
            self.filter_stats_label.config(text="")
    
    def log_monitor_activity(self, message: str) -> None:
        """Escribe un mensaje en el log de actividad del monitor."""
        if not hasattr(self, 'monitor_log'):
            return
        timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        self.monitor_log.configure(state='normal')
        self.monitor_log.insert('end', log_msg)
        self.monitor_log.see('end')
        self.monitor_log.configure(state='disabled')

    def delete_selected_channel(self):
        """Elimina canales seleccionados con confirmación"""
        if not hasattr(self, 'channel_tree'):
            return
            
        selected = self.channel_tree.selection()
        if not selected:
            ToastNotification.show(self.root, "Selecciona al menos un canal", "warning")
            return
        
        count = len(selected)
        if not messagebox.askyesno("Confirmar", f"¿Eliminar {count} canal(es) seleccionado(s)?"):
            return
        
        # Obtener URLs de canales seleccionados o identificarlos
        for item in selected:
            values = self.channel_tree.item(item)['values']
            url = values[1]
            norm_url = normalize_youtube_url(url)
            
            if self.db_manager:
                channels = self.db_manager.get_all_channels(active_only=False)
                target = next((ch for ch in channels if normalize_youtube_url(ch['channel_url']) == norm_url), None)
                if target: self.db_manager.remove_channel(target['id'])
            else:
                self.channels = [c for c in self.channels if normalize_youtube_url(c['url']) != norm_url]
        
        if not self.db_manager: self.save_config()
        self.update_channel_combo()
        self.refresh_channel_list()
        self.update_channel_stats()
        
        ToastNotification.show(self.root, f"🗑️ {count} canal(es) eliminado(s)", "success")
        self.log_monitor_activity(f"{count} canales eliminados")

    def check_channels_now(self):
        """Fuerza verificación inmediata de canales usando el motor paralelo."""
        if not self.monitor_service:
            ToastNotification.show(self.root, "❌ Servicio de monitor no disponible", "error")
            return
            
        ToastNotification.show(self.root, "🔄 Verificación PARALELA iniciada...", "info")
        self.log_monitor_activity("Iniciando escaneo masivo de canales...")
        
        def run_check():
            try:
                new_count = self.monitor_service.check_for_new_videos_parallel()
                self.root.after(0, lambda: self.finish_check(new_count))
            except Exception as e:
                self.root.after(0, lambda: ToastNotification.show(self.root, f"Error: {e}", "error"))

        threading.Thread(target=run_check, daemon=True).start()

    def finish_check(self, count):
        self.update_channel_stats()
        self.refresh_channel_list()
        msg = f"✅ Escaneo completado. {count} videos nuevos." if count > 0 else "✅ Escaneo completado. Sin novedades."
        ToastNotification.show(self.root, msg, "success" if count > 0 else "info")
        self.log_monitor_activity(f"Verificación finalizada: {count} nuevos.")

    def toggle_monitor_service(self):
        """Activa/desactiva el servicio de monitoreo automático"""
        if not self.monitor_service:
            ToastNotification.show(self.root, "❌ Servicio no disponible", "error")
            return
        
        if self.monitor_service.is_monitoring():
            self.monitor_service.stop_monitoring()
            ToastNotification.show(self.root, "⏸️ Monitor detenido", "warning")
            self.log_monitor_activity("Monitor detenido manualmente")
        else:
            channels = self.db_manager.get_all_channels(active_only=True) if self.db_manager else []
            if not channels:
                ToastNotification.show(self.root, "⚠️ No hay canales activos para monitorear", "warning")
                return
            self.monitor_service.start_monitoring()
            ToastNotification.show(self.root, "▶️ Monitor iniciado", "success")
            self.log_monitor_activity(f"Monitor iniciado con {len(channels)} canal(es) activo(s)")

    def show_monitor_stats(self):
        """Muestra ventana con estadísticas detalladas"""
        if not self.db_manager:
            messagebox.showerror("Error", "Servicio de base de datos no disponible.")
            return

        stats = self.db_manager.get_global_stats()
        
        win = tk.Toplevel(self.root)
        win.title("Estadísticas del Monitor KDP")
        win.geometry("400x350")
        win.resizable(False, False)
        win.transient(self.root)
        
        main = ttk.Frame(win, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main, text="📊 Resumen de Operaciones", font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        # Grid para stats
        g = ttk.Frame(main)
        g.pack(fill=tk.X)
        
        def add_row(parent, row, label, value, color):
            ttk.Label(parent, text=label, font=("Segoe UI", 10)).grid(row=row, column=0, sticky=tk.W, pady=5)
            ttk.Label(parent, text=value, font=("Segoe UI", 10, "bold"), foreground=color).grid(row=row, column=1, sticky=tk.E, pady=5)

        add_row(g, 0, "Canales Registrados:", stats.get('total_channels', 0), "#3b82f6")
        add_row(g, 1, "Videos Procesados:", stats.get('total_videos', 0), "#10b981")
        add_row(g, 2, "Videos con Error:", stats.get('failed_videos', 0), "#ef4444")
        add_row(g, 3, "Última Sincronización:", stats.get('last_check', 'Nunca'), "#06b6d4")
        
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        ttk.Button(main, text="Cerrar", command=win.destroy).pack(pady=10)

    def setup_schedule_tab(self):
        schedule_tab.setup_schedule_tab(self)
    
    def setup_settings_tab(self):
        settings_tab.SettingsTab(self.tab_settings, self)

    def manage_channels(self):
        """Ventana para gestionar canales guardados (Versión Pro)."""
        win = tk.Toplevel(self.root)
        win.title("Gestor de Canales Pro")
        win.geometry("800x600")
        
        # --- Barra de Herramientas Superior (Búsqueda y Filtros) ---
        toolbar = ttk.Frame(win, padding=5)
        toolbar.pack(fill=tk.X)
        
        ttk.Label(toolbar, text="Buscar:").pack(side=tk.LEFT, padx=2)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar, text="Categoría:").pack(side=tk.LEFT, padx=2)
        cat_filter_var = tk.StringVar(value="Todas")
        if self.db_manager:
            channels_for_cats = self.db_manager.get_all_channels(active_only=False)
        else:
            channels_for_cats = self.channels
        categories = sorted(list(set(c.get("category", "General") for c in channels_for_cats)))
        cat_combo = ttk.Combobox(toolbar, textvariable=cat_filter_var, values=["Todas"] + categories, state="readonly", width=15)
        cat_combo.pack(side=tk.LEFT, padx=5)

        def deselect_all_tree():
            tree.selection_remove(tree.selection())
            on_tree_select(None)

        # Botones movidos a la IZQUIERDA para que no se corten en ventanas estrechas
        ttk.Button(toolbar, text="✅ Todo", width=6, command=lambda: select_all_tree()).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="❌ Ninguno", width=8, command=deselect_all_tree).pack(side=tk.LEFT, padx=2)

        sel_count_var = tk.StringVar(value="0 seleccionados")
        ttk.Label(toolbar, textvariable=sel_count_var).pack(side=tk.RIGHT, padx=10)
        
        # Contador total de favoritos movido a la derecha
        # Obtener count real inicial
        initial_total = 0
        if self.db_manager:
            initial_total = len(self.db_manager.get_all_channels(active_only=False))
        else:
            initial_total = len(self.channels)
            
        ttk.Label(toolbar, textvariable=self.total_fav_var, font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT, padx=10)
        
        # --- Lista Principal (Treeview) ---
        list_frame = ttk.Frame(win, padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name", "url", "category", "active", "last_checked")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
        
        tree.heading("name", text="Nombre")
        tree.heading("url", text="Handle / URL")
        tree.heading("category", text="Categoría")
        tree.heading("active", text="Activo")
        tree.heading("last_checked", text="Última Verif.")
        
        tree.column("name", width=220)
        tree.column("url", width=120)
        tree.column("category", width=100)
        tree.column("active", width=60, anchor="center")
        tree.column("last_checked", width=110, anchor="center")
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        tree.config(yscrollcommand=scrollbar.set)
        
        def select_all_tree(event=None):
            tree.selection_set(tree.get_children())
            on_tree_select(None)
            return "break"

        # Menú Contextual para Canales
        context_menu = Menu(win, tearoff=0)
        context_menu.add_command(label="✏️ Editar", command=lambda: edit())
        context_menu.add_command(label="⏯️ Activar/Desactivar", command=lambda: toggle_active())
        context_menu.add_separator()
        context_menu.add_command(label="✅ Seleccionar Todo", command=select_all_tree)
        context_menu.add_separator()
        context_menu.add_command(label="❌ Eliminar", command=lambda: delete())
        context_menu.add_command(label="⬇️ Enviar a Cola", command=lambda: send_selection_to_queue())
        
        tree.bind("<Control-a>", select_all_tree)
        
        def show_context_menu(event):
            if tree.selection():
                context_menu.post(event.x_root, event.y_root)
        
        tree.bind("<Button-3>", show_context_menu)

        def on_tree_select(event):
            count = len(tree.selection())
            sel_count_var.set(f"{count} seleccionados")

        def refresh_list():
            tree.delete(*tree.get_children())
            query = search_var.get().lower()
            cat_filter = cat_filter_var.get()
            
            # Obtener canales de DB o fallback a self.channels
            if self.db_manager:
                channels = self.db_manager.get_all_channels(active_only=False)
            else:
                channels = self.channels
                
            for c in channels:
                name = c.get('channel_name') or c.get('name', 'Sin nombre')
                url = c.get('channel_url') or c.get('url', '')
                
                if query and query not in name.lower() and query not in url.lower():
                    continue
                if cat_filter != "Todas" and c.get("category", "General") != cat_filter:
                    continue
                
                status = "✅ Sí" if c.get("active", True) else "❌ No"
                display_url = normalize_youtube_url(url)
                
                tree.insert("", tk.END, values=(name, display_url, c.get("category", "General"), status, c.get("last_checked", "-")))
            
            # Actualizar etiqueta de total en esta ventana
            self.total_fav_var.set(f"Total: {len(channels)}")

        search_var.trace("w", lambda *args: refresh_list())
        cat_combo.bind("<<ComboboxSelected>>", lambda e: refresh_list())
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        refresh_list()
            
        input_frame = ttk.LabelFrame(win, text=" Agregar / Editar Canal ", padding=10)
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="Nombre:").grid(row=0, column=0, padx=5)
        name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=name_var, width=20).grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="URL (@):").grid(row=0, column=2, padx=5)
        url_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=url_var, width=20).grid(row=0, column=3, padx=5)
        
        ttk.Label(input_frame, text="Categoría:").grid(row=0, column=4, padx=5)
        cat_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=cat_var, width=15).grid(row=0, column=5, padx=5)

        def add():
            name, url, category = name_var.get().strip(), url_var.get().strip(), cat_var.get().strip() or "General"
            if not name or not url:
                messagebox.showwarning("Faltan datos", "Nombre y URL son obligatorios.", parent=win)
                return

            # Normalizar URL antes de guardar
            norm_url = normalize_youtube_url(url)

            if self.db_manager:
                if self.db_manager.add_channel(url, name):
                    refresh_list()
                    # Nota: categry no está en DB actualmente, podríamos añadirlo después
                    name_var.set(""); url_var.set(""); cat_var.set("")
                else:
                    messagebox.showwarning("Duplicado", f"El canal {norm_url} ya está en el monitor.", parent=win)
            else:
                if any(normalize_youtube_url(c['url']) == norm_url for c in self.channels):
                    messagebox.showwarning("Duplicado", f"El canal {norm_url} ya está en tus favoritos.", parent=win)
                    return
                new_channel = {"name": name, "url": url, "category": category, "active": True, "date_added": datetime.now().strftime("%Y-%m-%d")}
                self.channels.append(new_channel)
                refresh_list()
                self.save_config()
                name_var.set(""); url_var.set(""); cat_var.set("")
            
            self.update_channel_stats()
        
        def delete():
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showinfo("Info", "Selecciona al menos un canal para eliminar.", parent=win)
                return
            
            if messagebox.askyesno("Confirmar", f"¿Eliminar {len(selected_items)} canal(es)?", parent=win):
                # Comparar usando URLs normalizadas o IDs por seguridad
                removed_count = 0
                for item_id in selected_items:
                    url = tree.item(item_id)['values'][1]
                    norm_url = normalize_youtube_url(url)
                    
                    if self.db_manager:
                        # Buscar ID por URL para eliminar de DB
                        channels = self.db_manager.get_all_channels(active_only=False)
                        target = next((ch for ch in channels if normalize_youtube_url(ch['channel_url']) == norm_url), None)
                        if target and self.db_manager.remove_channel(target['id']):
                            removed_count += 1
                    else:
                        self.channels = [c for c in self.channels if normalize_youtube_url(c['url']) not in norm_url]
                        removed_count += 1
                
                self.update_channel_combo()
                refresh_list()
                self.update_channel_stats()
                messagebox.showinfo("Éxito", f"Se eliminaron {removed_count} canales.", parent=win)
        
        def edit():
            selected_items = tree.selection()
            if len(selected_items) != 1:
                messagebox.showinfo("Info", "Selecciona solo un canal para editar.", parent=win)
                return

            vals = tree.item(selected_items[0])['values']
            
            if self.db_manager:
                channels = self.db_manager.get_all_channels(active_only=False)
                target_channel = next((c for c in channels if normalize_youtube_url(c['channel_url']) == vals[1]), None)
            else:
                target_channel = next((c for c in self.channels if c['url'] == vals[1]), None)
            
            if not target_channel:
                messagebox.showwarning("Error", "No se encontró el canal seleccionado.", parent=win)
                return
            
            edit_win = tk.Toplevel(win); edit_win.title("Editar Canal"); edit_win.geometry("300x250")
            
            ch_name = target_channel.get('channel_name') or target_channel.get('name', '')
            ch_url = target_channel.get('channel_url') or target_channel.get('url', '')
            ch_active = target_channel.get("active", True)
            
            ttk.Label(edit_win, text="Nombre:").pack(pady=5); e_name = tk.Entry(edit_win); e_name.insert(0, ch_name); e_name.pack()
            ttk.Label(edit_win, text="URL (@):").pack(pady=5); e_url = tk.Entry(edit_win); e_url.insert(0, ch_url); e_url.pack()
            ttk.Label(edit_win, text="Categoría:").pack(pady=5); e_cat = tk.Entry(edit_win); e_cat.insert(0, target_channel.get("category", "General")); e_cat.pack()
            active_var = tk.BooleanVar(value=ch_active); ttk.Checkbutton(edit_win, text="Activo", variable=active_var).pack(pady=5)
            
            def save_edit():
                new_url = normalize_youtube_url(e_url.get())
                new_name = e_name.get()
                new_active = active_var.get()
                
                if self.db_manager:
                    self.db_manager.update_channel(target_channel['id'], name=new_name, url=new_url, active=new_active)
                else:
                    target_channel.update({'name': new_name, 'url': new_url, 'category': e_cat.get(), 'active': new_active})
                    self.save_config()
                
                self.update_channel_combo(); refresh_list(); edit_win.destroy()
            
            ttk.Button(edit_win, text="Guardar Cambios", command=save_edit).pack(pady=10)
            
        def toggle_active():
            selected_items = tree.selection()
            if not selected_items: return
            
            for item_id in selected_items:
                url = tree.item(item_id)['values'][1]
                norm_url = normalize_youtube_url(url)
                
                if self.db_manager:
                    channels = self.db_manager.get_all_channels(active_only=False)
                    target = next((ch for ch in channels if normalize_youtube_url(ch['channel_url']) == norm_url), None)
                    if target:
                        self.db_manager.toggle_channel_active(target['id'], not target['active'])
                else:
                    for c in self.channels:
                        if normalize_youtube_url(c['url']) == norm_url:
                            c['active'] = not c.get('active', True)
            
            refresh_list()
            self.update_channel_stats()
            if not self.db_manager: self.save_config()

        def send_selection_to_queue():
            selected_items = tree.selection()
            if not selected_items: return
            
            added_count = 0
            already_in_queue = 0
            inactive_skipped = 0
            
            for item_id in selected_items:
                vals = tree.item(item_id)['values']
                if vals[3] == "❌ No": 
                    inactive_skipped += 1
                    continue
                url = vals[1]
                # Normalizar URL para asegurar consistencia en la cola
                norm_url = normalize_youtube_url(url)
                if norm_url.startswith("@"):
                    full_url = f"https://www.youtube.com/{norm_url}"
                else:
                    full_url = norm_url
                
                # Check for duplicates in queue using normalized URLs
                queue_normalized = [normalize_youtube_url(q) for q in self.download_queue]
                
                if norm_url not in queue_normalized:
                    self.download_queue.append(full_url)
                    added_count += 1
                else:
                    already_in_queue += 1
            
            self.update_queue_ui()
            msg = f"✅ Se añadieron {added_count} canales a la cola."
            details = []
            if already_in_queue > 0:
                details.append(f"{already_in_queue} ya estaban en la cola (o duplicados)")
            if inactive_skipped > 0:
                details.append(f"{inactive_skipped} omitidos por estar INACTIVOS")
            
            if details:
                msg += "\n\nDetalles:\n• " + "\n• ".join(details)
            
            messagebox.showinfo("Cola Inteligente", msg, parent=win)

        def export_csv(selected=False):
            items_to_export = tree.selection() if selected else tree.get_children()
            if not items_to_export:
                messagebox.showinfo("Info", "No hay canales seleccionados para exportar." if selected else "No hay canales para exportar.")
                return
            
            f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if not f: return

            try:
                with open(f, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Name", "URL", "Category", "Active", "DateAdded"])
                    urls_to_export = {tree.item(item_id)['values'][1] for item_id in items_to_export}
                    
                    if self.db_manager:
                        channels = self.db_manager.get_all_channels(active_only=False)
                        for c in channels:
                            url = c.get('channel_url') or c.get('url', '')
                            if url in urls_to_export:
                                writer.writerow([
                                    c.get('channel_name') or c.get('name', ''),
                                    url,
                                    c.get("category", "General"),
                                    c.get("active", True),
                                    c.get("created_at", "")
                                ])
                    else:
                        for c in self.channels:
                            if c['url'] in urls_to_export:
                                writer.writerow([c['name'], c['url'], c.get("category", "General"), c.get("active", True), c.get("date_added", "")])
                messagebox.showinfo("Éxito", f"Se exportaron {len(urls_to_export)} canales.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")

        def import_csv():
            f = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            if not f: return
            try:
                added = 0
                skipped = 0
                with open(f, 'r', encoding='utf-8-sig') as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader, None)
                    
                    for row in reader:
                        if not row or not row[0].strip():
                            continue
                        
                        name = None
                        url = None
                        
                        if len(row) >= 2:
                            name = row[0].strip()
                            url = normalize_youtube_url(row[1].strip())
                        elif len(row) == 1:
                            linea = row[0].strip()
                            if ' - ' in linea:
                                partes = linea.split(' - ', 1)
                                handle = partes[0].strip()
                                name = partes[1].strip()
                                if not handle.startswith('@'):
                                    handle = '@' + handle
                                url = handle
                            else:
                                handle = linea.strip()
                                if not handle.startswith('@'):
                                    handle = '@' + handle
                                url = handle
                                name = handle
                        
                        if not name or not url:
                            skipped += 1
                            continue

                        if self.db_manager:
                            result = self.db_manager.add_channel(url, name)
                            if result:
                                added += 1
                            else:
                                skipped += 1
                        else:
                            current_urls = {normalize_youtube_url(c['url']) for c in self.channels}
                            if normalize_youtube_url(url) not in current_urls:
                                self.channels.append({"name": name, "url": url, "category": row[2] if len(row) > 2 else "General", "active": row[3].lower() == 'true' if len(row) > 3 else True, "date_added": row[4] if len(row) > 4 else datetime.now().strftime("%Y-%m-%d")})
                                added += 1
                            else:
                                skipped += 1
                self.update_channel_combo(); refresh_list(); self.save_config()
                msg = f"Se importaron {added} canales nuevos."
                if skipped > 0:
                    msg += f"\n({skipped} omitidos por ser duplicados)"
                messagebox.showinfo("Éxito", msg)
                
                if self.db_manager:
                    self.db_manager.log_import(
                        source_file=os.path.basename(f),
                        total=added + skipped,
                        new_count=added,
                        duplicates=skipped,
                        failed=0
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Error importando: {e}")

        def clean_duplicates():
            """Elimina entradas duplicadas basadas en la URL normalizada."""
            if not self.db_manager:
                original_count = len(self.channels)
                seen_urls = set()
                unique_channels = []
                for c in self.channels:
                    norm_url = normalize_youtube_url(c['url'])
                    if norm_url not in seen_urls:
                        seen_urls.add(norm_url)
                        unique_channels.append(c)
                self.channels = unique_channels
                removed = original_count - len(self.channels)
                if removed > 0:
                    self.save_config()
            else:
                # La DB ya previene duplicados en add_channel, pero si hay inconsistencias por normalización manual:
                channels = self.db_manager.get_all_channels(active_only=False)
                seen_urls = set()
                removed = 0
                for ch in channels:
                    norm_url = normalize_youtube_url(ch['channel_url'])
                    if norm_url in seen_urls:
                        self.db_manager.remove_channel(ch['id'])
                        removed += 1
                    else:
                        seen_urls.add(norm_url)
            
            if removed > 0:
                refresh_list()
                self.update_channel_combo()
                self.update_channel_stats()
                messagebox.showinfo("Limpieza", f"Se eliminaron {removed} canales duplicados.")
            else:
                messagebox.showinfo("Limpieza", "No se encontraron duplicados.")

        btn_frame = ttk.Frame(win, padding=5)
        btn_frame.pack(fill=tk.X)
        b_add = ttk.Button(btn_frame, text="➕ Agregar", command=add)
        b_add.pack(side=tk.LEFT, padx=5)
        ToolTip(b_add, "Agrega el canal actual a tus favoritos")

        b_edit = ttk.Button(btn_frame, text="✏️ Editar", command=edit)
        b_edit.pack(side=tk.LEFT, padx=5)
        ToolTip(b_edit, "Edita los detalles del canal seleccionado")

        b_toggle = ttk.Button(btn_frame, text="⏯️ Activar/Desactivar", command=toggle_active)
        b_toggle.pack(side=tk.LEFT, padx=5)
        ToolTip(b_toggle, "Cambia el estado de monitoreo del canal")

        b_del = ttk.Button(btn_frame, text="❌ Eliminar", command=delete)
        b_del.pack(side=tk.LEFT, padx=5)
        ToolTip(b_del, "Elimina el canal de favoritos")

        b_clean = ttk.Button(btn_frame, text="🧹 Limpiar Duplicados", command=clean_duplicates)
        b_clean.pack(side=tk.LEFT, padx=5)
        ToolTip(b_clean, "Elimina canales duplicados basándose en la URL normalizada")

        b_queue = ttk.Button(btn_frame, text="⬇️ Enviar a Cola", command=send_selection_to_queue, style="Primary.TButton")
        b_queue.pack(side=tk.RIGHT, padx=5)
        ToolTip(b_queue, "Envía los canales seleccionados y activos a la cola de descarga")
        
        io_frame = ttk.Frame(win, padding=10)
        io_frame.pack(fill=tk.X)
        ttk.Button(io_frame, text="📤 Exportar Todo", command=lambda: export_csv(False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="📤 Exportar Selección", command=lambda: export_csv(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="📥 Importar CSV", command=import_csv).pack(side=tk.LEFT, padx=5)
        
        refresh_list()

    def on_compact_mode_change(self, is_compact):
        """Callback ejecutado cuando cambia el modo compacto."""
        if is_compact:
            # Modo Compacto: Ocultar textos no esenciales, reducir paddings
            self.style.configure("TButton", padding=(5, 2))
            self.style.configure("Treeview", rowheight=25)
            # Podrías ocultar etiquetas de pestañas si tuvieras iconos, etc.
            # ToastNotification.show(self.root, "Modo Compacto Activado", "info")
        else:
            # Modo Normal: Restaurar estilos
            self.style.configure("TButton", padding=(12, 8))
            self.style.configure("Treeview", rowheight=35)
            # ToastNotification.show(self.root, "Modo Normal Restaurado", "info")

    def show_keybindings_editor(self):
        """Muestra una ventana para editar los atajos de teclado."""
        if not self.binding_manager:
            messagebox.showinfo("Error", "El gestor de atajos no está disponible.")
            return
            
        editor = tk.Toplevel(self.root)
        editor.title("Configurar Atajos de Teclado")
        editor.geometry("500x400")
        
        ttk.Label(editor, text="Selecciona una acción y pulsa 'Editar' para cambiar la tecla.", 
                 padding=10).pack(fill=tk.X)
        
        # Lista de atajos
        columns = ("action", "key")
        tree = ttk.Treeview(editor, columns=columns, show="headings", height=10)
        tree.heading("action", text="Acción")
        tree.heading("key", text="Combinación de Teclas")
        tree.column("action", width=200)
        tree.column("key", width=200)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def refresh_bindings():
            tree.delete(*tree.get_children())
            for action, key in self.binding_manager.bindings.items():
                tree.insert("", tk.END, values=(action, key))
                
        refresh_bindings()
        
        def edit_binding():
            selected = tree.selection()
            if not selected: return
            
            action = tree.item(selected[0])['values'][0]
            
            # Diálogo de captura
            capture_win = tk.Toplevel(editor)
            capture_win.title(f"Editando: {action}")
            capture_win.geometry("300x150")
            
            lbl = ttk.Label(capture_win, text="Pulsa la nueva combinación de teclas...", padding=20)
            lbl.pack()
            
            def on_key(event):
                # Lógica simple para construir secuencia (se puede mejorar)
                keysym = event.keysym
                state = event.state
                
                # Modificadores
                parts = []
                if state & 0x4: parts.append("Control")
                if state & 0x1: parts.append("Shift")
                if state & 0x20000: parts.append("Alt") # Alt gr/option depending on OS
                
                # Ignorar teclas modificadoras solas
                if keysym in ("Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"):
                    return
                
                parts.append(keysym)
                new_seq = f"<{'-'.join(parts)}>"
                
                self.binding_manager.rebind(action, new_seq)
                refresh_bindings()
                capture_win.destroy()
                
            capture_win.bind("<Key>", on_key)
            capture_win.focus_set()
            
        btn_frame = ttk.Frame(editor, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="✏️ Editar Seleccionado", command=edit_binding).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Listo", command=editor.destroy).pack(side=tk.RIGHT)

    def export_ui_config(self):
        """Exporta la configuración actual de UI (temas, atajos) a un archivo ZIP."""
        f = filedialog.asksaveasfilename(defaultextension=".zip", 
                                       filetypes=[("KDP UI Config", "*.zip")],
                                       initialfile="kdp_ui_config.zip")
        if not f: return
        
        try:
            with zipfile.ZipFile(f, 'w') as zf:
                # Include settings.json
                if os.path.exists(self.config_file):
                    zf.write(self.config_file, "settings.json")
                
                # Include keybindings.json
                bindings_path = "keybindings.json"
                if os.path.exists(bindings_path):
                    zf.write(bindings_path, bindings_path)
                    
                # Include themes directory
                if os.path.exists("themes"):
                    for root, dirs, files in os.walk("themes"):
                        for file in files:
                            zf.write(os.path.join(root, file), 
                                     os.path.relpath(os.path.join(root, file), "."))
                                     
            messagebox.showinfo("Éxito", f"Configuración exportada a:\n{f}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar configuración: {e}")

    def import_ui_config(self):
        """Importa una configuración de UI desde un archivo ZIP."""
        f = filedialog.askopenfilename(filetypes=[("KDP UI Config", "*.zip")])
        if not f: return
        
        if not messagebox.askyesno("Confirmar Importación", 
                                  "Esto sobrescribirá tu configuración actual y reiniciará la aplicación.\n¿Deseas continuar?"):
            return
            
        try:
            with zipfile.ZipFile(f, 'r') as zf:
                # Validate contents
                safe_files = ["settings.json", "keybindings.json"]
                has_valid_content = False
                for member in zf.namelist():
                    if member in safe_files or member.startswith("themes/"):
                        has_valid_content = True
                        break
                
                if not has_valid_content:
                    messagebox.showwarning("Archivo Inválido", "El archivo no parece ser una configuración válida.")
                    return
                
                # Extraer solo archivos seguros
                for member in zf.infolist():
                    if member.filename in safe_files or member.filename.startswith("themes/"):
                        # Sanitizar path para prevenir traversal
                        safe_name = os.path.basename(member.filename)
                        if safe_name and not safe_name.startswith("..") and "/" not in safe_name:
                            member.filename = safe_name
                            zf.extract(member, ".")
                
            messagebox.showinfo("Éxito", "Configuración importada correctamente.\nLa aplicación se cerrará ahora para aplicar los cambios.")
            self.root.destroy()
            sys.exit() # Force exit to restart manually by user or script
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al importar configuración: {e}")

    def update_channel_combo(self):
        """Actualiza la lista desplegable con los canales guardados desde la base de datos."""
        if self.db_manager:
            channels = self.db_manager.get_all_channels(active_only=True)
            names = [ch['channel_name'] for ch in channels]
        else:
            names = [c['name'] for c in self.channels]
        
        if hasattr(self, 'channel_combo'):
            self.channel_combo['values'] = names



    def generate_role_graph(self):
        if not generate_role_graph: return
        try:
            self.status_var.set("Generando gráfico...")
            self.root.update()
            success, msg = generate_role_graph.generate_graph()
            if success:
                messagebox.showinfo("Éxito", msg)
                self.open_folder(os.path.dirname(msg))
            else:
                messagebox.showerror("Error", msg)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al generar gráfico: {e}")
        finally:
            self.status_var.set("Listo")

    def convert_legal_to_pdf(self):
        if not convert_md_to_pdf: 
            messagebox.showwarning("Función No Disponible", "La exportación a PDF requiere librerías del sistema no instaladas (WeasyPrint/GTK).\nPor favor use la exportación Markdown por ahora.")
            return
        try:
            self.status_var.set("Convirtiendo a PDF...")
            self.root.update()
            
            legal_manual = os.path.join(self.base_dir, "knowledge", "manuals", "MANUAL de LEGALIDAD.md")
            output_pdf = os.path.join(self.base_dir, "outputs", "reports", "MANUAL_DE_LEGALIDAD.pdf")
            
            success, msg = convert_md_to_pdf(legal_manual, output_pdf)
            
            if success:
                messagebox.showinfo("Éxito", msg)
                self.open_folder(os.path.dirname(msg))
            else:
                messagebox.showerror("Error", msg)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al convertir a PDF: {e}")
        finally:
            self.status_var.set("Listo")

    def export_knowledge_base(self, format_type=None):
        if format_type is None:
            dialog = Toplevel(self.root)
            dialog.title("Exportar Base de Conocimiento")
            dialog.geometry("300x180")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Selecciona el formato de exportación:",
                    font=('Segoe UI', 11)).pack(pady=20)
            
            def do_export(fmt):
                dialog.destroy()
                self._run_kb_export(fmt)
            
            ttk.Button(dialog, text="📄 Exportar a HTML", 
                      command=lambda: do_export('html')).pack(fill=tk.X, padx=40, pady=5)
            ttk.Button(dialog, text="📑 Exportar a PDF", 
                      command=lambda: do_export('pdf')).pack(fill=tk.X, padx=40, pady=5)
            ttk.Button(dialog, text="📦 Exportar Ambos", 
                      command=lambda: do_export('both')).pack(fill=tk.X, padx=40, pady=5)
            ttk.Button(dialog, text="Cancelar", 
                      command=dialog.destroy).pack(pady=15)
            return
        
        self._run_kb_export(format_type)
    
    def _run_kb_export(self, format_type):
        try:
            from app.services.kb_exporter import KBExporter, export_kb
        except ImportError:
            try:
                from kb_exporter import KBExporter, export_kb
                from export_audit import ExportAuditLogger
            except ImportError:
                messagebox.showerror("Error", "Módulo de exportación no encontrado.")
                return
        
        self.status_var.set("Exportando Base de Conocimiento...")
        
        def export_task():
            try:
                formats = ['html'] if format_type == 'html' else ['pdf', 'html'] if format_type == 'both' else ['pdf']
                results = []
                
                for fmt in formats:
                    result = export_kb(fmt)
                    results.append(result)
                    
                    if result.success:
                        try:
                            audit = ExportAuditLogger()
                            audit.log_export(
                                format=result.format,
                                categories=[],
                                entries_count=result.entries_count,
                                file_size_bytes=result.file_size_bytes,
                                content_hash=result.content_hash or '',
                                output_path=result.output_path,
                                warnings=result.warnings
                            )
                        except Exception as audit_err:
                            logging.warning(f"Audit log failed: {audit_err}")
                
                html_result = next((r for r in results if r.format == 'html'), results[0])
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Exportación Completada",
                    f"Entradas: {html_result.entries_count}\n"
                    f"Categorías: {html_result.categories_count}\n"
                    f"Archivo: {html_result.output_path}"
                ))
                self.root.after(0, lambda: self.open_folder(str(Path(html_result.output_path).parent)))
                
            except Exception as e:
                logging.error(f"Export error: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error exportando KB: {e}"))
            finally:
                self.root.after(0, lambda: self.status_var.set("Listo"))
        
        threading.Thread(target=export_task, daemon=True).start()

    def analyze_manuals(self):
        """Analiza los 3 manuales en busca de contenido duplicado y banal."""
        try:
            from modules.manual_analyzer import ManualAnalyzer
        except ImportError:
            try:
                ManualAnalyzer = manual_analyzer.ManualAnalyzer
            except ImportError:
                messagebox.showerror("Error", "Módulo de análisis de manuales no encontrado.")
                return
        
        self.log("[📊] Iniciando análisis de manuales...")
        
        def analysis_task():
            try:
                analyzer = ManualAnalyzer(self.base_dir)
                analysis = analyzer.analyze_all_manuals()
                
                report_path = analyzer.save_report(analysis)
                json_path = analyzer.save_analysis_json(analysis)
                
                summary = analysis["summary"]
                
                self.root.after(0, lambda: self._show_analysis_results(summary, report_path, json_path, analysis))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error analizando manuales: {e}"))
                self.log(f"[❌] Error en análisis de manuales: {e}")
        
        threading.Thread(target=analysis_task, daemon=True).start()
    
    def _show_analysis_results(self, summary, report_path, json_path, analysis):
        """Muestra los resultados del análisis."""
        self.log(f"[📊] Análisis completado.")
        self.log(f"   Manuales: {summary['total_manuals']}")
        self.log(f"   Secciones totales: {summary['total_sections']}")
        self.log(f"   Duplicados: {summary['total_duplicates']}")
        self.log(f"   Banales: {summary['total_banal']}")
        self.log(f"   Score: {summary['health_score']}/100")
        self.log(f"   Reporte: {report_path}")
        
        health_emoji = "✅" if summary['health_score'] >= 80 else "⚠️" if summary['health_score'] >= 50 else "❌"
        
        msg = (
            f"{health_emoji} Score de Salud: {summary['health_score']}/100\n\n"
            f"📚 Manuales analizados: {summary['total_manuals']}\n"
            f"📝 Secciones totales: {summary['total_sections']}\n"
            f"🔁 Duplicados detectados: {summary['total_duplicates']}\n"
            f"📄 Secciones banales: {summary['total_banal']}\n\n"
            f"📊 Reporte MD: {report_path}\n"
            f"📋 Datos JSON: {json_path}"
        )
        
        if summary['total_duplicates'] > 0 or summary['total_banal'] > 0:
            msg += "\n\n⚠️ Se recomienda revisar el reporte para identificar las secciones problemáticas."
        
        if messagebox.askyesno("Análisis de Manuales", msg + "\n\n¿Abrir el reporte?"):
            self.open_folder(report_path)

    def merge_manual_content(self):
        """
        Sistema completo de relectura y fusión de manuales.
        Lee los 3 archivos, analiza contenido, detecta duplicados/banalidad,
        y permite agregar SOLO contenido nuevo sin borrar nada.
        """
        if not self.manual_merger:
            messagebox.showerror("Error", "Sistema de fusión de manuales no disponible.")
            return
        
        self.log("[🔄] Iniciando sistema de fusión de manuales...")
        
        win = tk.Toplevel(self.root)
        win.title("Fusión de Manuales - Agregar Contenido Nuevo")
        win.geometry("750x550")
        
        header = ttk.Label(win, text="📚 Sistema de Fusión de Manuales Protegidos", 
                          font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)
        
        info = ttk.Label(win, text="Lee, analiza y agrega SOLO contenido nuevo a los manuales.\nNUNCA se borra ni elimina contenido existente.",
                        justify=tk.CENTER, foreground="#64748b")
        info.pack(pady=5)
        
        stats_frame = ttk.LabelFrame(win, text=" Estado Actual de Manuales ", padding=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD, state=tk.DISABLED,
                            font=("Consolas", 9))
        stats_text.pack(fill=tk.BOTH, expand=True)
        
        def load_stats():
            report = self.manual_merger.full_analysis_report()
            stats_text.configure(state=tk.NORMAL)
            stats_text.delete("1.0", tk.END)
            stats_text.insert("1.0", report)
            stats_text.configure(state=tk.DISABLED)
        
        load_stats()
        
        input_frame = ttk.LabelFrame(win, text=" Agregar Contenido Nuevo ", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(input_frame, text="Manual destino:").grid(row=0, column=0, sticky=tk.W, pady=5)
        manual_var = tk.StringVar(value="LEGALIDAD")
        manual_combo = ttk.Combobox(input_frame, textvariable=manual_var, 
                                    values=["LEGALIDAD", "FORMULAS", "MATRIZ"],
                                    state="readonly", width=20)
        manual_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Fuente:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        source_var = tk.StringVar(value="Transcripción manual")
        source_entry = ttk.Entry(input_frame, textvariable=source_var, width=30)
        source_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        content_text = tk.Text(input_frame, height=12, wrap=tk.WORD, 
                              font=("Consolas", 9))
        content_text.grid(row=1, column=0, columnspan=4, sticky=tk.NSEW, pady=10)
        
        input_frame.columnconfigure(3, weight=1)
        input_frame.rowconfigure(1, weight=1)
        
        result_text = tk.Text(win, height=6, wrap=tk.WORD, state=tk.DISABLED,
                             font=("Consolas", 9))
        result_text.pack(fill=tk.X, padx=20, pady=5)
        
        def preview_content():
            content = content_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Aviso", "Ingresa contenido para previsualizar.")
                return
            
            manual_key = manual_var.get()
            analysis = self.manual_merger.analyze_new_content(manual_key, content)
            
            result_text.configure(state=tk.NORMAL)
            result_text.delete("1.0", tk.END)
            
            preview = f"📊 PREVISUALIZACIÓN PARA {self.manual_merger.PROTECTED_MANUALS[manual_key]}\n\n"
            preview += f"✅ Secciones que se AÑADIRÁN: {len(analysis['added'])}\n"
            for a in analysis['added']:
                preview += f"   • {a['header']} ({a['line_count']} líneas)\n"
            
            preview += f"\n⏭️ Duplicados que se OMITIRÁN: {len(analysis['skipped_duplicate'])}\n"
            for d in analysis['skipped_duplicate']:
                preview += f"   • {d['header']} - {d['reason']}\n"
            
            preview += f"\n📄 Banales que se OMITIRÁN: {len(analysis['skipped_banal'])}\n"
            for b in analysis['skipped_banal']:
                preview += f"   • {b['header']} - {b['reason']}\n"
            
            result_text.insert("1.0", preview)
            result_text.configure(state=tk.DISABLED)
        
        def execute_merge():
            content = content_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Aviso", "Ingresa contenido para fusionar.")
                return
            
            manual_key = manual_var.get()
            source = source_var.get().strip() or "Manual Merger"
            
            result = self.manual_merger.merge_new_content(manual_key, content, source=source)
            
            if "error" in result:
                messagebox.showerror("Error", result["error"])
                return
            
            result_text.configure(state=tk.NORMAL)
            result_text.delete("1.0", tk.END)
            result_text.insert("1.0", result.get("message", "Fusión completada."))
            result_text.configure(state=tk.DISABLED)
            
            self.log(f"[✅] Fusión: {result.get('message', 'OK')}")
            load_stats()
            content_text.delete("1.0", tk.END)
        
        def load_file_content():
            f = filedialog.askopenfilename(
                filetypes=[("Text/Markdown", "*.md *.txt *.text"), ("All files", "*.*")]
            )
            if not f:
                return
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                content_text.delete("1.0", tk.END)
                content_text.insert("1.0", content)
                self.log(f"[📂] Contenido cargado desde: {os.path.basename(f)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
        
        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="👁️ Previsualizar", command=preview_content).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 Cargar Archivo", command=load_file_content).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✅ Fusionar Contenido", command=execute_merge,
                  style="Success.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="🔄 Actualizar Stats", command=load_stats).pack(side=tk.RIGHT, padx=5)

    def show_video_tracker_stats(self):
        """Muestra estadísticas del tracker JSON de videos procesados."""
        if not self.video_tracker:
            messagebox.showinfo("Info", "Tracker de videos no disponible.")
            return
        
        stats = self.video_tracker.get_stats()
        
        msg = f"📊 TRACKER DE VIDEOS PROCESADOS (JSON Indestructible)\n\n"
        msg += f"Videos rastreados en total: {stats['total_videos_tracked']}\n"
        msg += f"Canales rastreados: {stats['total_channels_tracked']}\n"
        msg += f"Escaneos realizados: {stats['total_scans']}\n"
        msg += f"Tamaño del archivo: {stats['file_size_kb']} KB\n\n"
        
        s = stats['statistics']
        msg += f"📈 ESTADÍSTICAS ACUMULADAS:\n"
        msg += f"  Total escaneados: {s.get('total_scanned', 0)}\n"
        msg += f"  Nuevos detectados: {s.get('total_new', 0)}\n"
        msg += f"  Duplicados omitidos: {s.get('total_duplicates', 0)}\n"
        msg += f"  Descargados: {s.get('total_downloaded', 0)}\n"
        msg += f"  Fallidos: {s.get('total_failed', 0)}\n"
        
        if stats.get('last_scan'):
            ls = stats['last_scan']
            msg += f"\n🕐 ÚLTIMO ESCANEO:\n"
            msg += f"  Fecha: {ls.get('timestamp', 'N/A')}\n"
            msg += f"  Canales: {ls.get('channels_scanned', 0)}\n"
            msg += f"  Nuevos: {ls.get('new_videos_found', 0)}\n"
            msg += f"  Duración: {ls.get('duration_seconds', 0)}s\n"
        
        if messagebox.askyesno("Tracker de Videos", msg + "\n\n¿Abrir archivo JSON?"):
            tracker_path = self.video_tracker.tracker_file
            self.open_folder(str(tracker_path))

    def show_import_history(self):
        """Muestra historial de importaciones de canales."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Base de datos no disponible.")
            return
        
        history = self.db_manager.get_import_history()
        
        if not history:
            messagebox.showinfo("Historial", "No hay importaciones registradas aún.")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Historial de Importaciones")
        win.geometry("650x400")
        
        tree = ttk.Treeview(win, columns=("date", "source", "total", "new", "dup", "failed"), 
                           show="headings")
        tree.heading("date", text="Fecha")
        tree.heading("source", text="Archivo")
        tree.heading("total", text="Total")
        tree.heading("new", text="Nuevos")
        tree.heading("dup", text="Duplicados")
        tree.heading("failed", text="Fallidos")
        
        tree.column("date", width=140)
        tree.column("source", width=180)
        tree.column("total", width=70, anchor="center")
        tree.column("new", width=70, anchor="center")
        tree.column("dup", width=80, anchor="center")
        tree.column("failed", width=70, anchor="center")
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for h in history:
            tree.insert("", tk.END, values=(
                h.get('import_date', ''),
                h.get('source_file', ''),
                h.get('total_channels', 0),
                h.get('new_channels', 0),
                h.get('duplicate_channels', 0),
                h.get('failed_channels', 0)
            ))




    def generate_category_report(self):
        if not generate_category_report: return
        try:
            self.status_var.set("Generando reporte de categorías...")
            self.root.update()
            success, msg = generate_category_report.generate_report()
            if success:
                messagebox.showinfo("Éxito", msg)
                self.open_folder(os.path.dirname(msg))
            else:
                messagebox.showerror("Error", msg)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al generar el reporte: {e}")
        finally:
            self.status_var.set("Listo")

    def configure_ai(self):
        """Abre una ventana para configurar el proveedor de IA y la API Key."""
        win = tk.Toplevel(self.root)
        win.title("Configuración de IA Avanzada")
        win.geometry("400x250")
        win.transient(self.root)
        win.grab_set()

        frame = ttk.Frame(win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Proveedor de IA:").pack(anchor=tk.W)
        
        ai_provider_var = tk.StringVar(value=self.ai_provider)
        provider_combo = ttk.Combobox(frame, textvariable=ai_provider_var, values=["none", "openai", "gemini"], state="readonly")
        provider_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Clave API (API Key):").pack(anchor=tk.W)
        api_key_var = tk.StringVar(value=self.api_key)
        key_entry = ttk.Entry(frame, textvariable=api_key_var, show="*")
        key_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Prompt del Sistema (Instrucciones para la IA):").pack(anchor=tk.W)
        prompt_text = scrolledtext.ScrolledText(frame, height=5, width=40, font=('Segoe UI', 9))
        prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        prompt_text.insert("1.0", self.ai_system_prompt)

        def save_ai_config():
            self.ai_provider = ai_provider_var.get()
            self.api_key = api_key_var.get()
            self.ai_system_prompt = prompt_text.get("1.0", tk.END).strip()
            
            # Actualizar el integrador en vivo
            if self.integrator:
                self.integrator.ai_provider = self.ai_provider
                self.integrator.api_key = self.api_key
                self.integrator.system_prompt = self.ai_system_prompt
                
            self.save_config() # Guardar en settings.json
            messagebox.showinfo("Guardado", "Configuración de IA actualizada.", parent=win)
            win.destroy()

        ttk.Button(win, text="Guardar", command=save_ai_config).pack(pady=10)

    def schedule_daily_task(self):
        """Crea una tarea programada en Windows para ejecutar el monitor diariamente."""
        if sys.platform != 'win32':
            messagebox.showinfo("Info", "Esta función solo está disponible en Windows.")
            return
            
        exe_path = sys.executable
        # Si estamos congelados (exe), usamos el ejecutable actual
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            # Si es script, apuntamos a python y el script
            exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

        cmd = f'schtasks /create /tn "KDP_Master_Monitor" /tr "{exe_path} --monitor" /sc daily /st 03:00 /f'
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            messagebox.showinfo("Éxito", "Tarea programada creada.\nEl programa se ejecutará diariamente a las 03:00 AM.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"No se pudo crear la tarea programada:\n{e}")

    def save_config(self):
        encrypted_key = self.api_key
        if self.api_key and self.security:
            encrypted_key = self.security.encrypt(self.api_key)
        
        # Preservar configuraciones existentes como notifications
        existing_config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except:
                pass
        
        config = {
            "input_dir": self.input_dir.get(),
            "output_dir": self.output_dir.get(),
            "blacklist": self.blacklist,
            "channels": self.channels,
            "ai_provider": self.ai_provider,
            "ai_api_key": encrypted_key,
            "ai_system_prompt": self.ai_system_prompt,
            "download_queue": self.download_queue,
            "notifications": existing_config.get("notifications", {
                "enable_native": False,
                "enable_internal": True,
                "cooldown_minutes": 5,
                "summary_mode": False
            }),
            "dashboard": existing_config.get("dashboard", {
                "port": 8000,
                "host": "127.0.0.1",
                "db_path": "data/channel_monitor.db"
            })
        }
        try:
            temp_file = self.config_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, self.config_file)
        except Exception as e:
            try:
                self.logger.error(f"No se pudo guardar la configuración: {e}")
            except:
                pass

    def on_closing(self):
        """Procedimiento de cierre seguro Enterprise - minimiza a bandeja."""
        try:
            if self.queue_running:
                if not messagebox.askyesno("Saliendo", "Hay una descarga en curso. ¿Seguro que desea salir?"):
                    return
            
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.root.withdraw()
                self._run_tray_icon()
                self.status_var.set("Minimizado a bandeja - scheduler activo")
                return
            
            self.status_var.set("Cerrando sistema de forma segura...")
            self.root.update()
            
            # Realizar backup automático
            try:
                self.backup_data()
            except Exception as e:
                print(f"Error en backup al cerrar: {e}")
            
            try:
                self.save_config()
            except Exception as e:
                print(f"Error guardando config al cerrar: {e}")
            
            # Detener monitor si está activo
            if hasattr(self, 'monitor_service') and self.monitor_service:
                try:
                    self.monitor_service.stop_monitoring()
                except Exception:
                    pass
            
            # Detener scheduler si está activo
            if hasattr(self, 'schedule_manager') and self.schedule_manager:
                try:
                    self.schedule_manager.stop()
                except Exception:
                    pass
            
            # Detener icono de bandeja del sistema
            if hasattr(self, 'tray_icon') and self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass
                
            # Eliminar lock
            if os.path.exists(self.lock_file):
                try:
                    os.remove(self.lock_file)
                except Exception:
                    pass
        except Exception as e:
            try:
                log_dir = os.path.join(self.base_dir, "logs")
                os.makedirs(log_dir, exist_ok=True)
                with open(os.path.join(log_dir, "app.log"), "a", encoding="utf-8") as f:
                    f.write(f"Error al cerrar: {str(e)}\n")
            except Exception:
                print(f"Error en cierre: {e}")
        finally:
            try:
                self.root.destroy()
            except Exception:
                pass

    def validate_url_regex(self, url):
        # Regex para validar YouTube (Video, Playlist, Canal)
        youtube_regex = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
        return re.match(youtube_regex, url) is not None



    # --- Delegación a download_tab.py (ver arriba) ---

    def run_analysis(self):
        """Ejecuta el protocolo de integración en un hilo separado para no bloquear la UI."""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, "Iniciando Protocolo de Integración Multi-Thread...\n")
        
        out_path = self.output_dir.get()
        if not os.path.exists(out_path):
            self.analysis_text.insert(tk.END, "Error: Carpeta de salida no existe.\n")
            return

        files = [f for f in os.listdir(out_path) if f.endswith('.txt')]
        if not files:
            self.analysis_text.insert(tk.END, "No hay archivos .txt para integrar.\n")
            return

        def async_integration():
            for f in files:
                try:
                    with open(os.path.join(out_path, f), 'r', encoding='utf-8') as file:
                        content = file.read()
                        result = self.integrator.analyze_text(content, source_filename=f)
                        
                        def update_ui(file_name=f, res=result):
                            self.analysis_text.insert(tk.END, f"\n📄 Procesando: {file_name}\n")
                            for msg in res.get("integrated", []):
                                self.analysis_text.insert(tk.END, f"   ✅ {msg}\n")
                            for msg in res.get("duplicates", []):
                                self.analysis_text.insert(tk.END, f"   ⚠️ {msg}\n")
                            self.analysis_text.insert(tk.END, "-"*30 + "\n")
                            self.analysis_text.see(tk.END)
                        
                        self.root.after(0, update_ui)
                except Exception as e:
                    self.root.after(0, lambda ex=e, fn=f: self.logger.error(f"Error analizando {fn}: {ex}"))
            
            self.root.after(0, lambda: messagebox.showinfo("Integración Completa", "El protocolo de integración ha finalizado."))

        threading.Thread(target=async_integration, daemon=True).start()

    def generate_html(self):
        if not self.html_gen:
            return
        
        success, msg = self.html_gen.generate()
        if success:
            self.logger.info(f"Índice HTML generado: {msg}")
            messagebox.showinfo("Éxito", f"Índice generado correctamente.\n{msg}")
            self.open_folder(os.path.dirname(msg))
        else:
            self.logger.error(f"Error generando HTML: {msg}")
            messagebox.showerror("Error", msg)

    def run_search(self):
        query = self.search_var.get().strip()
        if not query:
            return
            
        self.search_results.delete(1.0, tk.END)
        self.search_results.insert(tk.END, f"Buscando '{query}' en archivos procesados...\n\n")
        
        # Búsqueda en SQLite (Base de Conocimiento)
        db_path = os.path.join(self.base_dir, "knowledge", "knowledge_base.db")
        found_count = 0
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT category, source, content, timestamp FROM knowledge_entries WHERE content LIKE ?", ('%' + query + '%',))
                rows = cursor.fetchall()
                
                for row in rows:
                    category, source, content, timestamp = row
                    found_count += 1
                    self.search_results.insert(tk.END, f"📂 Categoría: {category}\n")
                    self.search_results.insert(tk.END, f"🔗 Fuente: {source}\n")
                    self.search_results.insert(tk.END, f"📅 Fecha: {timestamp}\n")
                    # Mostrar un fragmento del contenido
                    start_idx = content.lower().find(query.lower())
                    snippet = content[max(0, start_idx-50):min(len(content), start_idx+150)].replace('\n', ' ')
                    self.search_results.insert(tk.END, f"📝 ...{snippet}...\n")
                    self.search_results.insert(tk.END, "-"*40 + "\n")
                
                conn.close()
            except Exception as e:
                self.logger.error(f"Error buscando en BD: {e}")
                self.search_results.insert(tk.END, f"Error en base de datos: {e}\n")
        
        # Búsqueda en archivos locales (PROCESADOS)
        out_path = self.output_dir.get()
        if os.path.exists(out_path):
             for f in os.listdir(out_path):
                if f.endswith('.txt'):
                    try:
                        path = os.path.join(out_path, f)
                        with open(path, 'r', encoding='utf-8') as file:
                            content = file.read()
                            if query.lower() in content.lower():
                                found_count += 1
                                self.search_results.insert(tk.END, f"📄 Archivo Procesado: {f}\n")
                                self.search_results.insert(tk.END, "-"*40 + "\n")
                    except Exception as e: pass
        
        # Búsqueda en RAW (transcripciones sin procesar)
        raw_path = self.input_dir.get()
        if os.path.exists(raw_path):
            for f in os.listdir(raw_path):
                if any(f.endswith(ext) for ext in ['.vtt', '.srt', '.txt']) and not f.startswith('CLEAN_'):
                    try:
                        path = os.path.join(raw_path, f)
                        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read()
                            if query.lower() in content.lower():
                                found_count += 1
                                self.search_results.insert(tk.END, f"📥 Transcripción Original: {f}\n")
                                self.search_results.insert(tk.END, "-"*40 + "\n")
                    except Exception as e: pass
        
        self.search_results.insert(tk.END, f"\nBúsqueda finalizada. {found_count} resultados encontrados.")

    def load_theme_preference(self):
        """Carga la preferencia de tema desde settings.json y la aplica."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    theme = cfg.get("theme", "dark")
                    self.current_theme = theme
                    if sv_ttk:
                        sv_ttk.set_theme(theme)
                        self.update_styles_for_theme(theme)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error cargando preferencia de tema: {e}")

    def apply_specific_theme(self, theme_name):
        """Aplica un tema específico usando el ThemeManager."""
        self.current_theme = theme_name
        
        # 1. Framework Avanzado
        if self.theme_manager:
            self.theme_manager.load_theme(theme_name)
        
        # 2. Base sv_ttk (si existe)
        if sv_ttk:
            try:
                sv_ttk.set_theme(theme_name)
            except:
                pass
                
        # 3. Estilos Legacy
        self.update_styles_for_theme(theme_name)
        
        # 4. Persistencia
        self.save_theme_preference(theme_name)
        
        # Notificación
        # ToastNotification.show(self.root, f"Tema cambiado a {theme_name.capitalize()}", "info")

    def toggle_theme(self):
        """Alterna entre tema claro y oscuro."""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_specific_theme(new_theme)

    def save_theme_preference(self, theme):
        try:
            cfg = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            cfg["theme"] = theme
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=4)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error guardando preferencia de tema: {e}")

    def update_styles_for_theme(self, theme):
        """Actualiza los estilos personalizados según el tema activo."""
        bg_color = "#1c1c1c" if theme == "dark" else "#f0f0f0"
        fg_color = "#ffffff" if theme == "dark" else "#2c3e50"
        self.root.configure(bg=bg_color)
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("Header.TLabel", foreground="#3498db" if theme == "dark" else "#2c3e50", background=bg_color)
        self.style.configure("TLabelframe", background=bg_color)
        self.style.configure("TLabelframe.Label", foreground=fg_color, background=bg_color)

    def panic_backup(self):
        """Crea un respaldo completo de emergencia del sistema."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"panic_backup_{timestamp}.zip"
            backup_path = os.path.join(self.base_dir, "backups", backup_name)
            
            if not os.path.exists(os.path.join(self.base_dir, "backups")):
                os.makedirs(os.path.join(self.base_dir, "backups"))

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for folder in ["knowledge", "data", "logs", "outputs"]:
                    folder_path = os.path.join(self.base_dir, folder)
                    if os.path.exists(folder_path):
                        for root, dirs, files in os.walk(folder_path):
                            for file in files:
                                zipf.write(os.path.join(root, file), 
                                           os.path.relpath(os.path.join(root, file), self.base_dir))
                
                # Archivos sueltos importantes
                for file in ["settings.json", ".env", "queue_state.json"]:
                    if os.path.exists(os.path.join(self.base_dir, file)):
                        zipf.write(os.path.join(self.base_dir, file), file)

            self.logger.info(f"PÁNICO: Backup total creado en {backup_path}")
            messagebox.showinfo("Botón de Pánico", f"Backup total completado con éxito:\n{backup_name}")
            self.audit_logger.info(f"Backup de pánico activado por el usuario. Archivo: {backup_name}")
        except Exception as e:
            self.logger.error(f"Error en backup de pánico: {e}")
            messagebox.showerror("Error", f"Fallo al crear el backup: {e}")

    def restore_backup(self):
        """Restaura un respaldo seleccionado por el usuario."""
        backup_file = filedialog.askopenfilename(
            initialdir=os.path.join(self.base_dir, "backups"),
            title="Seleccionar Backup para restaurar",
            filetypes=(("ZIP files", "*.zip"), ("all files", "*.*"))
        )
        if not backup_file:
            return

        if messagebox.askyesno("Confirmar Restauración", "Esto SOBREESCRIBIRÁ los datos actuales. ¿Está seguro?"):
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    for member in zipf.infolist():
                        safe_name = os.path.basename(member.filename)
                        if safe_name and not safe_name.startswith("..") and "/" not in safe_name:
                            member.filename = safe_name
                            zipf.extract(member, self.base_dir)
                
                self.logger.info(f"Sistema restaurado desde {backup_file}")
                messagebox.showinfo("Éxito", "Restauración completada. Se recomienda reiniciar la aplicación.")
                self.audit_logger.info(f"Restauración de sistema realizada desde: {backup_file}")
            except Exception as e:
                self.logger.error(f"Error restaurando backup: {e}")
                messagebox.showerror("Error", f"No se pudo restaurar el backup: {e}")

    # paste_from_clipboard delegada a download_tab.py (ver arriba)

    def toggle_monitor(self):
        """Activa/desactiva el modo vigilancia 24h."""
        if self.monitor_var.get():
            if not self.url_var.get().strip():
                self.monitor_var.set(False)
                messagebox.showwarning("URL requerida", "Ingresa una URL antes de activar el modo vigilancia.")
                return
            ToastNotification.show(self.root, "🔄 Modo vigilancia activado (24h)", "info")
            self.log("[🔄] Modo vigilancia activado. Próxima descarga en 24h.")
        else:
            if hasattr(self, '_monitor_timer_id'):
                self.root.after_cancel(self._monitor_timer_id)
            ToastNotification.show(self.root, "⏹️ Modo vigilancia desactivado", "info")
            self.log("[⏹️] Modo vigilancia desactivado.")

    def clear_ytdlp_cache(self):
        """Limpia la caché de yt-dlp para solucionar errores de descarga."""
        self.log("[*] Iniciando limpieza de caché de yt-dlp...")
        if messagebox.askyesno("Limpiar Caché", "¿Desea limpiar la caché de yt-dlp? Esto puede solucionar errores de 'HTTP 403 Forbidden'."):
            try:
                subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], check=True, capture_output=True)
                messagebox.showinfo("Éxito", "Caché de yt-dlp eliminada correctamente.")
                self.log("[+] Caché de yt-dlp eliminada con éxito.")
            except Exception as e:
                self.log(f"[-] Error limpiando caché: {e}")
                messagebox.showerror("Error", f"No se pudo limpiar la caché: {e}")

    # ==================== DAHSBOARD EXTENSION (v2.4) ====================
    
    def setup_dashboard_tab(self):
        """Configura la pestaña de Dashboard Web."""
        frame = ttk.Frame(self.tab_dashboard, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(frame, text="📊 Dashboard Web Remoto v2.4.2", font=("Segoe UI", 18, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="Monitorea el estado de tu sistema Enterprise Platinum desde cualquier dispositivo.", 
                 font=("Segoe UI", 11), foreground="gray").pack(pady=(0, 30))
        
        # Info Server
        info_frame = ttk.LabelFrame(frame, text=" Estado del Servidor ", padding=20)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        url_label = ttk.Label(info_frame, text="http://localhost:8000", 
                               font=("Consolas", 14, "bold"), foreground="#3b82f6", cursor="hand2")
        url_label.pack(pady=10)
        
        def get_dashboard_url():
            dashboard_config = self.settings.get("dashboard", {})
            port = dashboard_config.get("port", 8000)
            return f"http://127.0.0.1:{port}"
        
        url_label.bind("<Button-1>", lambda e: self.open_url(get_dashboard_url()))
        
        # Control Server
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        def toggle_server():
            if not hasattr(self, 'dashboard_process') or self.dashboard_process is None:
                dashboard_config = self.settings.get("dashboard", {})
                port = dashboard_config.get("port", 8000)
                db_path = dashboard_config.get("db_path", "data/channel_monitor.db")
                
                for attempt in range(5):
                    try:
                        self.dashboard_process = subprocess.Popen(
                            [sys_module.executable, "dashboard_server.py", "--port", str(port), "--db", db_path],
                            creationflags=subprocess.CREATE_NO_WINDOW if sys_module.platform == "win32" else 0
                        )
                        time.sleep(1)
                        
                        if self.dashboard_process.poll() is not None:
                            port += 1
                            self.dashboard_process = None
                            continue
                        
                        actual_port = port
                        btn_server.config(text="⏹️ Detener Servidor Web", style="Danger.TButton")
                        status_lbl.config(text=f"🟢 Servidor en http://127.0.0.1:{actual_port}", foreground="#10b981")
                        url_label.config(text=f"http://127.0.0.1:{actual_port}")
                        ToastNotification.show(self.root, f"Dashboard iniciado en puerto {actual_port}", "success")
                        break
                    except OSError:
                        port += 1
                        self.dashboard_process = None
                        continue
                else:
                    messagebox.showerror("Error", "No se pudo iniciar dashboard: puertos 8000-8004 ocupados")
            else:
                self.dashboard_process.terminate()
                self.dashboard_process = None
                btn_server.config(text="▶️ Iniciar Servidor Web", style="Success.TButton")
                status_lbl.config(text="⚫ Servidor Detenido", foreground="gray")
                url_label.config(text="http://localhost:8000")
                ToastNotification.show(self.root, "Dashboard Web Detenido", "info")

        btn_server = ttk.Button(btn_frame, text="▶️ Iniciar Servidor Web", command=toggle_server, style="Success.TButton", width=25)
        btn_server.pack(pady=5)
        
        status_lbl = ttk.Label(btn_frame, text="⚫ Servidor Detenido", font=("Segoe UI", 10))
        status_lbl.pack(pady=5)

    # ── Scheduler ───────────────────────────────────────────────────────────

    def toggle_scheduler(self):
        """Activa/desactiva el programador. Thread-safe."""
        try:
            self.scheduler_running = not self.scheduler_running
            estado = "🟢 ACTIVO" if self.scheduler_running else "🔴 INACTIVO"
            if hasattr(self, "logger"):
                self.logger.info(f"📅 Scheduler cambiado a: {estado}")
            else:
                print(f"📅 Scheduler cambiado a: {estado}")
            self.root.after(0, self._refresh_scheduler_ui)
        except Exception as e:
            msg = f"⚠️ Error en toggle_scheduler: {e}"
            (self.logger.error(msg) if hasattr(self, "logger") else print(msg))
            self.scheduler_running = False

    def _refresh_scheduler_ui(self):
        """Actualiza widgets del scheduler si existen (compatible con cualquier nombre)."""
        try:
            status_text = "🟢 ACTIVO" if self.scheduler_running else "🔴 INACTIVO"
            btn_text = "⏹ Detener" if self.scheduler_running else "▶ Iniciar"
            for var_name in ("schedule_status_var",):
                if hasattr(self, var_name):
                    getattr(self, var_name).set(status_text)
            for widget_name in ("schedule_btn", "btn_toggle_scheduler"):
                if hasattr(self, widget_name):
                    getattr(self, widget_name).configure(text=btn_text)
            for lbl_name in ("lbl_scheduler_status",):
                if hasattr(self, lbl_name):
                    getattr(self, lbl_name).configure(text=status_text)
        except Exception:
            pass

    def open_url(self, url):
        webbrowser.open(url)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = TranscriptionProcessorApp(root)
        root.mainloop()
    except Exception as e:
        # Manejo de errores global para que no se cierre silenciosamente
        try:
            error_msg = f"Ocurrió un error inesperado:\n{str(e)}\n\nDetalles:\n{traceback.format_exc()}"
            logging.error(error_msg)
            tkinter.messagebox.showerror("Error Crítico", error_msg)
        except:
            traceback.print_exc()
            print(f"Error Crítico: {e}")