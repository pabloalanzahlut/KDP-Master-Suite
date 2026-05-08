#!/usr/bin/env python3
"""
================================================================================
DIAGNOSTICO DEL DASHBOARD WEB - KDP Master
================================================================================
Script de diagnostico para identificar y reparar problemas de sincronizacion
del dashboard web. Ejecutar este script ante cualquier fallo del dashboard.

Uso: python diagnose_dashboard.py [--fix] [--test-endpoints]

Modulos:
    1. Verificacion de Base de Datos
    2. Verificacion de Configuracion (Token, Auth, SSE)
    3. Test de Endpoints del Servidor
    4. Auto-repair (opcional)

ubicacion sugerida: ./tools/analytics/diagnostic.py
================================================================================
"""

import sqlite3
import json
import os
import sys
import argparse
import subprocess
import socket
import time
from pathlib import Path
from datetime import datetime
import secrets
import urllib.request
import urllib.error

# ==================== CONFIGURACION ====================
PROJECT_ROOT = Path(".").resolve()  # Ir arriba de /tools/
DB_PATH = PROJECT_ROOT / "data" / "channel_monitor.db"
SETTINGS_PATH = PROJECT_ROOT / "settings.json"
SERVER_SCRIPT = PROJECT_ROOT / "dashboard_server.py"
DEFAULT_PORT = 8000

# Colores para terminal (sin acentos para Windows compatibility)
class Colors:
    GREEN = '[GREEN]'
    RED = '[RED]'
    YELLOW = '[YELLOW]'
    BLUE = '[BLUE]'
    CYAN = '[CYAN]'
    BOLD = '[BOLD]'
    END = '[END]'


def print_header(title):
    print(f"\n=== {title} ===\n")


def print_status(module, status, message=""):
    symbol = "[OK]" if status else "[FALLO]"
    status_text = "OK" if status else "FALLO"
    print(f"  {symbol} Modulo {module}: {status_text}")
    if message:
        print(f"      {message}")


# ==================== MODULO 1: VERIFICACION DE BASE DE DATOS ====================
def check_database():
    print_header("MODULO 1: Verificacion de Base de Datos")
    
    result = {
        "exists": False,
        "tables": False,
        "has_data": False,
        "channels": 0,
        "videos": 0,
        "processing": 0,
        "errors": []
    }
    
    # 1. Verificar que el archivo existe
    if DB_PATH.exists():
        print_status("DB-EXISTS", True, f"Archivo encontrado: {DB_PATH}")
        result["exists"] = True
    else:
        print_status("DB-EXISTS", False, f"Archivo no encontrado: {DB_PATH}")
        result["errors"].append("Base de datos no existe")
        return result
    
    # 2. Verificar tablas
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        
        required_tables = ["channels", "videos", "processing_history"]
        missing = [t for t in required_tables if t not in tables]
        
        if not missing:
            print_status("DB-TABLES", True, f"Tablas: {', '.join(tables)}")
            result["tables"] = True
        else:
            print_status("DB-TABLES", False, f"Faltan: {missing}")
            result["errors"].append(f"Tablas faltantes: {missing}")
            conn.close()
            return result
    except Exception as e:
        print_status("DB-TABLES", False, str(e))
        result["errors"].append(f"Error verificando tablas: {e}")
        return result
    
    # 3. Verificar datos
    try:
        cur.execute("SELECT COUNT(*) FROM channels WHERE active = 1")
        result["channels"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM videos")
        result["videos"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM processing_history")
        result["processing"] = cur.fetchone()[0]
        
        conn.close()
        
        if result["channels"] > 0 or result["videos"] > 0:
            print_status("DB-DATA", True, 
                f"Canales: {result['channels']}, Videos: {result['videos']}, Processing: {result['processing']}")
            result["has_data"] = True
        else:
            print_status("DB-DATA", False, "Base de datos vacia")
            result["errors"].append("No hay datos en la base de datos")
            
    except Exception as e:
        print_status("DB-DATA", False, str(e))
        result["errors"].append(f"Error verificando datos: {e}")
    
    return result


# ==================== MODULO 2: VERIFICACION DE CONFIGURACION ====================
def check_configuration():
    print_header("MODULO 2: Verificacion de Configuracion")
    
    result = {
        "settings_exists": False,
        "has_token": False,
        "has_dashboard_config": False,
        "enable_auth": None,
        "enable_sse": None,
        "token": None,
        "port": DEFAULT_PORT,
        "errors": []
    }
    
    # 1. Verificar que settings.json existe
    if SETTINGS_PATH.exists():
        print_status("CFG-FILE", True, f"Archivo encontrado: {SETTINGS_PATH}")
        result["settings_exists"] = True
    else:
        print_status("CFG-FILE", False, "settings.json no existe")
        result["errors"].append("settings.json no existe")
        return result
    
    # 2. Cargar configuracion
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print_status("CFG-LOAD", False, str(e))
        result["errors"].append(f"Error cargando settings: {e}")
        return result
    
    # 3. Verificar configuracion de dashboard
    if "dashboard" in config:
        print_status("CFG-DASHBOARD", True, "Seccion dashboard encontrada")
        result["has_dashboard_config"] = True
        
        dashboard = config["dashboard"]
        result["port"] = dashboard.get("port", DEFAULT_PORT)
        print(f"    Puerto configurado: {result['port']}")
    else:
        print_status("CFG-DASHBOARD", False, "Seccion dashboard no encontrada")
        result["errors"].append("Falta seccion 'dashboard' en settings.json")
    
    # 4. Verificar token
    if "dashboard_token" in config:
        result["has_token"] = True
        result["token"] = config["dashboard_token"]
        print_status("CFG-TOKEN", True, f"Token presente: {result['token'][:8]}...")
    else:
        print_status("CFG-TOKEN", False, "Token NO encontrado en settings.json")
        result["errors"].append("Falta 'dashboard_token' en settings.json")
    
    # 5. Verificar enable_auth
    result["enable_auth"] = config.get("enable_auth")
    if result["enable_auth"] is not None:
        print_status("CFG-AUTH", True, f"enable_auth: {result['enable_auth']}")
    else:
        print_status("CFG-AUTH", False, "enable_auth NO encontrado (default: True)")
        result["errors"].append("Falta 'enable_auth' en settings.json")
    
    # 6. Verificar enable_sse
    result["enable_sse"] = config.get("enable_sse")
    if result["enable_sse"] is not None:
        print_status("CFG-SSE", True, f"enable_sse: {result['enable_sse']}")
    else:
        print_status("CFG-SSE", False, "enable_sse NO encontrado (default: True)")
        result["errors"].append("Falta 'enable_sse' en settings.json")
    
    return result


# ==================== MODULO 3: TEST DE ENDPOINTS ====================
def find_server_port():
    for port in range(DEFAULT_PORT, DEFAULT_PORT + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    return port
        except:
            continue
    return None


def test_endpoints(port=None):
    print_header("MODULO 3: Test de Endpoints")
    
    result = {
        "server_running": False,
        "port": None,
        "endpoints": {}
    }
    
    # 1. Buscar servidor corriendo
    if port is None:
        port = find_server_port()
    
    if port:
        print_status("SERVER", True, f"Servidor detectado en puerto {port}")
        result["server_running"] = True
        result["port"] = port
    else:
        print_status("SERVER", False, f"No hay servidor corriendo en puertos {DEFAULT_PORT}-{DEFAULT_PORT+9}")
        print(f"    Inicia el servidor con: python dashboard_server.py")
        return result
    
    # 2. Test de endpoints
    endpoints_to_test = [
        ("/api/config", "CONFIG"),
        ("/api/token", "TOKEN"),
        ("/api/stats", "STATS"),
        ("/api/channels", "CHANNELS"),
    ]
    
    for path, name in endpoints_to_test:
        url = f"http://127.0.0.1:{port}{path}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                print_status(f"ENDPOINT-{name}", True, f"Status: {response.status}")
                result["endpoints"][name] = {"status": response.status, "data": data}
        except urllib.error.HTTPError as e:
            print_status(f"ENDPOINT-{name}", False, f"HTTP {e.code}")
            result["endpoints"][name] = {"status": e.code, "error": str(e)}
        except Exception as e:
            print_status(f"ENDPOINT-{name}", False, str(e))
            result["endpoints"][name] = {"error": str(e)}
    
    return result


# ==================== MODULO 4: AUTO-REPAIR ====================
def auto_repair():
    print_header("MODULO 4: Auto-repair")
    
    repaired = []
    
    # 1. Verificar y crear configuracion de dashboard
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        config = {}
    
    needs_save = False
    
    # Asegurar seccion dashboard
    if "dashboard" not in config:
        config["dashboard"] = {
            "port": DEFAULT_PORT,
            "host": "127.0.0.1",
            "db_path": "data/channel_monitor.db"
        }
        print(f"  -> Agregada seccion 'dashboard'")
        needs_save = True
    
    # Generar y guardar token
    if "dashboard_token" not in config:
        config["dashboard_token"] = secrets.token_hex(16)
        print(f"  -> Generado nuevo token")
        needs_save = True
    
    # Habilitar auth y SSE por defecto
    if "enable_auth" not in config:
        config["enable_auth"] = True
        print(f"  -> enable_auth = True")
        needs_save = True
    
    if "enable_sse" not in config:
        config["enable_sse"] = True
        print(f"  -> enable_sse = True")
        needs_save = True
    
    # Guardar configuracion
    if needs_save:
        try:
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"  [OK] Configuracion guardada en settings.json")
            repaired.append("configuracion")
        except Exception as e:
            print(f"  [FALLO] Error guardando configuracion: {e}")
    else:
        print(f"  [OK] Configuracion ya esta correcta")
    
    if repaired:
        print(f"\nReparaciones aplicadas: {', '.join(repaired)}")
    else:
        print(f"\nNo se necesitaron reparaciones")
    
    return repaired


# ==================== DIAGNOSTICO COMPLETO ====================
def run_full_diagnostic(fix=False, test_endpoints_flag=False):
    print(f"\n================================================================================")
    print(f"           DIAGNOSTICO DEL DASHBOARD WEB - KDP Master")
    print(f"                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"================================================================================\n")
    
    # Ejecutar modulos
    db_result = check_database()
    config_result = check_configuration()
    
    endpoints_result = None
    if test_endpoints_flag:
        endpoints_result = test_endpoints()
    
    # Auto-repair si se solicita
    repaired = []
    if fix:
        repaired = auto_repair()
    
    # Resumen
    print_header("RESUMEN DE DIAGNOSTICO")
    
    all_ok = True
    
    # DB
    if not db_result["has_data"]:
        print(f"  [FALLO] Base de datos vacia o sin datos")
        all_ok = False
    else:
        print(f"  [OK] Base de datos: {db_result['channels']} canales, {db_result['videos']} videos")
    
    # Config - Token
    if not config_result["has_token"]:
        print(f"  [FALLO] Falta token de autenticacion")
        all_ok = False
    else:
        print(f"  [OK] Token configurado")
    
    if config_result["enable_auth"] is None:
        print(f"  [WARNING] enable_auth no configurado (usara default)")
    
    # Endpoints
    if endpoints_result and not endpoints_result["server_running"]:
        print(f"  [FALLO] Servidor no esta corriendo")
        all_ok = False
    elif endpoints_result and endpoints_result["server_running"]:
        print(f"  [OK] Servidor corriendo en puerto {endpoints_result['port']}")
    
    # Resultado final
    print()
    if all_ok:
        print(f"================================================================================")
        print(f"  [OK] DIAGNOSTICO PASADO - Dashboard deberia funcionar")
        print(f"================================================================================")
        return 0
    else:
        print(f"================================================================================")
        print(f"  [FALLO] DIAGNOSTICO FALLIDO - Ejecuta con --fix para reparar")
        print(f"================================================================================")
        return 1


# ==================== MAIN ====================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Diagnostico del Dashboard Web - KDP Master",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python diagnose_dashboard.py              # Solo diagnostico
  python diagnose_dashboard.py --fix         # Diagnosticar y reparar
  python diagnose_dashboard.py --test        # Incluir test de endpoints
  python diagnose_dashboard.py --fix --test  # Full diagnostico + repair + test
        """
    )
    parser.add_argument("--fix", action="store_true", help="Aplicar reparaciones automaticamente")
    parser.add_argument("--test", action="store_true", help="Testear endpoints del servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Puerto del servidor para test")
    
    args = parser.parse_args()
    
    sys.exit(run_full_diagnostic(fix=args.fix, test_endpoints_flag=args.test))