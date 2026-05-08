# -*- coding: utf-8 -*-
"""Script para limpiar procesos huérfanos automáticamente."""
import subprocess
import sys
import socket
import glob

def is_port_open(port):
    """Verifica si un puerto está en uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def main():
    print("[INFO] Limpiando carpetas temporales de PyInstaller...")
    temp_dir = os.environ.get("TEMP") or os.environ.get("TMP")
    if temp_dir and os.path.exists(temp_dir):
        pyinstaller_temp_dirs = glob.glob(os.path.join(temp_dir, "_MEI*"))
        if pyinstaller_temp_dirs:
            for folder in pyinstaller_temp_dirs:
                try:
                    print(f"[INFO] Eliminando: {folder}")
                    shutil.rmtree(folder)
                except Exception as e:
                    print(f"[WARN] No se pudo eliminar {folder}: {e}")
        else:
            print("[INFO] No se encontraron carpetas temporales de PyInstaller.")
    else:
        print("[WARN] No se pudo determinar el directorio TEMP.")
    print("[INFO] Limpiando puertos del dashboard...")
    
    if sys.platform == "win32":
        for port in [8000, 8001, 8002, 8003, 8004]:
            if is_port_open(port):
                print(f"[INFO] Puerto {port} en uso, buscando proceso...")
                try:
                    result = subprocess.run(
                        f'netstat -ano | findstr :{port}',
                        shell=True, capture_output=True, text=True
                    )
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[-1]
                                try:
                                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                                    print(f"[OK] Proceso {pid} en puerto {port} terminado")
                                except:
                                    pass
                except:
                    pass
        print("[OK] Limpieza completada")
    else:
        print("[INFO] Solo disponible para Windows")

if __name__ == "__main__":
    main()