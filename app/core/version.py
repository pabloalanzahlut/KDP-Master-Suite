"""
Módulo centralizado de gestión de versión.
Proporciona acceso unificado a la versión de la aplicación.
"""

import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
VERSION_FILE = PROJECT_ROOT / "VERSION.txt"
SETTINGS_FILE = PROJECT_ROOT / "settings.json"

DEFAULT_VERSION = "2.4.4"

def get_version() -> str:
    """Obtiene la versión actual desde settings.json o VERSION.txt."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                if 'version' in settings and settings['version']:
                    return settings['version']
        except (json.JSONDecodeError, IOError):
            pass
    
    if VERSION_FILE.exists():
        try:
            return VERSION_FILE.read_text(encoding='utf-8').strip()
        except IOError:
            pass
    
    return DEFAULT_VERSION

def set_version(version: str) -> bool:
    """Guarda la versión en settings.json."""
    try:
        settings = {}
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        settings['version'] = version
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        
        return True
    except Exception:
        return False

def get_update_settings() -> dict:
    """Obtiene configuración de actualizaciones desde settings.json."""
    defaults = {
        'auto_check_updates': True,
        'last_update_check': None,
        'last_checked_version': None,
        'update_channel': 'stable'
    }
    
    if not SETTINGS_FILE.exists():
        return defaults
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        for key in defaults:
            if key not in settings:
                settings[key] = defaults[key]
        
        return settings
    except (json.JSONDecodeError, IOError):
        return defaults

def save_update_check(timestamp: str, version: str) -> bool:
    """Guarda timestamp y versión del último check de actualizaciones."""
    try:
        settings = {}
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        settings['last_update_check'] = timestamp
        settings['last_checked_version'] = version
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        
        return True
    except Exception:
        return False

__version__ = get_version()