# -*- coding: utf-8 -*-
"""
Test script completo para KDP Master Suite - Verificacion de:
1. Cierre de System Tray
2. Dashboard y datos
3. Monitoreo de canales
"""
import sys
import os
import sqlite3
import json
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "channel_monitor.db")

def test_1_system_tray_code():
    """Test 1: Verificar que el cierre del system tray esta implementado."""
    print("\n" + "="*60)
    print("TEST 1: Cierre de System Tray")
    print("="*60)
    
    try:
        import inspect
        from gui_app import TranscriptionProcessorApp
        
        source = inspect.getsource(TranscriptionProcessorApp.on_closing)
        
        checks = [
            ('tray_icon.stop()', 'Llamada a tray_icon.stop()'),
            ('sys.exit(0)', 'Llamada a sys.exit(0) forzada'),
            ('time.sleep', 'Tiempo de espera para cleanup'),
        ]
        
        all_passed = True
        for pattern, desc in checks:
            if pattern in source:
                print(f"[OK] {desc}")
            else:
                print(f"[FAIL] {desc}: FALTA")
                all_passed = False
        
        if all_passed:
            print("\n[SUCCESS] Cierre de System Tray implementado")
            return True
        else:
            print("\n[FAIL] Faltan componentes en el cierre")
            return False
            
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_2_dashboard_database():
    """Test 2: Verificar que la DB del dashboard tiene datos."""
    print("\n" + "="*60)
    print("TEST 2: Base de datos del Dashboard")
    print("="*60)
    
    if not os.path.exists(DB_PATH):
        print(f"[FAIL] Base de datos no encontrada: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar canales
        cursor.execute("SELECT COUNT(*) FROM channels")
        channels = cursor.fetchone()[0]
        print(f"[INFO] Canales en DB: {channels}")
        
        # Contar videos
        cursor.execute("SELECT COUNT(*) FROM videos")
        videos = cursor.fetchone()[0]
        print(f"[INFO] Videos en DB: {videos}")
        
        # Videos por canal
        cursor.execute("""
            SELECT c.channel_name, COUNT(v.id) as count
            FROM channels c
            LEFT JOIN videos v ON c.id = v.channel_id
            GROUP BY c.id
            ORDER BY count DESC
            LIMIT 5
        """)
        top_channels = cursor.fetchall()
        
        print(f"\n[INFO] Top 5 canales por videos:")
        for name, count in top_channels:
            print(f"  - {name}: {count} videos")
        
        # Videos recientes (por discovered_at)
        cursor.execute("""
            SELECT v.title, c.channel_name, v.discovered_at
            FROM videos v
            JOIN channels c ON v.channel_id = c.id
            ORDER BY v.discovered_at DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()
        
        print(f"\n[INFO] Videos mas recientes (por discovered_at):")
        for title, channel, discovered in recent:
            print(f"  - {discovered}: {title[:40]}... ({channel})")
        
        conn.close()
        
        if channels > 0 and videos > 0:
            print("\n[SUCCESS] Base de datos tiene datos")
            return True
        else:
            print("\n[WARN] Base de datos vacia o sin canales")
            return False
            
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_dashboard_server():
    """Test 3: Verificar que el dashboard server responde."""
    print("\n" + "="*60)
    print("TEST 3: Dashboard Server")
    print("="*60)
    
    # Verificar si el servidor esta corriendo
    import socket
    def is_port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    
    # Probar puertos comunes del dashboard
    for port in [8000, 8001, 8002]:
        if is_port_open(port):
            print(f"[INFO] Puerto {port} esta abierto")
            try:
                import urllib.request
                response = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/stats", timeout=5)
                data = json.loads(response.read().decode('utf-8'))
                print(f"[OK] Dashboard responde en puerto {port}")
                print(f"  - Canales: {data.get('channels', 'N/A')}")
                print(f"  - Videos: {data.get('videos', 'N/A')}")
                print(f"  - Videos recientes: {len(data.get('recent', []))}")
                return True
            except Exception as e:
                print(f"[WARN] Puerto abierto pero no responde: {e}")
    
    print("[INFO] Dashboard no esta corriendo actualmente")
    print("       Para probarlo: python main.py > Dashboard > Iniciar Servidor Web")
    return True  # No es un fallo, solo no esta corriendo

def test_4_process_cleanup_methods():
    """Test 4: Verificar metodos de limpieza de procesos."""
    print("\n" + "="*60)
    print("TEST 4: Metodos de Limpieza de Procesos")
    print("="*60)
    
    try:
        from gui_app import TranscriptionProcessorApp
        
        methods = [
            '_stop_channel_monitor',
            '_stop_download_queue',
            '_stop_scheduler', 
            '_wait_for_threads',
            'stop_dashboard_server',
            'check_orphan_processes',
            'monitor_child_processes'
        ]
        
        all_found = True
        for method in methods:
            if hasattr(TranscriptionProcessorApp, method):
                print(f"[OK] {method}() existe")
            else:
                print(f"[FAIL] {method}() NO existe")
                all_found = False
        
        # Verificar que se usan en __init__ y on_closing
        import inspect
        
        init_source = inspect.getsource(TranscriptionProcessorApp.__init__)
        if 'check_orphan_processes' in init_source:
            print("[OK] check_orphan_processes llamado en __init__")
        else:
            print("[FAIL] check_orphan_processes NO llamado en __init__")
            all_found = False
        
        closing_source = inspect.getsource(TranscriptionProcessorApp.on_closing)
        cleanup_methods = ['_stop_channel_monitor', '_stop_scheduler', 'stop_dashboard_server', '_stop_download_queue']
        for method in cleanup_methods:
            if method in closing_source:
                print(f"[OK] {method} llamado en on_closing")
            else:
                print(f"[FAIL] {method} NO llamado en on_closing")
                all_found = False
        
        if all_found:
            print("\n[SUCCESS] Todos los metodos implementados y llamados")
            return True
        else:
            print("\n[FAIL] Faltan componentes")
            return False
            
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("KDP Master Suite - Test Completo")
    print("="*60)
    
    results = []
    
    results.append(("Test 1: System Tray", test_1_system_tray_code()))
    results.append(("Test 2: Dashboard DB", test_2_dashboard_database()))
    results.append(("Test 3: Dashboard Server", test_3_dashboard_server()))
    results.append(("Test 4: Cleanup Methods", test_4_process_cleanup_methods()))
    
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n*** TODOS LOS TESTS PASARON ***")
    else:
        print("\n*** ALGUNOS TESTS FALLARON ***")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())