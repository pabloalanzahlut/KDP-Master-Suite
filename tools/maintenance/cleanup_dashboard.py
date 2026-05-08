# -*- coding: utf-8 -*-
"""Script para limpiar procesos huérfanos del dashboard y puertos."""
import subprocess
import sys
import os

def kill_dashboard_processes():
    """Elimina procesos relacionados con el dashboard."""
    print("[INFO] Buscando procesos del dashboard...")
    
    # Buscar procesos python relacionados con dashboard
    if sys.platform == "win32":
        try:
            # Buscar procesos python.exe
            result = subprocess.run(['tasklist'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            pids_to_kill = []
            for line in result.stdout.split('\n'):
                if 'python.exe' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            pids_to_kill.append(pid)
                        except:
                            pass
            
            if pids_to_kill:
                print(f"[INFO] Encontrados {len(pids_to_kill)} procesos python.exe")
                print(f"[INFO] PIDs: {pids_to_kill}")
                
                if input("[CONFIRM] ¿Desea terminarlos? (s/n): ").lower() == 's':
                    for pid in pids_to_kill:
                        try:
                            subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
                            print(f"[OK] Proceso {pid} terminado")
                        except:
                            pass
            else:
                print("[OK] No hay procesos python.exe activos")
                
        except Exception as e:
            print(f"[ERROR] {e}")

def free_dashboard_ports():
    """Libera los puertos del dashboard."""
    print("\n[INFO] Verificando puertos del dashboard...")
    
    if sys.platform == "win32":
        for port in [8000, 8001, 8002, 8003, 8004]:
            try:
                result = subprocess.run(
                    f'netstat -ano | findstr :{port}',
                    shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore'
                )
                if result.stdout:
                    print(f"[WARN] Puerto {port} en uso:")
                    for line in result.stdout.split('\n'):
                        print(f"  {line}")
                    
                    # Extraer PID
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line:
                            parts = line.split()
                            if len(parts) > 4:
                                try:
                                    pid = int(parts[-1])
                                    print(f"[INFO] Intentando liberar puerto {port} (PID: {pid})...")
                                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
                                    print(f"[OK] Proceso {pid} terminado")
                                except:
                                    pass
                else:
                    print(f"[OK] Puerto {port} libre")
            except Exception as e:
                print(f"[WARN] Error verificando puerto {port}: {e}")

def main():
    print("="*60)
    print("KDP Master - Limpiador de Procesos y Puertos")
    print("="*60)
    
    free_dashboard_ports()
    kill_dashboard_processes()
    
    print("\n[OK] Limpieza completada")

if __name__ == "__main__":
    main()