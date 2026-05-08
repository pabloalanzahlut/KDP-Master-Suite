"""
UI Backend Logic - Advanced Features
====================================
Implementación lógica del lado del backend para soportar características
avanzadas de UI/UX como temas, iconos, animaciones y plugins.
"""

import os
import json
import threading
import logging
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import time
import math

# Logger
logger = logging.getLogger("ui_backend")

class ThemeManager:
    """
    Gestiona la carga, guardado y aplicación de temas personalizados.
    """
    def __init__(self, themes_dir: str = "themes"):
        self.themes_dir = Path(themes_dir)
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.current_theme_name = "default"
        self.themes_cache = {}
        
        # Tema por defecto
        self.default_theme = {
            "name": "default",
            "colors": {
                "bg_primary": "#f8fafc",
                "bg_secondary": "#ffffff",
                "accent": "#3b82f6",
                "text_primary": "#0f172a",
                "success": "#10b981",
                "error": "#ef4444"
            },
            "fonts": {
                "header": ("Segoe UI", 22, "bold"),
                "body": ("Segoe UI", 10, "normal")
            }
        }
        
    def load_theme(self, theme_name: str) -> Dict:
        """Carga un tema desde JSON o caché."""
        if theme_name in self.themes_cache:
            return self.themes_cache[theme_name]
        
        theme_path = self.themes_dir / f"{theme_name}.json"
        
        if theme_path.exists():
            try:
                with open(theme_path, 'r', encoding='utf-8') as f:
                    theme = json.load(f)
                    self.themes_cache[theme_name] = theme
                    return theme
            except Exception as e:
                logger.error(f"Error cargando tema {theme_name}: {e}")
                return self.default_theme
        return self.default_theme

    def save_theme(self, theme_data: Dict):
        """Guarda un nuevo tema personalizado."""
        name = theme_data.get("name", "custom_theme")
        path = self.themes_dir / f"{name}.json"
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=4)
            self.themes_cache[name] = theme_data
        except Exception as e:
            logger.error(f"Error guardando tema {name}: {e}")

    def get_available_themes(self) -> List[str]:
        """Lista los temas disponibles en el directorio."""
        themes = ["default"]
        for file in self.themes_dir.glob("*.json"):
            themes.append(file.stem)
        return themes

class IconManager:
    """
    Gestiona la lógica de iconos, incluyendo soporte futuro para SVG.
    Abstrae la fuente de los iconos para la UI.
    """
    def __init__(self, assets_dir: str = "assets/icons"):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.icon_cache = {}
        
    def get_icon_path(self, icon_name: str, size: int = 24, as_svg: bool = False) -> Optional[str]:
        """
        Retorna la ruta al archivo de icono. Prioriza SVG si se solicita.
        """
        # Intenta buscar SVG primero si se solicita
        if as_svg:
            svg_path = self.assets_dir / f"{icon_name}.svg"
            if svg_path.exists():
                return str(svg_path)
                
        # Fallback a PNG
        png_path = self.assets_dir / f"{icon_name}_{size}px.png"
        if png_path.exists():
            return str(png_path)
            
        # Intenta buscar cualquier PNG con ese nombre
        png_generic = self.assets_dir / f"{icon_name}.png"
        if png_generic.exists():
            return str(png_generic)
            
        return None

class AnimationController:
    """
    Controlador lógico para animaciones.
    Calcula valores interpolados a lo largo del tiempo.
    """
    def __init__(self):
        self.animations = {}
        self._lock = threading.Lock()
        
    def ease_out_quad(self, t: float) -> float:
        return t * (2 - t)
        
    def ease_in_out_quad(self, t: float) -> float:
        return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t

    def animate_value(self, start_val: float, end_val: float, duration_ms: int, 
                     callback: Callable[[float], None], on_complete: Callable = None):
        """
        Ejecuta una animación de un valor numérico.
        NOTA: En Tkinter, esto debe integrarse con el mainloop (root.after).
        Esta clase provee la lógica "headless" o generadora de frames.
        """
        start_time = time.time() * 1000
        
        def step():
            now = time.time() * 1000
            elapsed = now - start_time
            progress = min(elapsed / duration_ms, 1.0)
            
            # Interpolación con easing
            eased_progress = self.ease_out_quad(progress)
            current_val = start_val + (end_val - start_val) * eased_progress
            
            # Ejecutar callback UI
            # IMPORTANTE: El callback debe ser thread-safe si se llama desde threads
            # Idealmente este generador se usa dentro de un loop de UI
            callback(current_val)
            
            if progress < 1.0:
                pass # El sistema de UI debe volver a llamar a step()
                return False # No completado
            else:
                if on_complete:
                    on_complete()
                return True # Completado
                
        return step

class LayoutController:
    """
    Gestiona el estado del layout (Compacto vs Full).
    """
    def __init__(self):
        self.compact_mode = False
        self.window_size = (1200, 800)
        self.compact_size = (400, 600)
        
    def toggle_compact_mode(self) -> Tuple[int, int]:
        """Alterna el modo y retorna las nuevas dimensiones."""
        self.compact_mode = not self.compact_mode
        return self.compact_size if self.compact_mode else self.window_size
        
    def set_window_size(self, width: int, height: int):
        if not self.compact_mode:
            self.window_size = (width, height)

class DashboardBackend:
    """
    Provee datos agregados para el dashboard visual.
    Se conecta al DatabaseManager.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        
    def get_activity_data(self, days: int = 7) -> Dict:
        """Retorna datos para gráficas de barras (Videos por día)."""
        data = self.db.get_daily_video_counts(days)
        # Formato { "labels": [...], "values": [...] }
        return {
            "labels": [d['date'] for d in data],
            "values": [d['count'] for d in data]
        }
        
    def get_status_data(self) -> Dict:
        """Retorna datos para gráficas de pastel (Distribución de estados)."""
        data = self.db.get_status_distribution()
        labels = list(data.keys())
        values = list(data.values())
        return {"labels": labels, "values": values}

class PluginManager:
    """
    Sistema de plugins simple para extender la UI.
    """
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_plugins = {}
        
    def discover_plugins(self):
        """Busca archivos .py en la carpeta de plugins."""
        for file in self.plugins_dir.glob("*.py"):
            if file.stem.startswith("__"): continue
            
            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Verificar interfaz del plugin
                if hasattr(module, "register_plugin"):
                    info = getattr(module, "PLUGIN_INFO", {"name": file.stem})
                    self.loaded_plugins[file.stem] = {
                        "module": module,
                        "info": info,
                        "enabled": True
                    }
                    logger.info(f"Plugin descubierto: {info.get('name')}")
            except Exception as e:
                logger.error(f"Error cargando plugin {file.stem}: {e}")

class ShortcutManager:
    """
    Gestiona atajos de teclado personalizables.
    """
    def __init__(self, config_file: str = "shortcuts.json"):
        self.config_file = Path(config_file)
        self.shortcuts = {
            "save": "<Control-s>",
            "settings": "<Control-comma>",
            "quit": "<Control-q>",
            "new": "<Control-n>",
            "refresh": "<F5>"
        }
        self.load_shortcuts()
        
    def load_shortcuts(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    custom = json.load(f)
                    self.shortcuts.update(custom)
            except Exception:
                pass
                
    def save_shortcuts(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.shortcuts, f, indent=4)
        except Exception as e:
            logger.error(f"Error guardando atajos: {e}")
            
    def get_binding(self, action: str) -> str:
        return self.shortcuts.get(action, "")

# Instancia global única para facilitar acceso si se desea
# ui_system = { ... }
