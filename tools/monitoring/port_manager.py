"""
KDP Master - Puerto Automático para Dashboard
==============================================
Script para detectar y liberar puertos del dashboard.
Ejecutar antes de iniciar la aplicación para evitar conflictos.
"""

import socket
import os
import sys
import json
import subprocess
from pathlib import Path

# Fix para Windows: forzar UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_DIR = Path(__file__).parent
SETTINGS_PATH = BASE_DIR / "settings.json"
DEFAULT_START_PORT = 7000
DEFAULT_END_PORT = 9999


def is_port_in_use(port, host="127.0.0.1"):
    """Verifica si un puerto está en uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def find_available_port(start_port=DEFAULT_START_PORT, end_port=DEFAULT_END_PORT):
    """Encuentra el primer puerto disponible en el rango."""
    for port in range(start_port, end_port):
        if not is_port_in_use(port):
            return port
    return None


def get_process_on_port(port):
    """Obtiene el proceso que está usando un puerto (Windows)."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        proc = subprocess.run(
                            ["tasklist", "/FI", f"PID eq {pid}"],
                            capture_output=True,
                            text=True,
                            encoding='utf-8'
                        )
                        for proc_line in proc.stdout.split("\n"):
                            if pid in proc_line and "PID" not in proc_line:
                                return pid, proc_line.strip()
                    except:
                        pass
                    return pid, "Proceso desconocido"
        return None, None
    except Exception as e:
        return None, f"Error: {e}"


def kill_process_on_port(port):
    """ Mata el proceso que está usando el puerto especificado."""
    pid, proc_info = get_process_on_port(port)
    if pid:
        try:
            subprocess.run(["taskkill", "/F", "/PID", pid], check=True)
            return True, f"Proceso {pid} ({proc_info}) terminado"
        except subprocess.CalledProcessError:
            return False, f"No se pudo terminar el proceso {pid}"
    return False, "No se encontró proceso en ese puerto"


def scan_ports(start=DEFAULT_START_PORT, end=DEFAULT_END_PORT):
    """Escanea el rango de puertos y muestra el estado."""
    print(f"\n[SCAN] Escaneando puertos {start}-{end}...\n")
    print(f"{'Puerto':<10} {'Estado':<15} {'Proceso':<40}")
    print("-" * 70)
    
    occupied = []
    available = []
    
    for port in range(start, end):
        if is_port_in_use(port):
            pid, proc = get_process_on_port(port)
            proc_display = proc[:38] if proc else "Desconocido"
            print(f"{port:<10} {'❌ OCUPADO':<15} {proc_display}")
            occupied.append((port, pid, proc))
        else:
            print(f"{port:<10} {'✅ LIBRE':<15} -")
            available.append(port)
    
    return occupied, available


def auto_configureDashboard():
    """Configura automáticamente el dashboard con el primer puerto libre."""
    print("🔧 Configurando dashboard automáticamente...\n")
    
    port = find_available_port()
    
    if port is None:
        print("❌ ERROR: No hay puertos disponibles en el rango 8000-9000")
        return False
    
    print(f"✅ Puerto disponible encontrado: {port}")
    
    # Cargar settings actuales
    settings = {}
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except:
            pass
    
    # Actualizar puerto
    if 'dashboard' not in settings:
        settings['dashboard'] = {}
    settings['dashboard']['port'] = port
    
    # Guardar
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        print(f"✅ Puerto configurado en settings.json: {port}")
        return True
    except Exception as e:
        print(f"❌ Error guardando settings: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestor de puertos del Dashboard KDP")
    parser.add_argument("--scan", action="store_true", help="Escanear puertos ocupados")
    parser.add_argument("--find", action="store_true", help="Encontrar primer puerto libre")
    parser.add_argument("--configure", action="store_true", help="Configurar dashboard con puerto libre")
    parser.add_argument("--kill", type=int, metavar="PORT", help="Matar proceso en puerto específico")
    parser.add_argument("--auto", action="store_true", help="Modo automático: scan + configure")
    
    args = parser.parse_args()
    
    if args.scan:
        scan_ports()
    elif args.find:
        port = find_available_port()
        if port:
            print(f"✅ Primer puerto libre: {port}")
        else:
            print("❌ No hay puertos libres")
    elif args.configure:
        auto_configureDashboard()
    elif args.kill:
        success, msg = kill_process_on_port(args.kill)
        print(f"{'✅' if success else '❌'} {msg}")
    elif args.auto:
        print("🚀 Modo automático: Escaneando y configurando...\n")
        occupied, available = scan_ports()
        
        if available:
            print(f"\n📋 Resumen: {len(available)} puertos libres, {len(occupied)} ocupados")
            auto_configureDashboard()
        else:
            print("\n⚠️ Todos los puertos ocupados. Opciones:")
            print("   1. Ejecutar con --kill <puerto> para liberar un puerto")
            print("   2. Cerrar otras aplicaciones que usen esos puertos")
    else:
        # Por defecto, mostrar menú
        print("=" * 60)
        print("🔌 GESTOR DE PUERTOS - KDP MASTER DASHBOARD")
        print("=" * 60)
        
        port = find_available_port()
        if port:
            print(f"\n✅ Puerto recomendado para dashboard: {port}")
        else:
            print("\n❌ No hay puertos disponibles")
        
        print(f"\nUsa: python {os.path.basename(__file__)} --scan")
        print("     python {os.path.basename(__file__)} --configure")
        print("     python {os.path.basename(__file__)} --auto")
        print("     python {os.path.basename(__file__)} --kill 8000")


if __name__ == "__main__":
    main()
