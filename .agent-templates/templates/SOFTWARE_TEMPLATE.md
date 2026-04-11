# 🏗️ Template: Aplicación de Escritorio SOMD

> **Arquitectura:** Service-Oriented Modular Desktop  
> **Versión:** 1.0.0  
> **Fecha:** 2026-04-09

---

## 1. Estructura del Proyecto

```
PROYECTO/
├── app/
│   ├── core/                    # Lógica fundamental
│   │   ├── config.py           # Configuración centralizada
│   │   ├── security.py       # Seguridad (encriptación)
│   │   ├── logger.py         # Logging
│   │   ├── ui_framework.py  # Framework UI
│   │   └── plugin_manager.py # Plugins
│   ├── database/              # Persistencia
│   │   └── db_manager.py     # Gestor DB
│   ├── services/              # Lógica de negocio
│   │   └── *.py            # Servicios
│   └── ui/                    # Interfaz
│       └── tabs/              # Pestañas
├── data/                     # Datos entrada
├── outputs/                   # Datos salida
├── logs/                     # Logs
├── gui_app.py                # Entry point
├── build_exe.py              # Build script
└── requirements.txt
```

---

## 2. Componentes core/config.py

```python
"""
Config - Gestión Centralizada de Configuración
"""
from pathlib import Path
import json
import os

class Config:
    def __init__(self):
        self.base_dir = self._get_base_dir()
        self.config_file = self.base_dir / "settings.json"
        self._load()
    
    def _get_base_dir(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        return Path(__file__).parent.parent
    
    def _load(self):
        defaults = {
            "input_dir": str(self.base_dir / "data"),
            "output_dir": str(self.base_dir / "outputs"),
            "ai_provider": "none",
            "ai_api_key": ""
        }
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                defaults.update(json.load(f))
        self.__dict__.update(defaults)
    
    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
```

---

## 3. Componentes core/security.py

```python
"""
Security - Encriptación AES-256-GCM
"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class SecurityManager:
    def __init__(self, key_file=None):
        self.key_file = key_file or Path.home() / ".app.key"
        self.key = self._load_or_create_key()
    
    def _load_or_create_key(self):
        if self.key_file.exists():
            return self.key_file.read_bytes()
        key = os.urandom(32)
        self.key_file.write_bytes(key)
        return key
    
    def encrypt(self, plaintext: str) -> str:
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return (nonce + ct).hex()
    
    def decrypt(self, ciphertext: str) -> str:
        aesgcm = AESGCM(self.key)
        data = bytes.fromhex(ciphertext)
        nonce, ct = data[:12], data[12:]
        return aesgcm.decrypt(nonce, ct, None).decode()
```

---

## 4. Componentes core/logger.py

```python
"""
Logger - Logging Rotativo con Auditoría
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

def setup_app_logging(base_dir):
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # App log
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=5e6, backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    ))
    logger.addHandler(handler)
    
    # Audit log
    audit = logging.getLogger("audit")
    audit.setLevel(logging.INFO)
    audit_handler = RotatingFileHandler(
        log_dir / "audit.log", maxBytes=1e6, backupCount=5
    )
    audit_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(message)s"
    ))
    audit.addHandler(audit_handler)
    
    return logger, audit
```

---

## 5. Componentes core/ui_framework.py

```python
"""
UI Framework - Tema y Responsive
"""
import sv_ttk
from tkinter import ttk

class ThemeManager:
    def __init__(self, root):
        self.root = root
        sv_ttk.set_theme("dark")
    
    def toggle_theme(self):
        current = sv_ttk.get_theme()
        new = "light" if current == "dark" else "dark"
        sv_ttk.set_theme(new)
        return new

class ResponsiveManager:
    def __init__(self, root):
        self.root = root
        self.bind("<Configure>", self._on_resize)
    
    def _on_resize(self, event):
        width = self.root.winfo_width()
        # Lógica responsive
        pass
```

---

## 6. Componentes database/db_manager.py

```python
"""
Database Manager - SQLite con Migraciones
"""
import sqlite3
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        self.conn.commit()
        return cursor
    
    def fetch_all(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()
```

---

## 7. Componentes services/template_service.py

```python
"""
Template Service - Lógica de Negocio
"""
import hashlib
from pathlib import Path

class TemplateService:
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.input_dir = Path("data")
        self.output_dir = Path("outputs")
    
    def process(self, file_path):
        # 1. Leer archivo
        content = file_path.read_text(encoding="utf-8")
        
        # 2. Deduplicar por MD5
        hash_md5 = hashlib.md5(content.encode()).hexdigest()
        if self._is_duplicate(hash_md5):
            return {"status": "duplicate", "hash": hash_md5}
        
        # 3. Procesar
        processed = self._process_content(content)
        
        # 4. Guardar
        output_path = self.output_dir / file_path.name
        output_path.write_text(processed, encoding="utf-8")
        
        # 5. Registrar en DB
        self._save_to_db(file_path.name, hash_md5)
        
        return {"status": "success", "output": str(output_path)}
    
    def _is_duplicate(self, hash_md5):
        if not self.db: return False
        result = self.db.fetch_all(
            "SELECT id FROM items WHERE hash = ?", (hash_md5,)
        )
        return len(result) > 0
    
    def _process_content(self, content):
        # Custom processing logic
        return content.strip()
    
    def _save_to_db(self, filename, hash_md5):
        if self.db:
            self.db.execute(
                "INSERT INTO items (name, hash) VALUES (?, ?)",
                (filename, hash_md5)
            )
```

---

## 8. GUI Entry Point (gui_app.py)

```python
"""
GUI App - Entry Point Principal
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import sv_ttk

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mi Aplicación v1.0")
        self.root.geometry("900x600")
        
        # Inicializar componentes
        from app.core.config import Config
        from app.core.security import SecurityManager
        from app.core.logger import setup_app_logging
        from app.database.db_manager import DatabaseManager
        
        self.config = Config()
        self.security = SecurityManager()
        self.logger, self.audit = setup_app_logging(self.config.base_dir)
        self.db = DatabaseManager(self.config.base_dir / "data" / "app.db")
        
        # UI
        self._create_ui()
        
        # Iniciar
        self.root.mainloop()
    
    def _create_ui(self):
        sv_ttk.set_theme("dark")
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab principal
        self.tab_main = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_main, text=" Principal ")
        
        # Contenido
        ttk.Label(self.tab_main, text="Bienvenido", font=("Segoe UI", 18)).pack(pady=20)
        
        # Status bar
        self.status = tk.StringVar(value="Sistema listo")
        tk.Label(self.root, textvariable=self.status, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

if __name__ == "__main__":
    App()
```

---

## 9. Build Script (build_exe.py)

```python
"""
Build Script - PyInstaller
"""
import PyInstaller.__main__
import shutil
from pathlib import Path

def build():
    output_dir = Path("dist")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    PyInstaller.__main__.run([
        "gui_app.py",
        "--name=Aplicacion",
        "--onefile",
        "--windowed",
        f"--distpath={output_dir}",
        "--clean"
    ])

if __name__ == "__main__":
    build()
```

---

## 10. Requisitos (requirements.txt)

```
# Core
cryptography>=41.0.0

# UI
sv-ttk>=0.3.1

# Data
yt-dlp>=2024.0.0

# Build
pyinstaller>=6.0.0
```

---

## 11. Checklist de Implementación

| Componente | Estado | Notas |
|-----------|--------|-------|
| Estructura de directorios | ⬜ | Crear carpetas app/, data/, outputs/, logs/ |
| Config centralizada | ⬜ | settings.json |
| Security (AES) | ⬜ | key file oculto |
| Logger | ⬜ | app.log + audit.log |
| Theme manager | ⬜ | Dark/Light toggle |
| Database SQLite | ⬜ | init + migrations |
| Service base | ⬜ | Template |
| GUI principal | ⬜ | Tabs + status bar |
| Build script | ⬜ | PyInstaller |
| requirements.txt | ⬜ | Dependencias |

---

## 12. Configuración (.env)

```env
# AI (opcional)
AI_PROVIDER=none
AI_API_KEY=

# Personalizado
CUSTOM_PARAM=value
```

---

*Template generado automáticamente desde KDP Master Suite v2.5.0*
*Arquitectura SOMD - Service-Oriented Modular Desktop*