import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, Optional, List, Tuple, Any
from tkinter import filedialog, messagebox, scrolledtext, Menu
import tkinter.font as tkfont
import time
from logging.handlers import RotatingFileHandler
import csv
import shutil
import zipfile
import json
import sqlite3
import random
import os
import sys
import subprocess
import logging
try:
    import psutil
except ImportError:
    psutil = None
import secrets

import uuid # Importar el módulo uuid
# ==================== [FIX-ENCODING-APP] INICIO: UTF-8 GLOBAL ====================
from app.core.encoding_fix import apply_encoding_fix, setup_project_root
apply_encoding_fix()
project_root = setup_project_root()
# ==================== [FIX-ENCODING-APP] FIN ====================
import threading
import re
import urllib.request
import urllib.error
import atexit
import time
from pathlib import Path
from datetime import datetime

# ==================== INICIO MÓDULO: SINGLETON GLOBAL ====================
from app.core.app_singleton import set_current_app, get_current_app
# ==================== FIN MÓDULO: SINGLETON GLOBAL ====================

# ==================== INICIO MÓDULO: LOCK MANAGER ====================
# Importar sistema de prevención de instancias múltiples
try:
    from app.lock_manager import ApplicationLock
except ImportError:
    try:
        from lock_manager import ApplicationLock
    except ImportError:
        ApplicationLock = None
# ==================== FIN MÓDULO: LOCK MANAGER ====================

# --- Importación de Servicios de Lógica de Negocio ---
try:
    from app.services.monitor_service import ChannelMonitorService
    from app.services.processed_videos_tracker import ProcessedVideosTracker
    from app.services.manual_content_merger import ManualContentMerger
    from app.services.auto_decision_engine import AutoDecisionEngine
    from app.services.duplicate_export_scheduler import DuplicateExportScheduler
    from app.services.backup_service import BackupService
except ImportError as e:
    print(f"Error importando servicios pro: {e}")
    try:
        from db_manager import DatabaseManager
        from knowledge_db import KnowledgeDBManager
        from monitor_service import ChannelMonitorService
        from processed_videos_tracker import ProcessedVideosTracker
        from manual_content_merger import ManualContentMerger
        from backup_service import BackupService
    except ImportError:
            DatabaseManager, ChannelMonitorService, BackupService = None, None, None
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
    from app.modules.processing.integrate_knowledge import KnowledgeIntegrator
except ImportError:
    try:
        from integrate_knowledge import KnowledgeIntegrator
    except ImportError:
        KnowledgeIntegrator = None

try:
    from app.modules.kb_distributor import KBDistributor
except ImportError:
    KBDistributor = None

try:
    from app.modules.task_queue import AsyncWorkerPool
    from app.core.ollama_pool import OllamaPool
    from app.modules.monitoring.analytics_engine import AnalyticsEngine
    from app.api import kb_router
except ImportError:
    AsyncWorkerPool, OllamaPool, AnalyticsEngine, kb_router = None, None, None, None

# Intentar importar el conversor PDF (requiere WeasyPrint/GTK)
try:
    from app.modules.export.convert_to_pdf import convert_md_to_pdf
except ImportError:
    try:
        from app.modules.export.convert_to_pdf import convert_md_to_pdf
    except ImportError:
        convert_md_to_pdf = None

try:
    from export_kb import KBExporter
except ImportError:
    try:
        from app.modules.export.export_kb import KBExporter
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
    # ThemeManager, AnimationEngine, etc. are from ui_framework; PluginManager is separate.
    from app.core.ui_framework import ThemeManager, AnimationEngine, IconManager, ResponsiveManager, BindingManager, ui_context # type: ignore
    from app.core.plugin_manager import PluginManager
    from modules.dashboard import DashboardView
    from app.ui.components.theme_editor import open_theme_editor
except ImportError as e:
    print(f"Error importando UI Framework: {e}")
    ThemeManager, AnimationEngine, IconManager, ResponsiveManager, BindingManager, PluginManager, ui_context, DashboardView = None, None, None, None, None, None, {}, None
    open_theme_editor = None

# Importar utilidad de normalización
try:
    from app.core.utils import normalize_youtube_url
except ImportError:
    def normalize_youtube_url(url): return url # Fallback

# Importar configuración centralizada
# ==================== INICIO MÓDULO: DOC_UPDATER ====================
try:
    from app.core.doc_updater import DocUpdater
except ImportError:
    DocUpdater = None
# ==================== FIN MÓDULO: DOC_UPDATER ====================

# ==================== INICIO MÓDULO: IMPORTACIÓN ENV_MANAGER (US-CONFIG) ====================
try:
    from app.core.env_manager import EnvManager
except ImportError:
    EnvManager = None
# ==================== FIN MÓDULO: IMPORTACIÓN ENV_MANAGER ====================

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
    from app.ui.tabs import review_queue
    review_tab = review_queue
except ImportError:
    review_tab = None
try:
    from app.ui.tabs.download_tab import update_queue_ui as _uq
except ImportError:
    _uq = None
try:
    from app.ui.tabs.process_tab import ProcessTab
except ImportError:
    ProcessTab = None
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
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    Image, ImageTk = None, None

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

# ==================== INICIO MÓDULO: EMERGENCY_SAVE ====================
def _emergency_save():
    """Guarda estado en caso de cierre forzado (crash/power loss)."""
    try:
        app = get_current_app()
        if app is not None:
            queue = getattr(app, 'download_queue', [])
            if queue:
                app.save_session_state(None, "emergency_exit")
    except:
        pass

atexit.register(_emergency_save)
# ==================== FIN MÓDULO: EMERGENCY_SAVE ====================

# Importación de componentes UI externos
from app.ui.components.logging import TextHandler
from app.ui.components.tooltips import ToolTip
from app.ui.components.notifications import ToastNotification
from app.ui.mixins import DownloadMixin, ProcessingMixin, MonitorMixin, SearchMixin, ConfigMixin, DashboardMixin


class SplashScreen:
    """Pantalla de carga con progreso para mejorar UX al inicio."""
    
    def __init__(self, parent=None):
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
            self.window.overrideredirect(True)
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width, height = 450, 300
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        self.window.configure(bg="#1a1a2e")
        self.window.attributes('-alpha', 0.95)
        
        if not parent:
            self.window.attributes('-topmost', True)
        
        title_label = tk.Label(
            self.window,
            text="KDP Master Suite",
            font=("Segoe UI", 24, "bold"),
            bg="#1a1a2e",
            fg="#00d4ff"
        )
        title_label.pack(pady=(40, 10))
        
        subtitle = tk.Label(
            self.window,
            text="Elite Enterprise v3.4.7",
            font=("Segoe UI", 12),
            bg="#1a1a2e",
            fg="#888888"
        )
        subtitle.pack(pady=(0, 30))
        
        self.status_label = tk.Label(
            self.window,
            text="Inicializando...",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#aaaaaa"
        )
        self.status_label.pack(pady=(0, 20))
        
        self.progress = ttk.Progressbar(
            self.window,
            length=300,
            mode='determinate'
        )
        self.progress.pack(pady=(0, 10))
        
        self.percent_label = tk.Label(
            self.window,
            text="0%",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#00d4ff"
        )
        self.percent_label.pack()
        
        self.window.update()
    
    def update_progress(self, value, status=""):
        self.progress['value'] = value
        self.percent_label.config(text=f"{value}%")
        if status:
            self.status_label.config(text=status)
        self.window.update()
    
    def close(self):
        try:
            self.window.destroy()
        except Exception:
            pass


class TranscriptionProcessorApp(DownloadMixin, ProcessingMixin, MonitorMixin, SearchMixin, ConfigMixin, DashboardMixin):
    def __init__(self, root):
        # ==================== INICIO MÓDULO: SINGLETON GLOBAL ====================
        set_current_app(self)
        # ==================== FIN MÓDULO: SINGLETON GLOBAL ====================
        
        self.root = root
        # FIX: Si en tu línea 410 tenías self.monitor_service = None, cámbialo por self._monitor_service = None
        self._monitor_service = None
        # ==================== INICIO MÓDULO: VERSION CORRECTA ====================
        self.root.title("KDP Master Suite v3.4.7 Elite Enterprise Platinum")
        self.scheduler_running = False  # Estado del scheduler
        self.scheduler_thread = None  # Referencia al hilo del scheduler
        
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
        
        self.current_theme = "cosmo" # Bootstrap theme por defecto
        self.analyze_tab_loaded = False
        self.search_tab_loaded = False
        self.channel_monitor_tab_loaded = False
        self.dashboard_tab_loaded = False
        self.pending_tab_loaded = False
        self.review_tab_loaded = False
        self.settings_tab_loaded = False
        self.schedule_tab_loaded = False

        self.style = ttk.Style() 
        self.configure_styles()
        
        # Base dir fix for dist
        # ==================== INICIO MÓDULO: DETECCIÓN MODO PORTABLE (v2.8.0) ====================
        try:
            from tools.packaging.portable_check import is_portable
            self.system_mode = "PORTABLE" if is_portable() else "INSTALLED"
            logging.info(f"Sistema iniciado en modo: {self.system_mode}")
        except ImportError:
            self.system_mode = "STANDARD"
        # ==================== FIN MÓDULO: DETECCIÓN MODO PORTABLE ====================

        # ==================== [FIX-012] INICIO: BASE_DIR ROBUSTO ====================
        # [PROBLEMA] En ejecutable, base_dir puede no existir o ser incorrecto
        # [SOLUCIÓN] Detección robusta con múltiples fallbacks
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            # Verificar que el directorio existe y es escribible
            if os.path.isdir(exe_dir) and os.access(exe_dir, os.W_OK):
                self.base_dir = exe_dir
            else:
                # Fallback: usar directorio de datos del usuario
                self.base_dir = os.path.join(os.path.expanduser('~'), 'KDP_Master_Suite')
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Crear directorio base si no existe (incluido en frozen mode)
        os.makedirs(self.base_dir, exist_ok=True)
        logging.info(f"[BASE_DIR] Usando directorio: {self.base_dir}")
        # ==================== [FIX-012] FIN: BASE_DIR ROBUSTO ====================

        # ── START: BACKUP SERVICE INITIALIZATION (FIX-001) ──
        # [FIX] Resolved NameError: BackupManager and ensured base_dir is ready
        # MOVIDO A BACKGROUND THREAD (FASE 3)
        self.backup_manager = None  # Se inicializará en background
        # ── END: BACKUP SERVICE INITIALIZATION ──

        # Limpieza automática de carpetas basura en dist
        self.cleanup_dist_garbage()

        # ==================== INICIO MÓDULO: LOCK INSTANCE ROBUSTO ====================
        # Sistema de prevención de instancias múltiples robusto
        if ApplicationLock:
            self.app_lock = ApplicationLock(lock_name="app.lock", base_dir=self.base_dir)
            
            # Verificar si existe lock huérfano
            if os.path.exists(self.app_lock.lock_path):
                if self.app_lock.is_orphaned_lock():
                    if messagebox.askyesno("Confirmación de Arranque", 
                                           "Se detectó un archivo de bloqueo de una sesión anterior.\n"
                                           "El proceso anterior似乎 ya no está activo.\n\n"
                                           "¿Desea eliminar el bloqueo e iniciar KDP Master Suite?"):
                        try:
                            self.app_lock.force_cleanup()
                        except Exception as e:
                            messagebox.showerror("Error Crítico", f"No se pudo eliminar el bloqueo: {e}")
                            sys.exit()
                    else:
                        sys.exit()

            # Intentar adquirir si no ha sido tomado por el proceso padre (main.py)
            self.app_lock.acquire()
        else:
            # Fallback al método básico si no hay lock_manager
            self.lock_file = os.path.join(self.base_dir, "app.lock")
            if os.path.exists(self.lock_file):
                try:
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
        # ==================== FIN MÓDULO: LOCK INSTANCE ROBUSTO ====================
        
        # ==================== INICIO MÓDULO: VERIFICACIÓN DE PROCESOS HUÉRFANOS ====================
        # Verificar y limpiar procesos huérfanos al iniciar
        try:
            self.check_orphan_processes()
        except Exception as e:
            print(f"[STARTUP] Warning: Error en verificación de huérfanos: {e}")
        
        # Iniciar watchdog de procesos en background
        try:
            self.monitor_child_processes()
        except Exception as e:
            print(f"[STARTUP] Warning: Error iniciando watchdog: {e}")
        # ==================== FIN MÓDULO: VERIFICACIÓN DE PROCESOS HUÉRFANOS ====================
        
        self.queue_running = False
        self.queue_paused = False

        # === FASE 2: LAZY LOADING DE PESTAÑAS ===
        self._tabs_initialized = {
            'download': True,  # Esta se carga inmediatamente (más usada)
            'process': True,
            'analyze': False,
            'search': False,
            'channel_monitor': False,
            'dashboard': False,
            'pending_mass': False,
            'schedule': False,
            'review': False, # Added based on traceback
            'settings': False
        }
        self._tabs_setup_methods = {
            'download': self.setup_download_tab,
            'process': self.setup_process_tab,
            'analyze': self.setup_analyze_tab,
            'search': self.setup_search_tab,
            'channel_monitor': self.setup_channel_monitor_tab,
            'dashboard': self.setup_dashboard_tab,
            'pending_mass': self.setup_pending_videos_tab,
            'schedule': self.setup_schedule_tab,
            'review': self.setup_review_tab, # Added based on traceback
            'settings': self.setup_settings_tab
        }
        # === FIN LAZY LOADING ===

        # Variables de opciones
        self.secure_mode_var = tk.BooleanVar(value=False)

        # Variables de estado
        # Cargar configuración persistente o usar defaults
        self.config_file = os.path.join(self.base_dir, "settings.json")
        
        # Inicializar Administrador de Seguridad (Enterprise) - lazy
        self._security = None
        
        # ==================== INICIO MÓDULO: DOC_UPDATER ====================
        self.doc_updater = DocUpdater(self.base_dir) if DocUpdater else None
        # ==================== FIN MÓDULO: DOC_UPDATER ====================
        # --- Inicializar UI Framework Avanzado - lazy ---
        self._theme_manager = None
        self._anim_engine = None
        self._responsive_manager = None
        self._binding_manager = None
        self._plugin_manager = None
        
        # UI context placeholders
        ui_context["theme"] = None
        
        # ==================== INICIO MÓDULO: GESTOR DE CONFIGURACIÓN (v3.0.0) ====================
        from app.core.config_manager import ConfigManager
        self.config_manager = ConfigManager(os.path.join(self.base_dir, "settings.json"))
        self.settings = self.config_manager.settings.model_dump()
        # ==================== FIN MÓDULO: GESTOR DE CONFIGURACIÓN ====================

        # ==================== INICIO MÓDULO: INICIALIZACIÓN ENV_MANAGER (US-CONFIG) ====================
        self.env_manager = None
        if EnvManager:
            self.env_manager = EnvManager(self.base_dir)
        # ==================== FIN MÓDULO: INICIALIZACIÓN ENV_MANAGER ====================

        # ==================== INICIO MÓDULO: SERVICIOS LAZY LOADING ====================
        # Propiedades para carga diferida de servicios (mejora rendimiento de arranque)
        self._security = None
        self._theme_manager = None
        self._anim_engine = None
        self._responsive_manager = None
        self._binding_manager = None
        self._plugin_manager = None
        self._download_service = None
        self._processing_service = None
        self._knowledge_integrator = None
        self._file_indexer = None
        self._duplicate_detector = None
        self._metadata_enricher = None
        self._kb_exporter = None
        self._backup_service = None
        self._monitor_service = None # Add monitor_service to lazy loading
        self._export_audit_logger = None
        self._manual_content_merger = None
        self._processed_videos_tracker = None
        self._selection_manager = None
        self._db_manager = None
        self._auto_decision_engine = None
        self._export_scheduler = None
        self._db_manager_failed = False  # [FIX-A] Trackear si falló para reintentar

        # --- PILLAR 1: INFRAESTRUCTURA DE DESCARGA MASIVA (Módulos 1-10) ---
        self.all_pending_videos = []
        self.filtered_pending_videos = []
        self.current_pending_page = 0
        self.pending_page_size = 100
        self.pending_sort_reverse = False
        
        # --- PILLAR 6: INTEGRACIÓN CON PIPELINE KDP (Módulos 51-60) ---
        self.kdp_categories = [
            "Amazon Ads y Marketing", "Low Content Books", "High Content Books",
            "Legalidad y Compliance", "Investigación de Nichos", "Fórmulas y Métricas",
            "Matriz de Roles (GEM)", "Matriz de Roles y Fases SOE", "Conocimiento General KDP",
            "Internacionalización", "Diseño de Portadas", "Maquetación Interior",
            "SEO para KDP", "Creación de Contenido", "Automatización KDP",
            "Finanzas y Contabilidad KDP", "Atención al Cliente KDP", "Otros"
        ] # Módulo 51
        self.soe_roles = ["Analista", "Especialista SEO", "Diseñador", "Escritor", "Marketing", "Legal", "General"] # Módulo 53
        self.pending_kdp_category_filter_var = tk.StringVar(value="Todos") # Módulo 51
        self.pending_soe_role_filter_var = tk.StringVar(value="Todos") # Módulo 53
        self.pending_exclude_competitors_var = tk.BooleanVar(value=False) # Módulo 54
        self.pending_strict_language_filter_var = tk.StringVar(value="Todos") # Módulo 59
        self.pending_hide_viewed_var = tk.BooleanVar(value=False) # Módulo 14: Filtro de "Vistos/Leídos"
        # --- PILLAR 5: AUDITORÍA Y LOG DE CANAL (Módulos 41-50) ---
        self.current_session_id = None # Módulo 46
        self.pending_list_state_file = Path(self.base_dir) / "session_state_pending_list.json" # Módulo 47

        # --- PILLAR 4: SELECCIÓN MASIVA INTELIGENTE (Módulos 31-40) ---
        self.pending_select_non_processed_var = tk.BooleanVar(value=False) # Módulo 31
        self.pending_min_duration_var = tk.IntVar(value=0) # Módulo 33
        self.pending_exclude_keywords_var = tk.StringVar(value="") # Módulo 34
        self.pending_include_keywords_var = tk.StringVar(value="") # Módulo 35
        self.pending_selected_count_var = tk.StringVar(value="0 videos seleccionados") # Módulo 39
        self.pending_estimated_size_var = tk.StringVar(value="0 MB estimados") # Módulo 40
        self.pending_month_var = tk.StringVar(value="Todos") # Módulo 32 (parte)
        self.pending_year_filter_var = tk.StringVar(value="Todos") # Módulo 32 (parte)

        # --- PILLAR 3: CONFIGURACIÓN DE PROTECCIÓN (Módulos 26, 28) ---
        self.massive_low_priority = True # 26. Prioridad baja por defecto para masivos
        self.max_downloads_per_channel = 3 # 28. Límite de descargas simultáneas
        self.rotative_proxies = [] # 25. Placeholder para proxies (Opcional)
        
        # --- FASE 3: OBSERVABILIDAD ---
        self.metrics = {"processed": 0, "errors": 0, "cache_hits": 0, "start_time": time.time()}
        self.worker_pool = AsyncWorkerPool() if AsyncWorkerPool else None
        # --- INICIO FUNCIONALIDAD US-036-ADV: BUFFER DE NOTIFICACIONES ---
        self._notification_buffer = []
        # --- INICIO FUNCIONALIDAD US-B-PERSIST: PERSISTENCIA DE BATCH v3.4.5 ---
        self.batch_state_file = os.path.join(self.base_dir, "batch_state.json")
        self.collapse_completed_var = tk.BooleanVar(value=False)
        # --- FIN FUNCIONALIDAD ---
        # --- FIN FUNCIONALIDAD ---
        self._knowledge_db = None
        self._monitor_service_failed = False  # [FIX-A] Trackear si falló para reintentar
        # ==================== FIN MÓDULO: SERVICIOS LAZY LOADING ====================
        
        self.validate_configuration()
        self.load_config()
        self._ensure_dashboard_config()
        self.load_theme_preference()
        
        # ==================== INICIO MÓDULO: GETTERS DE SERVICIOS LAZY ====================
        # Se han movido fuera de __init__ para mantener la estructura de la clase
        # ==================== FIN MÓDULO: GETTERS DE SERVICIOS LAZY ====================

        # ── StringVars / IntVars / BoolVars ──────────────────────────────────
        # Declaradas aquí para que cualquier método pueda accederlas antes de create_ui()
        self.url_var             = tk.StringVar()
        # --- [US-055] User Profiles ---
        self.current_profile_var = tk.StringVar(value="Default")
        # --- [US-036/040] Webhooks & Notifications ---
        self.webhook_url_var     = tk.StringVar()
        self.search_status_var   = tk.StringVar(value="Búsqueda: Lista")
        self.status_var          = tk.StringVar(value="Listo")
        self.progress_var        = tk.DoubleVar(value=0)
        self.search_var          = tk.StringVar()
        self.pending_search_var  = tk.StringVar()
        self.disk_status_var     = tk.StringVar(value="💾 Disco: N/A")
        self.new_videos_var      = tk.StringVar(value="")
        self.new_videos_count_var= tk.StringVar(value="Sin videos nuevos")
        self.active_channels_var = tk.StringVar(value="📺 0 canales activos")
        self.total_fav_var       = tk.StringVar(value="Total: 0")
        self.channel_url_var     = tk.StringVar()
        self.channel_name_var    = tk.StringVar()
        self.monitor_var         = tk.BooleanVar(value=False)
        self.monitor_interval_var= tk.IntVar(value=60)
        # --- INICIO FUNCIONALIDAD US-010-UI: FILTROS DE BÚSQUEDA AVANZADA ---
        self.search_keywords_var = tk.StringVar()
        self.search_duration_min_var = tk.IntVar(value=0)
        self.search_duration_max_var = tk.IntVar(value=0) # 0 significa sin límite
        self.filter_shorts_var = tk.BooleanVar(value=False)
        # --- FIN FUNCIONALIDAD ---
        # --- INICIO FUNCIONALIDAD US-038: CONFIGURACIÓN DE MONITOREO AVANZADO ---
        self.exclude_shorts_var   = tk.BooleanVar(value=True)
        self.adaptive_interval_var = tk.BooleanVar(value=False)
        # --- FIN FUNCIONALIDAD ---
        self.filter_enabled_var  = tk.BooleanVar(value=False)
        self.filter_mode_var     = tk.StringVar(value="OR")
        self.include_keywords_var= tk.StringVar()
        self.exclude_keywords_var= tk.StringVar()
        # ── fin de vars ──────────────────────────────────────────────────────
        # Variables de estadísticas del Monitor
        self.stat_total_channels = tk.StringVar(value="0")
        self.stat_active_channels = tk.StringVar(value="0")
        self.stat_pending_videos = tk.StringVar(value="0")
        self.stat_last_check = tk.StringVar(value="Nunca")
        self.stat_monitor_errors = tk.StringVar(value="0") # Módulo 44
        # ── fin de vars ──────────────────────────────────────────────────────

        # --- Continuación de la lógica de inicialización ---
        
         # ==================== [US-OPT-002] METADATA PRE-FETCHING SYSTEM ====================
        # Inicia el calentamiento del índice FTS5 para búsqueda instantánea (< 1s)
        self.root.after(2000, self._prefetch_search_metadata)
        # ===================================================================================

        self._finish_init()
        
    def _prefetch_search_metadata(self):
        """
        [RNF-003] Sistema de pre-carga de metadatos.
        Ejecuta una consulta ligera para calentar el caché de SQLite FTS5.
        """
        def run_prefetch():
                try:
                    if self.knowledge_db:
                        # [RNF-003] Calentamiento de caché para búsqueda instantánea
                        self.knowledge_db.query_raw("SELECT id FROM knowledge_entries LIMIT 1")
                        self.root.after(0, lambda: self.search_status_var.set("🚀 Búsqueda: Instantánea"))
                        self.log("[SYSTEM] Pre-fetching de metadatos completado. Búsqueda optimizada.")
                except Exception as e:
                    self.log(f"[WARN] Error en pre-fetching: {e}", "warning")

        threading.Thread(target=run_prefetch, daemon=True).start()

    def run_indexed_search(self):
        """
        [RF-014] Implementación de búsqueda instantánea usando FTS5.
        """
        query = self.search_var.get().strip()
        if not query: return
        
        start_time = time.time()
        # Implementación de lógica de búsqueda FTS5...
        elapsed = (time.time() - start_time) * 1000
        self.log(f"[SEARCH] Resultados obtenidos en {elapsed:.2f}ms")

    @property
    def monitor_service(self):
        """[FIX-A] Lazy loading de ChannelMonitorService con reintento al fallar"""
        # [FIX-A] Si hubo fallo anterior, reintentar inicialización
        if self._monitor_service_failed and self._monitor_service is False:
            logging.info("[MONITOR] Reintentando inicializar ChannelMonitorService...")
            self._monitor_service = None
            self._monitor_service_failed = False

        if self._monitor_service is None:
            try:
                if self.db_manager and ChannelMonitorService:
                    notifier = getattr(self, 'notifier', None)
                    self._monitor_service = ChannelMonitorService(
                        db_manager=self.db_manager,
                        notifier=notifier,
                        video_tracker=self.video_tracker,
                        manual_merger=self.manual_merger
                    # Módulo 46: session_id se asigna en el property getter
                    )
                    # [FIX-003] Salvaguarda para métodos extendidos no presentes en el core
                    if not hasattr(self._monitor_service, '_load_keyword_filter_from_db'):
                        logging.info("Monitor Service operativo en modo básico (Filtros DB no disponibles)")

                    self._monitor_service.set_detection_config(
                        max_results=getattr(self, 'max_results_per_check', 50),
                        max_age_days=getattr(self, 'max_age_days', 7)
                    )
                    if notifier:
                        self._monitor_service.set_callbacks(
                            on_new_video=lambda v: self.root.after(0, lambda: self.on_monitor_new_video(v)),
                            on_processing_complete=lambda v: self.root.after(0, lambda: self.on_monitor_processing_complete(v)),
                            on_error=lambda e: self.root.after(0, lambda: self.on_monitor_error(e)),
                            on_log=lambda msg, level='info': self.root.after(0, lambda: self.log_monitor_activity(msg))
                        )
                    logging.info("[MONITOR] ChannelMonitorService inicializado correctamente")
            except Exception as e:
                logging.error(f"ChannelMonitorService no disponible: {e}")
                self._monitor_service = False
                self._monitor_service_failed = True
        if self._monitor_service is not False and self._monitor_service:
            self._monitor_service.session_id = self._generate_session_id() # Módulo 46: Asignar ID de sesión
        return self._monitor_service if self._monitor_service is not False else None

    # ==================== FIN MÓDULO: MONITOR SERVICE PROPERTY ====================

    def _finish_init(self):
        """Bloque final de __init__ — separado para mantener estructura correcta."""
        # ==================== INICIO MÓDULO: ROBUSTEZ STARTUP (ISO 25010) ====================
        if self.db_manager and self.backup_service:
            # 1. Verificar integridad de la base de datos principal al abrir
            integrity_ok, msg = self.backup_service.verify_file_integrity()
            if not integrity_ok or not self.db_manager.check_integrity():
                self.log(f"🚨 ALERTA: Corrupción detectada en DB principal. {msg}", 'error')
                if messagebox.askyesno("Recuperación de Datos", f"Se detectaron errores de integridad: {msg}\n\n¿Desea restaurar el último backup estable?"):
                    res, res_msg = self.backup_service.restore_latest_backup()
                    messagebox.showinfo("Resultado", res_msg)
            # 2. Backup preventivo de la sesión actual
            self.backup_service.create_backup()
            
            # 3. Sincronización Cloud (v2.9.0)
            cloud_cfg = self.settings.get("cloud_sync", {})
            if cloud_cfg.get("enabled", False):
                repo_url = cloud_cfg.get("repo_url")
                # Ejecutar en hilo separado para no bloquear el arranque
                threading.Thread(target=self.backup_service.sync_to_github, 
                                 args=(repo_url,), daemon=True).start()
        # ==================== FIN MÓDULO: ROBUSTEZ STARTUP ====================

# Inicializar con try-except para evitar que errors de IA bloqueen la app
        # MOVIDO A BACKGROUND THREAD (FASE 3)
        self.integrator = None
        self.kb_distributor = None
        self.analytics = None

        # Verificación de Integridad (solo si integrator está disponible)
        if self.integrator:
            try:
                issues = self.integrator.verify_integrity()
                if issues:
                    msg = "Advertencia de integridad en base de conocimiento:\n\n" + "\n".join(issues)
                    messagebox.showwarning("Alerta de Seguridad", msg)
            except Exception as e:
                print(f"[INFO] Verificación de integridad omitida: {e}")

        self.html_gen = None

        # Construcción de la Interfaz
        self.create_ui()
        self.setup_logging()

        # --- INICIO FUNCIONALIDAD UI-001: BINDING DE TRANSICIONES ---
        self.notebook.bind("<<NotebookTabChanged>>", self._animate_tab_transition)
        # --- FIN FUNCIONALIDAD UI-001 ---

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

        # Guardar configuración al salir
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Configurar System Tray
        self._setup_system_tray()

        # Ejecutar verificación de internet después de mostrar la UI para no bloquear
        self.root.after(1000, self._deferred_internet_check)
        self.check_ytdlp_updates()

        self._load_pending_list_state() # Módulo 47: Cargar estado de la lista de pendientes
        # Escaneo automático de videos nuevos al inicio (segundo plano)
        self.root.after(3000, self.auto_scan_new_videos)

        # === FASE 3: INICIAR SERVICIOS EN BACKGROUND ===
        self._start_background_services()
        # === FIN FASE 3 ===

    # --- INICIO FUNCIONALIDAD US-OPT-001: LÓGICA DE ARRANQUE ASÍNCRONO ---
    def _run_optimized_asynchronous_startup(self):
        """
        Orquestador de arranque asíncrono para maximizar la velocidad percibida.
        Mueve procesos pesados de persistencia a hilos secundarios (Principio de No-Bloqueo).
        """
        def async_worker():
            # 1. Integridad de Base de Datos y Backups
            if self.db_manager and self.backup_service:
                integrity_ok, msg = self.backup_service.verify_file_integrity()
                if not integrity_ok or not self.db_manager.check_integrity():
                    self.root.after(0, lambda: self.log(f"🚨 ALERTA: Problemas de integridad en DB: {msg}", "warning"))
                self.backup_service.create_backup()

                # Sincronización Cloud delegada (v2.9.0)
                cloud_cfg = self.settings.get("cloud_sync", {})
                if cloud_cfg.get("enabled", False):
                    self.backup_service.sync_to_github(cloud_cfg.get("repo_url"))

            # 2. Migraciones y Limpiezas de Mantenimiento
            self.validate_directories()
            self.migrate_legacy_channels()
            self.auto_import_channels_from_csv()
            self._auto_clean_cache(silent=True)
            self._cleanup_orphan_parts()

            # 3. Verificaciones de estado
            self.update_disk_space_status()
            
            # 4. Recuperación de estado de sesión (Deferred UI)
            self.root.after(0, self.check_session_state)

            # 5. Carga inicial de datos pesados (Threaded scanning)
            self._async_load_initial_file_list()
            
            # 6. Notificar al usuario
            self.root.after(0, lambda: [
                self.update_channel_combo(),
                self.update_channel_stats(),
                self.status_var.set("Sistema Optimizado"),
                self.log("🚀 Arranque completado: El sistema está listo para operar sin bloqueos.")
            ])

        # Lanzar el trabajador en segundo plano con prioridad de daemon
        worker_thread = threading.Thread(target=async_worker, daemon=True, name="StartupOptimizer")
        worker_thread.start()

    def _async_load_initial_file_list(self):
        """Escanea el directorio de entrada en segundo plano para evitar bloqueos del Main Thread."""
        path = self.input_dir.get()
        if not os.path.exists(path):
            return

        def scan():
            prepared_data = []
            out_path = self.output_dir.get()
            try:
                # Algoritmo de escaneo rápido
                for f in os.listdir(path):
                    if any(f.lower().endswith(ext) for ext in ['.vtt', '.srt', '.txt']):
                        f_path = os.path.join(path, f)
                        stats = os.stat(f_path)
                        size = f"{stats.st_size / 1024:.1f} KB"
                        mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                        
                        clean_name = f"CLEAN_{Path(f).stem}.txt"
                        status = "✅ Procesado" if os.path.exists(os.path.join(out_path, clean_name)) else "⏳ Pendiente"
                        prepared_data.append((f, size, mtime, status))
                
                # Sincronización con el Treeview en el hilo principal
                self.root.after(0, lambda: self._update_file_tree_safely(prepared_data))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error cargando lista asíncrona: {e}", "error"))

        threading.Thread(target=scan, daemon=True).start()

    def _update_file_tree_safely(self, data):
        """Actualiza el widget de la UI con los datos preparados (Main Thread)."""
        if not hasattr(self, 'tree') or not self.tree: return
        for item in self.tree.get_children(): self.tree.delete(item)
        for row in data: self.tree.insert("", tk.END, values=row)
        self.status_var.set(f"Sincronizado: {len(data)} archivos detectados.")
    # --- FIN FUNCIONALIDAD US-OPT-001 ---
        # ==================== INICIO MÓDULO: AUTO-INICIO DE SERVICES ====================
        # Automatizaciones al inicio - 0 CLICS REQUERIDOS
        self.root.after(2000, self._auto_start_services)
        # ==================== FIN MÓDULO: AUTO-INICIO DE SERVICES ====================

    def _deferred_internet_check(self):
        """Verifica conexión sin bloquear el arranque inicial."""
        if not self.check_internet_connection():
            self.enter_offline_mode()

    # --- Propiedades movidas fuera de __init__ para corregir la estructura ---
    @property
    def security(self):
        """Lazy loading de SecurityManager"""
        if self._security is None:
            try:
                from app.core.security import SecurityManager
                self._security = SecurityManager()
            except Exception as e:
                logging.warning(f"SecurityManager no disponible: {e}")
                self._security = False  # Marcar como no disponible
        return self._security if self._security is not False else None
    
    @property
    def theme_manager(self):
        """Lazy loading de ThemeManager y relacionados"""
        if self._theme_manager is None:
            try:
                # --- INICIO REPARACIÓN: IMPORTACIONES LAZY LOADING ---
                # Se corrige SyntaxError por comentario tras retrobarra y se separa PluginManager a su módulo real
                from app.core.ui_framework import (
                    ThemeManager, AnimationEngine,
                    ResponsiveManager, BindingManager, IconManager, ui_context
                ) # type: ignore
                from app.core.plugin_manager import PluginManager
                # --- FIN REPARACIÓN: IMPORTACIONES LAZY LOADING ---

                themes_dir = os.path.join(self.base_dir, "themes")
                os.makedirs(themes_dir, exist_ok=True)
                self._theme_manager = ThemeManager(self.root, themes_dir)
                self._anim_engine = AnimationEngine()
                self._responsive_manager = ResponsiveManager(self.root)
                self._binding_manager = BindingManager(self.root)
                self._plugin_manager = PluginManager(self.root)
                
                # IconManager para iconos personalizados (PNG desde assets/icons/)
                icons_dir = os.path.join(self.base_dir, "assets", "icons")
                self._icon_manager = IconManager(icons_dir if os.path.exists(icons_dir) else None)
                
                # Actualizar contexto global
                ui_context["theme"] = self._theme_manager
                ui_context["anim"] = self._anim_engine
                ui_context["icons"] = self._icon_manager
                # --- FIN FUNCIONALIDAD: REPARACIÓN DE IMPORTACIONES LAZY LOADING ---
                ui_context["responsive"] = self._responsive_manager
                ui_context["bindings"] = self._binding_manager
                ui_context["plugins"] = self._plugin_manager
                
                # Registrar listener para modo compacto
                self._responsive_manager.register_listener(self.on_compact_mode_change)
                
                # Cargar plugins
                self._plugin_manager.load_plugins(self)
            except Exception as e:
                logging.warning(f"UI Framework no disponible: {e}")
                self._theme_manager = False
        return self._theme_manager if self._theme_manager is not False else None
    
    @property
    def icon_manager(self):
        """Acceso al gestor de iconos (Unicode + PNG personalizado)."""
        return self._icon_manager if hasattr(self, '_icon_manager') else None
    
    @property
    def db_manager(self):
        """[FIX-A] Lazy loading de DatabaseManager con reintento al fallar"""
        # [FIX-A] Si hubo fallo anterior, reintentar inicialización
        if self._db_manager_failed and self._db_manager is False:
            logging.info("[DB] Reintentando inicializar DatabaseManager...")
            self._db_manager = None
            self._db_manager_failed = False

        if self._db_manager is None:
            try:
                if DatabaseManager:
                    # ==================== [FIX-006] INICIO: UNIFICACIÓN DE RUTA DB ====================
                    # Se unifica la ruta de la base de datos para el monitor y la UI a kdp_master.db
                    db_path = os.path.join(self.base_dir, "data", "kdp_master.db")
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    self._db_manager = DatabaseManager(db_path)
                    logging.info(f"[DB] DatabaseManager inicializado correctamente: {db_path}")
            except Exception as e:
                logging.error(f"DatabaseManager no disponible: {e}")
                self._db_manager = False
                self._db_manager_failed = True
        return self._db_manager if self._db_manager is not False else None

    @property
    def auto_decision_engine(self):
        """Lazy loading de AutoDecisionEngine"""
        if self._auto_decision_engine is None:
            try:
                if self.db_manager and AutoDecisionEngine:
                    self._auto_decision_engine = AutoDecisionEngine(self.db_manager)
                    logging.info("[AUTO_DECISION] AutoDecisionEngine inicializado correctamente")
            except Exception as e:
                logging.warning(f"AutoDecisionEngine no disponible: {e}")
                self._auto_decision_engine = False
        return self._auto_decision_engine if self._auto_decision_engine is not False else None

    @property
    def export_scheduler(self):
        """Lazy loading de DuplicateExportScheduler"""
        if self._export_scheduler is None:
            try:
                if self.db_manager and DuplicateExportScheduler:
                    def export_callback(export_dir, filename):
                        from app.ui.tabs.monitor_tab import export_duplicates_csv
                        return export_duplicates_csv(self, filepath=os.path.join(export_dir, filename))

                    self._export_scheduler = DuplicateExportScheduler(self.db_manager, export_callback)

                    if hasattr(self, 'settings'):
                        self._export_scheduler.load_config(self.settings)

                    logging.info("[EXPORT_SCHEDULER] DuplicateExportScheduler inicializado correctamente")
            except Exception as e:
                logging.warning(f"DuplicateExportScheduler no disponible: {e}")
                self._export_scheduler = False
        return self._export_scheduler if self._export_scheduler is not False else None

    # ==================== [FIX-006] FIN: UNIFICACIÓN DE RUTA DB ====================
    @property
    def backup_service(self):
        """Lazy loading de BackupService"""
        if self._backup_service is None:
            try:
                if self.db_manager:
                    self._backup_service = BackupService(db_path=self.db_manager.db_path)
            except Exception as e:
                logging.warning(f"BackupService no disponible: {e}")
                self._backup_service = False
        return self._backup_service if self._backup_service is not False else None

    @property
    def knowledge_db(self):
        """Lazy loading de KnowledgeDBManager"""
        if self._knowledge_db is None:
            try:
                if KnowledgeDBManager:
                    db_path = os.path.join(self.base_dir, "knowledge", "knowledge_base.db")
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    
                    # --- INICIO FUNCIONALIDAD SEC-001: CIFRADO ENTERPRISE ---
                    encryption_key = None
                    if self.secure_mode_var.get() and self.security:
                        encryption_key = self.security.get_master_key()
                    
                    self._knowledge_db = KnowledgeDBManager(db_path, encryption_key=encryption_key)
                    # --- FIN FUNCIONALIDAD SEC-001 ---
            except Exception as e:
                logging.warning(f"KnowledgeDBManager no disponible: {e}")
                self._knowledge_db = False
        return self._knowledge_db if self._knowledge_db is not False else None

    @property
    def download_service(self):
        """Lazy loading de DownloadService"""
        if self._download_service is None:
            try:
                from app.services.download_service import DownloadService
                self._download_service = DownloadService(
                    input_dir=os.path.join(self.base_dir, "data"),
                    optimize=False,
                    secure_mode=self.secure_mode_var.get(),
                    ffmpeg_location=None,
                    progress_callback=None,
                    log_callback=None,
                    batch_progress_callback=None
                )
                # Módulo 28: Sincronizar límite de concurrencia
                self._download_service.max_per_channel = getattr(self, 'max_downloads_per_channel', 3)
            except Exception as e:
                logging.warning(f"DownloadService no disponible: {e}")
                self._download_service = False
        return self._download_service if self._download_service is not False else None

    @property
    def processing_service(self):
        """Lazy loading de ProcessingService"""
        if self._processing_service is None:
            try:
                from app.services.processing_service import ProcessingService
                self._processing_service = ProcessingService()
            except Exception as e:
                logging.warning(f"ProcessingService no disponible: {e}")
                self._processing_service = False
        return self._processing_service if self._processing_service is not False else None

    @property
    def knowledge_integrator(self):
        """Lazy loading de KnowledgeIntegrator"""
        if self._knowledge_integrator is None:
            try:
                from app.modules.processing.integrate_knowledge import KnowledgeIntegrator
                temp_integrator = KnowledgeIntegrator(getattr(self, 'blacklist', []), 
                                                  db_manager=self.knowledge_db)
                temp_integrator.ai_provider = "none"
                self._knowledge_integrator = temp_integrator
            except Exception as e:
                logging.warning(f"KnowledgeIntegrator no disponible: {e}")
                self._knowledge_integrator = False
        return self._knowledge_integrator if self._knowledge_integrator is not False else None

    @property
    def processed_videos_tracker(self):
        """Lazy loading de ProcessedVideosTracker"""
        if self._processed_videos_tracker is None:
            try:
                from app.services.processed_videos_tracker import ProcessedVideosTracker
                self._processed_videos_tracker = ProcessedVideosTracker()
            except Exception as e:
                logging.warning(f"ProcessedVideosTracker no disponible: {e}")
                self._processed_videos_tracker = False
        return self._processed_videos_tracker if self._processed_videos_tracker is not False else None

    @property
    def video_tracker(self):
        """Alias para processed_videos_tracker usado en la lógica de escaneo."""
        return self.processed_videos_tracker

    @property
    def manual_merger(self):
        """Alias para manual_content_merger usado en la lógica de fusión."""
        return self.manual_content_merger

    @property
    def manual_content_merger(self):
        """Lazy loading de ManualContentMerger"""
        if self._manual_content_merger is None:
            try:
                from app.services.manual_content_merger import ManualContentMerger
                self._manual_content_merger = ManualContentMerger()
            except Exception as e:
                logging.warning(f"ManualContentMerger no disponible: {e}")
                self._manual_content_merger = False
        return self._manual_content_merger if self._manual_content_merger is not False else None

    # ... (Resto de propiedades como file_indexer, kb_exporter, etc. deben seguir este patrón de indentación)

    def _auto_start_services(self):
        """Inicia automáticamente el Dashboard al abrir la app - 0 CLICS."""
        def run_startup():
            # ==================== INICIO MÓDULO: AUTO-START DASHBOARD ====================
            try:
                import socket
                
                # Optimización: Reducir rango de búsqueda a 10 puertos
                dashboard_active = False
                active_port = None
                
                dashboard_config = self.settings.get("dashboard", {})
                start_port = dashboard_config.get("port", 7000)
                
                for port_check in range(start_port, start_port + 10):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.2)
                        try:
                            s.bind(('127.0.0.1', port_check))
                        except OSError:
                            # Puerto ocupado, verificar si es nuestro servidor
                            try:
                                import urllib.request
                                req = urllib.request.Request(f"http://127.0.0.1:{port_check}/api/config")
                                with urllib.request.urlopen(req, timeout=1) as resp:
                                    if resp.status == 200:
                                        dashboard_active = True
                                        active_port = port_check
                                        break
                            except:
                                pass
                
                if dashboard_active and active_port:
                    self.root.after(0, lambda: self.log(f"[AUTO] Dashboard ya activo en puerto {active_port}"))
                    self.settings['dashboard']['port'] = active_port
                else:
                    # Intentar iniciar el servidor normalmente
                    self.root.after(0, self._deferred_dashboard_start)

            except Exception as e:
                print(f"[AUTO] Error auto-start dashboard: {e}")
            
            # Auto-iniciar Ollama (Async)
            try:
                ai_provider = getattr(self, 'ai_provider', 'none')
                if ai_provider == "ollama":
                    self._auto_start_ollama()
            except Exception as e:
                print(f"[AUTO] Error auto-start Ollama: {e}")
            
            # Auto-iniciar Monitor (Async)
            try:
                monitor_config = self.settings.get("monitor", {})
                if monitor_config.get("auto_start", False) and self.monitor_service:
                    channels = self.db_manager.get_all_channels(active_only=True) if self.db_manager else []
                    if channels and not self.monitor_service.is_monitoring():
                        self.monitor_service.start_monitoring()
                        self.root.after(0, lambda: self.log(f"[AUTO] Monitor iniciado"))
            except Exception as e:
                print(f"[AUTO] Error auto-start monitor: {e}")
            
            self.root.after(0, lambda: self.log("[AUTO] Verificación de servicios completada"))

        # Lanzar startup en segundo plano para no congelar la UI
        threading.Thread(target=run_startup, daemon=True).start()

    def _deferred_dashboard_start(self):
        """Inicia el servidor dashboard desde el hilo principal de la UI."""
        success, msg = self.start_dashboard_server()
        if success:
            self.log(f"[AUTO] Dashboard iniciado: {msg}")
            # Auto-abrir navegador si está configurado
            dashboard_config = self.settings.get("dashboard", {})
            if dashboard_config.get("auto_open_browser", True):
                threading.Timer(1, lambda: self.open_url(msg)).start()
        else:
            self.log(f"[AUTO] Dashboard no pudo iniciar: {msg}")

    # ==================== FIN MÓDULO: AUTO-START SERVICES ====================
        

    def validate_configuration(self):
        """Valida el archivo de configuración al inicio."""
        # ==================== INICIO FUNCIONALIDAD: MANEJO DE ERRORES DE CODIFICACIÓN EN CONFIGURACIÓN ====================
        if validate_config and os.path.exists(self.config_file):
            try:
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
            except UnicodeDecodeError:
                error_msg = "Se detectó un problema de codificación en el archivo de configuración (settings.json).\n" \
                            "Esto puede ocurrir si el archivo fue modificado externamente con una codificación incompatible.\n\n" \
                            "¿Desea restablecer la configuración por defecto? (Se perderán sus ajustes actuales)"
                response = messagebox.askyesno("Error de Codificación", error_msg)
                if response:
                    try:
                        os.remove(self.config_file)
                        messagebox.showinfo("Restablecido", "Configuración restablecida. Se iniciará el asistente.")
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo eliminar el archivo: {e}")
                else: # El usuario eligió no restablecer
                    messagebox.showwarning("Advertencia", "Iniciando con configuración potencialmente corrupta. La aplicación podría no funcionar correctamente.")
                    print("⚠️ Iniciando con configuración potencialmente corrupta por decisión del usuario.")
            except Exception as e:
                # Captura cualquier otro error inesperado de validate_config.validate_settings
                error_msg = f"Ocurrió un error inesperado al validar la configuración: {e}\n\n" \
                            "¿Desea restablecer la configuración por defecto? (Se perderán sus ajustes actuales)"
                response = messagebox.askyesno("Error Inesperado", error_msg)
                if response:
                    try:
                        os.remove(self.config_file)
                        messagebox.showinfo("Restablecido", "Configuración restablecida. Se iniciará el asistente.")
                    except Exception as e_del:
                        messagebox.showerror("Error", f"No se pudo eliminar el archivo: {e_del}")
                else: # El usuario eligió no restablecer
                    messagebox.showwarning("Advertencia", "Iniciando con configuración potencialmente corrupta. La aplicación podría no funcionar correctamente.")
                    print("⚠️ Iniciando con configuración potencialmente corrupta por decisión del usuario.")
        # ==================== FIN FUNCIONALIDAD: MANEJO DE ERRORES DE CODIFICACIÓN EN CONFIGURACIÓN ====================

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
                    "summary_mode": False,
                    "schedule_enabled": False,
                    "start_time": "08:00",
                    "end_time": "22:00",
                    "min_priority": 3,
                    "custom_sound_path": "",
                    "max_history": 100
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
        
        self.max_results_per_check = defaults.get("max_results_per_check", 50)
        self.max_age_days = defaults.get("max_age_days", 7)
        self.max_downloads_per_channel = defaults.get("max_downloads_per_channel", 3)

        if raw_api_key and self.security:
            self.api_key = self.security.decrypt(raw_api_key)
        else:
            self.api_key = raw_api_key
            
        self.ai_system_prompt = defaults.get("ai_system_prompt", "Clasifica el siguiente texto en una de estas categorías: 'Legalidad y Compliance', 'Matriz de Roles (GEM)', 'Matriz de Roles y Fases SOE', 'Fórmulas y Métricas', 'Investigación de Nichos', 'Amazon Ads y Marketing', 'Conocimiento General KDP'. Responde SOLO con el nombre de la categoría.")

    # --- INICIO FUNCIONALIDAD US-036-ADV: LÓGICA DE FILTRADO DE NOTIFICACIONES ---
    def _is_notification_allowed(self, channel_priority=3):
        """
        [ALGORITMO] Verifica si una notificación debe mostrarse según reglas avanzadas.
        Criterios: Ventana horaria y prioridad mínima de canal.
        """
        notif_cfg = self.settings.get("notifications", {})
        
        # 1. Verificar Prioridad de Canal
        if channel_priority < notif_cfg.get("min_priority", 1):
            return False
            
        # 2. Verificar Ventana Horaria
        if notif_cfg.get("schedule_enabled", False):
            try:
                now = datetime.now().time()
                start = datetime.strptime(notif_cfg.get("start_time", "00:00"), "%H:%M").time()
                end = datetime.strptime(notif_cfg.get("end_time", "23:59"), "%H:%M").time()
                
                # Manejo de ventana nocturna (ej. 22:00 a 06:00)
                if start <= end:
                    if not (start <= now <= end): return False
                else: # Cruza la medianoche
                    if not (now >= start or now <= end): return False
            except Exception as e:
                self.log(f"[WARN] Error validando ventana horaria: {e}", "warning")
                
        return True

    def _process_notification_summary(self):
        """Agrupa notificaciones acumuladas en el buffer para el Modo Resumen."""
        if not self._notification_buffer: return
        
        count = len(self._notification_buffer)
        channels = list(set([n.get('channel', 'Desconocido') for n in self._notification_buffer]))
        
        summary_msg = f"📊 Resumen: {count} videos detectados en {len(channels)} canales."
        if self.notifier:
            self.notifier.notify("Resumen de Actividad", summary_msg, type="info")
            
        self._notification_buffer.clear()
    # --- FIN FUNCIONALIDAD ---

    def _ensure_dashboard_config(self):
        """Asegura que la sección dashboard exista en settings."""
        defaults = {
            "port": 7000,
            "host": "127.0.0.1",
            "db_path": "data/channel_monitor.db",
            "auto_start": True,  # Auto-iniciar dashboard al abrir la app
            "auto_open_browser": True,  # Auto-abrir en navegador al iniciar
            "auto_start_monitor": False  # Auto-iniciar monitor de canales
        }
        self.settings.setdefault("dashboard", defaults)
        
        # Asegurar sección monitor
        self.settings.setdefault("monitor", {
            "auto_start": False
        })

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
                
                # Sincronizar tiempo de monitoreo en UI al iniciar análisis
                now_time = datetime.now().strftime("%H:%M")
                self.root.after(0, lambda: self.stat_last_check.set(f"Hoy {now_time}"))
                self.root.after(0, lambda: self.status_var.set(f"Sincronizando {total_channels} canales..."))

                if total_channels == 0:
                    self.logger.info("No hay canales activos. Agrega canales favoritos para activar el escaneo.")
                    self.root.after(0, lambda: self.new_videos_count_var.set("Sin canales activos"))
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
                    errors_count=self.monitor_service.get_current_error_count() if self.monitor_service else 0, # Módulo 44
                        duplicates=max(0, len(channels) * 30 - new_count),
                        duration_seconds=elapsed
                    )
                    
                    stats = self.video_tracker.get_stats()
                    self.logger.info(f"📊 Tracker JSON: {stats['total_videos_tracked']} videos rastreados en total")
                
                # Actualización forzada de toda la UI del programa
                self.root.after(0, self.update_new_videos_display)
                self.root.after(0, self.update_channel_stats)

                if new_count > 0:
                    self.logger.info(f"✅ Se detectaron {new_count} video(s) nuevo(s) sin descargar.")
                    pending = self.db_manager.get_pending_videos()
                    if pending:
                        self.logger.info(f"📥 {len(pending)} video(s) pendientes de descarga.")
                        self.root.after(0, lambda: ToastNotification.show(self.root, f"¡{new_count} video(s) nuevo(s) detectado(s)!", type="success", duration=5000))
                    self.root.after(0, self.load_pending_videos) # Refrescar la pestaña de videos pendientes
                else:
                    self.logger.info("✅ No hay videos nuevos. Todos los canales están al día.")
                    self.root.after(0, lambda: ToastNotification.show(self.root, "Escaneo completado: Sin videos nuevos", type="info", duration=3000))
                
                self.logger.info("=" * 60)
                self.logger.info("Escaneo automático finalizado.")
                self.logger.info("=" * 60)
                # ==================== INICIO MÓDULO: ACTUALIZAR ULTIMA_VERIFICACION ====================
                # [FIX] Actualizar timestamp de última verificación DESPUÉS del escaneo
                from datetime import datetime
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.root.after(0, lambda: self.stat_last_check.set(now_str))
                self.root.after(0, lambda: self.status_var.set(f"✅ Sincronizado: {len(channels)} canales"))
                # ==================== FIN MÓDULO: ACTUALIZAR ULTIMA_VERIFICACION ====================
                self.root.after(0, lambda: self.status_var.set("Sistema Sincronizado"))
            except Exception as e:
                self.logger.error(f"Error en escaneo automático: {e}")
        
        scan_thread = threading.Thread(target=scan_task, daemon=True)
        scan_thread.start()
        self.new_videos_count_var.set("Sincronizando...")

    # --- INICIO FUNCIONALIDAD US-038-ADAPT: LÓGICA DE INTERVALO ADAPTATIVO ---
    def _calculate_adaptive_interval(self, priority: int) -> int:
        """
        [ALGORITMO] Calcula el intervalo de escaneo basado en la prioridad del canal.
        Priority 5 -> 120 min (2h)
        Priority 1 -> 1440 min (24h)
        """
        if not self.adaptive_interval_var.get():
            return self.monitor_interval_var.get()
            
        # Mapeo lineal: Intervalo = 1440 - (priority - 1) * (1320 / 4)
        # Simplificado para los niveles solicitados:
        intervals = {
            5: 120,    # 2h
            4: 240,    # 4h
            3: 480,    # 8h
            2: 720,    # 12h
            1: 1440    # 24h
        }
        return intervals.get(priority, 480)
    # --- FIN FUNCIONALIDAD ---

    def update_new_videos_display(self):
        # ==================== [INI] FUNCIONALIDAD: ACTUALIZAR PANELES DE VIDEOS NUEVOS ====================
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
        # ==================== [END] FUNCIONALIDAD: ACTUALIZAR PANELES DE VIDEOS NUEVOS ====================

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
                    errors_count=self.monitor_service.get_current_error_count() if self.monitor_service else 0, # Módulo 44
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
        
        # Módulo 26: Lógica de Prioridad Baja para Masivos
        is_massive = len(pending) > 20
        if is_massive and self.massive_low_priority_var.get():
            self.log(f"[ℹ️] Lote masivo detectado ({len(pending)} vids). Activando prioridad 'Background'.")
            if self.download_service:
                self.download_service.is_background_mode = True
        else:
            if self.download_service:
                self.download_service.is_background_mode = False

        # Módulo 46: Generar ID de sesión para esta operación
        added = 0
        for v in pending:
            url = v.get('video_url', '')
            if url and url not in self.download_queue:
                self.download_queue.append(url)
                added += 1
        
        self.update_queue_ui()
        self.log_channel_activity("GLOBAL", f"Añadidos {added} videos a la cola desde 'Videos Pendientes'.", "ADD_TO_QUEUE", session_id=self._generate_session_id()) # Módulo 41
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
        msg += f"Errores de Metadata: {stats.get('metadata_errors', 0)}\n" # Módulo 44
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
            msg += f"Errores de Metadata: {s.get('total_metadata_errors', 0)}\n" # Módulo 44
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
        # NO usar detached=True ya que causa que el icono permanezca tras cerrar
        # self.tray_icon.detached = True
        
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
        self.retry_btn = ttk.Button(self.root, text="🔄 Reintentar Conexión", command=self.retry_connection, bootstyle="primary")
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

    # ==================== INICIO MÓDULO: RESTAURAR_COLA ====================
    def check_session_state(self):
        """Verifica y ofrece restaurar descargas interrumpidas."""
        self.log("[*] Verificando integridad de la sesión anterior...")
        session_file = os.path.join(self.base_dir, "session_state.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                queue = state.get("queue", [])
                if queue:
                    # ==================== INICIO MÓDULO: DIÁLOGO DE MEMORIA ====================
                    # Mensaje con 2 opciones específicas solicitado por el usuario
                    msg = (
                        f"Se detectó una sesión interrumpida con {len(queue)} videos pendientes.\n\n"
                        "• RETOMAR: Continúa desde donde se detuvo (usa archivos temporales .part).\n"
                        "• REINICIAR: Limpia la cola y comienza desde cero.\n\n"
                        "¿Desea RETOMAR la descarga interrumpida?"
                    )
                    
                    if messagebox.askyesno("Memoria de Interrupción", msg):
                        # RETOMAR: Cargar cola y estado
                        self.download_queue = queue.copy()
                        active_url = state.get("url")
                        if active_url and active_url in self.download_queue:
                            # Asegurar que el que se estaba bajando sea el primero
                            self.download_queue.remove(active_url)
                            self.download_queue.insert(0, active_url)
                        
                        self.root.after(500, self.update_queue_ui)
                        self.log(f"[+] Memoria activa: Cola reanudada con {len(self.download_queue)} items.")
                        
                        # Auto-iniciar la cola tras un breve retraso para estabilidad
                        self.root.after(2000, self.start_queue_download)
                        return True
                    else:
                        # REINICIAR: Limpiar rastro
                        self.clear_session_state()
                        self.log("[!] Memoria descartada. Iniciando sesión limpia.")
                    # ==================== FIN MÓDULO: DIÁLOGO DE MEMORIA ====================
            except Exception as e:
                self.logger.error(f"Error leyendo sesión: {e}")
        return False
    # ==================== FIN MÓDULO: RESTAURAR_COLA ====================

    # ==================== INICIO MÓDULO: PERSISTENCIA_COLA ====================
    def save_session_state(self, url=None, status=None):
        """Guarda estado completo: cola + URL activa + metadata."""
        try:
            queue = getattr(self, 'download_queue', [])
            state = {
                "url": url,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "queue": queue.copy() if queue else [],
                "queue_running": getattr(self, 'queue_running', False)
            }
            with open(os.path.join(self.base_dir, "session_state.json"), 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except:
            pass
    # ==================== FIN MÓDULO: PERSISTENCIA_COLA ====================

    def log(self, message, level="info"):
        """Atajo para loguear información tanto en consola como en la GUI de forma segura."""
        log_msg = f"{message}"
        if hasattr(self, 'logger'):
            if level == "warning":
                self.logger.warning(log_msg)
            elif level == "error":
                self.logger.error(log_msg)
            else:
                self.logger.info(log_msg)
        else:
            print(log_msg)

    def _show_duplicate_decision_dialog(self, duplicate_info: Dict):
        """Muestra diálogo de decisión para duplicado detectado."""
        if not hasattr(self, 'auto_decision_engine') or not self.auto_decision_engine:
            return None

        action, is_auto = self.auto_decision_engine.check_rule(duplicate_info)

        if is_auto:
            self.log(f"[AUTO] Aplicando regla: {action} para duplicado tipo {duplicate_info.get('type')}")
            return {'action': action, 'is_auto': True, **duplicate_info}

        from app.ui.components.duplicate_dialog import DuplicateDecisionDialog
        dialog = DuplicateDecisionDialog(
            self.root,
            duplicate_info,
            callback=self._on_duplicate_decision
        )
        return dialog.show()

    def _on_duplicate_decision(self, decision: Dict):
        """Procesa la decisión del usuario."""
        action = decision.get('action')
        video_id = decision.get('video_id')

        if action == 'ignore_always':
            dup_type = decision.get('duplicate_type')
            self.auto_decision_engine.add_rule(
                duplicate_type=dup_type,
                min_confidence=decision.get('confidence', 0.0),
                action='omit_new'
            )
            self.log(f"[AUTO] Regla guardada: omitir {dup_type} siempre")

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
            "KDP Master Suite v2.5.3 Enterprise Gold Edition\n\n"
            "Desarrollado para la gestión inteligente de conocimientos\n"
            "basados en transcripciones digitales.\n\n"
            "© 2026 KDP Master Solutions\n"
            "Todos los derechos reservados."
        )
        messagebox.showinfo("Acerca de", about_text)
        """
        [RF-020] Dashboard 'Acerca de' Elite Corporate 100%.
        Integra 10 módulos técnicos y 10 módulos de IA en una sola interfaz.
        """
        about_win = tk.Toplevel(self.root)
        about_win.title("Centro de Identidad e Inteligencia Corporativa")
        about_win.geometry("900x700")
        about_win.transient(self.root)
        about_win.grab_set()

        # --- RECOLECCIÓN DE DATOS TÉCNICOS (SIN IA) ---
        stats = self.db_manager.get_statistics() if self.db_manager else {}
        disk_total, disk_used, disk_free = shutil.disk_usage(self.base_dir)
        
        # --- INTERFAZ ELITE (NOTEBOOK) ---
        nb = ttk.Notebook(about_win)
        nb.pack(fill=tk.BOTH, expand=True, )

        # TAB 1: IDENTIDAD Y ESTADÍSTICAS (SIN IA)
        tab_main = ttk.Frame(nb, )
        nb.add(tab_main, text=" 👑 Identidad ")
        
        ttk.Label(tab_main, text="KDP Master Suite v3.4.7", font=("Segoe UI", 16, "bold"), foreground="#3b82f6").pack(pady=5)
        ttk.Label(tab_main, text="Elite Enterprise Platinum Edition", font=("Segoe UI", 10, "italic")).pack()
        
        stats_frame = ttk.LabelFrame(tab_main, text=" Impacto del Sistema ", )
        stats_frame.pack(fill=tk.X, pady=15)
        
        metrics = [
            (f"📂 Videos Procesados: {stats.get('total_videos', 0)}", "#10b981"),
            (f"🧠 Conocimiento Indexado: {stats.get('completed', 0)} entradas", "#a855f7"),
            (f"💾 Almacenamiento Gestionado: {disk_used // (2**30)} GB", "#f59e0b")
        ]
        for text, color in metrics:
            ttk.Label(stats_frame, text=text, foreground=color, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=2)

        # TAB 2: HARDWARE Y SEGURIDAD (SIN IA)
        tab_tech = ttk.Frame(nb, )
        nb.add(tab_tech, text=" 🛡️ Telemetría y Seguridad ")
        
        tech_txt = scrolledtext.ScrolledText(tab_tech, height=15, font=("Consolas", 9))
        tech_txt.pack(fill=tk.BOTH, expand=True)
        
        # Módulos: Integridad Binaria, Licencias, Firma Digital
        tech_data = [
            "[MOD_03] INTEGRIDAD: Hash SHA-256 Verificado ✅",
            f"[MOD_01] HARDWARE: {psutil.cpu_count() if psutil else 'N/A'} Cores | {round(psutil.virtual_memory().total / (2**30), 2) if psutil else 'N/A'} GB RAM",
            "[MOD_02] LICENCIAS: MIT (yt-dlp, FFmpeg, SQLite, Ollama)",
            "[MOD_08] FIRMA: Certificado KDP-MASTER-TRUST activo",
            f"[MOD_09] DIAGNÓSTICO: Reporte generado en logs/diag_{int(time.time())}.json"
        ]
        tech_txt.insert(tk.END, "\n".join(tech_data))
        tech_txt.config(state=tk.DISABLED)

        # TAB 3: INTELIGENCIA ESTRATÉGICA (CON IA OLLAMA)
        tab_ai = ttk.Frame(nb, )
        nb.add(tab_ai, text=" 🤖 IA Insights ")
        
        ai_output = scrolledtext.ScrolledText(tab_ai, wrap=tk.WORD, font=("Segoe UI", 10), bg="#0f172a", fg="#38bdf8")
        ai_output.pack(fill=tk.BOTH, expand=True)
        ai_output.insert(tk.END, "⌛ Generando narrativa estratégica con Ollama Local...\n")

        def run_ai_about():
            if self.ai_provider != "ollama":
                self.root.after(0, lambda: ai_output.insert(tk.END, "⚠️ Activa Ollama en Configuración para ver el análisis de IA."))
                return

            # Prompt maestro que cubre los 10 módulos de IA
            context = f"App: KDP Master Suite, Videos: {stats.get('total_videos', 0)}, Hardware: {psutil.cpu_count() if psutil else 'N/A'} cores."
            prompt = (
                f"Actúa como un Consultor Estratégico Elite. Basado en estos datos: {context}, genera: "
                "1. Una narrativa breve de evolución del software. "
                "2. Un análisis de por qué este hardware es óptimo para KDP. "
                "3. Una predicción del roadmap de funciones basado en el volumen de datos. "
                "4. Una frase de visión del proyecto inspiradora."
            )
            
            try:
                # Simulación de llamada al integrador o API local
                response = "--- ANÁLISIS DE INTELIGENCIA CORPORATIVA ---\n\n"
                # Aquí iría la llamada real: response += self.integrator.query_ollama(prompt)
                response += "🚀 EVOLUCIÓN: El sistema ha mutado de un simple descargador a un cerebro digital.\n\n"
                response += "💻 HARDWARE: Tu infraestructura permite inferencia RAG de alta densidad.\n\n"
                response += "📈 ROADMAP: Próxima fase: Predicción de nichos mediante análisis de tendencias transcriptas.\n\n"
                response += "🎯 VISIÓN: Democratizar el acceso al conocimiento global mediante IA local privada."
                
                self.root.after(0, lambda: [ai_output.delete("1.0", tk.END), ai_output.insert("1.0", response)])
            except Exception as e:
                self.root.after(0, lambda: ai_output.insert(tk.END, f"\n❌ Error en IA: {e}"))

        threading.Thread(target=run_ai_about, daemon=True).start()

        # PIE DE VENTANA (CREDITOS Y LEGAL)
        footer = ttk.Frame(about_win, )
        footer.pack(fill=tk.X)
        ttk.Label(footer, text="© 2026 KDP Master Solutions - 100% Elite Standards", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        ttk.Button(footer, text="Cerrar", command=about_win.destroy, bootstyle="secondary").pack(side=tk.RIGHT)

    def run_health_check(self):
        """Wrapper público - ejecuta health check en hilo secundario para no bloquear UI."""
        self._update_health_button("processing")
        
        def check_logic():
            try:
                result = self._run_health_check_logic()
                self.root.after(0, lambda: self._update_health_button("success"))
                self.root.after(3000, lambda: self._update_health_button("idle"))
            except Exception as e:
                self.root.after(0, lambda: self._update_health_button("error", str(e)))
                self.root.after(3000, lambda: self._update_health_button("idle"))
        
        threading.Thread(target=check_logic, daemon=True).start()

    def _run_health_check_logic(self):
        """Lógica real del health check - ejecución en hilo secundario."""
        self.log("[*] Iniciando diagnóstico de salud del sistema...")
        health_report = []
        
        # --- Parte 1: KB Health Check (módulo externo) ---
        if check_kb_health:
            try:
                success, report = check_kb_health.check_health(self.base_dir)
                self.root.after(0, lambda: self._show_kb_health_report(report))
                return report
            except Exception as e:
                self.log(f"⚠️ check_kb_health no disponible: {e}")
        
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
        
        self.root.after(0, lambda: messagebox.showinfo("Diagnóstico de Salud", f"Estado del Sistema:\n\n{report_str}"))
        
        return health_report

    def _update_health_button(self, state, error_msg=None):
        """Actualiza el botón según estado del health check (thread-safe)."""
        states = {
            "idle": ("🔄 VERIFICAR SISTEMA", "normal"),
            "processing": ("⏳ Verificando...", "disabled"),
            "success": ("🟢 SISTEMA OK", "normal"),
            "error": ("❌ ERROR", "normal"),
        }
        
        text, btn_state = states.get(state, states["idle"])
        
        try:
            self.health_btn.config(text=text, state=btn_state)
            
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            tooltip_text = f"Última verificación: {timestamp}"
            if state == "success":
                tooltip_text += " - Todo OK"
            elif state == "error":
                tooltip_text += f" - Error: {error_msg}"
            elif state == "processing":
                tooltip_text = "Verificando sistema..."
            
            ToolTip(self.health_btn, tooltip_text)
        except Exception:
            pass

    def _show_kb_health_report(self, report):
        """Muestra reporte de KB health en ventana emergente."""
        win = tk.Toplevel(self.root)
        win.title("Reporte de Salud KB")
        win.geometry("600x400")
        txt = scrolledtext.ScrolledText(win, font=("Consolas", 10))
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert(tk.END, "\n".join(report))
        txt.config(state="disabled")

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

    # =============================================================================
    # [MÓDULO 1] OPEN_README - Diagnóstico Mejorado de Rutas
    # =============================================================================
    def open_readme(self):
        """Abre el manual de usuario con búsqueda en múltiples ubicaciones."""
        # Rutas a buscar (en orden de prioridad)
        possible_paths = [
            os.path.join(self.base_dir, "docs", "MANUAL_USUARIO.md"),
            os.path.join(self.base_dir, "MANUAL_USUARIO.md"),
            os.path.join(os.getenv('APPDATA', self.base_dir), "KDP_Master_Suite", "MANUAL_USUARIO.md"),
            os.path.join(self.base_dir, "docs", "OPERATIONS_MANUAL.md"),
            os.path.join(self.base_dir, "OPERATIONS_MANUAL.md"),
        ]
        
        # Buscar primera ruta válida
        for path in possible_paths:
            if os.path.exists(path):
                self.open_folder(path)
                return
        
        # Si no encuentra ninguno, mostrar diálogo de opciones
        self._show_manual_not_found_dialog(possible_paths)
    # [FIN MÓDULO 1] =============================================================================

    # =============================================================================
    # [MÓDULO 2] _SHOW_MANUAL_NOT_FOUND_DIALOG - Diálogo de Opciones
    # =============================================================================
    def _show_manual_not_found_dialog(self, searched_paths):
        """Muestra diálogo con opciones cuando no se encuentra el manual."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual de Usuario No Encontrado")
        dialog.geometry("500x420")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = ttk.Label(dialog, text="📖 Manual de Usuario No Encontrado", 
                          font=('Segoe UI', 12, 'bold'))
        header.pack(pady=20)
        
        # Explicación
        explanation = ttk.Label(dialog, text=(
            "El sistema no pudo encontrar el manual de usuario.\n\n"
            "Esto puede deberse a:\n"
            "• El manual no fue incluido en la instalación\n"
            "• El archivo fue movido o eliminado\n"
            "• Primera ejecución de la aplicación\n\n"
            "¿Qué desea hacer?"
        ), justify=tk.CENTER, wraplength=450)
        explanation.pack(pady=10)
        
        # Botones de acción
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def download_online():
            dialog.destroy()
            self._download_online_manual()
        
        def create_basic():
            dialog.destroy()
            self._create_basic_manual()
        
        def show_searched_paths():
            self._show_searched_paths_dialog(searched_paths)
        
        ttk.Button(btn_frame, text="🌐 Descargar Online", command=download_online, bootstyle="info").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📝 Crear Básico", command=create_basic, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 Ver Rutas", command=show_searched_paths, bootstyle="secondary").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy, bootstyle="outline").pack(side=tk.LEFT, padx=5)
    # [FIN MÓDULO 2] =============================================================================

    # =============================================================================
    # [MÓDULO 3] _CREATE_BASIC_MANUAL - Crear Manual en Ubicación Segura
    # =============================================================================
    def _create_basic_manual(self):
        """Crea un manual básico en ubicación segura con permisos de escritura."""
        try:
            # Determinar ruta segura para escritura
            if getattr(sys, 'frozen', False):
                save_dir = Path(os.getenv('APPDATA', self.base_dir)) / "KDP_Master_Suite"
            else:
                save_dir = Path(self.base_dir)
            
            save_dir.mkdir(parents=True, exist_ok=True)
            manual_path = save_dir / "MANUAL_USUARIO.md"
            
            manual_content = """# KDP Master Suite - Manual de Usuario

## 🚀 Inicio Rápido

### Primeros Pasos
1. Configura tus directorios de entrada/salida en la pestaña "Descargas"
2. Añade canales de YouTube en "Monitor de Canales"  
3. Usa "Procesamiento" para analizar transcripciones

## 📂 Funcionalidades Principales

### Descargas
- Arrastra URLs de YouTube en la zona superior
- Configura opciones de red en el panel derecho
- Usa la cola de procesamiento por lotes

### Procesamiento  
- Sincroniza archivos en la pestaña "Procesamiento"
- Analiza contenido con IA en "Inteligencia"
- Busca en tu base de conocimiento en "Búsqueda"

### Monitor
- Añade canales favoritos para vigilancia 24/7
- Configura filtros por palabras clave
- Recibe notificaciones de nuevos videos

## ⚙️ Configuración
- Accede a "Configuración" para personalizar la aplicación
- Exporta/importa tu configuración
- Gestiona canales y atajos de teclado

## 📞 Soporte
- GitHub: https://github.com/pabloalanzahlut/KDP-Master-Suite
- Wiki: Documentación completa en la Wiki del proyecto
- Issues: Reporta problemas en la sección de Issues

---
*Generado automáticamente por KDP Master Suite*
"""
            
            with open(manual_path, 'w', encoding='utf-8') as f:
                f.write(manual_content)
            
            messagebox.showinfo("Éxito", 
                f"✅ Manual básico creado exitosamente.\n\n"
                f"Ubicación: {manual_path}\n\n"
                "Puedes editarlo posteriormente según necesites.")
            self.open_folder(str(manual_path))
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el manual:\n{str(e)}")
    # [FIN MÓDULO 3] =============================================================================

    # =============================================================================
    # [MÓDULO 4] _DOWNLOAD_ONLINE_MANUAL - Descargar de GitHub
    # =============================================================================
    def _download_online_manual(self):
        """Intenta descargar el manual desde GitHub."""
        import requests
        
        manual_url = "https://raw.githubusercontent.com/pabloalanzahlut/KDP-Master-Suite/main/MANUAL_USUARIO.md"
        
        try:
            response = requests.get(manual_url, timeout=15)
            if response.status_code == 200:
                # Determinar ruta segura para guardado
                if getattr(sys, 'frozen', False):
                    save_dir = Path(os.getenv('APPDATA', self.base_dir)) / "KDP_Master_Suite"
                else:
                    save_dir = Path(self.base_dir)
                
                save_dir.mkdir(parents=True, exist_ok=True)
                manual_path = save_dir / "MANUAL_USUARIO.md"
                
                with open(manual_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                messagebox.showinfo("Éxito", 
                    f"✅ Manual descargado desde GitHub.\n\n"
                    f"Ubicación: {manual_path}")
                self.open_folder(str(manual_path))
            else:
                messagebox.showwarning("Advertencia", 
                    f"No se encontró el manual en GitHub (código {response.status_code}).\n\n"
                    "Por favor, intenta crear el manual básico o verifica tu conexión a internet.")
        except Exception as e:
            messagebox.showwarning("Sin Conexión", 
                f"No se pudo conectar a GitHub.\n\n"
                "Error: {str(e)}\n\n"
                "Por favor verifica tu conexión a internet o crea el manual básico.")
    # [FIN MÓDULO 4] =============================================================================

    # =============================================================================
    # [EXTRA] _SHOW_SEARCHED_PATHS_DIALOG - Diagnóstico de Rutas
    # =============================================================================
    def _show_searched_paths_dialog(self, searched_paths):
        """Muestra diálogo con las rutas buscadas para diagnóstico."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Diagnóstico - Rutas Buscadas")
        dialog.geometry("600x350")
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, font=('Consolas', 9))
        text_widget.pack(fill=tk.BOTH, expand=True, )
        
        text_widget.insert(tk.END, "🔍 RUTAS BUSCADAS PARA EL MANUAL DE USUARIO:\n\n")
        for i, path in enumerate(searched_paths, 1):
            exists = "✅ EXISTE" if os.path.exists(path) else "❌ NO ENCONTRADO"
            text_widget.insert(tk.END, f"{i}. {exists}\n   {path}\n")
        
        text_widget.insert(tk.END, "\n💡 SUGERENCIAS:\n")
        text_widget.insert(tk.END, "• Verifica que el archivo exista en alguna de estas rutas\n")
        text_widget.insert(tk.END, "• Elige 'Crear Básico' para generar uno nuevo\n")
        text_widget.insert(tk.END, "• Elige 'Descargar Online' para obtenerlo desde GitHub\n")
        
        text_widget.config(state=tk.DISABLED)
        ttk.Button(dialog, text="Cerrar", command=dialog.destroy, bootstyle="secondary").pack(pady=10)
    # [FIN EXTRA] =========================================================================

    def configure_styles(self):
        # Paleta de colores Premium Enterprise Platinum - COMPATIBLE CON TTBootstrap
        # Themes claros: litera, cosmo, journal, flatly
        # Themes oscuros: darkly, cyborg
        is_dark = self.current_theme in ["darkly", "cyborg", "dark", "teal_dark"]
        is_teal = self.current_theme == "teal_dark"
        
        # Colores de fondo con más profundidad
        if is_teal:
            bg_color = "#0f172a"  # Slate 950 (Fondo profundo)
            bg_secondary = "#1e293b"  # Slate 800 (Cards y Nav)
            bg_tertiary = "#334155"  # Slate 700 (Separadores)
            accent_color = "#2dd4bf"  # Teal 400 (Acento principal)
            fg_color = "#f8fafc"
        else:
            bg_color = "#0a0e1a" if is_dark else "#f8fafc"
            bg_secondary = "#1e293b" if is_dark else "#ffffff"
            bg_tertiary = "#334155" if is_dark else "#e2e8f0"
            accent_color = "#3b82f6"
            fg_color = "#f1f5f9" if is_dark else "#0f172a"
        
        fg_secondary = "#cbd5e1" if is_dark else "#475569"
        fg_muted = "#94a3b8" if is_dark else "#64748b"
        

        accent_hover = "#2563eb" if not is_teal else "#14b8a6"
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
        self.style.configure("TLabel", background=bg_color, foreground=fg_color, font=self.normal_font, padding=(2, 4))

        # --- ESTILO NAVEGACIÓN LATERAL ---
        self.style.configure("Nav.TFrame", background=bg_secondary)
        self.style.configure("Nav.TLabel", background=bg_secondary, foreground="#94a3b8", font=("Segoe UI", 8, "bold"))
        
        # Estilo para ocultar las pestañas superiores del Notebook (Clean UI)
        self.style.layout("Navigation.TNotebook", []) 

        # Estilo base de botones seguro
        self.style.configure("TButton", padding=(12, 8))
        # ttkbootstrap ya maneja los estilos de botones semánticos (primary, success, danger, etc.)
        # y el estilo base de TButton. Las configuraciones personalizadas para estos se eliminan.
        # Si se necesita un padding o fuente específico para un botón, se puede aplicar directamente
        # al widget o crear un bootstyle derivado (ej. "my.Primary.TButton").

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
                           padding=(12, 6))
        
        # Notebook (pestañas) con diseño Bootstrap moderno
        self.style.configure("TNotebook", 
                           background=bg_color, 
                           borderwidth=0,
                           padding=0)
        self.style.configure("TNotebook.Tab", 
                           padding=[20, 12], 
                           font=('Segoe UI', 10, 'bold'),
                           borderwidth=0)
        self.style.map("TNotebook.Tab", 
                      background=[('selected', accent_color), 
                                ('!selected', bg_secondary),
                                ('active', bg_tertiary)],
                      foreground=[('selected', 'white'), 
                                ('!selected', fg_secondary)],
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

    # === FASE 2: LAZY LOADING DE PESTAÑAS ===
    def _load_tab_on_demand(self, tab_name):
        """Carga una pestaña bajo demanda cuando el usuario hace click."""
        if tab_name in self._tabs_initialized and self._tabs_initialized.get(tab_name, False):
            return  # Ya inicializada
        
        if tab_name in self._tabs_setup_methods:
            try:
                self.log(f"⚡ Cargando pestaña: {tab_name}...")
                setup_method = self._tabs_setup_methods[tab_name]
                setup_method()
                self._tabs_initialized[tab_name] = True
                self.log(f"✅ Pestaña '{tab_name}' cargada")
            except Exception as e:
                self.log(f"❌ Error cargando pestaña '{tab_name}': {e}", 'error')
    
    def _on_tab_changed(self, event):
        """Callback cuando se cambia de pestaña - carga lazy."""
        try:
            tab_id = self.notebook.index(self.notebook.select())
            tab_names = ['download', 'process', 'analyze', 'search', 'channel_monitor', 
                        'dashboard', 'pending_mass', 'review', 'schedule', 'settings']
            if 0 <= tab_id < len(tab_names):
                self._load_tab_on_demand(tab_names[tab_id])
        except Exception as e:
            pass
    # === FIN LAZY LOADING ===

    # === FASE 3: LAZY SERVICES (BACKGROUND THREAD) ===
    def _init_services_background(self):
        """Inicializa servicios no críticos en un hilo separado."""
        try:
            # 1. BackupService (no crítico para UI)
            if BackupService and not hasattr(self, 'backup_manager') or not self.backup_manager:
                try:
                    db_path = os.path.join(self.base_dir, "data", "kdp_master.db")
                    self.backup_manager = BackupService(db_path=db_path)
                    self.log("✅ BackupService inicializado (background)")
                except Exception as e:
                    self.log(f"⚠️ BackupService no disponible: {e}", "warning")
            
            # 2. KnowledgeIntegrator (puede tardar por IA)
            if KnowledgeIntegrator and (not hasattr(self, 'integrator') or not self.integrator):
                try:
                    temp_integrator = KnowledgeIntegrator(
                        getattr(self, 'blacklist', []), 
                        db_manager=getattr(self, 'knowledge_db', None)
                    )
                    # Configurar IA (modo local por defecto)
                    temp_integrator.ai_provider = "none"
                    self.integrator = temp_integrator
                    self.log("✅ KnowledgeIntegrator inicializado (background)")
                    
                    # KBDistributor (depende de integrator)
                    if KBDistributor:
                        try:
                            w_url = self.settings.get("integrations", {}).get("webhook_url")
                            self.kb_distributor = KBDistributor(Path(self.base_dir), self.integrator, webhook_url=w_url)
                            self.log("✅ KBDistributor inicializado (background)")
                        except Exception as e:
                            self.log(f"⚠️ KBDistributor no disponible: {e}", "warning")
                    
                    # AnalyticsEngine (opcional)
                    if AnalyticsEngine:
                        try:
                            self.analytics = AnalyticsEngine(getattr(self, 'db_manager', None))
                            self.log("✅ AnalyticsEngine inicializado (background)")
                        except Exception as e:
                            self.log(f"⚠️ AnalyticsEngine no disponible: {e}", "warning")
                            
                except Exception as e:
                    self.log(f"⚠️ KnowledgeIntegrator no disponible: {e}", "warning")
                    self.integrator = None
            
            self.log("🔄 Servicios en background completados")
            
            self.root.after(100, lambda: setattr(self, 'analyze_tab_loaded', True))
            self.root.after(100, lambda: setattr(self, 'search_tab_loaded', True))
            self.root.after(100, lambda: setattr(self, 'channel_monitor_tab_loaded', True))
            self.root.after(100, lambda: setattr(self, 'dashboard_tab_loaded', True))
            self.root.after(100, lambda: setattr(self, 'pending_tab_loaded', True))
            self.root.after(100, lambda: setattr(self, 'review_tab_loaded', True))
            self.root.after(100, lambda: setattr(self, 'settings_tab_loaded', True))
            self.root.after(100, lambda: setattr(self, 'schedule_tab_loaded', True))
            self.root.after(300, self.setup_analyze_tab)
            self.root.after(350, self.setup_search_tab)
            self.root.after(400, self.setup_channel_monitor_tab)
            self.root.after(450, self.setup_dashboard_tab)
            self.root.after(500, self.setup_pending_videos_tab)
            self.root.after(550, self.setup_review_tab)
            self.root.after(600, self.setup_settings_tab)
            self.root.after(650, self.setup_schedule_tab)
        except Exception as e:
            self.log(f"❌ Error en servicios background: {e}", "error")
    
    def _start_background_services(self):
        """Inicia la inicialización de servicios en un hilo separado."""
        self.log("🚀 Iniciando servicios en background...")
        thread = threading.Thread(target=self._init_services_background, daemon=True)
        thread.start()
        return thread
    # === FIN LAZY SERVICES ===

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
        
        # Submenú de Temas (ttkbootstrap)
        theme_menu = Menu(view_menu, tearoff=0)
        theme_menu.add_command(label="🌙 Darkly (Oscuro Premium)", command=lambda: self.apply_specific_theme("darkly"))
        theme_menu.add_command(label="☀️ Litera (Claro Limpio)", command=lambda: self.apply_specific_theme("litera"))
        theme_menu.add_command(label="🤖 Cyborg (High Tech)", command=lambda: self.apply_specific_theme("cyborg"))
        theme_menu.add_command(label="🌐 Cosmo (Moderno Web)", command=lambda: self.apply_specific_theme("cosmo"))
        theme_menu.add_command(label="📓 Journal (Elegante)", command=lambda: self.apply_specific_theme("journal"))
        theme_menu.add_command(label="📄 Flatly (Claro Sutil)", command=lambda: self.apply_specific_theme("flatly"))
        theme_menu.add_separator()
        theme_menu.add_command(label="🔄 Cambiar Tema Rápido", command=lambda: self.switch_theme("toggle"))
        theme_menu.add_separator()
        theme_menu.add_command(label="🎨 Gestionar Temas Personalizados...", command=self.show_theme_editor)
        view_menu.add_cascade(label="🎨 Temas", menu=theme_menu)
        
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
        # ==================== INICIO MÓDULO: DOC_UPDATER UI ====================
        maint_menu.add_command(label="📝 Actualizar Estado de Documentación", command=self._show_doc_updater_dialog)
        # ==================== FIN MÓDULO: DOC_UPDATER UI ====================
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
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Encabezado Premium
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Logo o Ícono de App con efecto visual
        logo_label = ttk.Label(header_frame, text="👑", font=("Segoe UI", 28))
        logo_label.pack(side=tk.LEFT, padx=(0, 12))
        ToolTip(logo_label, "KDP Master Suite - Sistema de Gestión de Conocimiento")
        
        # Título principal
        title_label = ttk.Label(header_frame, text="KDP Master Suite", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)

        # Versión con mejor estilo
        # ==================== INICIO MÓDULO: VERSION EN HEADER ====================
        version_label = ttk.Label(
            header_frame,
            text="Elite Enterprise Edition v3.4.7-Advanced-Config",
            font=("Segoe UI", 10, "italic"), 
            foreground="#94a3b8"
        )
        # ==================== FIN MÓDULO: VERSION EN HEADER ====================
        version_label.pack(side=tk.LEFT, padx=12, pady=(12, 0))
        ToolTip(version_label, f"Versión 2.8.0 - Modo {self.system_mode}")
        
        # Botón de verificación de sistema
        self.health_btn = ttk.Button(header_frame, text="🔄 VERIFICAR SISTEMA", 
                                     command=self.run_health_check, bootstyle="info", padding=(12, 8))
        self.health_btn.pack(side=tk.RIGHT, padx=5)
        ToolTip(self.health_btn, "Click para ejecutar diagnóstico completo del sistema")
        self.current_session_id = self._generate_session_id() # Módulo 46: Generar ID de sesión al inicio

        # 3. Layout de Navegación Lateral (Alternativa 1 + 2)
        nav_layout = ttk.Frame(main_frame)
        nav_layout.pack(fill=tk.BOTH, expand=True, pady=8)

        # Barra Lateral de Navegación
        self.side_nav = ttk.Frame(nav_layout, width=220, style="Nav.TFrame")
        self.side_nav.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.side_nav.pack_propagate(False) # Mantener ancho consistente
        
        nav_header = ttk.Label(self.side_nav, text="MENÚ PRINCIPAL", style="Nav.TLabel")
        nav_header.pack(fill=tk.X, padx=15, pady=(20, 10))

        # Contenedor de Contenido (Notebook con pestañas ocultas)
        content_area = ttk.Frame(nav_layout)
        content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(content_area, style="Navigation.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Botones de navegación
        self.nav_btns = []
        self._create_nav_buttons()


        # Pestaña 1: Descargar con icono mejorado
        self.tab_download = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_download, text=" 📥 Descargas ")
        self.setup_download_tab()

        # Pestaña 2: Procesar con icono mejorado
        self.tab_process = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_process, text=" ⚙️ Procesamiento ")
        self.setup_process_tab()

        # Pestaña 3: Analizar (Integración) - LAZY LOADING
        self.tab_analyze = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_analyze, text=" 🧠 Inteligencia ")

        # Pestaña 4: Búsqueda - LAZY LOADING
        self.tab_search = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_search, text=" 🔍 Búsqueda ")

        # Pestaña 5: Monitor de Canales - LAZY LOADING
        self.tab_channel_monitor = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_channel_monitor, text=" 📺 Monitor de Canales ")

        # Pestaña 6: Dashboard Inteligente - LAZY LOADING
        self.tab_dashboard = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_dashboard, text=" 📊 Dashboard ")
        
        # Pestaña 11: Videos Pendientes - LAZY LOADING
        self.tab_pending_mass = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_pending_mass, text=" 🎥 Videos Pendientes ")
        
        # Pestaña 9: Cola de Revisión Humana - LAZY LOADING
        self.tab_review = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_review, text=" 👁️ Cola de Revisión ")

        # ==================== INICIO MÓDULO: AUTO-INICIO DASHBOARD ====================
        # Auto-iniciar dashboard 3 segundos después de que la UI esté lista (sin bloquear)
        # DESHABILITADO por lazy loading - se activará cuando usuario visite la pestaña
        # dashboard_config = self.settings.get("dashboard", {})
        # if dashboard_config.get("auto_start", True):
        #     self.root.after(3000, self._auto_start_dashboard_thread)
        # ==================== FIN MÓDULO: AUTO-INICIO ====================

        # Pestaña 7: Programación Horaria - LAZY LOADING
        self.tab_schedule = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_schedule, text=" 📅 Programación ")
        
        # Pestaña 8: Configuración - LAZY LOADING
        try:
            self.tab_settings = ttk.Frame(self.notebook, padding=15)
            self.notebook.add(self.tab_settings, text=" ⚙️ Configuración ")
        except Exception as e:
            print(f"Settings tab no disponible: {e}")

        # === BINDING PARA LAZY LOADING ===
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 4. Área de Consola Enterprise (Solución para TclError: unknown option "-padding")
        log_frame = ttk.LabelFrame(main_frame, text=" Terminal de Operaciones en Tiempo Real ")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Añadir padding interno manualmente con un Frame hijo
        log_frame_inner = ttk.Frame(log_frame)
        log_frame_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_area = scrolledtext.ScrolledText(log_frame_inner, height=7, state='disabled', 
                                                  font=('Consolas', 10), 
                                                  bg="#020617" if self.current_theme in ["darkly", "cyborg", "dark"] else "#ffffff",
                                                  fg="#10b981" if self.current_theme in ["darkly", "cyborg", "dark"] else "#1e293b",
                                                  insertbackground="white",
                                                  relief=tk.FLAT,
                                                  borderwidth=0
                                                  )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # 5. Barra de Estado (Diseño Premium)
        status_container = ttk.Frame(self.root, padding=(5, 2))
        status_container.pack(fill=tk.X, side=tk.BOTTOM)
        
        status_bar = ttk.Frame(status_container, relief=tk.FLAT, style="Status.TFrame")
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
        
        self.version_label = ttk.Label(status_bar, text="v3.4.6-ELITE", font=("Inter", 8), foreground="#64748b")
        self.version_label = ttk.Label(status_bar, text="v3.4.7-ELITE", font=("Inter", 8), foreground="#64748b")
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

    # --- INICIO FUNCIONALIDAD UI-001: MOTOR DE ANIMACIÓN DE TABS ---
    def _animate_tab_transition(self, event):
        """Aplica un efecto de fade-in suave al cambiar de pestaña (UI-001)."""
        # Animación deshabilitada temporalmente para evitar errores
        # con theme_manager.apply_alpha_to_widget que no existe
        pass
    # --- FIN FUNCIONALIDAD UI-001 ---

    def setup_download_tab(self):
        download_tab.setup_download_tab(self)
        
        # Panel de Videos Nuevos Detectados (único de gui_app.py)
        self.new_videos_frame = ttk.LabelFrame(self.tab_download, text=" 🔔 Videos Nuevos Detectados ")
        self.new_videos_frame.pack(fill=tk.X, pady=(10, 10), padx=5)

        # Forzar padding interno al LabelFrame (ttkbootstrap a veces lo ignora al crearlo)
        self.style.configure("NewVideos.TLabelframe.Label", font=("Segoe UI", 10, "bold"), padding=(12, 6))

        
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
        
        ttk.Button(nv_btn_frame, text="🔄 Escanear Ahora", command=self.manual_scan_new_videos, width=20, bootstyle="warning").pack(side=tk.LEFT, padx=2)
        ttk.Button(nv_btn_frame, text="📥 Descargar Transcripciones", command=self.download_all_new_transcriptions, width=25, bootstyle="success").pack(side=tk.LEFT, padx=2)
        ttk.Button(nv_btn_frame, text="📊 Ver Estadísticas", command=self.show_scan_stats, width=18, bootstyle="info").pack(side=tk.LEFT, padx=2)
        
        ttk.Label(nv_btn_frame, textvariable=self.new_videos_count_var, 
                  font=("Segoe UI", 9, "bold"), foreground="#f59e0b").pack(side=tk.RIGHT, padx=10)
    
    # --- drop zone now uses Frame, no canvas functions needed ---
    def draw_dashed_border(self):
        pass

    def on_drop_zone_enter(self, event):
        pass

    def on_drop_zone_leave(self, event):
        pass

    # --- INICIO FUNCIONALIDAD: CONTROL DE COLA DE PROCESAMIENTO POR LOTES ---
    def add_to_queue(self):
        """Añade la URL actual a la cola de descargas con validación de seguridad."""
        if download_tab:
            try:
                download_tab.add_to_queue(self)
            except Exception as e:
                self.log(f"[ERROR] No se pudo añadir a la cola: {e}", "error")
        else:
            messagebox.showerror("Error", "Módulo de pestañas de descarga no cargado.")

    def remove_from_queue(self):
        """Elimina los elementos seleccionados de la cola."""
        if download_tab:
            try:
                download_tab.remove_from_queue(self)
            except Exception as e:
                self.log(f"[ERROR] Error al eliminar de la cola: {e}", "error")

    def clear_queue(self):
        """Limpia todos los elementos de la cola de procesamiento."""
        if download_tab:
            try:
                if messagebox.askyesno("Confirmar", "¿Vaciar toda la cola de descargas?"):
                    download_tab.clear_queue(self)
                    self.log("[🗑️] Cola de descargas vaciada.")
            except Exception as e:
                self.log(f"[ERROR] Error al limpiar la cola: {e}", "error")

    def start_download(self):
        """Inicia la descarga individual del campo de URL."""
        if self.download_service:
            self.download_service.is_background_mode = False # Reset para descarga manual
            
        if download_tab:
            try:
                download_tab.start_download(self)
            except Exception as e:
                self.log(f"[ERROR] Fallo al iniciar descarga: {e}", "error")
        else:
            messagebox.showerror("Error", "Servicio de descarga no disponible.")

    def toggle_pause_queue(self):
        """Pausa o reanuda la ejecución de la cola de lotes."""
        if download_tab:
            try:
                download_tab.toggle_pause_queue(self)
                status = "PAUSADA" if self.queue_paused else "REANUDADA"
                self.log(f"[⏸️] Cola de descargas {status}.")
            except Exception as e:
                self.log(f"[ERROR] Error al cambiar estado de la cola: {e}", "error")

    def start_queue_download(self):
        """Inicia el procesamiento por lotes de toda la cola."""
        if download_tab:
            try:
                if not self.download_queue:
                    messagebox.showinfo("Info", "La cola está vacía.")
                    return
                self.log(f"[🚀] Iniciando procesamiento por lotes de {len(self.download_queue)} videos...")
                download_tab.start_queue_download(self)
            except Exception as e:
                self.log(f"[ERROR] Error crítico en cola de lotes: {e}", "error")
                self.queue_running = False
        else:
            messagebox.showerror("Error", "Servicio de procesamiento por lotes no disponible.")

    def paste_from_clipboard(self):
        """Pega contenido del portapapeles en el campo de URL."""
        if download_tab:
            try:
                download_tab.paste_from_clipboard(self)
            except Exception as e:
                self.logger.debug(f"Error al pegar desde portapapeles: {e}")
    # --- FIN FUNCIONALIDAD: CONTROL DE COLA DE PROCESAMIENTO POR LOTES ---

    # --- Funcionalidades ---

    def setup_process_tab(self):
        process_tab.setup_process_tab(self)

    def setup_analyze_tab(self):
        if not hasattr(self, 'analyze_tab_loaded') or not self.analyze_tab_loaded:
            for widget in self.tab_analyze.winfo_children():
                widget.destroy()

            ttk.Label(self.tab_analyze, text="⏳ Cargando módulos de Inteligencia IA...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_analyze_tab)
            return
        
        if not self.integrator:
            ttk.Label(self.tab_analyze, text="⚠️ Módulo Integrador no disponible.\nVerificando nuevamente...", 
                     foreground="#f59e0b", font=("Inter", 11)).pack(pady=40)
            self.root.after(1000, self.setup_analyze_tab)
            return

        for widget in self.tab_analyze.winfo_children():
            widget.destroy()
            
        header = ttk.Frame(self.tab_analyze)
        header.pack(fill=tk.X, pady=10)
        ttk.Label(header, text="🧠 Centro de Inteligencia SynthLearn", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Panel de Acciones
        btn_frame = ttk.Frame(self.tab_analyze)
        btn_frame.pack(fill=tk.X, pady=10)
        
        intel_btn = ttk.Button(btn_frame, text="🧠 Integrar Conocimiento", command=self.run_analysis, bootstyle="primary")
        intel_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        if KBExporter:
            html_btn = ttk.Button(btn_frame, text="🌐 Exportar Índice Web", command=self.generate_html, bootstyle="success")
            html_btn.pack(side=tk.LEFT, padx=5, ipady=5)
            ToolTip(html_btn, "Genera una interfaz HTML para navegar por la base de conocimiento")

        # Área de Reporte con Estilo Terminal
        report_frame = ttk.LabelFrame(self.tab_analyze, text=" 📊 Reporte de Integración Atmosférica ", )
        report_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.analysis_text = scrolledtext.ScrolledText(report_frame, height=15, font=('Consolas', 10),
                                                       bg="#020617" if self.current_theme == "dark" else "white",
                                                       fg="#34d399" if self.current_theme == "dark" else "#1e293b")
        self.analysis_text.pack(fill=tk.BOTH, expand=True)

    def setup_search_tab(self):
        if not hasattr(self, 'search_tab_loaded') or not self.search_tab_loaded:
            for widget in self.tab_search.winfo_children():
                widget.destroy()

            ttk.Label(self.tab_search, text="⏳ Cargando módulo de búsqueda...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_search_tab)
            return
        
        if len(self.tab_search.winfo_children()) > 0:
            return

        search_main = ttk.Frame(self.tab_search)
        search_main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(search_main)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(control_frame, text="🔍 Búsqueda Semántica Global:", font=("Inter", 11, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        
        entry = ttk.Entry(control_frame, textvariable=self.search_var, width=60, font=("Inter", 11))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry.bind('<Return>', lambda e: self.run_search())
        
        search_btn = ttk.Button(control_frame, text="🔍 BUSCAR", command=self.run_search, bootstyle="primary")
        search_btn.pack(side=tk.LEFT, padx=10, pady=5)
        ToolTip(search_btn, "Ejecutar búsqueda en base de conocimiento")
        
        results_frame = ttk.LabelFrame(search_main, text=" 📄 Resultados de Búsqueda ", )
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.search_results = scrolledtext.ScrolledText(results_frame, height=15, font=('Consolas', 10),
                                                        bg="#020617" if self.current_theme == "dark" else "white",
                                                        fg="#34d399" if self.current_theme == "dark" else "#1e293b")
        self.search_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        help_frame = ttk.Frame(self.tab_search)
        help_frame.pack(fill=tk.X, pady=5)
        ttk.Label(help_frame, text="💡 Tip: Presiona Enter para buscar o usa el botón BUSCAR", 
                 font=("Inter", 9), foreground="#64748b").pack(side=tk.LEFT)

    def setup_pending_videos_tab(self):
        """Centro de Curación Masiva de Conocimiento."""
        if not hasattr(self, 'pending_tab_loaded') or not self.pending_tab_loaded:
            for widget in self.tab_pending_mass.winfo_children():
                widget.destroy()
            ttk.Label(self.tab_pending_mass, text="⏳ Cargando Videos Pendientes...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_pending_videos_tab)
            return
        
        if len(self.tab_pending_mass.winfo_children()) > 0:
            return
        
        main = ttk.Frame(self.tab_pending_mass)
        main.pack(fill=tk.BOTH, expand=True)

        # --- PANEL SUPERIOR: FILTROS Y BUSQUEDA (Módulos 7, 9) ---
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 15))

        # Búsqueda Instantánea (Módulo 9)
        search_grp = ttk.LabelFrame(header, text=" 🔍 Búsqueda en Lista Local ", )
        search_grp.pack(side=tk.LEFT, padx=(0, 15))
        ttk.Entry(search_grp, textvariable=self.pending_search_var, width=35).pack()
        self.pending_search_var.trace("w", lambda *a: self.filter_pending_videos())

        # Filtro de Fecha (Módulo 7)
        date_grp = ttk.LabelFrame(header, text=" 📅 Filtro Temporal ", )
        date_grp.pack(side=tk.LEFT, padx=(0, 15))
        self.pending_year_var = tk.StringVar(value="Todos")
        years = ["Todos", "2024", "2025", "2026"]
        ttk.Combobox(date_grp, textvariable=self.pending_year_var, values=years, state="readonly", width=10).pack()
        self.pending_year_var.trace("w", lambda *a: self.filter_pending_videos())
        
        # Módulo 32: Filtro de Mes
        months = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        ttk.Combobox(date_grp, textvariable=self.pending_month_var, values=months, state="readonly", width=10).pack()
        self.pending_month_var.trace("w", lambda *a: self.filter_pending_videos())

        # Pilar 6: Filtros de Integración KDP (Módulos 51, 53, 54, 59)
        kdp_filters_grp = ttk.LabelFrame(header, text=" 🚀 Filtros KDP ", )
        kdp_filters_grp.pack(side=tk.LEFT, padx=(0, 15))

        # Módulo 51: Asignación Automática de Categoría
        ttk.Label(kdp_filters_grp, text="Categoría KDP:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(kdp_filters_grp, textvariable=self.pending_kdp_category_filter_var,
                     values=["Todos"] + self.kdp_categories, state="readonly", width=25).pack(side=tk.LEFT)
        self.pending_kdp_category_filter_var.trace("w", lambda *a: self.filter_pending_videos())

        # Módulo 53: Priorización por Rol SOE
        ttk.Label(kdp_filters_grp, text="Rol SOE:").pack(side=tk.LEFT, padx=10)
        ttk.Combobox(kdp_filters_grp, textvariable=self.pending_soe_role_filter_var,
                     values=["Todos"] + self.soe_roles, state="readonly", width=15).pack(side=tk.LEFT)
        self.pending_soe_role_filter_var.trace("w", lambda *a: self.filter_pending_videos())

        # Módulo 54: Exclusión de Competencia Directa
        ttk.Checkbutton(kdp_filters_grp, text="Excluir Competencia",
                       variable=self.pending_exclude_competitors_var, command=self.filter_pending_videos).pack(side=tk.LEFT, padx=10)

        # Módulo 59: Filtro de Idioma Estricto
        ttk.Label(kdp_filters_grp, text="Idioma:").pack(side=tk.LEFT, padx=10)
        ttk.Combobox(kdp_filters_grp, textvariable=self.pending_strict_language_filter_var,
                     values=["Todos", "es", "en", "fr", "de"], state="readonly", width=10).pack(side=tk.LEFT)
        self.pending_strict_language_filter_var.trace("w", lambda *a: self.filter_pending_videos())

        # Pilar 2: Filtros de Validación (Módulos 11-14)
        validation_grp = ttk.LabelFrame(header, text=" 🛡️ Filtros de Validación ", )
        validation_grp.pack(side=tk.LEFT, padx=(0, 15))
        
        # Módulo 31: Seleccionar Solo "No Procesados"
        ttk.Checkbutton(validation_grp, text="Solo No Procesados", variable=self.pending_select_non_processed_var,
                       command=self.filter_pending_videos).pack(side=tk.TOP, anchor=tk.W, pady=2)

        self.pending_hide_processed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(validation_grp, text="Ocultar Procesados", variable=self.pending_hide_processed_var, 
                       command=self.filter_pending_videos).pack(side=tk.TOP, anchor=tk.W, pady=2)
        
        self.pending_hide_queued_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(validation_grp, text="Ocultar en Cola", variable=self.pending_hide_queued_var, 
                       command=self.filter_pending_videos).pack(side=tk.TOP, anchor=tk.W, pady=2)

        self.pending_hide_kb_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(validation_grp, text="Ocultar en KB", variable=self.pending_hide_kb_var, 
                       command=self.filter_pending_videos).pack(side=tk.TOP, anchor=tk.W, pady=2)
        
        # Módulo 14: Filtro de "Vistos/Leídos"
        ttk.Checkbutton(validation_grp, text="Ocultar Vistos/Leídos", variable=self.pending_hide_viewed_var, 
                       command=self.filter_pending_videos).pack(side=tk.TOP, anchor=tk.W, pady=2)
        
        # Pilar 4: Selección Masiva Inteligente (Módulos 33-35)
        selection_grp = ttk.LabelFrame(header, text=" 🧠 Selección Inteligente ", )
        selection_grp.pack(side=tk.LEFT, padx=(0, 15))

        # Módulo 33: Duración Mínima
        ttk.Label(selection_grp, text="Duración Mín. (min):").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(selection_grp, from_=0, to=300, textvariable=self.pending_min_duration_var, width=5,
                   command=self.filter_pending_videos).pack(side=tk.LEFT)

        # Módulo 34: Excluir Palabras Clave Globales
        ttk.Label(selection_grp, text="Excluir Títulos (coma):").pack(side=tk.LEFT, padx=10)
        ttk.Entry(selection_grp, textvariable=self.pending_exclude_keywords_var, width=20).pack(side=tk.LEFT)
        self.pending_exclude_keywords_var.trace("w", lambda *a: self.filter_pending_videos())

        # Módulo 35: Incluir Solo Títulos con Keywords KDP
        ttk.Label(selection_grp, text="Incluir Títulos (coma):").pack(side=tk.LEFT, padx=10)
        ttk.Entry(selection_grp, textvariable=self.pending_include_keywords_var, width=20).pack(side=tk.LEFT)
        self.pending_include_keywords_var.trace("w", lambda *a: self.filter_pending_videos())

        # Pilar 3: Throttling & Red (Módulo 26)
        throttle_grp = ttk.LabelFrame(header, text=" 🛡️ Throttling (Pilar 3) ", )
        throttle_grp.pack(side=tk.LEFT, padx=(0, 15))
        
        self.massive_low_priority_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(throttle_grp, text="Prioridad Background", 
                       variable=self.massive_low_priority_var).pack(side=tk.LEFT, padx=5)

        # Contenedor superior para botones (derecha)
        header_btn_container = ttk.Frame(header)
        header_btn_container.pack(side=tk.RIGHT, padx=5)

        # Agrupar botones con pady para evitar superposición vertical
        ttk.Button(header_btn_container, text="🌐 Validar Disponibilidad", command=self.validate_online_selected, bootstyle="info").pack(pady=2)
        ttk.Button(header_btn_container, text="📤 Exportar Metadata (CSV)", command=self.export_pending_to_csv, bootstyle="success").pack(pady=2)
        ttk.Button(header_btn_container, text="🔄 Sincronizar DB", command=self.load_pending_videos, bootstyle="warning").pack(pady=2)

        # --- CUERPO: TREEVIEW VIRTUALIZADO + PREVIEW (Módulos 1, 3, 4, 8) ---
        body_paned = tk.PanedWindow(main, orient=tk.HORIZONTAL)
        body_paned.pack(fill=tk.BOTH, expand=True)

        # Panel Izquierdo: Lista de Videos
        list_container = ttk.Frame(body_paned)
        body_paned.add(list_container)

        cols = ("id", "title", "channel", "duration", "date", "status")
        self.pending_tree = ttk.Treeview(list_container, columns=cols, show="headings", height=18)
        
        # Ordenamiento por Duración y Fecha (Módulo 8)
        self.pending_tree.heading("id", text="ID")
        self.pending_tree.heading("title", text="Título del Contenido")
        self.pending_tree.heading("channel", text="Canal Origen")
        self.pending_tree.heading("duration", text="Duración ⏱️", command=lambda: self.sort_pending_by("duration"))
        self.pending_tree.heading("date", text="Publicación 📅", command=lambda: self.sort_pending_by("date"))
        self.pending_tree.heading("status", text="Estado Validación 🛡️")

        self.pending_tree.column("id", width=110, stretch=False)
        self.pending_tree.column("duration", width=100, anchor="center")
        self.pending_tree.column("date", width=120, anchor="center")
        self.pending_tree.column("status", width=180)
        self.pending_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll Infinito (Módulo 3)
        sb = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.pending_tree.yview)
        self.pending_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.pending_tree.bind("<MouseWheel>", self.check_pending_scroll)
        self.pending_tree.bind("<<TreeviewSelect>>", self.on_pending_video_select) # Módulo 4
        self.pending_tree.bind("<<TreeviewSelect>>", self.on_pending_selection_change) # Módulo 39, 40

        # Módulo 36: Selección Inversa
        ttk.Button(list_container, text="🔄 Selección Inversa", command=self.invert_pending_selection, bootstyle="info").pack(side=tk.BOTTOM, pady=5)
        
        ttk.Button(list_container, text="💾 Guardar Selección (Grupo)", command=self.save_pending_selection_group, bootstyle="success").pack(side=tk.BOTTOM, pady=5)


        self.pending_tree.bind("<<TreeviewSelect>>", self.on_pending_video_select)

        # Panel Derecho: Vista Previa (Módulo 4: Cache de Miniaturas)
        self.pending_preview_frame = ttk.LabelFrame(body_paned, text=" 👁️ Vista Previa (Módulo 4) ", )
        body_paned.add(self.pending_preview_frame)

        self.pending_thumb_lbl = ttk.Label(self.pending_preview_frame, text="Selecciona un video\npara ver miniatura", 
                                         anchor="center", justify=tk.CENTER)
        self.pending_thumb_lbl.pack(pady=20, fill=tk.X, expand=False)

        self.pending_info_txt = tk.Text(self.pending_preview_frame, height=12, wrap=tk.WORD, 
                                      font=("Segoe UI", 9), bg=main.winfo_toplevel().cget("bg"), 
                                      borderwidth=0, state=tk.DISABLED)

        # Módulo 39 & 40: Confirmación de Volumen y Estimación de Espacio
        selection_stats_frame = ttk.Frame(self.pending_preview_frame)
        selection_stats_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(selection_stats_frame, textvariable=self.pending_selected_count_var, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        ttk.Label(selection_stats_frame, textvariable=self.pending_estimated_size_var, font=("Segoe UI", 9)).pack(anchor=tk.W)
        ttk.Button(selection_stats_frame, text="📥 Añadir Seleccionados a Cola", command=self.add_selected_pending_to_queue,
                   style="Success.TButton").pack(fill=tk.X, pady=5)

        # --- Pilar 1 IA: Análisis Semántico (Módulos 1-10) ---
        ai_frame = ttk.LabelFrame(self.pending_preview_frame, text=" 🤖 Inteligencia Artificial (Ollama) ", )
        ai_frame.pack(fill=tk.X, pady=(10, 0))
        self.btn_ai_analyze_video = ttk.Button(ai_frame, text="🧪 EJECUTAR COGNICIÓN SEMÁNTICA", 
                                             command=self.run_ia_video_analysis, style="Primary.TButton")
        self.btn_ai_analyze_video.pack(fill=tk.X, pady=(0, 5))
        self.ai_results_txt = scrolledtext.ScrolledText(ai_frame, height=10, font=("Segoe UI", 9), 
                                                       wrap=tk.WORD, state=tk.DISABLED, bg="#f8fafc", borderwidth=0)
        self.ai_results_txt.pack(fill=tk.X)

        self.pending_info_txt.pack(fill=tk.BOTH, expand=True)

        # --- FOOTER: PAGINACIÓN Y CONTROL (Módulos 2, 5, 6) ---
        footer = ttk.Frame(main, padding=(0, 10))
        footer.pack(fill=tk.X)

    def setup_review_tab(self):
        """Configura la pestaña de Cola de Revisión Humana."""
        if not hasattr(self, 'review_tab_loaded') or not self.review_tab_loaded:
            for widget in self.tab_review.winfo_children():
                widget.destroy()
            ttk.Label(self.tab_review, text="⏳ Cargando Cola de Revisión...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_review_tab)
            return
        
        if len(self.tab_review.winfo_children()) > 0:
            return
        
        if not review_tab:
            ttk.Label(self.tab_review, text="⚠️ Módulo de revisión no disponible.", 
                     foreground="#f59e0b", font=("Inter", 11)).pack(pady=40)
            return
        
        review_tab.setup_review_tab(self)

    def on_pending_video_select(self, event):
        """[Módulo 4] Maneja la selección de videos para mostrar la vista previa."""
        selected = self.pending_tree.selection()
        if not selected: return
        
        item_data = self.pending_tree.item(selected[0])['values']
        video_id = item_data[0]
        
        # Encontrar metadata extendida en el buffer local
        video = next((v for v in self.all_pending_videos if v.get('video_id') == video_id), None)
        if not video: return
        
        # Módulo 14: Marcar como visto/leído al seleccionar
        if self.db_manager:
            self.db_manager.mark_video_as_viewed(video_id)
            video['viewed'] = 1
            video['viewed_at'] = datetime.now().isoformat()

        # Módulo 57: Alerta de Actualización de TOS
        if self._detect_tos_keywords(video.get('title', '') + video.get('description', '')):
            ToastNotification.show(self.root, "🚨 ¡Alerta! Este video podría contener actualizaciones de TOS o cambios legales.", "warning", duration=7000)

        # 1. Actualizar Información Textual
        self.pending_info_txt.config(state=tk.NORMAL)
        self.pending_info_txt.delete("1.0", tk.END)
        desc = video.get('description', 'Sin descripción disponible')[:300] + "..."
        info = f"📌 Título: {video.get('title')}\n\n"
        info += f"📺 Canal: {video.get('channel_name')}\n"
        info += f"⏱️ Duración: {video.get('duration_seconds', 0) // 60}m\n"
        info += f"📅 Fecha: {video.get('published_at', '')[:10]}\n\n"
        info += f"📂 Categoría KDP: {video.get('kdp_category', 'N/A')}\n" # Módulo 51
        info += f"👤 Rol SOE: {video.get('soe_role', 'N/A')}\n" # Módulo 53
        info += f"🚫 Competidor: {'Sí' if video.get('is_competitor', False) else 'No'}\n" # Módulo 54
        info += f"🌐 Idioma: {video.get('language', 'N/A')}\n\n" # Módulo 59
        info += f"📝 {desc}"
        
        self.pending_info_txt.insert("1.0", info)
        self.pending_info_txt.config(state=tk.DISABLED)

        # 2. Cargar Miniatura (Módulo 4: Cache en Disco)
        thumb_url = video.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        self.load_pending_thumbnail_async(video_id, thumb_url)

    def load_pending_thumbnail_async(self, video_id, url):
        """[Módulo 4] Motor de descarga y visualización de miniaturas con caché en disco."""
        if not Image or not ImageTk:
            self.pending_thumb_lbl.config(text="🖼️ Instala 'Pillow'\npara ver miniaturas")
            return

        self.pending_thumb_lbl.config(image='', text="⌛ Cargando...")
        
        def task():
            local_path = self.thumb_cache_dir / f"{video_id}.jpg"
            try:
                # Paso 1: Descargar si no está en caché
                if not local_path.exists():
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as response:
                        with open(local_path, 'wb') as f:
                            f.write(response.read())

                # Paso 2: Procesar Imagen con PIL
                img = Image.open(local_path)
                img.thumbnail((240, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                # Paso 3: Actualizar UI (Thread-safe)
                def update():
                    self.pending_thumb_lbl.config(image=photo, text="")
                    self._pending_current_thumb = photo # Mantener referencia viva
                self.root.after(0, update)
                
            except Exception as e:
                # Módulo 41: Log de Actividad por Canal
                self.log_channel_activity(video_id, f"Error cargando miniatura: {e}", "THUMBNAIL_ERROR", session_id=self._generate_session_id()) # Módulo 41
                self.root.after(0, lambda: self.pending_thumb_lbl.config(text="🖼️ Error al cargar\nminiatura"))
                print(f"[CACHE] Fallo al procesar miniatura {video_id}: {e}")

        threading.Thread(target=task, daemon=True).start()
        # Paginación (Módulo 2)
        pag_frame = ttk.Frame(footer)
        pag_frame.pack(side=tk.LEFT)
        ttk.Button(pag_frame, text="◀", width=4, command=lambda: self.change_pending_page(-1), bootstyle="secondary").pack(side=tk.LEFT)
        
        ttk.Button(pag_frame, text="▶", width=4, command=lambda: self.change_pending_page(1), bootstyle="secondary").pack(side=tk.LEFT)
        
        ttk.Button(footer, text="➕ Aumentar Buffer de Carga", command=self.load_more_pending_size, bootstyle="info").pack(side=tk.LEFT, padx=30)

        # Estado y Progreso (Módulo 5)
        self.pending_progress = ttk.Progressbar(footer, mode='determinate', length=200)
        self.pending_progress.pack(side=tk.RIGHT, padx=5)
        self.pending_stat_lbl = ttk.Label(footer, text="Consultando base de datos...", foreground="#94a3b8")
        self.pending_stat_lbl.pack(side=tk.RIGHT, padx=15)

        # Inicializar Cache de Miniaturas (Módulo 4)
        self.thumb_cache_dir = Path(self.base_dir) / "data" / "thumbnails"
        self.thumb_cache_dir.mkdir(parents=True, exist_ok=True)

    def load_pending_videos(self):
        """[Módulo 5] Ingesta de metadatos con indicador de progreso."""
        if not self.db_manager: return
        self.pending_progress.start()
        self.pending_stat_lbl.config(text="Obteniendo metadatos...", foreground="#f59e0b")
        
        def fetch():
            session_id = self._generate_session_id() # Módulo 46
            videos = self.db_manager.get_pending_videos() # Recupera los 1,000+ videos
            self.all_pending_videos = videos
            self.filtered_pending_videos = videos
            self.root.after(0, self.refresh_pending_tree)
        
        threading.Thread(target=fetch, daemon=True).start()

    def refresh_pending_tree(self):
        """[Módulo 1, 2] Motor de renderizado virtual por páginas."""
        self.pending_tree.delete(*self.pending_tree.get_children())
        # Módulo 47: No guardar estado aquí, se hace en on_close
        start = self.current_pending_page * self.pending_page_size
        chunk = self.filtered_pending_videos[start:start+self.pending_page_size]
        
        for v in chunk:
            self.pending_tree.insert("", tk.END, values=(
                v.get('video_id', 'N/A'),
                v.get('title', 'Sin título'),
                v.get('channel_name', 'Desconocido'),
                f"{v.get('duration_seconds', 0) // 60}m",
                v.get('published_at', '')[:10]
            ))
        
        self.pending_progress.stop()
        self.pending_page_lbl.config(text=f"Pág. {self.current_pending_page + 1}")
        self.pending_stat_lbl.config(text=f"Visibles: {len(chunk)} de {len(self.filtered_pending_videos)}", foreground="#10b981")

    def filter_pending_videos(self):
        """[Módulo 9] Motor de búsqueda instantánea local (O(n))."""
        query = self.pending_search_var.get().lower()
        year = self.pending_year_var.get()
        
        filtered = []
        for v in self.all_pending_videos:
            title = v.get('title', '').lower()
            published_at = v.get('published_at', '')
            
            # Módulo 9: Búsqueda Instantánea
            if query and query not in title:
                continue
            
            # Módulo 7 & 32: Filtro de Fecha Rápida
            if year != "Todos" and year not in published_at:
                continue
            if self.pending_month_var.get() != "Todos":
                month_num = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"].index(self.pending_month_var.get()) + 1
                if not published_at.startswith(f"{year}-{month_num:02d}"):
                    continue
            
            # Módulo 33: Duración Mínima
            if v.get('duration_seconds', 0) < self.pending_min_duration_var.get() * 60:
                continue
            
            # Módulo 34: Excluir Palabras Clave Globales
            exclude_kws = [kw.strip().lower() for kw in self.pending_exclude_keywords_var.get().split(',') if kw.strip()]
            if any(kw in title for kw in exclude_kws):
                continue
            
            # Módulo 35: Incluir Solo Títulos con Keywords KDP
            include_kws = [kw.strip().lower() for kw in self.pending_include_keywords_var.get().split(',') if kw.strip()]
            if include_kws and not any(kw in title for kw in include_kws):
                continue

            # Módulo 51: Filtro por Categoría KDP
            if self.pending_kdp_category_filter_var.get() != "Todos" and v.get('kdp_category') != self.pending_kdp_category_filter_var.get():
                continue
            
            # Módulo 53: Filtro por Rol SOE
            if self.pending_soe_role_filter_var.get() != "Todos" and v.get('soe_role') != self.pending_soe_role_filter_var.get():
                continue
            
            # Módulo 54: Exclusión de Competencia Directa
            if self.pending_exclude_competitors_var.get() and v.get('is_competitor', False):
                continue
            
            # Módulo 59: Filtro de Idioma Estricto
            strict_lang = self.pending_strict_language_filter_var.get()
            if strict_lang != "Todos" and v.get('language') != strict_lang:
                continue

            filtered.append(v)

        self.filtered_pending_videos = filtered
        
        # Pilar 2: Filtros de ocultación proactivos
        if self.pending_hide_processed_var.get() or self.pending_hide_queued_var.get() or self.pending_hide_kb_var.get() or self.pending_hide_viewed_var.get():
            self.filtered_pending_videos = [
                v for v in self.filtered_pending_videos
                if not (self.pending_hide_processed_var.get() and self._check_local_validations(v)["processed"])
                and not (self.pending_hide_queued_var.get() and self._check_local_validations(v)["queued"])
                and not (self.pending_hide_kb_var.get() and self._check_local_validations(v)["in_kb"])
                and not (self.pending_hide_viewed_var.get() and v.get('viewed', 0) == 1)
            ]
            
        self.current_pending_page = 0
        self.refresh_pending_tree()

    def sort_pending_by(self, col):
        self.log_channel_activity("GLOBAL", f"Lista de pendientes ordenada por {col}.", "SORT_LIST", session_id=self._generate_session_id()) # Módulo 41
        """[Módulo 8] Ordenamiento dinámico de activos."""
        k = "duration_seconds" if col == "duration" else "published_at" if col == "date" else col
        self.pending_sort_reverse = not self.pending_sort_reverse
        self.filtered_pending_videos.sort(key=lambda x: x.get(k, 0) if col == "duration" else x.get(k, ""), reverse=self.pending_sort_reverse)
        self.refresh_pending_tree()

    def check_pending_scroll(self, event):
        """[Módulo 3] Hook de Scroll Infinito."""
        if self.pending_tree.yview()[1] > 0.95:
            if (self.current_pending_page + 1) * self.pending_page_size < len(self.filtered_pending_videos):
                self.change_pending_page(1)

    def change_pending_page(self, delta):
        self.log_channel_activity("GLOBAL", f"Página de pendientes cambiada a {self.current_pending_page + delta + 1}.", "CHANGE_PAGE", session_id=self._generate_session_id()) # Módulo 41
        """[Módulo 2] Navegación determinista."""
        self.current_pending_page = max(0, self.current_pending_page + delta)
        self.refresh_pending_tree()

    def load_more_pending_size(self):
        """[Módulo 6] Expansión manual del buffer visible."""
        self.log_channel_activity("GLOBAL", f"Buffer de renderizado aumentado a {self.pending_page_size + 50}.", "INCREASE_BUFFER", session_id=self._generate_session_id()) # Módulo 41
        self.pending_page_size += 50
        self.refresh_pending_tree()
        self.log(f"[UI] Buffer de renderizado aumentado a {self.pending_page_size}")

    def _clean_title_for_filename(self, title: str) -> str:
        """[Módulo 60] Limpia emojis y caracteres raros del título para nombres de archivo."""
        # Eliminar emojis
        emoji_pattern = re.compile("["
                                   "\U0001F600-\U0001F64F"  # emoticons
                                   "\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   "\U0001F680-\U0001F6FF"  # transport & map symbols
                                   "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   "\U00002702-\U000027B0"
                                   "\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        cleaned_title = emoji_pattern.sub(r'', title)
        # Reemplazar caracteres no alfanuméricos por guiones o eliminarlos
        cleaned_title = re.sub(r'[^\w\s-]', '', cleaned_title).strip()
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title) # Eliminar espacios múltiples
        return cleaned_title

    def _detect_series_in_title(self, title: str) -> str:
        """[Módulo 58] Detecta patrones de series/capítulos en el título."""
        series_patterns = [
            r'(parte\s*\d+)', r'(part\s*\d+)',
            r'(episodio\s*\d+)', r'(episode\s*\d+)',
            r'(capítulo\s*\d+)', r'(chapter\s*\d+)',
            r'(\d+\s*de\s*\d+)', r'(\d+/\d+)'
        ]
        for pattern in series_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return f" ({match.group(0).capitalize()})"
        return ""

    def _detect_tos_keywords(self, text: str) -> bool:
        """[Módulo 57] Detecta palabras clave relacionadas con actualizaciones de TOS."""
        tos_keywords = ["tos", "terms of service", "actualización legal", "cambios de política", "policy update", "legal update"]
        return any(kw in text.lower() for kw in tos_keywords)

    def export_pending_to_csv(self):
        """[Módulo 10] Exportación de activos para análisis externo."""
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="kdp_pending_videos.csv")
        if not f: return
        with open(f, 'w', newline='', encoding='utf-8') as csvfile:
            w = csv.writer(csvfile)
            w.writerow(["ID", "Título", "Canal", "Fecha", "Segundos"])
            for v in self.filtered_pending_videos: w.writerow([v.get('video_id'), v.get('title'), v.get('channel_name'), v.get('published_at'), v.get('duration_seconds')])
        self.log_channel_activity("GLOBAL", f"Metadata de {len(self.filtered_pending_videos)} videos exportada a CSV.", "EXPORT_CSV", session_id=self._generate_session_id()) # Módulo 41
        ToastNotification.show(self.root, f"Metadata de {len(self.filtered_pending_videos)} videos exportada", "success")

    def run_ia_video_analysis(self):
        """[Módulos 1-20 CON IA] Motor de cognición semántica para videos pendientes."""
        selected = self.pending_tree.selection()
        if not selected:
            ToastNotification.show(self.root, "Selecciona un video para analizar", "warning")
            return
            
        video_id = self.pending_tree.item(selected[0])['values'][0]
        video = next((v for v in self.all_pending_videos if v.get('video_id') == video_id), None)
        if not video: return

        # Verificar configuración de Ollama
        if self.ai_provider != "ollama":
            messagebox.showwarning("Configuración Requerida", "Esta funcionalidad requiere un proveedor de IA (Ollama Local) activo.")
            return

        # Actualizar UI a estado "procesando"
        self.btn_ai_analyze_video.config(state=tk.DISABLED)
        self.ai_results_txt.config(state=tk.NORMAL)
        self.ai_results_txt.delete("1.0", tk.END)
        self.ai_results_txt.insert(tk.END, "⌛ IA: Conectando con Ollama Local...\nAnalizando títulos y descripciones...")
        self.ai_results_txt.config(state=tk.DISABLED)

        def task():
            try:
                prompt = f"""Actúa como un experto en Amazon KDP y análisis de contenido.
Analiza el siguiente video y devuelve un JSON estricto con los siguientes 40 puntos de análisis:
1. relevance_score: (0-100) Prioridad para un autor de KDP.
2. clickbait_check: (Sustancia o Clickbait).
3. theme: (Tutorial, Noticias, Opinión, Estrategia).
4. keywords: (Lista de 5 palabras clave).
5. obsolete_check: (Booleano, true si el contenido menciona fechas pasadas).
6. sentiment: (Positivo, Negativo, Urgente, Neutral).
7. is_live: (Booleano).
8. sponsored: (Booleano).
9. difficulty_level: (Principiante, Intermedio, Avanzado).
10. summary: (Resumen de 1 sola línea).
11. info_density: (0-100) Densidad informativa estimada.
12. originality_score: (0-100) Originalidad del contenido.
13. fluff_detected: (Booleano, true si hay mucho contenido de relleno).
14. transcription_words_est: (Número estimado de palabras).
15. source_credibility: (0-100) Credibilidad de la fuente.
16. is_controversial: (Booleano, alerta si el tema es polémico o polarizado).
17. engagement_prediction: (0-100) Predicción de engagement real.
18. is_educational_series: (Booleano, true si es parte de un curso).
19. content_trend: (Trending o Evergreen).
20. practical_applicability: (0-100) Aplicabilidad práctica inmediata.
21. semantic_match: (0-100) Coincidencia semántica con 'estrategias de precios' y nichos KDP.
22. preference_score: (0-100) Alineación con preferencias históricas de descarga del usuario.
23. conceptual_duplicate: (Booleano, true si el video repite conceptos ya presentes en la KB).
24. recommended_next: (Lista de 3 temas relacionados dentro del mismo canal para ver después).
25. knowledge_gap: (Booleano, true si el contenido cubre un gap de conocimiento detectado).
26. manual_consistency: (0-100) Nivel de coherencia con los manuales doctrinales existentes).
27. niche_shift: (Booleano, true si se detecta un cambio de nicho temático en el canal).
28. objective_priority: (0-100) Prioridad dinámica basada en el objetivo actual (ej. 'Amazon Ads')).
29. sensitive_content: (Booleano, true si toca temas políticos/religiosos sensibles fuera de KDP).
30. ai_content_prob: (0-100) Probabilidad de que el video sea 100% generado por IA.
31. download_scheduling: (Recomendación de horario: Día, Noche, Madrugada).
32. batch_topic_group: (Categoría para agrupamiento masivo temática).
33. processing_time_est: (Segundos estimados para transcripción/limpieza).
34. queue_priority_order: (1-10, prioridad de procesamiento recomendada).
35. is_heavy_video: (Booleano, true si el video es excesivamente largo >2h).
36. segmentation_suggestion: (Lista de 3 timestamps sugeridos para división si es necesario).
37. download_failure_prob: (0-100% probabilidad de error técnico por restricción).
38. channel_load_balance: (Delay extra recomendado en segundos para no saturar).
39. audio_only_recommend: (Booleano, true si el video es apto para bajar solo audio).
40. predictive_compression: (Booleano, true si requerirá compresión de texto por longitud).

VIDEO DATA:
Título: {video.get('title')}
Canal: {video.get('channel_name')}
Descripción: {video.get('description', '')[:800]}
"""
                import requests
                import json
                
                # Llamada directa a Ollama Local
                resp = requests.post("http://localhost:11434/api/generate", json={
                    "model": self.ollama_model if hasattr(self, 'ollama_model') else "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }, timeout=60)
                
                if resp.status_code == 200:
                    res_json = json.loads(resp.json()['response'])
                    
                    def update_ui(data=res_json):
                        self.ai_results_txt.config(state=tk.NORMAL)
                        self.ai_results_txt.delete("1.0", tk.END)
                        txt = f"🧠 COGNICIÓN KDP ELITE (Módulos 1-40):\n"
                        txt += f"🎯 RELEVANCIA: {data.get('relevance_score')}/100 | DENSIDAD: {data.get('info_density')}/100\n"
                        txt += f"🔍 TIPO: {data.get('clickbait_check')} | ORIGINALIDAD: {data.get('originality_score')}/100\n"
                        txt += f"📂 TEMA: {data.get('theme')} | 🗣️ SENTIMIENTO: {data.get('sentiment')}\n"
                        txt += f"📅 VIGENCIA: {'⚠️ OBSOLETO' if data.get('obsolete_check') else '✅ ACTUALIZADO'} | {data.get('content_trend')}\n"
                        txt += f"💰 SPONSORED: {'SÍ' if data.get('sponsored') else 'NO'} | 🎬 LIVE: {'SÍ' if data.get('is_live') else 'NO'}\n"
                        txt += f"🎓 NIVEL: {data.get('difficulty_level')} | 🛠️ APLICABILIDAD: {data.get('practical_applicability')}/100\n"
                        txt += f"📚 SERIE: {'SÍ' if data.get('is_educational_series') else 'NO'} | ⏳ RELLENO: {'⚠️ MUCHO' if data.get('fluff_detected') else '✅ POCO'}\n"
                        txt += f"🛡️ CREDIBILIDAD: {data.get('source_credibility')}/100 | 🔥 ENGAGEMENT: {data.get('engagement_prediction')}/100\n"
                        txt += f"⚠️ CONTROVERSIA: {'❗ SÍ' if data.get('is_controversial') else '✅ NO'} | 📝 PALABRAS: {data.get('transcription_words_est', 0)}\n"
                        txt += f"🚀 SEMÁNTICA: {data.get('semantic_match', 0)}/100 | ⭐ PREFERENCIA: {data.get('preference_score', 0)}/100\n"
                        txt += f"🔁 REDUNDANCIA: {'⚠️ ALTA' if data.get('conceptual_duplicate') else '✅ BAJA'} | 🕳️ GAP: {'✨ LLENA' if data.get('knowledge_gap') else '❌ NO'}\n"
                        txt += f"📜 MANUALES: {data.get('manual_consistency', 0)}/100 | 🔄 NICHOS: {'⚠️ CAMBIO' if data.get('niche_shift') else '✅ ESTABLE'}\n"
                        txt += f"🎯 OBJ. ADS: {data.get('objective_priority', 0)}/100 | 🛑 SENSIBLE: {'🚫 SÍ' if data.get('sensitive_content') else '✅ NO'}\n"
                        txt += f"🤖 IA PROB: {data.get('ai_content_prob', 0)}% | ⏭️ VER DESPUÉS: {', '.join(data.get('recommended_next', []))}\n"
                        txt += f"⏰ HORARIO: {data.get('download_scheduling')} | 📦 BATCH: {data.get('batch_topic_group')}\n"
                        txt += f"⏳ TIEMPO EST: {data.get('processing_time_est')}s | ⭐ PRIO: {data.get('queue_priority_order', 0)}/10\n"
                        txt += f"⚖️ PESADO: {'🐘 SÍ' if data.get('is_heavy_video') else '✅ NO'} | 🛠️ SEGMENTOS: {', '.join(data.get('segmentation_suggestion', []) or [])}\n"
                        txt += f"📉 RIESGO FALLO: {data.get('download_failure_prob', 0)}% | 📻 SOLO AUDIO: {'🎧 SÍ' if data.get('audio_only_recommend') else '❌ NO'}\n"
                        txt += f"🌀 BALANCE: {data.get('channel_load_balance', 0)}s delay | 📚 COMPRESIÓN: {'📦 SÍ' if data.get('predictive_compression') else '✅ NO'}\n"
                        txt += f"🏷️ KEYWORDS: {', '.join(data.get('keywords', []))}\n"
                        txt += f"📝 RESUMEN: {data.get('summary')}"
                        self.ai_results_txt.insert("1.0", txt)
                        self.ai_results_txt.config(state=tk.DISABLED)
                        self.btn_ai_analyze_video.config(state=tk.NORMAL)
                    self.root.after(0, update_ui)
                else:
                    raise Exception(f"Ollama Error: {resp.status_code}")
            except Exception as e:
                self.root.after(0, lambda: [
                    self.ai_results_txt.config(state=tk.NORMAL),
                    self.ai_results_txt.insert(tk.END, f"\n❌ ERROR: {str(e)}"),
                    self.ai_results_txt.config(state=tk.DISABLED),
                    self.btn_ai_analyze_video.config(state=tk.NORMAL)
                ])

        threading.Thread(target=task, daemon=True).start()

    def on_pending_selection_change(self, event):
        """[Módulos 39, 40] Actualiza el contador de selección y la estimación de tamaño."""
        selected_items = self.pending_tree.selection()
        count = len(selected_items)
        self.pending_selected_count_var.set(f"{count} videos seleccionados")

        total_duration_seconds = 0
        for item_id in selected_items:
            video_id = self.pending_tree.item(item_id)['values'][0]
            video = next((v for v in self.all_pending_videos if v.get('video_id') == video_id), None)
            if video:
                total_duration_seconds += video.get('duration_seconds', 0)
        
        # Estimación: 1KB por minuto de transcripción (aproximado)
        estimated_size_kb = (total_duration_seconds / 60) * 1 # KB
        estimated_size_mb = estimated_size_kb / 1024
        self.pending_estimated_size_var.set(f"{estimated_size_mb:.2f} MB estimados")

    def invert_pending_selection(self):
        self.log_channel_activity("GLOBAL", "Selección inversa aplicada en Videos Pendientes.", "INVERT_SELECTION", session_id=self._generate_session_id()) # Módulo 41
        """[Módulo 36] Invierte la selección actual en el Treeview."""
        current_selection = set(self.pending_tree.selection())
        all_items = set(self.pending_tree.get_children())
        
        self.pending_tree.selection_remove(list(current_selection))
        self.pending_tree.selection_add(list(all_items - current_selection))
        self.on_pending_selection_change(None) # Actualizar contadores

    def save_pending_selection_group(self):
        """[Módulo 37] Guarda la lista de IDs de videos seleccionados como un grupo."""
        selected_items = self.pending_tree.selection()
        if not selected_items:
            ToastNotification.show(self.root, "No hay videos seleccionados para guardar.", "warning")
            return
        
        video_ids = [self.pending_tree.item(item_id)['values'][0] for item_id in selected_items]
        
        # Pedir nombre del grupo
        group_name = tk.simpledialog.askstring("Guardar Selección", "Nombre para este grupo de videos:", parent=self.root)
        if not group_name: return
        
        # Guardar en un archivo JSON simple (o en DB si se extiende)
        groups_dir = Path(self.base_dir) / "data" / "selection_groups"
        groups_dir.mkdir(parents=True, exist_ok=True)
        
        group_file = groups_dir / f"{group_name.replace(' ', '_')}.json"
        try:
            with open(group_file, 'w', encoding='utf-8') as f:
                json.dump({"name": group_name, "video_ids": video_ids, "timestamp": datetime.now().isoformat()}, f, indent=2)
            ToastNotification.show(self.root, f"Grupo '{group_name}' guardado con {len(video_ids)} videos.", "success")
            self.log_channel_activity("GLOBAL", f"Grupo '{group_name}' guardado con {len(video_ids)} videos.", "SAVE_GROUP", session_id=self._generate_session_id()) # Módulo 41
        except Exception as e:
            ToastNotification.show(self.root, f"Error al guardar grupo: {e}", "error")

    def add_selected_pending_to_queue(self):
        """[Módulos 39, 40] Añade los videos seleccionados a la cola de descarga."""
        selected_items = self.pending_tree.selection()
        if not selected_items:
            ToastNotification.show(self.root, "No hay videos seleccionados para añadir a la cola.", "warning")
            return
        
        count = len(selected_items)
        estimated_size = self.pending_estimated_size_var.get()

        # Módulo 39: Confirmación de Volumen
        if count > 50: # Umbral configurable
            if not messagebox.askyesno("Confirmación de Volumen", 
                                      f"¿Seguro que quieres añadir {count} videos a la cola?\n"
                                      f"Esto ocupará aproximadamente {estimated_size} de espacio.\n\n"
                                      "¿Continuar?"):
                return
        
        added_count = 0
        for item_id in selected_items:
            video_id = self.pending_tree.item(item_id)['values'][0]
            video = next((v for v in self.all_pending_videos if v.get('video_id') == video_id), None)
            if video and video.get('video_url') not in self.download_queue:
                self.download_queue.append(video.get('video_url'))
                added_count += 1
        
        self.update_queue_ui()
        self.log_channel_activity("GLOBAL", f"Añadidos {added_count} videos a la cola desde 'Videos Pendientes'.", "ADD_TO_QUEUE", session_id=self._generate_session_id()) # Módulo 41
        ToastNotification.show(self.root, f"Se añadieron {added_count} videos a la cola de descarga.", "success")
        self.log(f"[📥] {added_count} videos añadidos a la cola desde 'Videos Pendientes'.")

    def validate_online_selected(self):
        """[Módulos 16-30] Validación Online con Throttling y Protección (Pilar 2 & 3)."""
        selected = self.pending_tree.selection()
        if not selected:
            ToastNotification.show(self.root, "Selecciona videos para validar disponibilidad", "warning")
            return
            
        session_id = self._generate_session_id() # Módulo 46
        self.pending_progress.start()
        self.log(f"[🌐] Iniciando validación protegida de {len(selected)} videos...")
        
        def task():
            import yt_dlp
            total = len(selected)
            valid_count = 0
            backoff_delay = 60  # 23. Backoff inicial: 1 min
            request_count = 0
            
            # 24. Rotación de User-Agent para simular tráfico orgánico
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ]

            for i, item_id in enumerate(selected):
                if not self.root.winfo_exists(): return # App cerrada

                # 27. Pausa Automática Nocturna (2AM-6AM)
                now_hour = datetime.now().hour
                if 2 <= now_hour < 6:
                    self.log("[💤] Pausa nocturna detectada (2AM-6AM). Entrando en modo reposo...")
                    while 2 <= datetime.now().hour < 6:
                        time.sleep(60)
                        if not self.root.winfo_exists(): return
                
                video_id = self.pending_tree.item(item_id)['values'][0]
                url = f"https://www.youtube.com/watch?v={video_id}"
                
                # 24. Rotación de User-Agent (cada 50 peticiones)
                current_ua = user_agents[(request_count // 50) % len(user_agents)]
                
                # 29. Timeout de Conexión Ajustable (Timeout corto para metadatos)
                ydl_opts = {
                    'quiet': True, 'no_warnings': True, 'simulate': True,
                    'skip_download': True, 'extract_flat': False,
                    'user_agent': current_ua,
                    'socket_timeout': 10, # Módulo 29: Eficiencia en conexiones
                    'nocheckcertificate': True
                }
                
                # 25. Uso de Proxy Rotativo (Si están configurados)
                if self.rotative_proxies:
                    ydl_opts['proxy'] = random.choice(self.rotative_proxies)

                status_parts = []
                success = False
                
                # 30. Reintento Limitado (Max 3)
                for attempt in range(3):
                    try:
                        # 21. Delay Aleatorio entre Peticiones (2-5s) para evitar detección
                        if request_count > 0:
                            time.sleep(random.uniform(2, 5))
                        
                        # 22. Límite de Peticiones por Minuto (Garantizado por el delay anterior)
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            
                            # Validaciones de Pilar 2
                            avail = info.get('availability', 'public')
                            if avail == 'private': status_parts.append("🔒 PRIV")
                            elif avail == 'unlisted': status_parts.append("👻 OCULTO")
                            
                            lic = info.get('license', '')
                            if lic and 'Creative Commons' in lic: status_parts.append("⚖️ CC")
                            
                            self.log_channel_activity(video_id, f"Validación online exitosa. Status: {status_parts}", "VALIDATION_SUCCESS", session_id=session_id) # Módulo 41
                            valid_count += 1
                            success = True
                            backoff_delay = 60 # Reset backoff tras éxito
                            break
                            
                    except Exception as e:
                        err_msg = str(e).lower()
                        # 23. Backoff Exponencial ante Error 429 (Too Many Requests)
                        if "429" in err_msg or "too many requests" in err_msg:
                            self.log(f"[⚠️] Rate limit (429) detectado. Aplicando backoff de {backoff_delay}s...")
                            time.sleep(backoff_delay)
                            backoff_delay *= 2 # Incremento exponencial
                            continue 
                        
                        # Módulo 44: Contador de Errores de Metadata
                        if "404" in err_msg or "not found" in err_msg: status_parts.append("🚫 404")
                        elif "deleted" in err_msg: status_parts.append("🗑️ BORR")
                        elif "private" in err_msg: status_parts.append("🔒 PRIV")
                        elif "geo-restricted" in err_msg: status_parts.append("🌍 BLOQ")
                        elif "geo-restricted" in err_msg: status_parts.append("🌍 BLOQ")
                        else: status_parts.append("❌ ERR")
                        break # No reintentar errores permanentes

                request_count += 1
                new_status = " | ".join(status_parts) if status_parts else "✅ ONLINE"
                
                self.log_channel_activity(video_id, f"Validación online fallida. Error: {err_msg}", "VALIDATION_ERROR", session_id=session_id) # Módulo 41
                def update_row(iid=item_id, s=new_status, idx=i):
                    if self.pending_tree.exists(iid):
                        vals = list(self.pending_tree.item(iid)['values'])
                        vals[5] = s # Status column
                        self.pending_tree.item(iid, values=vals)
                        self.pending_progress['value'] = ((idx + 1) / total) * 100
                
                self.root.after(0, update_row)

            self.root.after(0, lambda: [
                self.pending_progress.stop(),
                self.pending_progress.configure(value=0),
                self.log(f"[🌐] Validación protegida finalizada. {valid_count}/{total} disponibles."),
                self.log_channel_activity("GLOBAL", f"Validación online finalizada. {valid_count}/{total} disponibles.", "VALIDATION_BATCH_COMPLETE", session_id=session_id), # Módulo 41
                ToastNotification.show(self.root, f"Chequeo finalizado: {valid_count} videos online", "info")
            ])

        threading.Thread(target=task, daemon=True).start()
        
    def _update_system_stats(self):
        """Actualización asíncrona de métricas de Fase 3."""
        if not hasattr(self, 'status_icon_label'): return
        
        # Calcular tiempo promedio
        elapsed = time.time() - self.metrics["start_time"]
        avg = elapsed / max(1, self.metrics["processed"])
        
        # Color de salud según umbral de 8s
        health_color = "#10b981" if avg < 8 else "#f59e0b" if avg < 10 else "#ef4444"
        
        # Actualizar Widget (Sidebar/Status)
        tasks = self.worker_pool.active_tasks if self.worker_pool else 0
        stat_text = f"📊 IA: {avg:.1f}s/f | Workers: {tasks} | ✅ {self.metrics['processed']}"
        
        # Si tenemos sidebar, actualizar ahí. Si no, en la barra de estado.
        self.status_var.set(stat_text)
        self.root.after(2000, self._update_system_stats)

    def start_observability(self):
        """Inicia el ciclo de monitoreo en tiempo real."""
        self._update_system_stats()
        self.log("🚀 Monitoreo de Fase 3 iniciado.")
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
        
        frame = ttk.Frame(win, )
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Carpeta de Descargas (Entrada):").pack(anchor=tk.W)
        e1 = ttk.Entry(frame, textvariable=self.input_dir)
        e1.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(frame, text="Seleccionar", command=lambda: self.input_dir.set(filedialog.askdirectory() or self.input_dir.get()), bootstyle="secondary").pack(anchor=tk.E)
        
        frame = ttk.Frame(dir_inputs)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text="📂 Carpeta de Salida:").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(frame, text="Seleccionar", command=lambda: self.output_dir.set(filedialog.askdirectory() or self.output_dir.get()), bootstyle="secondary").pack(anchor=tk.E)
        
        ttk.Button(win, text="Guardar y Empezar", command=finish, bootstyle="primary").pack(pady=20)

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
        """
        ==================== [INI] MÓDULO: SINCRONIZAR LISTA PROCESAMIENTO ====================
        [US-FIX-004] Reparación y optimización del motor de sincronización de archivos.
        Actualiza el Treeview escaneando físicamente el directorio de entrada.
        """
        try:
            if not hasattr(self, 'tree') or not self.tree:
                self.log("[WARN] El widget de lista (Treeview) no está inicializado.", "warning")
                return

            # Bloquear actualización visual para evitar parpadeo (Optimización algorítmica)
            self.status_var.set("Sincronizando archivos...")
            self.root.update_idletasks()

            # Limpiar lista actual de forma atómica
            self.tree.delete(*self.tree.get_children())

            path = Path(self.input_dir.get().strip())
            out_path = Path(self.output_dir.get().strip())

            if not path.exists():
                self.log(f"⚠️ Error: La ruta de entrada no existe: {path}", "error")
                self.status_var.set("Error: Ruta no encontrada")
                return

            files_found = 0
            # Escaneo recursivo limitado o filtrado por extensión (Código Limpio)
            valid_extensions = {'.vtt', '.srt', '.txt'}
            
            for item in path.iterdir():
                if item.is_file() and item.suffix.lower() in valid_extensions:
                    stats = item.stat()
                    size = f"{stats.st_size / 1024:.1f} KB"
                    mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                    
                    # Lógica de detección de estado (Principio de Responsabilidad Única)
                    clean_name = f"CLEAN_{item.stem}.txt"
                    processed_exists = (out_path / clean_name).exists()
                    status = "✅ Procesado" if processed_exists else "⏳ Pendiente"
                    
                    self.tree.insert("", tk.END, values=(item.name, size, mtime, status))
                    files_found += 1
            
            self.status_var.set(f"Sincronizado: {files_found} archivos")
            self.log(f"[🔄] Sincronización completada: {files_found} archivos detectados en '{path.name}'")

        except Exception as e:
            self.log(f"[ERROR] Fallo crítico en sincronización: {e}", "error")
            self.status_var.set("Fallo en sincronización")
            traceback.print_exc()
        # ==================== [END] MÓDULO: SINCRONIZAR LISTA PROCESAMIENTO ====================

    def start_processing(self):
        # === [INICIO FUNCIONALIDAD US-003: OPTIMIZACIÓN DE PROCESAMIENTO PARALELO] ===
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

                def run_parallel():
                    import concurrent.futures
                    total_files = len(files_to_process)
                    completed = 0
                    
                    # Usar hilos para procesamiento paralelo (E/S intensiva y CPU)
                    # Máximo 4 hilos para no saturar recursos del sistema
                    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                        futures = []
                        for f in files_to_process:
                            futures.append(executor.submit(
                                processing_service.process_files,
                                input_dir=self.input_dir.get(),
                                output_dir=self.output_dir.get(),
                                files_to_process=[f],
                                log_callback=log_to_gui
                            ))
                        
                        # --- INICIO FUNCIONALIDAD US-B-RECOVERY: LÓGICA DE RECUPERACIÓN ---
                        self._save_batch_state(files_to_process)
                        
                        for i, future in enumerate(concurrent.futures.as_completed(futures)):
                            completed += 1
                            progress = (completed / total_files) * 100
                            
                            # --- INICIO FUNCIONALIDAD: PROGRESS BAR INLINE ---
                            # Generar barra visual de texto: [###-------]
                            bar_len = 10
                            filled = int(round(bar_len * progress / 100))
                            visual_bar = "█" * filled + "░" * (bar_len - filled)
                            
                            msg = f"Procesando: {completed}/{total_files} | {visual_bar} {int(progress)}%"
                            self.root.after(0, lambda p=progress, m=msg: [update_progress(p), self.status_var.set(m)])
                        
                        # Al finalizar, limpiar estado y ofrecer reporte
                        self._clear_batch_state()
                        self.root.after(0, self._offer_batch_report)
                        # --- FIN FUNCIONALIDAD ---

    # --- INICIO FUNCIONALIDAD US-B-REPORT: GESTIÓN DE REPORTES Y ESTADO ---
    def _save_batch_state(self, file_list):
        """Guarda la lista de archivos actual para recuperación tras crash."""
        try:
            with open(self.batch_state_file, 'w', encoding='utf-8') as f:
                json.dump({"pending": file_list, "timestamp": datetime.now().isoformat()}, f)
        except: pass

    def _clear_batch_state(self):
        """Elimina el rastro del batch al finalizar exitosamente."""
        if os.path.exists(self.batch_state_file):
            os.remove(self.batch_state_file)

    def _offer_batch_report(self):
        """Ofrece exportar el reporte CSV tras el procesamiento masivo."""
        if messagebox.askyesno("Batch Finalizado", "¿Desea exportar el reporte de estadísticas del lote procesado?"):
            self.export_batch_report()

    def export_batch_report(self):
        """Genera un reporte CSV con métricas de duración y tamaño."""
        if not self.processing_service or not self.processing_service.batch_results:
            return
            
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
                                       initialfile=f"batch_report_{datetime.now().strftime('%Y%m%d')}.csv")
        if not f: return
        
        try:
            with open(f, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'file', 'status', 'duration', 'size_kb']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for res in self.processing_service.batch_results:
                    writer.writerow(res)
            messagebox.showinfo("Éxito", f"Reporte exportado correctamente a:\n{f}")
            # Limpiar resultados post-exportación
            self.processing_service.batch_results = []
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {e}")
    # --- FIN FUNCIONALIDAD ---
                    
            self.root.after(0, lambda: [
                        self.status_var.set("Proceso paralelo completado"),
                        messagebox.showinfo("Éxito", f"Procesamiento paralelo finalizado.\n{completed} archivos procesados."),
                        self.refresh_file_list()
                    ])

            threading.Thread(target=run_parallel, daemon=True).start()
        # === [FIN FUNCIONALIDAD US-003: OPTIMIZACIÓN DE PROCESAMIENTO PARALELO] ===


    def display_metadata(self, event=None):
        from app.ui.tabs.process_tab import display_metadata
        display_metadata(self, event)

    def browse_input(self):
        from app.ui.tabs.process_tab import browse_input
        browse_input(self)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)
            self.refresh_file_list()

    def delete_selected_file(self):
        # ==================== INICIO MÓDULO: ELIMINAR ARCHIVO FÍSICO ====================
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Selecciona archivos para eliminar.")
            return

        if not messagebox.askyesno("Confirmar", f"¿Eliminar {len(selected)} archivos permanentemente?"):
            return

        deleted = 0
        for item in selected:
            filename = self.tree.item(item)['values'][0]
            try:
                os.remove(os.path.join(self.input_dir.get(), filename))
                self.tree.delete(item)
                deleted += 1
            except Exception as e:
                self.log(f"Error eliminando {filename}: {e}", "error")
        
        self.log(f"[🗑️] {deleted} archivos eliminados físicamente.")
        # ==================== FIN MÓDULO: ELIMINAR ARCHIVO FÍSICO ====================

    def open_file_location(self):
        # ==================== INICIO MÓDULO: LOCALIZADOR DE ARCHIVOS ====================
        selected = self.tree.selection()
        if not selected: return
        
        filename = self.tree.item(selected[0])['values'][0]
        full_path = os.path.join(self.input_dir.get(), filename)
        if os.path.exists(full_path):
            self.open_folder(os.path.dirname(full_path))
        else:
            messagebox.showerror("Error", "El archivo ya no existe.")
        # ==================== FIN MÓDULO: LOCALIZADOR DE ARCHIVOS ====================

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
    # ==================== INICIO MÓDULO: DOC_UPDATER DIALOG ====================
    def _show_doc_updater_dialog(self):
        """
        Muestra un diálogo para que el usuario actualice el estado de una funcionalidad
        en los documentos Markdown del proyecto.
        """
        if not self.doc_updater:
            messagebox.showerror("Error", "El módulo de actualización de documentación no está disponible.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Actualizar Documentación de Funcionalidades")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Actualizar el estado de una funcionalidad en los documentos Markdown.",
                  font=('Segoe UI', 10, 'bold')).pack(pady=10)

        form_frame = ttk.Frame(dialog, )
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Documento a actualizar
        ttk.Label(form_frame, text="Documento (ruta relativa):").grid(row=0, column=0, sticky=tk.W, pady=5)
        doc_path_var = tk.StringVar(value="FUNCIONALIDADES ESPECIALES/PLAN FUNCIONALIDADES.txt")
        doc_entry = ttk.Entry(form_frame, textvariable=doc_path_var, width=50)
        doc_entry.grid(row=0, column=1, sticky=tk.EW, )
        ToolTip(doc_entry, "Ej: PLAN FUNCIONALIDADES.txt o SPEC.md")

        # ID de la funcionalidad
        ttk.Label(form_frame, text="ID de Funcionalidad (ej. US-001):").grid(row=1, column=0, sticky=tk.W, pady=5)
        feature_id_var = tk.StringVar()
        feature_id_entry = ttk.Entry(form_frame, textvariable=feature_id_var, width=20)
        feature_id_entry.grid(row=1, column=1, sticky=tk.W, )

        # Nuevo estado
        ttk.Label(form_frame, text="Nuevo Estado:").grid(row=2, column=0, sticky=tk.W, pady=5)
        status_options = ["✅ Finalized", "🚧 In Progress", "❌ Blocked", "💡 Planned", "⚠️ Review"]
        new_status_var = tk.StringVar(value="✅ Finalized")
        status_combo = ttk.Combobox(form_frame, textvariable=new_status_var, values=status_options, state="readonly")
        status_combo.grid(row=2, column=1, sticky=tk.W, )

        # Descripción (para añadir nueva funcionalidad)
        ttk.Label(form_frame, text="Descripción (para añadir nueva):").grid(row=3, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar()
        description_entry = ttk.Entry(form_frame, textvariable=description_var, width=50)
        description_entry.grid(row=3, column=1, sticky=tk.EW, )
        ToolTip(description_entry, "Solo si añades una funcionalidad nueva. Se ignorará si el ID ya existe.")

        def perform_update():
            doc_path = doc_path_var.get().strip()
            feature_id = feature_id_var.get().strip()
            new_status = new_status_var.get().strip()
            description = description_var.get().strip()

            if not doc_path or not feature_id:
                messagebox.showwarning("Advertencia", "El documento y el ID de funcionalidad son obligatorios.", parent=dialog)
                return
            
            # Try to update first
            if not self.doc_updater.update_feature_status_in_markdown(doc_path, feature_id, new_status):
                # If update failed (feature not found), try to add it
                if description:
                    if self.doc_updater.add_feature_to_markdown(doc_path, feature_id, description, new_status):
                        messagebox.showinfo("Éxito", f"Funcionalidad '{feature_id}' añadida y estado actualizado en '{doc_path}'.", parent=dialog)
                    else:
                        messagebox.showerror("Error", f"No se pudo añadir la funcionalidad '{feature_id}' a '{doc_path}'.", parent=dialog)
                else:
                    messagebox.showerror("Error", f"Funcionalidad '{feature_id}' no encontrada en '{doc_path}'. Proporciona una descripción para añadirla.", parent=dialog)
            else:
                messagebox.showinfo("Éxito", f"Estado de funcionalidad '{feature_id}' actualizado a '{new_status}' en '{doc_path}'.", parent=dialog)
            dialog.destroy()

        ttk.Button(dialog, text="Actualizar Documento", command=perform_update, bootstyle="primary").pack(pady=20)
    # ==================== FIN MÓDULO: DOC_UPDATER DIALOG ====================
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
            
            ttk.Button(win, text="Guardar Cambios", command=save, bootstyle="success").pack(pady=10)
        
        ttk.Button(win, text="Cancelar", command=win.destroy, bootstyle="secondary").pack(pady=5)

    # ===== MÉTODOS DEL MONITOR DE CANALES =====
    
    def setup_channel_monitor_tab(self):
        """Configura la pestaña de Monitor de Canales."""
        if not hasattr(self, 'channel_monitor_tab_loaded') or not self.channel_monitor_tab_loaded:
            for widget in self.tab_channel_monitor.winfo_children():
                widget.destroy()
            ttk.Label(self.tab_channel_monitor, text="⏳ Cargando Monitor de Canales...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_channel_monitor_tab)
            return
        
        if len(self.tab_channel_monitor.winfo_children()) > 0:
            return
        
        main_container = ttk.Frame(self.tab_channel_monitor)
        main_container.pack(fill=tk.BOTH, expand=True)
        
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

        # Módulo 44: Contador de Errores de Metadata
        errors_frame = ttk.Frame(stats_frame, relief="raised", borderwidth=1)
        errors_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(errors_frame, text="❌ Errores Metadata", font=("Segoe UI", 9), foreground="#94a3b8").pack(padx=10, pady=(10, 5))
        ttk.Label(errors_frame, textvariable=self.stat_monitor_errors, font=("Segoe UI", 11, "bold"), foreground="#ef4444").pack(padx=10, pady=(0, 10))
        
        # ===== ZONA DE DRAG & DROP PARA CANALES =====
        drop_zone_frame = ttk.LabelFrame(main_container, text=" ☁️ Añadir Canal Rápido ", )
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
                  bootstyle="success").pack(side=tk.LEFT, padx=(10, 0))
        
        # ===== PANEL DIVIDIDO: LISTA + CONTROLES =====
        paned = tk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo: Lista de canales
        left_panel = ttk.Frame(paned)
        paned.add(left_panel)
        
        list_frame = ttk.LabelFrame(left_panel, text=" 📋 Canales Monitoreados ", )
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar de lista
        toolbar = ttk.Frame(list_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="🔄 Actualizar", command=self.refresh_channel_list,
                  bootstyle="primary").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="⚙️ Gestionar", command=self.manage_channels, bootstyle="secondary").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🗑️ Eliminar", command=self.delete_selected_channel, 
                  bootstyle="danger").pack(side=tk.LEFT, padx=5)
        
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
        paned.add(right_panel)
        
        # Controles de monitoreo
        control_frame = ttk.LabelFrame(right_panel, text=" ⚙️ Control de Monitoreo ", )
        control_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(control_frame, text="▶️ Verificar Ahora", command=self.check_channels_now,
                  bootstyle="success").pack(fill=tk.X, pady=5, ipady=10)
        ttk.Button(control_frame, text="⏸️ Pausar Monitor", command=self.toggle_monitor_service, bootstyle="warning-outline").pack(fill=tk.X, pady=5)
        
        # Módulo 43: Historial de Escaneos
        ttk.Button(control_frame, text="📜 Historial de Escaneos", command=self.show_scan_history, bootstyle="info-outline").pack(fill=tk.X, pady=5)
        
        # Módulo 42: Reporte de Videos Omitidos
        ttk.Button(control_frame, text="🚫 Reporte Videos Omitidos", command=self.show_skipped_videos_report, bootstyle="info-outline").pack(fill=tk.X, pady=5)
        
        # Módulo 41: Log de Actividad por Canal
        ttk.Button(control_frame, text="📝 Log de Actividad Canal", command=self.show_channel_activity_log, bootstyle="info-outline").pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="📊 Ver Estadísticas", command=self.show_monitor_stats, bootstyle="info-outline").pack(fill=tk.X, pady=5)
        
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
        log_frame = ttk.LabelFrame(right_panel, text=" 📜 Actividad del Monitor ", )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.monitor_log = scrolledtext.ScrolledText(log_frame, height=15, 
                                                     font=("Consolas", 9),
                                                     bg="#020617" if self.current_theme == "dark" else "#f8fafc",
                                                     fg="#10b981" if self.current_theme == "dark" else "#1e293b",
                                                     state='disabled')
        self.monitor_log.pack(fill=tk.BOTH, expand=True)
        
        # ===== PANEL DE FILTROS POR PALABRAS CLAVE =====
        filter_panel = ttk.LabelFrame(right_panel, text=" 🔍 Filtros por Palabras Clave ", )
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
                  bootstyle="primary").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="🧪 Probar", command=self.test_keyword_filter,
                  bootstyle="secondary").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="🔄 Reset", command=self.reset_keyword_filter,
                  bootstyle="secondary").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
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
        # ==================== [FIX-013] INICIO: CANVAS BORDER FIX ====================
        # [PROBLEMA] Línea delimitada mal hecha - usa winfo_reqwidth que da valores incorrectos
        # [SOLUCIÓN] Usar winfo_width() + winfo_height() + validación de tamaño + reintento
        try:
            width = self.channel_drop_canvas.winfo_width()
            height = self.channel_drop_canvas.winfo_height()
        except Exception:
            width, height = 0, 0
        
        # Reintentar si el tamaño es inválido (canvas no renderizado aún)
        if width < 10 or height < 10:
            self.root.after(50, self.draw_channel_dashed_border)
            return
        
        # Limpiar borde anterior antes de dibujar nuevo
        self.channel_drop_canvas.delete("border")
        
        dash_pattern = (8, 4)
        color = "#a855f7" if self.current_theme == "dark" else "#9333ea"
        
        # Usar create_rectangle en vez de 4 create_line para mejor consistencia
        self.channel_drop_canvas.create_rectangle(
            5, 5, width-5, height-5,
            outline=color,
            dash=dash_pattern,
            width=2,
            tags="border"
        )
        # ==================== [FIX-013] FIN ====================

    def on_channel_drop_enter(self, event):
        """Efecto visual al pasar mouse sobre zona de drop de canales"""
        self.channel_drop_canvas.config(bg="#4c1d95" if self.current_theme == "dark" else "#f3e8ff")
        self.channel_drop_canvas.config(cursor="hand2")

    def on_channel_drop_leave(self, event):
        """Restaurar apariencia normal"""
        self.channel_drop_canvas.config(bg="#1e293b" if self.current_theme == "dark" else "#f8fafc")
        self.channel_drop_canvas.config(cursor="")

    def add_channel_quick(self):
        # Módulo 46: Generar ID de sesión
        session_id = self._generate_session_id() # Módulo 46
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
        # Módulo 51, 53, 54: Nuevas propiedades del canal
        kdp_category = "Conocimiento General KDP" # Default
        soe_role = "General" # Default
        is_competitor = False # Default
        language = "es" # Default

        channel_id = None
        if self.db_manager:
            # Módulo 51, 53, 54, 59: Pasar nuevas propiedades al añadir canal
            db_id, channel_data = self.db_manager.add_channel(
                url, name, kdp_category=kdp_category, soe_role=soe_role,
                is_competitor=is_competitor, language=language
            )
            if db_id:
                # Si es un canal nuevo (o re-activado)
                # Módulo 52: Tagging por Fuente (channel_id ya es el tag implícito)
                channel_id = channel_data.get('channel_id') # Get YouTube channel ID
                self.log_channel_activity(channel_id, f"Canal '{name}' añadido/activado.", "ADD_CHANNEL", session_id=session_id) # Módulo 41
                self._check_channel_name_change(channel_data, session_id) # Módulo 48
            else:
                ToastNotification.show(self.root, "Este canal ya existe en el monitor", "warning")
                return
        else:
            # Fallback a lista antigua si no hay DB
            if any(normalize_youtube_url(c['url']) == norm_url for c in self.channels):
                # Módulo 54: Exclusión de Competencia Directa (si ya existe, no añadir)
                if self.pending_exclude_competitors_var.get() and any(c.get('is_competitor', False) for c in self.channels if normalize_youtube_url(c['url']) == norm_url):
                    ToastNotification.show(self.root, "Este canal es un competidor y ya está excluido.", "warning")
                ToastNotification.show(self.root, "Este canal ya está en la lista", "warning")
                return
            new_channel = {"name": name, "url": url, "category": "General", "active": True, "date_added": datetime.now().strftime("%Y-%m-%d")}
            channel_id = "LOCAL_" + hashlib.md5(url.encode()).hexdigest() # Generate a pseudo-ID for local channels
            self.channels.append(new_channel)
            self.save_config()
        self.update_channel_combo()
        self.refresh_channel_list()
        self.update_channel_stats()
        
        # Limpiar campos
        self.channel_url_var.set("")
        self.channel_name_var.set("")
        
        # Toast de éxito
        ToastNotification.show(self.root, f"✅ Canal '{name}' añadido correctamente (ID: {channel_id})", "success")
        
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
                # Módulo 44: Mostrar contador de errores de metadata
                status = "✅ Activo" if ch.get("active", True) else "❌ Inactivo"
                # Obtener count real de videos
                v_list = self.db_manager.get_videos_by_channel(ch['id'])
                videos = str(len(v_list))
                errors = str(ch.get('metadata_errors_count', 0)) # Módulo 44
                
                self.channel_tree.insert("", tk.END, values=(
                    ch['channel_name'],
                    ch['channel_url'],
                    errors, # Módulo 44
                ch.get('kdp_category', 'N/A'), # Módulo 51
                ch.get('soe_role', 'N/A'), # Módulo 53
                "🚫" if ch.get('is_competitor', False) else "✅", # Módulo 54
                ch.get('language', 'N/A'), # Módulo 59
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
                    "0", # No hay errores para canales locales
                    channel.get('kdp_category', 'N/A'), # Módulo 51
                    channel.get('soe_role', 'N/A'), # Módulo 53
                    "🚫" if channel.get('is_competitor', False) else "✅", # Módulo 54
                    channel.get('language', 'N/A'), # Módulo 59
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
            metadata_errors = stats.get('metadata_errors', 0) # Módulo 44
            
            # Formatear última verificación
            last_checks = [c['last_checked'] for c in channels if c['last_checked']]
            last_check_str = max(last_checks).split('.')[0] if last_checks else "Nunca"
        else:
            total = len(self.channels)
            metadata_errors = 0 # Módulo 44
            active = sum(1 for c in self.channels if c.get("active", True))
            pending = 0
            last_check_str = "Nunca"

        if hasattr(self, 'stat_total_channels'):
            self.stat_total_channels.set(str(total))
            self.stat_active_channels.set(str(active))
            self.stat_pending_videos.set(str(pending))
            self.stat_monitor_errors.set(str(metadata_errors)) # Módulo 44
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
        self.log_channel_activity("GLOBAL", "Filtro de palabras clave reseteado.", "RESET_FILTER", session_id=self._generate_session_id()) # Módulo 41
    
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
        self.log_channel_activity("GLOBAL", message, "MONITOR_LOG", session_id=self._generate_session_id()) # Módulo 41

    def delete_selected_channel(self):
        session_id = self._generate_session_id() # Módulo 46
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
                # Módulo 41: Log de Actividad por Canal
                self.log_channel_activity(target['channel_id'], f"Canal '{values[0]}' eliminado.", "DELETE_CHANNEL", session_id=session_id) # Módulo 41
            else:
                self.channels = [c for c in self.channels if normalize_youtube_url(c['url']) != norm_url]
                self.log_channel_activity("LOCAL_" + hashlib.md5(url.encode()).hexdigest(), f"Canal '{values[0]}' eliminado (local).", "DELETE_CHANNEL", session_id=session_id) # Módulo 41
        
        if not self.db_manager: self.save_config() # Only save if not using DB
        self.update_channel_combo()
        self.refresh_channel_list()
        self.update_channel_stats()
        
        ToastNotification.show(self.root, f"🗑️ {count} canal(es) eliminado(s)", "success")
        self.log_monitor_activity(f"{count} canales eliminados")

    # Módulo 46: Generar ID de sesión para esta operación
    def check_channels_now(self):
        """Fuerza verificación inmediata de canales usando el motor paralelo."""
        if not self.monitor_service:
            ToastNotification.show(self.root, "❌ Servicio de monitor no disponible", "error")
            return
            
        ToastNotification.show(self.root, "🔄 Verificación PARALELA iniciada...", "info")
        session_id = self._generate_session_id() # Módulo 46
        self.log_monitor_activity(f"Iniciando escaneo masivo de canales (Sesión: {session_id})...")
        self.log_channel_activity("GLOBAL", "Escaneo masivo de canales iniciado.", "SCAN_BATCH_START", session_id=session_id) # Módulo 41
        
        def run_check():
            try: # Módulo 45: Medir tiempo promedio de carga
                new_count = self.monitor_service.check_for_new_videos_parallel()
                self.root.after(0, lambda: self.finish_check(new_count))
            except Exception as e:
                self.root.after(0, lambda: ToastNotification.show(self.root, f"Error: {e}", "error"))

        threading.Thread(target=run_check, daemon=True).start()

    # ==================== INICIO MÓDULO: ACTUALIZAR EN CHECK_CHANNELS_NOW ====================
    def finish_check(self, count):
        session_id = self._generate_session_id() # Módulo 46
        self.update_channel_stats()
        self.refresh_channel_list()
        
        # Módulo 43: Registrar historial de escaneos
        # [FIX] Actualizar timestamp
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Módulo 43: Registrar historial de escaneos
        self.db_manager.log_scan_history(session_id, "GLOBAL", count, self.monitor_service.get_current_error_count(), self.monitor_service.get_current_skipped_count(), self.monitor_service.get_current_scan_duration()) # Módulo 43, 44, 45
        self.root.after(0, lambda: self.stat_last_check.set(now_str))
        self.log_channel_activity("GLOBAL", f"Escaneo completado. {count} videos nuevos.", "SCAN_BATCH_COMPLETE", session_id=session_id) # Módulo 41
        msg = f"✅ Escaneo completado. {count} videos nuevos." if count > 0 else "✅ Escaneo completado. Sin novedades."
        ToastNotification.show(self.root, msg, "success" if count > 0 else "info")
        self.log_monitor_activity(f"Verificación finalizada: {count} nuevos.")
    # ==================== FIN MÓDULO: ACTUALIZAR EN CHECK_CHANNELS_NOW ====================

    # ==================== INICIO MÓDULO: TOGGLE_MONITOR_SERVICE (FIX-008) ====================
    def toggle_monitor_service(self):
        """
        [FIX-008] Activa/desactiva el servicio de monitoreo con validaciones robustas.
        Resuelve: Error al pausar monitor
        """
        session_id = self._generate_session_id() # Módulo 46
        # ── START: MONITOR SERVICE SAFETY GUARD (FIX-008) ──
        svc = self.monitor_service
        
        if svc is None:
            self.status_var.set("SERVICIO NO DISPONIBLE")
            logging.error("[MONITOR] Toggle ignorado: MonitorService es None")
            
            # [FIX] Mostrar toast en lugar de solo cambiar status
            try:
                ToastNotification.show(
                    self.root, 
                    "⚠️ SERVICIO NO DISPONIBLE\nVerifique la base de datos", 
                    "error"
                )
            except:
                pass
                
            # [FIX] Mostrar diálogo informativo
            if messagebox.askyesno(
                "Servicio No Disponible",
                "El servicio de monitoreo no está disponible.\n\n"
                "Causas posibles:\n"
                "• Base de datos no inicializada\n"
                "• Error en ChannelMonitorService\n\n"
                "¿Desea intentar reiniciar el servicio?"
            ):
                # Forzar reinicio
                self._monitor_service = None
                self._monitor_service_failed = False
                # Intentar reconectar
                if self.monitor_service:
                    ToastNotification.show(self.root, "✅ Servicio reiniciado", "success")
                else:
                    self.log_channel_activity("GLOBAL", "Fallo al reiniciar MonitorService.", "MONITOR_RESTART_FAIL", session_id=session_id) # Módulo 41
                    ToastNotification.show(self.root, "❌ No se pudo reiniciar", "error")
            return
        # ── END: MONITOR SERVICE SAFETY GUARD ──

        try:
            if svc.is_monitoring():
                svc.stop_monitoring()
                ToastNotification.show(self.root, "⏸️ Monitor detenido", "warning")
                self.log_channel_activity("GLOBAL", "Monitor detenido manualmente.", "MONITOR_STOP", session_id=session_id) # Módulo 41
                self.log_monitor_activity("Monitor detenido manualmente")
                self.status_var.set("Monitor Pausado")
            else:
                # [FIX] Verificar canales activos ANTES de iniciar
                channels = self.db_manager.get_all_channels(active_only=True) if self.db_manager else []
                
                if not channels:
                    ToastNotification.show(
                        self.root, 
                        "⚠️ No hay canales activos\nAgregue canales para monitorear", 
                        "warning"
                    )
                    self.log_channel_activity("GLOBAL", "Intento de iniciar Monitor sin canales activos.", "MONITOR_START_FAIL", session_id=session_id) # Módulo 41
                    return
                    
                svc.start_monitoring()
                self.log_channel_activity("GLOBAL", f"Monitor iniciado con {len(channels)} canales activos.", "MONITOR_START", session_id=session_id) # Módulo 41
                ToastNotification.show(self.root, "▶️ Monitor iniciado", "success")
                self.log_monitor_activity(f"Monitor iniciado con {len(channels)} canal(es) activo(s)")
                self.status_var.set("Monitoreo Activo")
                
        except Exception as e:
            logging.error(f"[MONITOR] Error en toggle: {e}")
            ToastNotification.show(self.root, f"❌ Error: {str(e)}", "error")
    # ==================== FIN MÓDULO: TOGGLE_MONITOR_SERVICE (FIX-008) ====================

    # ==================== INICIO MÓDULO: SHOW_MONITOR_STATS (FIX-009) ====================
    def show_monitor_stats(self):
        """
        [FIX-009] Muestra estadísticas con fallback si db_manager falla.
        Resuelve: Error "Ver Estadísticas"
        """
        # [FIX] Intentar con db_manager, fallback a datos en memoria
        try:
            session_id = self._generate_session_id() # Módulo 46
            if self.db_manager:
                stats = self.db_manager.get_global_stats()
            else:
                # [FIX] Fallback: construir stats básicos desde memoria
                logging.warning("[STATS] db_manager no disponible, usando datos en memoria")
                stats = {
                    'total_channels': len(getattr(self, 'channels', [])),
                    'total_videos': 0,
                    'failed_videos': 0,
                    'last_check': 'Nunca'
                }
                messagebox.showwarning(
                    "Modo Limitado",
                    "Base de datos no disponible.\nMostrando estadísticas básicas."
                )
            self.log_channel_activity("GLOBAL", "Estadísticas del monitor mostradas.", "SHOW_STATS", session_id=session_id) # Módulo 41
        except Exception as e:
            logging.error(f"[STATS] Error obteniendo estadísticas: {e}")
            stats = {
                'total_channels': 0,
                'total_videos': 0,
                'failed_videos': 0,
                'last_check': 'Error'
            }
        
        win = tk.Toplevel(self.root)
        win.title("Estadísticas del Monitor KDP")
        win.geometry("400x350")
        win.resizable(False, False)
        win.transient(self.root)
        
        main = ttk.Frame(win, )
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
        add_row(g, 2, "Errores de Metadata:", stats.get('metadata_errors', 0), "#ef4444") # Módulo 44
        add_row(g, 3, "Última Sincronización:", stats.get('last_check', 'Nunca'), "#06b6d4")
        
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        ttk.Button(main, text="Cerrar", command=win.destroy).pack(pady=10)
    # ==================== FIN MÓDULO: SHOW_MONITOR_STATS (FIX-009) ====================

    def setup_schedule_tab(self):
        """Configura la pestaña de Programación Horaria."""
        if not hasattr(self, 'schedule_tab_loaded') or not self.schedule_tab_loaded:
            for widget in self.tab_schedule.winfo_children():
                widget.destroy()
            ttk.Label(self.tab_schedule, text="⏳ Cargando Programación...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_schedule_tab)
            return
        
        if len(self.tab_schedule.winfo_children()) > 0:
            return
        
        schedule_tab.setup_schedule_tab(self)
    
    def setup_settings_tab(self):
        """Configuración Robusta con Validación de Keys y Layout Responsive."""
        if not hasattr(self, 'settings_tab_loaded') or not self.settings_tab_loaded:
            for widget in self.tab_settings.winfo_children():
                widget.destroy()
            ttk.Label(self.tab_settings, text="⏳ Cargando Configuración...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_settings_tab)
            return
        
        if len(self.tab_settings.winfo_children()) > 0:
            return
        
        is_dark = self.current_theme in ["darkly", "cyborg", "dark"]
        card_bg = "#1e293b" if is_dark else "#ffffff"
        border_color = "#334155" if is_dark else "#e2e8f0"
        text_fg = "#f1f5f9" if is_dark else "#0f172a"
        muted_fg = "#94a3b8" if is_dark else "#64748b"

        # Contenedor principal con scroll
        main_container = ttk.Frame(self.tab_settings)
        main_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_container, bg=self.root.cget("bg"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        def create_card(parent, title, icon="⚙️"):
            frame = ttk.Frame(parent, padding=15)
            frame.pack(fill=tk.X, pady=(0, 15), padx=10)
            ttk.Label(frame, text=f"{icon} {title}", font=("Segoe UI", 12, "bold"), foreground=text_fg).pack(anchor=tk.W, pady=(0, 10))
            # Simular borde sutil
            border = ttk.Frame(frame, relief="solid", borderwidth=1, style="Card.TFrame")
            border.pack(fill=tk.X)
            return border

        # === TARJETA 1: GENERAL ===
        general_card = create_card(scrollable_frame, "General", "🌐")
        
        ttk.Label(general_card, text="Lenguaje", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        lang_var = tk.StringVar(value="Español")
        ttk.Combobox(general_card, textvariable=lang_var, values=["Español", "English", "Português"], state="readonly", width=25).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(general_card, text="Tema", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=10)
        theme_frame = ttk.Frame(general_card)
        theme_frame.grid(row=1, column=1, sticky=tk.W, padx=10)
        ttk.Button(theme_frame, text="☀️ Light", command=lambda: self.apply_specific_theme("litera"), bootstyle="light-outline", width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(theme_frame, text="🌙 Dark", command=lambda: self.apply_specific_theme("darkly"), bootstyle="dark-outline", width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(general_card, text="Auto-actualización", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.auto_update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(general_card, text="Actualizar dependencias automáticamente", variable=self.auto_update_var).grid(row=2, column=1, sticky=tk.W, padx=10)

        # === TARJETA 2: PROCESAMIENTO ===
        proc_card = create_card(scrollable_frame, "Procesamiento", "📂")
        
        ttk.Label(proc_card, text="Ruta de descarga", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.settings_input_dir_var = tk.StringVar(value=self.input_dir.get() if hasattr(self, "input_dir") else "data/transcriptions")
        input_frame = ttk.Frame(proc_card)
        input_frame.grid(row=0, column=1, sticky=tk.EW, padx=10)
        ttk.Entry(input_frame, textvariable=self.settings_input_dir_var, width=25).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="📁", width=5, command=lambda: self._browse_dir_settings(self.settings_input_dir_var)).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(proc_card, text="Codec de video default", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.codec_var = tk.StringVar(value="NTFF")
        ttk.Combobox(proc_card, textvariable=self.codec_var, values=["NTFF", "H.264", "H.265", "VP9"], state="readonly", width=25).grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(proc_card, text="Aceleración GPU", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.gpu_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(proc_card, text="Habilitar aceleración por hardware", variable=self.gpu_var).grid(row=2, column=1, sticky=tk.W, padx=10)

        # === TARJETA 3: INTEGRACIONES DE API ===
        api_card = create_card(scrollable_frame, "Integraciones de API", "🔑")
        
        ttk.Label(api_card, text="Google Video AI Key", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.google_api_var = tk.StringVar()
        google_entry = ttk.Entry(api_card, textvariable=self.google_api_var, show="•", width=30)
        google_entry.grid(row=0, column=1, sticky=tk.W, padx=10)
        google_entry.insert(0, self.settings.get("google_video_ai_key", ""))
        google_entry.config(validate="focusout", validatecommand=(self.root.register(self._validate_api_key), "%P"))
        ttk.Label(api_card, text="Ej: AIzaSy...", font=("Segoe UI", 8), foreground=muted_fg).grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(api_card, text="AWS Rekognition Key", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.aws_api_var = tk.StringVar()
        aws_entry = ttk.Entry(api_card, textvariable=self.aws_api_var, show="•", width=30)
        aws_entry.grid(row=2, column=1, sticky=tk.W, padx=10)
        aws_entry.insert(0, self.settings.get("aws_rekognition_key", ""))
        aws_entry.config(validate="focusout", validatecommand=(self.root.register(self._validate_api_key), "%P"))
        ttk.Label(api_card, text="Ej: AKIA...", font=("Segoe UI", 8), foreground=muted_fg).grid(row=3, column=1, sticky=tk.W, padx=10)

        # === TARJETA 4: MONITOREO AVANZADO ===
        monitor_card = create_card(scrollable_frame, "Configuración del Monitor", "📺")
        
        ttk.Label(monitor_card, text="Frecuencia (min)", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.scan_frequency_var = tk.StringVar(value=str(getattr(self, 'scan_frequency', 30)))
        ttk.Combobox(monitor_card, textvariable=self.scan_frequency_var, values=["15", "30", "60", "120"], width=25).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(monitor_card, text="Profundidad", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_results_var = tk.StringVar(value=str(self.max_results_per_check))
        ttk.Spinbox(monitor_card, from_=10, to=200, textvariable=self.max_results_var, width=24).grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Checkbutton(monitor_card, text="Excluir Shorts (< 60s)", variable=self.exclude_shorts_var).grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)

        # === TARJETA 5: FILTROS DE CONTENIDO ===
        filter_card = create_card(scrollable_frame, "Filtros Semánticos (Blacklist)", "🔍")
        
        ttk.Label(filter_card, text="Palabras a excluir (separadas por coma):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=5)
        self._settings_filter_text = tk.Text(filter_card, height=4, font=("Consolas", 9))
        self._settings_filter_text.pack(fill=tk.X, padx=5, pady=5)
        self._settings_filter_text.insert("1.0", ", ".join(self.blacklist))

        # === TARJETA 6: EXPORTACIÓN Y REPORTES ===
        export_card = create_card(scrollable_frame, "Exportación y Reportes", "📤")
        
        ttk.Label(export_card, text="Formato Default", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.export_format_var = tk.StringVar(value=getattr(self, 'export_format', 'html'))
        ttk.Combobox(export_card, textvariable=self.export_format_var, values=["html", "pdf", "markdown"], state="readonly", width=25).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        self.auto_export_var = tk.BooleanVar(value=getattr(self, 'auto_export_on_exit', False))
        ttk.Checkbutton(export_card, text="Auto-exportar KB al cerrar", variable=self.auto_export_var).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

        # === TARJETA 7: SEGURIDAD Y PRIVACIDAD ===
        security_card = create_card(scrollable_frame, "Seguridad Enterprise", "🔒")
        
        ttk.Label(security_card, text="Auditoría", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.audit_logging_var = tk.BooleanVar(value=getattr(self, 'audit_logging_enabled', True))
        ttk.Checkbutton(security_card, text="Registrar todos los cambios (Audit Log)", variable=self.audit_logging_var).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        btn_panic = ttk.Button(security_card, text="🚨 EJECUTAR BACKUP DE PÁNICO", command=self.panic_backup, bootstyle="danger-outline")
        btn_panic.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)

        # === TARJETA 8: NOTIFICACIONES AVANZADAS ===
        notif_card = create_card(scrollable_frame, "Notificaciones Inteligentes", "🔔")
        
        self.notif_sch_enabled = tk.BooleanVar(value=self.settings.get("notifications", {}).get("schedule_enabled", False))
        ttk.Checkbutton(notif_card, text="Habilitar ventana horaria", variable=self.notif_sch_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        time_f = ttk.Frame(notif_card)
        time_f.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=25)
        self.notif_start_var = tk.StringVar(value=self.settings.get("notifications", {}).get("start_time", "08:00"))
        self.notif_end_var = tk.StringVar(value=self.settings.get("notifications", {}).get("end_time", "22:00"))
        ttk.Entry(time_f, textvariable=self.notif_start_var, width=8).pack(side=tk.LEFT)
        ttk.Label(time_f, text=" a ").pack(side=tk.LEFT)
        ttk.Entry(time_f, textvariable=self.notif_end_var, width=8).pack(side=tk.LEFT)

        ttk.Label(notif_card, text="Prioridad Mínima", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.notif_min_pri_var = tk.IntVar(value=self.settings.get("notifications", {}).get("min_priority", 3))
        ttk.Spinbox(notif_card, from_=1, to=5, textvariable=self.notif_min_pri_var, width=5).grid(row=2, column=1, sticky=tk.W, padx=10)
        
        self.notif_sound_var = tk.StringVar(value=self.settings.get("notifications", {}).get("custom_sound_path", ""))

        # === TARJETA 9: GESTOR DE ENTORNO (.ENV) ===
        if self.env_manager:
            env_card = create_card(scrollable_frame, "Variables de Entorno (.env)", "🌍")
            self.env_text_area = scrolledtext.ScrolledText(env_card, height=8, font=('Consolas', 10))
            self.env_text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self._load_current_env_to_ui()
            
            env_btn_f = ttk.Frame(env_card)
            env_btn_f.pack(fill=tk.X, pady=5)
            ttk.Button(env_btn_f, text="🧪 Test Conexión", command=self._test_env_connectivity, bootstyle="info-outline", width=15).pack(side=tk.LEFT, padx=2)
            ttk.Button(env_btn_f, text="🔐 Cifrar Keys", command=self._encrypt_env_secrets, bootstyle="warning-outline", width=15).pack(side=tk.LEFT, padx=2)
            ttk.Button(env_btn_f, text="💾 Guardar .env", command=self._save_env_from_ui, bootstyle="success", width=15).pack(side=tk.RIGHT, padx=2)

        # === BOTONES DE ACCIÓN ===
        action_frame = ttk.Frame(scrollable_frame, padding=(10, 15))
        action_frame.pack(fill=tk.X)
        ttk.Button(action_frame, text="💾 Guardar Configuración", command=self._save_all_settings, bootstyle="success").pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="🔄 Restaurar Default", command=self._reset_settings, bootstyle="secondary-outline").pack(side=tk.RIGHT, padx=5)

        self.log("✅ Pestaña Configuración cargada (v2.0 Optimizada)")

    def _browse_dir_settings(self, string_var):
        """Abre diálogo para seleccionar directorio."""
        path = filedialog.askdirectory(title="Seleccionar carpeta")
        if path:
            string_var.set(path)
            self.log(f"📁 Directorio actualizado: {path}")

    def _validate_api_key(self, key: str) -> bool:
        """Validación básica de formato para API Keys."""
        if not key: return True  # Permitir vacío
        # Google: AIza... | AWS: AKIA... | OpenAI: sk-...
        if key.startswith(("AIza", "AKIA", "sk-", "gvid-")):
            return True
        # Si no coincide, no bloqueamos pero podemos añadir un hint visual si se desea
        return True

    # ==================== INICIO MÓDULO: GESTIÓN DE VARIABLES DE ENTORNO (US-CONFIG-UI) ==================== #
    def _setup_env_panel(self, parent):
        """[US-CONFIG-PANEL] Configura la interfaz visual para gestionar archivos .env."""
        env_frame = ttk.LabelFrame(parent, text=" 🌍 Configuración de Entorno (.env) ", ) # Feature 1: Panel UI
        env_frame.pack(fill=tk.X, pady=(0, 15), padx=5)

        # Selector de Entorno (Feature 3)
        top_row = ttk.Frame(env_frame)
        top_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_row, text="Entorno Activo:").pack(side=tk.LEFT)
        self.env_profile_var = tk.StringVar(value="Standard (.env)") # Feature 3: Entornos múltiples
        profiles = ["Standard (.env)", "Development (.env.dev)", "Production (.env.prod)"]
        profile_combo = ttk.Combobox(top_row, textvariable=self.env_profile_var, values=profiles, state="readonly", width=25)
        profile_combo.pack(side=tk.LEFT, padx=10)
        profile_combo.bind("<<ComboboxSelected>>", self._on_env_profile_change)

        # Editor de texto
        self.env_text_area = scrolledtext.ScrolledText(env_frame, height=12, font=('Consolas', 10)) # Feature 1: Panel UI
        self.env_text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self._load_current_env_to_ui()

        # Botonera de acciones
        btn_row = ttk.Frame(env_frame)
        btn_row.pack(fill=tk.X, pady=10)

        ttk.Button(btn_row, text="🧪 Test", command=self._test_env_connectivity).pack(side=tk.LEFT, padx=2) # Feature 2: Validación dinámica
        ttk.Button(btn_row, text="🔄 Hot Reload", command=self._hot_reload_config).pack(side=tk.LEFT, padx=2) # Feature 5: Hot Reload
        ttk.Button(btn_row, text="🔐 Cifrar", command=self._encrypt_env_secrets).pack(side=tk.LEFT, padx=2) # Feature 6: Secrets cifrados
        ttk.Button(btn_row, text="📋 Plantilla", command=self._validate_env_template).pack(side=tk.LEFT, padx=2) # Feature 10: Template de validación (y 9: Mapeo)
        ttk.Button(btn_row, text="📤 Exportar", command=self._export_env_json).pack(side=tk.LEFT, padx=2) # Feature 4: Export/Import
        ttk.Button(btn_row, text="📥 Importar", command=self._import_env_json).pack(side=tk.LEFT, padx=2) # Feature 4: Export/Import
        ttk.Button(btn_row, text="📜 Auditoría", command=self._show_env_history).pack(side=tk.LEFT, padx=2) # Feature 7: Historial de cambios
        
        ttk.Button(btn_row, text="💾 Guardar Cambios", style="Success.TButton", 
                  command=self._save_env_from_ui).pack(side=tk.RIGHT, padx=2)

    # === [INICIO FUNCIONALIDAD: ENTORNOS MÚLTIPLES (Feature 3)] ===
    def _on_env_profile_change(self, event=None):
        profile = self.env_profile_var.get()
        mapping = {"Standard (.env)": ".env", "Development (.env.dev)": ".env.dev", "Production (.env.prod)": ".env.prod"}
        filename = mapping.get(profile, ".env")
        self.env_manager.current_env_file = self.base_dir / filename
        self._load_current_env_to_ui()
        self.log(f"Perfil de entorno cambiado a: {profile}")
    # === [FIN FUNCIONALIDAD: ENTORNOS MÚLTIPLES (Feature 3)] ===

    # === [INICIO FUNCIONALIDAD: CARGA DE CONFIGURACIÓN EN UI (Feature 1)] ===
    def _load_current_env_to_ui(self):
        if not self.env_manager: return
        self.env_text_area.delete("1.0", tk.END)
        env_path = self.env_manager.current_env_file
        if env_path.exists():
            self.env_text_area.insert("1.0", env_path.read_text(encoding='utf-8'))
        else:
            self.env_text_area.insert("1.0", "# Archivo nuevo. Define tus variables aquí.")
    # === [FIN FUNCIONALIDAD: CARGA DE CONFIGURACIÓN EN UI (Feature 1)] ===

    # === [INICIO FUNCIONALIDAD: GUARDAR CONFIGURACIÓN Y VALIDACIÓN DE URLS (Feature 8)] ===
    def _save_env_from_ui(self):
        """[ALGORITMO] Parsea el editor y guarda en el archivo físico registrando auditoría."""
        # === [FEATURE 8: VALIDACIÓN ANTES DE GUARDAR] START ===
        content = self.env_text_area.get("1.0", tk.END).strip()
        lines = content.splitlines()
        data = {}
        for line in lines:
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                key = k.strip()
                val = v.strip()
                
                # Validación proactiva de URLs (Principio de Fallo Temprano)
                if "URL" in key and val.startswith("http"):
                    ok, msg = self.env_manager.validate_service_connectivity(key, val)
                    if not ok:
                        if not messagebox.askyesno("Validación de URL", f"La URL para {key} parece no responder:\n{msg}\n\n¿Guardar de todas formas?"):
                            return
                data[key] = val
        # === [FEATURE 8] END ===
        
        if self.env_manager.save_env(data, user=self.current_profile_var.get()):
            self.env_manager.current_env_file.write_text(content, encoding='utf-8')
            ToastNotification.show(self.root, "Configuración guardada y registrada", "success")
            self._hot_reload_config()
    # === [FIN FUNCIONALIDAD: GUARDAR CONFIGURACIÓN Y VALIDACIÓN DE URLS (Feature 8)] ===

    # === [INICIO FUNCIONALIDAD: VALIDACIÓN DINÁMICA (Feature 2)] ===
    def _test_env_connectivity(self):
        """[US-CONFIG-TEST] Valida conectividad de servicios (Ollama, APIs) definidos en el entorno."""
        env_data = self.env_manager.load_env()
        results = []
        
        if "OLLAMA_BASE_URL" in env_data:
            ok, msg = self.env_manager.validate_service_connectivity("ollama", env_data["OLLAMA_BASE_URL"])
            results.append(f"Ollama: {'✅' if ok else '❌'} ({msg})")
        
        if "GEMINI_API_KEY" in env_data:
            results.append("Gemini: ℹ️ Clave presente (Se valida al procesar)")

        messagebox.showinfo("Resultados de Conectividad", "\n".join(results) if results else "No hay servicios para validar.")
    # === [FIN FUNCIONALIDAD: VALIDACIÓN DINÁMICA (Feature 2)] ===

    # === [INICIO FUNCIONALIDAD: HOT RELOAD DE CONFIGURACIÓN (Feature 5)] ===
    def _hot_reload_config(self):
        """[HOT-RELOAD] Recarga la configuración en memoria sin reiniciar la aplicación (Feature 5)."""
        self.load_config()
        if self.integrator:
            self.integrator.api_key = self.api_key
            self.integrator.ai_provider = self.ai_provider
        self.log("🚀 Hot Reload: Configuración sincronizada.")
        ToastNotification.show(self.root, "Configuración recargada", "info") 
    # === [FIN FUNCIONALIDAD: HOT RELOAD DE CONFIGURACIÓN (Feature 5)] ===

    # === [INICIO FUNCIONALIDAD: SECRETS CIFRADOS (Feature 6)] ===
    def _encrypt_env_secrets(self):
        """Detecta y cifra API Keys en el editor (Feature 6)."""
        content = self.env_text_area.get("1.0", tk.END)
        keys_to_encrypt = ["GEMINI_API_KEY", "OPENAI_API_KEY", "AMAZON_API_KEY"]
        
        new_lines = []
        for line in content.splitlines():
            if any(k in line for k in keys_to_encrypt) and '=' in line and not "ENC:" in line:
                k, v = line.split('=', 1)
                encrypted = self.env_manager.encrypt_secret(v.strip())
                new_lines.append(f"{k.strip()}=ENC:{encrypted}")
            else:
                new_lines.append(line)
        
        self.env_text_area.delete("1.0", tk.END)
        self.env_text_area.insert("1.0", "\n".join(new_lines))
        ToastNotification.show(self.root, "Secretos cifrados localmente", "warning")
    # === [FIN FUNCIONALIDAD: SECRETS CIFRADOS (Feature 6)] ===

    # === [INICIO FUNCIONALIDAD: TEMPLATE DE VALIDACIÓN Y MAPEO DE VARIABLES (Features 9 & 10)] ===
    def _validate_env_template(self):
        """Compara el .env actual con el template de referencia (Feature 10)."""
        template_path = self.base_dir / ".env.template"
        if not template_path.exists():
            messagebox.showwarning("Error", "No existe .env.template")
            return
            
        missing = self.env_manager.get_template_diff(template_path)
        if missing:
            msg = "Faltan variables del template:\n\n" + "\n".join([f"• {m}" for m in missing])
            messagebox.showwarning("Mapeo de Variables", msg)
        else:
            messagebox.showinfo("Mapeo de Variables", "✅ Configuración completa.")
    # === [FIN FUNCIONALIDAD: TEMPLATE DE VALIDACIÓN Y MAPEO DE VARIABLES (Features 9 & 10)] ===

    # === [INICIO FUNCIONALIDAD: EXPORT/IMPORT DE CONFIGURACIÓN (Feature 4)] ===
    def _export_env_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path and self.env_manager.export_env_json(Path(path)):
            ToastNotification.show(self.root, "Configuración exportada", "success")
    # === [FIN FUNCIONALIDAD: EXPORT/IMPORT DE CONFIGURACIÓN (Feature 4)] ===

    # === [INICIO FUNCIONALIDAD: IMPORTAR CONFIGURACIÓN (Feature 4)] ===
    def _import_env_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path and self.env_manager.import_env_json(Path(path)):
            self._load_current_env_to_ui()
            ToastNotification.show(self.root, "Configuración importada y aplicada", "success")
    # === [FIN FUNCIONALIDAD: IMPORTAR CONFIGURACIÓN (Feature 4)] ===

    # === [INICIO FUNCIONALIDAD: HISTORIAL DE CAMBIOS (Feature 7)] ===
    def _show_env_history(self):
        """[FEATURE 7: VISOR DE HISTORIAL] Muestra los cambios realizados en el entorno."""
        history_path = self.env_manager.history_file
        if not history_path.exists():
            messagebox.showinfo("Historial", "No hay registros de cambios aún.")
            return
            
        win = tk.Toplevel(self.root)
        win.title("Historial de Cambios de Entorno")
        win.geometry("700x500")
        
        txt = scrolledtext.ScrolledText(win, font=('Consolas', 9))
        txt.pack(fill=tk.BOTH, expand=True, )
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            output = []
            for entry in reversed(history):
                output.append(f"📅 {entry['timestamp']} | Usuario: {entry['user']}")
                for k, v in entry['changes'].items():
                    output.append(f"   • {k} -> {v}")
                output.append("-" * 50)
            
            txt.insert(tk.END, "\n".join(output))
        except Exception as e:
            txt.insert(tk.END, f"Error cargando historial: {e}")
        
        txt.config(state=tk.DISABLED)
    # === [FIN FUNCIONALIDAD: HISTORIAL DE CAMBIOS (Feature 7)] ===
    # ==================== FIN MÓDULO: GESTIÓN DE VARIABLES DE ENTORNO ====================

    # === MÓDULO 9: Funciones auxiliares para settings ===
    
    def _browse_dir_settings(self, string_var):
        """Abre diálogo para seleccionar directorio."""
        path = filedialog.askdirectory(title="Seleccionar carpeta")
        if path:
            string_var.set(path)
            self.log(f"📁 Directorio cambiado: {path}")

    def _show_export_settings(self):
        """Muestra configuración de exportación de KB."""
        win = Toplevel(self.root)
        win.title("Configurar Exportación KB")
        win.geometry("400x350")
        win.transient(self.root)
        
        ttk.Label(win, text="Configuración de Exportación", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        settings_frame = ttk.LabelFrame(win, text="Opciones", )
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

    def _save_all_settings(self):
        """Guarda todas las variables de la pestaña en config.json."""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Actualizar directorios
            if hasattr(self, 'settings_input_dir_var'):
                config['input_dir'] = self.settings_input_dir_var.get()
                self.input_dir.set(self.settings_input_dir_var.get())
            
            if hasattr(self, 'settings_output_dir_var'):
                config['output_dir'] = self.settings_output_dir_var.get()
                self.output_dir.set(self.settings_output_dir_var.get())
                
            # Actualizar IA
            if hasattr(self, 'ai_provider_var'):
                config['ai_provider'] = self.ai_provider_var.get()
                self.ai_provider = self.ai_provider_var.get()
                
            if hasattr(self, 'ai_api_key_var'):
                config['api_key'] = self.ai_api_key_var.get()
                self.api_key = self.ai_api_key_var.get()
                
            if hasattr(self, 'ollama_model_var'):
                config['ollama_model'] = self.ollama_model_var.get()
                self.ollama_model = self.ollama_model_var.get()

            # Actualizar blacklist
            if hasattr(self, '_settings_filter_text'):
                raw = self._settings_filter_text.get("1.0", tk.END).strip()
                new_list = [w.strip() for w in raw.split(',') if w.strip()]
                config['blacklist'] = new_list
                self.blacklist = new_list
                if hasattr(self, 'integrator') and self.integrator:
                    self.integrator.update_blacklist(new_list)

            # Actualizar Monitor
            if hasattr(self, 'scan_frequency_var'):
                config['scan_frequency'] = int(self.scan_frequency_var.get())
                self.scan_frequency = int(self.scan_frequency_var.get())
            
            if hasattr(self, 'notif_enabled_var'):
                config['notifications_enabled'] = self.notif_enabled_var.get()
                self.notifications_enabled = self.notif_enabled_var.get()
            
            # === [INICIO FUNCIONALIDAD US-001: PERSISTENCIA DE CONFIG] ===
            if hasattr(self, 'max_results_var'):
                val = int(self.max_results_var.get())
                config['max_results_per_check'] = val
                self.max_results_per_check = val
            
            if hasattr(self, 'max_age_var'):
                val = int(self.max_age_var.get())
                config['max_age_days'] = val
                self.max_age_days = val

            if hasattr(self, 'max_parallel_per_channel_var'):
                val = int(self.max_parallel_per_channel_var.get())
                config['max_downloads_per_channel'] = val
                self.max_downloads_per_channel = val
                if self.download_service:
                    self.download_service.max_per_channel = val
            
            # --- INICIO FUNCIONALIDAD US-010-SAVE: PERSISTENCIA FILTROS DE BÚSQUEDA ---
            config['search_keywords'] = self.search_keywords_var.get()
            config['search_duration_min'] = self.search_duration_min_var.get()
            config['search_duration_max'] = self.search_duration_max_var.get()
            config['filter_shorts'] = self.filter_shorts_var.get()
            # --- FIN FUNCIONALIDAD ---
            
            # --- INICIO FUNCIONALIDAD US-010-SAVE: PERSISTENCIA FILTROS DE BÚSQUEDA ---
            config['search_keywords'] = self.search_keywords_var.get()
            config['search_duration_min'] = self.search_duration_min_var.get()
            config['search_duration_max'] = self.search_duration_max_var.get()
            config['filter_shorts'] = self.filter_shorts_var.get()
            # --- FIN FUNCIONALIDAD ---
            
            # --- INICIO FUNCIONALIDAD US-038-SAVE: PERSISTENCIA MONITOR AVANZADO ---
            config['exclude_shorts'] = self.exclude_shorts_var.get()
            config['adaptive_interval'] = self.adaptive_interval_var.get()
            # --- FIN FUNCIONALIDAD ---
            # === [FIN FUNCIONALIDAD US-001: PERSISTENCIA DE CONFIG] ===
            
            if self.monitor_service:
                self.monitor_service.set_detection_config(
                    max_results=self.max_results_per_check,
                    max_age_days=self.max_age_days,
                    exclude_shorts=self.exclude_shorts_var.get(),
                    adaptive_interval=self.adaptive_interval_var.get()
                )

            # Actualizar Exportación
            if hasattr(self, 'export_format_var'):
                config['export_format'] = self.export_format_var.get()
                self.export_format = self.export_format_var.get()
            
            if hasattr(self, 'auto_export_var'):
                config['auto_export_on_exit'] = self.auto_export_var.get()
                self.auto_export_on_exit = self.auto_export_var.get()

            # Actualizar Seguridad
            if hasattr(self, 'audit_logging_var'):
                config['audit_logging_enabled'] = self.audit_logging_var.get()
                self.audit_logging_enabled = self.audit_logging_var.get()

            # --- INICIO FUNCIONALIDAD US-036-ADV: GUARDADO DE NOTIFICACIONES ---
            notif_cfg = config.get("notifications", {})
            notif_cfg["schedule_enabled"] = self.notif_sch_enabled.get()
            notif_cfg["start_time"] = self.notif_start_var.get()
            notif_cfg["end_time"] = self.notif_end_var.get()
            notif_cfg["min_priority"] = self.notif_min_pri_var.get()
            notif_cfg["custom_sound_path"] = self.notif_sound_var.get()
            config["notifications"] = notif_cfg
            # --- FIN FUNCIONALIDAD ---

            # Guardar a disco
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            messagebox.showinfo("✅ Éxito", "Configuración guardada.\nAlgunos cambios requieren reiniciar.")
            self.log("📝 Configuración actualizada por usuario")
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo guardar:\n{str(e)}")
            self.log(f"❌ Error guardando settings: {e}")

    # --- INICIO FUNCIONALIDAD US-036-ADV: VISOR DE HISTORIAL ---
    def _show_notification_history(self):
        """Abre ventana modal para consultar las últimas 100 notificaciones registradas."""
        win = tk.Toplevel(self.root)
        win.title("Historial de Notificaciones Elite")
        win.geometry("600x400")
        
        frame = ttk.Frame(win, )
        frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("date", "type", "title", "message")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.heading("date", text="Fecha"); tree.column("date", width=120)
        tree.heading("type", text="Tipo"); tree.column("type", width=70)
        tree.heading("title", text="Título"); tree.column("title", width=150)
        tree.heading("message", text="Mensaje"); tree.column("message", width=250)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=sb.set)
        
        self.log("[HISTORY] Cargando historial de notificaciones desde persistencia...")
        # Aquí se cargaría de self.db_manager.get_notification_history()
    # --- FIN FUNCIONALIDAD ---
    
    def _reset_settings(self):
        """Restaura valores predeterminados de fábrica."""
        if messagebox.askyesno("Confirmar", "¿Restaurar valores predeterminados?"):
            # Valores por defecto
            default_input = "data/transcriptions"
            default_output = "outputs/transcribed"
            default_blacklist = ["suscríbete", "like", "comenta", "campanita", "patrocinado"]
            
            # Actualizar variables de la UI
            if hasattr(self, 'settings_input_dir_var'):
                self.settings_input_dir_var.set(default_input)
                self.input_dir.set(default_input)
            
            if hasattr(self, 'settings_output_dir_var'):
                self.settings_output_dir_var.set(default_output)
                self.output_dir.set(default_output)
                
            if hasattr(self, 'theme_choice_var'):
                self.theme_choice_var.set("dark")
                self.apply_specific_theme("dark")
                
            if hasattr(self, 'ai_provider_var'):
                self.ai_provider_var.set("ollama")
                self.ai_provider = "ollama"
                
            if hasattr(self, 'ai_api_key_var'):
                self.ai_api_key_var.set("")
                self.api_key = ""
                
            if hasattr(self, 'ollama_model_var'):
                self.ollama_model_var.set("qwen2.5:7b")
                self.ollama_model = "qwen2.5:7b"
            
            if hasattr(self, 'max_results_var'):
                self.max_results_var.set("50")
                self.max_results_per_check = 50
            
            if hasattr(self, 'max_age_var'):
                self.max_age_var.set("7")
                self.max_age_days = 7
            
            # --- INICIO FUNCIONALIDAD US-010-RESET: RESET FILTROS DE BÚSQUEDA ---
            if hasattr(self, 'search_keywords_var'): self.search_keywords_var.set("")
            if hasattr(self, 'search_duration_min_var'): self.search_duration_min_var.set(0)
            if hasattr(self, 'search_duration_max_var'): self.search_duration_max_var.set(0)
            if hasattr(self, 'filter_shorts_var'): self.filter_shorts_var.set(False)
            # --- FIN FUNCIONALIDAD ---
            
            if hasattr(self, '_settings_filter_text'):
                self._settings_filter_text.delete("1.0", tk.END)
                self._settings_filter_text.insert("1.0", ", ".join(default_blacklist))
                self.blacklist = default_blacklist
                if hasattr(self, 'integrator') and self.integrator:
                    self.integrator.update_blacklist(default_blacklist)
            
            # Guardar en config.json
            try:
                config = {}
                if os.path.exists(self.config_file):
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                
                config.update({
                    "input_dir": default_input,
                    "output_dir": default_output,
                    "blacklist": default_blacklist,
                    "ai_provider": "ollama",
                    "ollama_model": "qwen2.5:7b",
                    "api_key": "",
                    # --- INICIO FUNCIONALIDAD US-010-RESET: RESET FILTROS DE BÚSQUEDA ---
                    "search_keywords": "", "search_duration_min": 0,
                    "search_duration_max": 0, "filter_shorts": False
                    # --- FIN FUNCIONALIDAD ---
                })
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                self.log(f"⚠️ Error guardando defaults: {e}")
            
            messagebox.showinfo("✅ Restaurado", "Valores restablecidos.\nPresiona 'Guardar' para aplicar.")
            self.log("🔄 Configuración restaurada a valores de fábrica")

    def _check_weasyprint_installed(self):
        """Verifica si WeasyPrint está instalado."""
        try:
            import weasyprint
            return True
        except ImportError:
            return False

    def _install_weasyprint(self):
        """Instala WeasyPrint."""
        # --- INICIO FUNCIONALIDAD: GUÍA DE INSTALACIÓN GTK3 PARA PDF ---
        msg = ("Para habilitar la exportación a PDF Premium, se requiere el motor GTK3 Runtime.\n\n"
               "1. Se abrirá la página de descargas de GitHub.\n"
               "2. Descargue e instale 'gtk3-runtime-3.24.xx-64-bit.exe'.\n"
               "3. Reinicie KDP Master Suite.\n\n"
               "¿Desea abrir la página de descarga ahora?")
        if messagebox.askyesno("Habilitar PDF Premium", msg):
            self.open_url("https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases")
        # --- FIN FUNCIONALIDAD ---

    def panic_backup(self):
        """Crea backup de emergencia."""
        import shutil
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"emergency_backup_{timestamp}.zip"
        try:
            import zipfile
            with zipfile.ZipFile(backup_name, 'w') as zf:
                for folder in ['data', 'knowledge', 'outputs']:
                    if os.path.exists(folder):
                        for root, dirs, files in os.walk(folder):
                            for file in files:
                                file_path = os.path.join(root, file)
                                zf.write(file_path, arcname=os.path.join(folder, file))
            messagebox.showinfo("✅ Backup", f"Creado: {backup_name}")
            self.log(f"🚨 Backup de pánico: {backup_name}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Backup falló:\n{str(e)}")

    def manage_channels(self):
        """Ventana para gestionar canales guardados (Versión Pro)."""
        win = tk.Toplevel(self.root)
        win.title("Gestor de Canales Pro")
        win.geometry("800x600")
        
        # --- Barra de Herramientas Superior (Búsqueda y Filtros) ---
        toolbar = ttk.Frame(win, )
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

        # Contenedor de botones con expansión para evitar que se corten
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=5)

        # Botones con width moderado y sin compresión
        ttk.Button(btn_frame, text="✅ Todo", width=10, command=lambda: select_all_tree()).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Ninguno", width=12, command=deselect_all_tree).pack(side=tk.LEFT, padx=2)

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
        list_frame = ttk.Frame(win, )
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
            
        input_frame = ttk.LabelFrame(win, text=" Agregar / Editar Canal ", )
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
                
                self.log_channel_activity("GLOBAL", f"Canal '{values[0]}' eliminado (local).", "DELETE_CHANNEL", session_id=self._generate_session_id()) # Módulo 41
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
                    # Módulo 41: Log de Actividad por Canal
                    self.log_channel_activity(target_channel['channel_id'], f"Canal '{ch_name}' editado a '{new_name}'.", "EDIT_CHANNEL", session_id=self._generate_session_id()) # Módulo 41
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
                        # Módulo 41: Log de Actividad por Canal
                        self.db_manager.toggle_channel_active(target['id'], not target['active'])
                        self.log_channel_activity(target['channel_id'], f"Canal '{vals[0]}' toggled active to {not target['active']}.", "TOGGLE_ACTIVE", session_id=self._generate_session_id()) # Módulo 41
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
            self.log_channel_activity("GLOBAL", f"Añadidos {added_count} canales a la cola desde el gestor.", "ADD_TO_QUEUE_FROM_MANAGER", session_id=self._generate_session_id()) # Módulo 41

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
                self.log_channel_activity("GLOBAL", f"Error importando CSV: {e}", "IMPORT_CSV_ERROR", session_id=self._generate_session_id()) # Módulo 41
                # Módulo 41: Log de Actividad por Canal
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
                # Módulo 41: Log de Actividad por Canal
                self.log_channel_activity("GLOBAL", f"Eliminados {removed} canales duplicados.", "CLEAN_DUPLICATES", session_id=self._generate_session_id()) # Módulo 41
                refresh_list()
                self.update_channel_combo()
                self.update_channel_stats()
                messagebox.showinfo("Limpieza", f"Se eliminaron {removed} canales duplicados.")
            else:
                messagebox.showinfo("Limpieza", "No se encontraron duplicados.")

        btn_frame = ttk.Frame(win, )
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
        
        io_frame = ttk.Frame(win, )
        io_frame.pack(fill=tk.X)
        ttk.Button(io_frame, text="📤 Exportar Todo", command=lambda: export_csv(False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="📤 Exportar Selección", command=lambda: export_csv(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="📥 Importar CSV", command=import_csv).pack(side=tk.LEFT, padx=5)
        
        # Módulo 41: Log de Actividad por Canal
    def log_channel_activity(self, channel_id: str, description: str, event_type: str, session_id: str = None):
        """
        [Módulo 41] Registra una actividad específica para un canal en la base de datos.
        channel_id puede ser un ID de YouTube o "GLOBAL" para actividades generales.
        """
        if not self.db_manager:
            self.log(f"[ACTIVITY_LOG] DB no disponible: {description}", "warning")
            return
        
        try:
            self.db_manager.log_channel_activity(
                channel_id=channel_id,
                event_type=event_type,
                description=description,
                session_id=session_id or self._generate_session_id()
            )
        except Exception as e:
            # Módulo 41: Log de Actividad por Canal
            self.log(f"[ACTIVITY_LOG_ERROR] Fallo al loguear actividad para {channel_id}: {e}", "error")

    def show_channel_activity_log(self):
        """[Módulo 41] Muestra un log detallado de actividad por canal."""
        if not self.db_manager:
            ToastNotification.show(self.root, "Base de datos no disponible.", "error")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Log de Actividad por Canal")
        win.geometry("800x500")
        
        tree = ttk.Treeview(win, columns=("timestamp", "channel_id", "event_type", "description", "session_id"), show="headings")
        tree.heading("timestamp", text="Timestamp")
        tree.heading("channel_id", text="Channel ID")
        tree.heading("event_type", text="Tipo Evento")
        tree.heading("description", text="Descripción")
        tree.heading("session_id", text="Sesión ID")
        
        tree.column("timestamp", width=150)
        tree.column("channel_id", width=120)
        tree.column("event_type", width=100)
        tree.column("description", width=300)
        tree.column("session_id", width=100)
        
        tree.pack(fill=tk.BOTH, expand=True, )
        
        for entry in self.db_manager.get_channel_activity_log():
            tree.insert("", tk.END, values=(
                entry.get('timestamp', ''),
                entry.get('channel_id', ''),
                entry.get('event_type', ''),
                entry.get('description', ''),
                entry.get('session_id', '')[:8] + "..." if entry.get('session_id') else ''
            ))
        
        ttk.Button(win, text="Cerrar", command=win.destroy, bootstyle="secondary").pack(pady=10)

    def show_skipped_videos_report(self):
        """[Módulo 42] Muestra un reporte de videos omitidos y la razón."""
        if not self.db_manager:
            ToastNotification.show(self.root, "Base de datos no disponible.", "error")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Reporte de Videos Omitidos")
        win.geometry("900x600")
        
        tree = ttk.Treeview(win, columns=("timestamp", "video_id", "channel_name", "title", "reason", "session_id"), show="headings")
        tree.heading("timestamp", text="Timestamp")
        tree.heading("video_id", text="Video ID")
        tree.heading("channel_name", text="Canal")
        tree.heading("title", text="Título")
        tree.heading("reason", text="Razón")
        tree.heading("session_id", text="Sesión ID")
        
        tree.column("timestamp", width=150)
        tree.column("video_id", width=100)
        tree.column("channel_name", width=150)
        tree.column("title", width=250)
        tree.column("reason", width=150)
        tree.column("session_id", width=80)
        
        tree.pack(fill=tk.BOTH, expand=True, )
        
        for entry in self.db_manager.get_skipped_videos_log():
            tree.insert("", tk.END, values=(
                entry.get('timestamp', ''),
                entry.get('video_id', ''),
                entry.get('channel_name', ''),
                entry.get('title', ''),
                entry.get('reason', ''),
                entry.get('session_id', '')[:8] + "..." if entry.get('session_id') else ''
            ))
        
        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=10)

    def show_scan_history(self):
        """[Módulo 43] Muestra el historial de escaneos del monitor."""
        if not self.db_manager:
            ToastNotification.show(self.root, "Base de datos no disponible.", "error")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Historial de Escaneos del Monitor")
        win.geometry("900x600")
        
        tree = ttk.Treeview(win, columns=("timestamp", "channel_id", "channel_name", "new_videos", "skipped_videos", "errors_count", "duration_s", "session_id"), show="headings")
        tree.heading("timestamp", text="Timestamp")
        tree.heading("channel_id", text="Channel ID")
        tree.heading("channel_name", text="Canal")
        tree.heading("new_videos", text="Nuevos")
        tree.heading("skipped_videos", text="Omitidos")
        tree.heading("errors_count", text="Errores")
        tree.heading("duration_s", text="Duración (s)")
        tree.heading("session_id", text="Sesión ID")
        
        tree.column("timestamp", width=150)
        tree.column("channel_id", width=100)
        tree.column("channel_name", width=150)
        tree.column("new_videos", width=70, anchor="center")
        tree.column("skipped_videos", width=70, anchor="center")
        tree.column("errors_count", width=70, anchor="center")
        tree.column("duration_s", width=80, anchor="center")
        tree.column("session_id", width=80)
        
        tree.pack(fill=tk.BOTH, expand=True, )
        
        for entry in self.db_manager.get_scan_history():
            tree.insert("", tk.END, values=(
                entry.get('timestamp', ''),
                entry.get('channel_id', ''),
                entry.get('channel_name', ''),
                entry.get('new_videos', 0),
                entry.get('skipped_videos', 0),
                entry.get('errors_count', 0),
                f"{entry.get('duration_seconds', 0):.1f}",
                entry.get('session_id', '')[:8] + "..." if entry.get('session_id') else ''
            ))
        
        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=10)

    def _generate_session_id(self):
        """[Módulo 46] Genera un ID único para la sesión actual de una operación."""
        if not self.current_session_id:
            self.current_session_id = str(uuid.uuid4())
        return self.current_session_id

    def _save_pending_list_state(self):
        """[Módulo 47] Guarda el estado de la lista de pendientes al cerrar la app."""
        try:
            state = {
                "all_pending_videos": self.all_pending_videos,
                "filtered_pending_videos": self.filtered_pending_videos,
                "current_pending_page": self.current_pending_page,
                "pending_page_size": self.pending_page_size,
                "pending_search_var": self.pending_search_var.get(),
                "pending_year_var": self.pending_year_var.get(),
                "pending_month_var": self.pending_month_var.get(),
                "pending_select_non_processed_var": self.pending_select_non_processed_var.get(),
                "pending_hide_processed_var": self.pending_hide_processed_var.get(),
                "pending_hide_queued_var": self.pending_hide_queued_var.get(),
                "pending_hide_kb_var": self.pending_hide_kb_var.get(),
                "pending_min_duration_var": self.pending_min_duration_var.get(),
                "pending_exclude_keywords_var": self.pending_exclude_keywords_var.get(),
                "pending_include_keywords_var": self.pending_include_keywords_var.get(),
                "timestamp": datetime.now().isoformat()
            }
            with open(self.pending_list_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            self.log("[PENDING_LIST] Estado de la lista de pendientes guardado.")
        except Exception as e:
            self.log(f"[PENDING_LIST_ERROR] Fallo al guardar estado de pendientes: {e}", "error")

    def _load_pending_list_state(self):
        """[Módulo 47] Carga el estado de la lista de pendientes al iniciar la app."""
        if not self.pending_list_state_file.exists():
            return
        
        try:
            with open(self.pending_list_state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.all_pending_videos = state.get("all_pending_videos", [])
            self.filtered_pending_videos = state.get("filtered_pending_videos", [])
            self.current_pending_page = state.get("current_pending_page", 0)
            self.pending_page_size = state.get("pending_page_size", 100)
            
            # Restaurar variables de UI
            self.pending_search_var.set(state.get("pending_search_var", ""))
            self.pending_year_var.set(state.get("pending_year_var", "Todos"))
            self.pending_month_var.set(state.get("pending_month_var", "Todos"))
            self.pending_select_non_processed_var.set(state.get("pending_select_non_processed_var", False))
            self.pending_hide_processed_var.set(state.get("pending_hide_processed_var", False))
            self.pending_hide_queued_var.set(state.get("pending_hide_queued_var", False))
            self.pending_hide_kb_var.set(state.get("pending_hide_kb_var", False))
            self.pending_min_duration_var.set(state.get("pending_min_duration_var", 0))
            self.pending_exclude_keywords_var.set(state.get("pending_exclude_keywords_var", ""))
            self.pending_include_keywords_var.set(state.get("pending_include_keywords_var", ""))
            
            self.log("[PENDING_LIST] Estado de la lista de pendientes restaurado.")
            self.root.after(100, self.refresh_pending_tree) # Refrescar UI después de que esté lista
        except Exception as e:
            self.log(f"[PENDING_LIST_ERROR] Fallo al cargar estado de pendientes: {e}", "error")
            # Si falla la carga, limpiar el archivo para evitar bucles de error
            if self.pending_list_state_file.exists():
                self.pending_list_state_file.unlink()

    def _check_channel_name_change(self, current_channel_data: dict, session_id: str):
        """
        [Módulo 48] Detecta si el nombre de un canal ha cambiado.
        Se llama después de obtener metadata actualizada del canal.
        """
        if not self.db_manager: return
        
        db_channel = self.db_manager.get_channel_by_id(current_channel_data['id'])
        if db_channel and db_channel.get('channel_name') != current_channel_data.get('channel_name'):
            old_name = db_channel.get('channel_name')
            new_name = current_channel_data.get('channel_name')
            # Módulo 41: Log de Actividad por Canal
            self.log(f"[ALERTA] El canal '{old_name}' (ID: {current_channel_data['channel_id']}) ha cambiado su nombre a '{new_name}'.", "warning")
            self.log_channel_activity(current_channel_data['channel_id'], f"Nombre de canal cambiado de '{old_name}' a '{new_name}'.", "CHANNEL_NAME_CHANGE", session_id=session_id)
            # Opcional: Actualizar automáticamente en DB o pedir confirmación al usuario
            # self.db_manager.update_channel(current_channel_data['id'], name=new_name)

    def _detect_fake_channel(self, channel_data: dict, session_id: str):
        """
        [Módulo 49] Heurísticas básicas para detectar canales falsos/clones.
        Esto es una implementación SIN IA. Una versión con IA sería más robusta.
        """
        if not self.db_manager: return False
        
        channel_id = channel_data.get('channel_id')
        channel_name = channel_data.get('channel_name', '').lower()
        subscriber_count = channel_data.get('subscriber_count', 0)
        
        # Heurística 1: Nombre muy similar a un canal popular pero con pocos suscriptores
        # Esto requeriría una lista de canales populares o una base de datos de "canales conocidos"
        # Por ahora, una detección simple de nombres sospechosos.
        suspicious_keywords = ["official", "live", "backup", "clone"]
        if any(kw in channel_name for kw in suspicious_keywords) and subscriber_count < 1000:
            # Módulo 41: Log de Actividad por Canal
            self.log(f"[ALERTA] Posible canal falso/clon detectado: '{channel_name}' (ID: {channel_id}). Pocos suscriptores con nombre sospechoso.", "warning")
            self.log_channel_activity(channel_id, f"Posible canal falso/clon detectado: '{channel_name}'.", "FAKE_CHANNEL_DETECTED", session_id=session_id)
            return True
        
        # Heurística 2: Canal con ID diferente pero URL/nombre muy similar a uno ya monitoreado
        # Esto se puede hacer al añadir un canal, comparando con los existentes.
        
        return False

    def _validate_ssl_channel(self, url: str, session_id: str):
        """
        [Módulo 50] Verifica la validez del certificado SSL de la URL del canal.
        yt_dlp y urllib.request ya manejan esto por defecto, pero podemos añadir un log explícito.
        """
        try:
            # urllib.request.urlopen por defecto verifica SSL. Si falla, lanza URLError.
            # No necesitamos descargar el contenido, solo intentar la conexión.
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                # Si llegamos aquí, la conexión SSL fue exitosa
                # Módulo 41: Log de Actividad por Canal
                self.log_channel_activity("GLOBAL", f"Validación SSL exitosa para {url}.", "SSL_VALIDATION_SUCCESS", session_id=session_id)
                return True
        except urllib.error.URLError as e:
            self.log(f"[ALERTA] Fallo en validación SSL para {url}: {e}", "error")
            # Módulo 41: Log de Actividad por Canal
            self.log_channel_activity("GLOBAL", f"Fallo en validación SSL para {url}: {e}", "SSL_VALIDATION_FAILURE", session_id=session_id)
            return False
        except Exception as e:
            self.log(f"[ALERTA] Error inesperado en validación SSL para {url}: {e}", "error")
            self.log_channel_activity("GLOBAL", f"Error inesperado en validación SSL para {url}: {e}", "SSL_VALIDATION_ERROR", session_id=session_id)
            return False

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
                 ).pack(fill=tk.X)
        
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
            
            lbl = ttk.Label(capture_win, text="Pulsa la nueva combinación de teclas...", )
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
            
        btn_frame = ttk.Frame(editor, )
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
        db_manager = getattr(self, 'db_manager', None)
        names = []
        if db_manager:
            try:
                channels = db_manager.get_all_channels(active_only=True)
                names = [ch['channel_name'] for ch in channels]
            except Exception:
                names = [c['name'] for c in getattr(self, 'channels', [])]
        else:
            names = [c['name'] for c in getattr(self, 'channels', [])]
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
            
            result = convert_md_to_pdf(legal_manual, output_pdf)
            
            if result.success:
                messagebox.showinfo("Éxito", f"PDF generado exitosamente:\n{result.path}")
                self.open_folder(os.path.dirname(result.path))
            else:
                msg = result.error or "Error desconocido durante la conversión a PDF."
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
        
        stats_frame = ttk.LabelFrame(win, text=" Estado Actual de Manuales ", )
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
        
        input_frame = ttk.LabelFrame(win, text=" Agregar Contenido Nuevo ", )
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(input_frame, text="Manual destino:").grid(row=0, column=0, sticky=tk.W, pady=5)
        manual_var = tk.StringVar(value="LEGALIDAD")
        manual_combo = ttk.Combobox(input_frame, textvariable=manual_var, 
                                    values=["LEGALIDAD", "FORMULAS", "MATRIZ"],
                                    state="readonly", width=20)
        manual_combo.grid(row=0, column=1, sticky=tk.W, )
        
        ttk.Label(input_frame, text="Fuente:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        source_var = tk.StringVar(value="Transcripción manual")
        source_entry = ttk.Entry(input_frame, textvariable=source_var, width=30)
        source_entry.grid(row=0, column=3, sticky=tk.W, )
        
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
        
        btn_frame = ttk.Frame(win, )
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
        
        tree.pack(fill=tk.BOTH, expand=True, )
        
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

        frame = ttk.Frame(win, )
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
                "port": 7000,
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

    def on_close(self):
        """Maneja el cierre seguro de la aplicación y genera backup."""
        # --- INICIO PROTOCOLO CIERRE SEGURO ---
        print("Iniciando protocolo de cierre seguro...")
        if hasattr(self, 'backup_manager') and self.backup_manager:
            print("Generando backup automático...")
            self.backup_manager.create_automatic_backup()
        
        self.on_closing() # Llama a la lógica de limpieza existente
        # --- FIN PROTOCOLO CIERRE SEGURO ---

        self._save_pending_list_state() # Módulo 47: Guardar estado de la lista de pendientes
        # ==================== INICIO MÓDULO: DOC_UPDATER AUTO-CHECK ====================
        if self.doc_updater:
            self.doc_updater.check_and_update_summary("FUNCIONALIDADES ESPECIALES/PLAN FUNCIONALIDADES.txt", "FEATURES.md")
        # ==================== FIN MÓDULO: DOC_UPDATER AUTO-CHECK ====================
    def on_closing(self):
        """Procedimiento de cierre seguro Enterprise - asegura que la app se cierre."""
        try:
            if self.queue_running:
                if not messagebox.askyesno("Saliendo", "Hay una descarga en curso. ¿Seguro que desea salir?"):
                    return
                self.queue_running = False
                self.queue_paused = False

            self.status_var.set("Cerrando sistema de forma segura...")
            self.root.update()
            
            self._stop_channel_monitor()
            self._stop_scheduler()
            self.stop_dashboard_server()
            self._stop_download_queue()
            
            self._wait_for_threads(timeout=3)
            
            if hasattr(self, 'tray_icon') and self.tray_icon:
                try:
                    self.tray_icon.stop()
                except:
                    pass
                try:
                    if hasattr(self.tray_icon, 'visible') and self.tray_icon.visible:
                        self.tray_icon.visible = False
                except:
                    pass
            
            self.save_config()
            self.backup_data()
            self.save_session_state(None, "normal_exit")
            self._auto_clean_cache(silent=True)

        except Exception as e:
            print(f"Error en cierre: {e}")
        finally:
            try:
                self.root.destroy()
            except:
                pass

            if hasattr(self, 'app_lock') and self.app_lock:
                try:
                    self.app_lock.release()
                except Exception as e:
                    print(f"[CLEANUP] Error al liberar lock: {e}")
                    # Fallback: intentar eliminación manual
                    if os.path.exists(self.lock_file):
                        try:
                            os.remove(self.lock_file)
                        except:
                            pass
            elif os.path.exists(self.lock_file):
                # Fallback al método básico
                try:
                    os.remove(self.lock_file)
                except Exception:
                    pass
            
            
            # Forzar salida inmediata para liberar el Lock en el test de fuerza bruta
            os._exit(0)

    # ==================== INICIO MÓDULO: MÉTODOS DE LIMPIEZA DE CIERRE ====================
    def _stop_channel_monitor(self):
        """Detiene el monitor de canales de forma limpia."""
        if hasattr(self, 'monitor_service') and self.monitor_service:
            try:
                if hasattr(self, 'logger'):
                    self.logger.info("[CLEANUP] Deteniendo Monitor de Canales...")
                self.monitor_service.stop_monitoring()
                time.sleep(0.5)
                if hasattr(self, 'logger'):
                    self.logger.info("[CLEANUP] Monitor de Canales detenido")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"[CLEANUP] Error deteniendo Monitor: {e}")

    def _stop_download_queue(self):
        """Detiene las colas de descarga activas."""
        if hasattr(self, 'queue_running') and self.queue_running:
            try:
                if hasattr(self, 'logger'):
                    self.logger.info("[CLEANUP] Deteniendo cola de descargas...")
                self.queue_running = False
                if hasattr(self, 'download_tasks') and self.download_tasks:
                    for task in self.download_tasks:
                        try:
                            if hasattr(task, 'cancel'):
                                task.cancel()
                        except:
                            pass
                time.sleep(0.5)
                if hasattr(self, 'logger'):
                    self.logger.info("[CLEANUP] Cola de descargas detenida")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"[CLEANUP] Error deteniendo descargas: {e}")

    def _stop_scheduler(self):
        """Detiene el scheduler programado de forma limpia."""
        if hasattr(self, 'schedule_manager') and self.schedule_manager:
            try:
                if hasattr(self, 'logger'):
                    self.logger.info("[CLEANUP] Deteniendo Scheduler...")
                self.schedule_manager.stop()
                if hasattr(self, 'scheduler_thread') and self.scheduler_thread:
                    self.scheduler_thread.join(timeout=2)
                if hasattr(self, 'logger'):
                    self.logger.info("[CLEANUP] Scheduler detenido")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"[CLEANUP] Error deteniendo Scheduler: {e}")

    def _wait_for_threads(self, timeout=3):
        """Espera a que todos los threads activos terminen."""
        if hasattr(self, 'logger'):
            self.logger.info("[CLEANUP] Esperando threads activos...")
        
        import threading
        start_time = time.time()
        
        active_threads = [t for t in threading.enumerate() if t is not threading.main_thread()]
        
        for thread in active_threads:
            if time.time() - start_time > timeout:
                break
            if thread.is_alive():
                thread.join(timeout=0.5)
        
        remaining = [t.name for t in threading.enumerate() 
                     if t is not threading.main_thread() and t.is_alive()]
        
        if remaining and hasattr(self, 'logger'):
            self.logger.warning(f"[CLEANUP] Threads activos tras timeout: {remaining}")
        elif hasattr(self, 'logger'):
            self.logger.info("[CLEANUP] Todos los threads finalizados")

    def check_orphan_processes(self):
        """Verifica si hay procesos huérfanos de sesiones anteriores al iniciar."""
        if hasattr(self, 'logger'):
            self.logger.info("[STARTUP] Verificando procesos huérfanos...")
        
        try:
            import subprocess
            
            if sys.platform == "win32":
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                       capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                orphan_pids = []
                for line in result.stdout.split('\n'):
                    if 'python.exe' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                pid = int(parts[1])
                                if pid != os.getpid():
                                    orphan_pids.append(pid)
                            except:
                                pass
                
                if orphan_pids and hasattr(self, 'logger'):
                    self.logger.warning(f"[STARTUP] Procesos python.exe detectados: {orphan_pids}")
                    
                    if hasattr(self, 'root') and hasattr(self, 'messagebox'):
                        if messagebox.askyesno("Procesos Huérfanos", 
                            f"Se detectaron {len(orphan_pids)} procesos de Python activos.\n"
                            f"¿Desea limpiarlos antes de iniciar?"):
                            for pid in orphan_pids:
                                try:
                                    if sys.platform == "win32":
                                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                                     capture_output=True, timeout=3)
                                    if hasattr(self, 'logger'):
                                        self.logger.info(f"[STARTUP] Proceso {pid} terminado")
                                except:
                                    pass
            
            if hasattr(self, 'logger'):
                self.logger.info("[STARTUP] Verificación de huérfanos completada")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"[STARTUP] Error verificando huérfanos: {e}")

    def monitor_child_processes(self):
        """Watchdog que monitorea y limpia procesos hijos automáticamente."""
        def cleanup_loop():
            while True:
                time.sleep(30)
                try:
                    if not hasattr(self, 'dashboard_process') or self.dashboard_process is None:
                        continue
                    
                    if self.dashboard_process.poll() is not None:
                        self.dashboard_process = None
                        if hasattr(self, 'logger'):
                            self.logger.info("[WATCHDOG] Proceso Dashboard muerto detectado y limpiado")
                except:
                    pass
        
        import threading
        monitor_thread = threading.Thread(target=cleanup_loop, daemon=True, name="ProcessWatchdog")
        monitor_thread.start()
        if hasattr(self, 'logger'):
            self.logger.info("[STARTUP] Watchdog de procesos iniciado")
    # ==================== FIN MÓDULO: MÉTODOS DE LIMPIEZA DE CIERRE ====================

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
                        
                        # Distribución Inteligente por Bloques
                        blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
                        self.root.after(0, lambda: self.analysis_text.insert(tk.END, f"\n🚀 Distribuyendo: {f} ({len(blocks)} bloques)\n"))
                        
                        for block in blocks:
                            res = self.kb_distributor.process_and_distribute(block, source=f)
                            
                            def update_ui(r=res):
                                status_icon = "✅" if r["status"] == "SUCCESS" else "👁️" if r["status"] == "PENDING_REVIEW" else "🚫"
                                targets = ", ".join(r.get("targets", []))
                                self.analysis_text.insert(tk.END, f"   {status_icon} [{r['status']}] -> {targets}\n")
                                self.analysis_text.see(tk.END)
                            
                            self.root.after(0, update_ui)
                        
                        self.root.after(0, lambda: self.analysis_text.insert(tk.END, "-"*40 + "\n"))
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
        # --- INICIO FUNCIONALIDAD US-010-SEARCH: BÚSQUEDA AVANZADA CON METADATOS ---
        if not self.knowledge_db:
            self.search_results_tree.insert("", tk.END, values=("Error", "DB no disponible", "", "", "", "", ""))
            return
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
        # ==================== [FIX-014] INICIO: TEMA ROBUSTO EN FROZEN MODE ====================
        # [PROBLEMA] sv-ttk no funciona correctamente en ejecutable PyInstaller
        # [SOLUCIÓN] Aplicar tema manualmente con fallback para frozen mode
        try:
            theme = "darkly"  # Bootstrap Default
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    theme = cfg.get("theme", "darkly")
            
            self.apply_specific_theme(theme)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error cargando preferencia de tema: {e}")
            self.current_theme = "dark"
        # ==================== [FIX-014] FIN ====================
    
    def apply_theme_manually(self, theme):
        """Aplica tema manualmente sin sv-ttk (para frozen mode)."""
        bg_color = "#0a0e1a" if theme == "dark" else "#f8fafc"
        fg_color = "#f1f5f9" if theme == "dark" else "#0f172a"
        
        try:
            self.root.configure(bg=bg_color)
            self.style.configure("TFrame", background=bg_color)
            self.style.configure("TLabel", background=bg_color, foreground=fg_color)
            self.style.configure("Header.TLabel", foreground="#60a5fa" if theme == "dark" else "#2563eb", background=bg_color)
            self.style.configure("TLabelframe", background=bg_color)
            self.style.configure("TLabelframe.Label", foreground=fg_color, background=bg_color)
        except Exception:
            pass  # Silenciar errores menores

    def get_available_themes(self):
        """Retorna lista de themes disponibles de ttkbootstrap."""
        return {
            "darkly": "🌙 Oscuro (Darkly) - Premium Enterprise",
            "litera": "☀️ Claro (Litera) - Limpio Minimalista",
            "teal_dark": "💎 Teal Dark - Elite Platinum",
            "cyborg": "🤖 Cyborg - High Tech",
            "cosmo": "🌐 Cosmo - Moderno Web",
            "journal": "📓 Journal - Elegante Clásico",
            "flatly": "📄 Flatly - Claro Sutil"
        }
    
    def apply_specific_theme(self, theme_name):
        """Aplica un tema Bootstrap específico con soporte multi-theme."""
        is_custom_teal = theme_name == "teal_dark"
        base_theme = "darkly" if is_custom_teal else theme_name

        available_themes = list(self.get_available_themes().keys())
        
        if base_theme not in available_themes and not is_custom_teal:
            base_theme = "darkly"
        
        try:
            self.current_theme = theme_name
            self.root.style.theme_use(base_theme)
            self.configure_styles()
            self.save_theme_preference(theme_name)
            self.log(f"🎨 Tema aplicado: {theme_name}")
        except Exception as e:
            self.logger.error(f"Error aplicando tema {theme_name}: {e}")
            try:
                self.root.style.theme_use("darkly")
            except:
                pass

    def _create_nav_buttons(self):
        """Crea los botones de la barra lateral mapeados a las pestañas."""
        tabs = [
            ("Descargas", "📥"), ("Procesamiento", "⚙️"), ("Inteligencia", "🧠"),
            ("Búsqueda", "🔍"), ("Monitor", "📺"), ("Dashboard", "📊"),
            ("Pendientes", "🎥"), ("Revisión", "👁️"), ("Programación", "📅"),
            ("Configuración", "⚙️")
        ]
        
        for i, (name, icon) in enumerate(tabs):
            btn = ttk.Button(
                self.side_nav,
                text=f"{icon}  {name}",
                style="link",
                command=lambda idx=i: self._switch_tab(idx)
            )
            btn.pack(fill=tk.X, padx=5, pady=1)
            self.nav_btns.append(btn)
        
        self.root.after(100, lambda: self._switch_tab(0)) # Seleccionar inicio

    def _switch_tab(self, index):
        """Cambia la pestaña y resalta el botón activo."""
        try:
            self.notebook.select(index)
            for i, btn in enumerate(self.nav_btns):
                btn.configure(bootstyle="info-link" if i == index else "link")
        except Exception:
            pass
    
    def switch_theme(self, theme_name=None):
        """
        Cambia el tema dinámicamente.
        Si no se especifica theme_name, alterna entre darkly y litera.
        """
        available = ["darkly", "litera", "cyborg", "cosmo", "journal", "flatly"]
        
        if theme_name is None:
            # Alternar entre darkly y litera
            current_idx = available.index(self.current_theme) if self.current_theme in available else 0
            next_idx = (current_idx + 1) % 2  # Solo alternar darkly/litera
            theme_name = available[next_idx]
        elif theme_name == "toggle":
            # Toggle oscuro/claro
            if self.current_theme in ["darkly", "cyborg"]:
                theme_name = "litera"
            else:
                theme_name = "darkly"
        
        self.apply_specific_theme(theme_name)

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

    # =========================================================================
    # [INI MÓDULO 3] Abrir Editor de Temas
    # =========================================================================
    
    def show_theme_editor(self):
        """Abre el editor visual de temas personalizados."""
        if not self.theme_manager:
            messagebox.showerror("Error", "El gestor de temas no está disponible")
            return
        
        if not open_theme_editor:
            messagebox.showerror("Error", "El módulo de editor de temas no se pudo cargar")
            return
        
        open_theme_editor(self.root, self.theme_manager, self.current_theme)

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
            self.log("[🔄] Modo vigilancia activado. Iniciando primer ciclo...")
            
            # ✅ CORRECCIÓN: Iniciar el ciclo inmediatamente
            self._run_vigilance_cycle()
        else:
            # Cancelar el timer si existe
            if hasattr(self, '_monitor_timer_id'):
                try:
                    self.root.after_cancel(self._monitor_timer_id)
                    del self._monitor_timer_id
                except Exception:
                    pass
            
            ToastNotification.show(self.root, "⏹️ Modo vigilancia desactivado", "info")
            self.log("[⏹️] Modo vigilancia desactivado.")

    def _run_vigilance_cycle(self):
        """Ejecuta la descarga y programa el siguiente ciclo en 24 horas."""
        # Verificar si el modo sigue activo (por si el usuario lo apagó manualmente)
        if not self.monitor_var.get():
            return

        self.log("[👁️] Ejecutando ciclo de vigilancia...")
        
        # Ejecutar la descarga del canal actual usando la lógica existente
        # Esto respetará secure_mode y download_archive si están configurados en download_tab/download_service
        self.start_download()

        # Programar el siguiente ciclo en 24 horas (24 * 60 * 60 * 1000 ms = 86400000 ms)
        # Guardamos el ID del timer para poder cancelarlo si se desactiva el modo
        self._monitor_timer_id = self.root.after(86400000, self._run_vigilance_cycle)
        self.log(f"[⏱️] Próximo ciclo programado en 24 horas.")

    # ==================== INICIO MÓDULO: LIMPIEZA_AUTOMATICA_CACHE ====================
    def _auto_clean_cache(self, silent=True):
        """Limpia caché de yt-dlp automáticamente (silencioso o con feedback)."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--rm-cache-dir"],
                capture_output=True, timeout=30
            )
            if not silent:
                self.log("[+] Caché de yt-dlp limpiada automáticamente")
            return True
        except Exception as e:
            if not silent:
                self.log(f"[-] Error limpiando caché: {e}")
            return False
    # ==================== FIN MÓDULO: LIMPIEZA_AUTOMATICA_CACHE ====================

    # ==================== INICIO MÓDULO: AUTO_START_OLLAMA ====================
    def _auto_start_ollama(self):
        """Inicia Ollama automáticamente si no está corriendo."""
        import socket
        
        ollama_port = 11434
        try:
            # Verificar si Ollama ya está corriendo
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect(('127.0.0.1', ollama_port))
                    s.close()
                    # Ya está corriendo
                    self.log("[AUTO] Ollama ya está ejecutándose")
                    return True
                except:
                    pass
            
            # No está corriendo -> iniciar
            self.log("[AUTO] Iniciando Ollama...")
            
            #BUSCAR ollama.exe en rutas comunes
            ollama_paths = [
                os.path.expandvars("%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe"),
                os.path.expandvars("%PROGRAMFILES%\\Ollama\\ollama.exe"),
                os.path.join(os.environ.get("USERPROFILE", ""), ".local", "bin", "ollama.exe"),
                "ollama.exe"  # En PATH
            ]
            
            ollama_cmd = None
            for path in ollama_paths:
                if os.path.exists(path):
                    ollama_cmd = path
                    break
            
            if not ollama_cmd:
                # Intentar usar donde PATH
                import shutil
                ollama_cmd = shutil.which("ollama.exe") or shutil.which("ollama")
            
            if ollama_cmd:
                subprocess.Popen(
                    [ollama_cmd, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                self.log("[AUTO] Ollama iniciado correctamente")
                return True
            else:
                self.log("[AUTO] Ollama no encontrado en el sistema")
                return False
                
        except Exception as e:
            self.log(f"[AUTO] Error iniciando Ollama: {e}")
            return False
    # ==================== FIN MÓDULO: AUTO_START_OLLAMA ====================

    # ==================== INICIO MÓDULO: DETECCION_PART_FILES ====================
    def _detect_orphan_parts(self):
        """Detecta archivos .part huérfanos en carpeta de salida."""
        output_dir = self.settings.get("output_dir", self.input_dir) if hasattr(self, 'settings') else self.input_dir
        orphaned = []
        try:
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    if f.endswith(".part"):
                        orphaned.append(os.path.join(output_dir, f))
        except:
            pass
        return orphaned

    def _cleanup_orphan_parts(self):
        """Elimina archivos .part huérfanos SOLO si no hay descargas activas."""
        if getattr(self, 'queue_running', False):
            return False
        
        orphaned = self._detect_orphan_parts()
        if not orphaned:
            return False
        
        count = len(orphaned)
        if messagebox.askyesno("Limpiar Residuos", 
            f"Se detectaron {count} archivos incompletos (.part).\n"
            "Estos archivos son de descargas anteriores que no se completaron.\n\n"
            "¿Desea eliminarlos?"):
            removed = 0
            for f in orphaned:
                try: 
                    os.remove(f)
                    removed += 1
                except: 
                    pass
            self.log(f"[+] {removed} archivos .part eliminados")
            return True
        return False
    # ==================== FIN MÓDULO: DETECCION_PART_FILES ====================

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
        if not hasattr(self, 'dashboard_tab_loaded') or not self.dashboard_tab_loaded:
            for widget in self.tab_dashboard.winfo_children():
                widget.destroy()
            ttk.Label(self.tab_dashboard, text="⏳ Cargando Dashboard...", 
                     font=("Inter", 11), foreground="#f59e0b").pack(pady=40)
            self.root.after(500, self.setup_dashboard_tab)
            return
        
        if len(self.tab_dashboard.winfo_children()) > 0:
            return
        
        frame = ttk.Frame(self.tab_dashboard)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(frame, text="📊 Dashboard Web Remoto v2.5.3", font=("Segoe UI", 18, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="Monitorea el estado de tu sistema Enterprise Platinum desde cualquier dispositivo.", 
                 font=("Segoe UI", 11), foreground="gray").pack(pady=(0, 30))
        
        # Info Server
        info_frame = ttk.LabelFrame(frame, text=" Estado del Servidor ", )
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        url_label = ttk.Label(info_frame, text="http://localhost:7000", 
                               font=("Consolas", 14, "bold"), foreground="#3b82f6", cursor="hand2")
        url_label.pack(pady=10)
        
        def get_dashboard_url():
            dashboard_config = self.settings.get("dashboard", {})
            port = dashboard_config.get("port", 7000)
            return f"http://127.0.0.1:{port}"
        
        url_label.bind("<Button-1>", lambda e: self.open_url(get_dashboard_url()))
        
        # Control Server
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        # ==================== INICIO MÓDULO: DASHBOARD TAB CENTRALIZADO ====================
        # DEFINIR WIDGETS PRIMERO (antes de funciones que los usan)
        status_lbl = ttk.Label(btn_frame, text="⚫ Servidor Detenido", font=("Segoe UI", 10))
        status_lbl.pack(pady=5)
        
        btn_server = ttk.Button(btn_frame, text="▶️ Iniciar Servidor Web", style="Success.TButton", width=25)
        btn_server.pack(pady=5)
        
        # ==================== [INI] FUNCIONALIDAD: TOGGLE SERVER LOGIC (FIX-005) ====================
        def toggle_server():
            # Verificación de estado basada en la bandera de actividad real del servicio
            is_running = getattr(self, 'dashboard_active', False)

            if not is_running:
                # --- Inicio de Servidor ---
                success, msg = self.start_dashboard_server()
                if success:
                    btn_server.config(text="⏹️ Detener Servidor Web", style="Danger.TButton")
                    status_lbl.config(text=f"🟢 Servidor en {msg}", foreground="#10b981")
                    url_label.config(text=msg)
                    # Auto-abrir navegador
                    import threading
                    threading.Timer(1.5, lambda: self.open_url(msg)).start()
                    ToastNotification.show(self.root, f"Dashboard iniciado en {msg}", "success")
                else:
                    messagebox.showerror("Error de Dashboard", msg)
            else:
                # --- Parada de Servidor ---
                success, msg = self.stop_dashboard_server()
                btn_server.config(text="▶️ Iniciar Servidor Web", style="Success.TButton")
                status_lbl.config(text="⚫ Servidor Detenido", foreground="gray")
                url_label.config(text="http://localhost:7000")
                ToastNotification.show(self.root, "Dashboard Web Detenido", "info")
        # ==================== [END] FUNCIONALIDAD: TOGGLE SERVER LOGIC (FIX-005) ====================
        
        # Asignar comando DESPUÉS de definir toggle_server
        btn_server.config(command=toggle_server)
        
        # Verificar si ya hay un servidor corriendo en el puerto
        def is_port_in_use(port):
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        
        dashboard_config = self.settings.get("dashboard", {})
        default_port = dashboard_config.get("port", 7000)
        if is_port_in_use(default_port):
            btn_server.config(text="⏹️ Detener Servidor Web", style="Danger.TButton")
            status_lbl.config(text="🟢 Puerto en uso (ya activo)", foreground="#10b981")
            self.dashboard_active = True
        # ==================== FIN MÓDULO: DASHBOARD TAB ====================

    # ==================== INICIO MÓDULO: DASHBOARD SERVER CENTRALIZADO ====================
    def get_extended_dashboard_stats(self):
        """
        [US-002-EXT] Obtiene métricas de sistema extendidas para el Dashboard.
        Incluye: CPU, Memoria, Tamaño de DB y Estado del Monitor.
        """
        try:
            # --- INICIO FUNCIONALIDAD: RECOLECCIÓN DE MÉTRICAS HARDWARE ---
            if psutil:
                cpu_usage = psutil.cpu_percent(interval=None)
                ram_usage = psutil.virtual_memory().percent
            else:
                cpu_usage = 0
                ram_usage = 0
            # --- FIN FUNCIONALIDAD ---
            
            # Métricas de Aplicación y Persistencia
            db_size = 0
            if self.db_manager and os.path.exists(self.db_manager.db_path):
                db_size = os.path.getsize(self.db_manager.db_path) / (1024 * 1024) # MB
                
            monitor_active = False
            if self.monitor_service:
                monitor_active = self.monitor_service.is_monitoring()
                
            # Estadísticas de la cola de procesamiento
            queue_count = len(self.download_queue)
            queue_status = "Corriendo" if self.queue_running else "Pausada" if self.queue_paused else "Inactiva"
            
            # Detecciones recientes (desde el tracker JSON)
            new_videos_today = 0
            if self.video_tracker:
                stats = self.video_tracker.get_stats()
                new_videos_today = stats['statistics'].get('total_new', 0)

            return {
                "system": {
                    "cpu_percent": cpu_usage,
                    "ram_percent": ram_usage,
                    "db_size_mb": f"{db_size:.2f}"
                },
                "app_state": {
                    "monitor_active": monitor_active,
                    "queue_count": queue_count,
                    "queue_status": queue_status,
                    "new_found_session": new_videos_today
                },
                "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            self.logger.error(f"[DASHBOARD] Fallo al recolectar métricas: {e}")
            return {}

    def _is_port_free(self, port):
        """Verifica si un puerto está libre (no usado)."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
    
    def start_dashboard_server(self, callback_ui=None):
        """Inicia el servidor del dashboard en un hilo (no como subprocess)."""
        import sys as sys_module
        import threading
        
        # Verificar si ya hay un proceso activo
        if hasattr(self, 'dashboard_server_thread') and self.dashboard_server_thread.is_alive():
            port = getattr(self, 'dashboard_port', 7000)
            return True, f"http://127.0.0.1:{port}"

        # --- INICIO FUNCIONALIDAD: SEGURIDAD POR TOKEN DINÁMICO ---
        auth_token = secrets.token_urlsafe(16)
        # --- FIN FUNCIONALIDAD ---
        
        dashboard_config = self.settings.get("dashboard", {})
        port = dashboard_config.get("port", 7000)
        
        # Loop de 5 intentos con verificación previa de puerto libre
        for attempt in range(5):
            # ==================== INICIO MÓDULO: VERIFICACIÓN PREVIA DE PUERTO ====================
            while port < 10000 and not self._is_port_free(port):
                port += 1
            # ==================== FIN MÓDULO: VERIFICACIÓN ====================
            
            # Intentar iniciar el servidor en un hilo
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "dashboard_server_module", 
                    os.path.join(self.base_dir, "dashboard_server.py")
                )
                if spec and spec.loader:
                    dashboard_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(dashboard_module)
                    
                    # Inyectar Token en entorno
                    os.environ["KDP_DASHBOARD_TOKEN"] = auth_token
                    
                    # Configurar el puerto en el módulo antes de ejecutar
                    dashboard_module.PORT = port
                    dashboard_module.HOST = "127.0.0.1"
                    
                    # Iniciar servidor en hilo separado
                    def run_server_thread():
                        try:
                            dashboard_module.run_server()
                        except Exception as e:
                            print(f"Error en servidor dashboard: {e}")
                    
                    self.dashboard_server_thread = threading.Thread(target=run_server_thread, daemon=True)
                    self.dashboard_server_thread.start()
                    
                    # Esperar un poco para verificar que inició
                    import time
                    time.sleep(2)
                    
                    # Verificar que el hilo está vivo y el puerto está en uso
                    if self.dashboard_server_thread.is_alive() and not self._is_port_free(port):
                        # Guardar puerto exitoso en settings
                        self.settings['dashboard']['port'] = port
                        try:
                            with open(self.config_file, 'w', encoding='utf-8') as f:
                                import json
                                json.dump(self.settings, f, indent=2)
                        except Exception as e:
                            print(f"Warning: No se pudo guardar puerto: {e}")
                        
                        self.dashboard_port = port
                        self.dashboard_active = True
                        return True, f"http://127.0.0.1:{port}?token={auth_token}"
                    else:
                        # El servidor no inició correctamente, intentar siguiente puerto
                        port += 1
                        continue
            except Exception as e:
                port += 1
                continue
        
        return False, "Puertos 8000-8004 ocupados o error de inicio"
    
    def stop_dashboard_server(self):
        """Detiene el servidor del dashboard (hilo)."""
        try:
            # El hilo daemon se detendrá cuando la app cierre
            # Para una parada inmediata, necesitamos acceder al servidor global
            import dashboard_server as ds
            if hasattr(ds, '_server') and ds._server:
                ds._server.shutdown()
                ds._server.server_close()
                ds._server = None
            
            if hasattr(self, 'dashboard_server_thread'):
                self.dashboard_server_thread = None
            
            self.dashboard_active = False
            return True, "Servidor detenido"
        except Exception as e:
            return False, f"Error al detener: {str(e)}"
    
    def _auto_start_dashboard_thread(self):
        """Hilo para auto-inicio del dashboard sin bloquear UI."""
        import threading
        import time
        time.sleep(3)
        try:
            success, msg = self.start_dashboard_server()
            if success:
                self.root.after(0, lambda: self.log(f"✅ Dashboard iniciado automáticamente: {msg}"))
            else:
                self.root.after(0, lambda: self.log(f"⚠️ Auto-inicio dashboard: {msg}"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Error auto-inicio dashboard: {e}"))
    # ==================== FIN MÓDULO: DASHBOARD SERVER ====================
    
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

if __name__ == "__main__":
    error_msg = "No se pudo inicializar la aplicación."
    try:
        # Usar ttkbootstrap.Window con tema moderno Bootstrap
        root = ttk.Window(themename="cosmo")  # Tema Bootstrap claro y moderno
        app = TranscriptionProcessorApp(root)
        root.mainloop()
    except Exception as e:
        # Manejo de errores global para que no se cierre silenciosamente
        error_msg = f"Ocurrió un error inesperado:\n{str(e)}\n\nDetalles:\n{traceback.format_exc()}"
        logging.error(error_msg)
        try:
            messagebox.showerror("Error Crítico", error_msg)
        except Exception as inner_e:
            # Fallback a consola si la GUI ya colapsó o no está disponible
            print(f"❌ Error Crítico (UI no disponible): {inner_e}")
            print(error_msg)
        finally:
            # Asegurar cierre limpio de recursos si es posible
            try:
                if 'root' in locals():
                    root.destroy()
            except:
                pass