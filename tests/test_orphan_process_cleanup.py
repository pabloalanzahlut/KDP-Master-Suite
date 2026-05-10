# -*- coding: utf-8 -*-
"""
Test Script: Verifica la limpieza de procesos huérfanos al cerrar la app
EJECUTAR DESDE LA CARPETA RAÍZ DEL PROYECTO: python test_orphan_process_cleanup.py
"""
import sys
import os
import subprocess
import time
import socket

# Configurar UTF-8 para evitar errores de codificación en Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_port_in_use(port):
    """Verifica si un puerto está en uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_by_name(name):
    """Busca procesos por nombre (Windows)."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {name}'],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        return name in result.stdout
    except:
        return False

def test_1_dashboard_cleanup():
    """Test 1: Verificar que stop_dashboard_server() funciona correctamente."""
    print("\n" + "="*60)
    print("TEST 1: Limpieza del proceso dashboard")
    print("="*60)
    
    # Verificar que el método existe en gui_app
    try:
        from gui_app import TranscriptionProcessorApp
        print("[OK] gui_app importado correctamente")
        
        # Verificar que stop_dashboard_server existe
        if hasattr(TranscriptionProcessorApp, 'stop_dashboard_server'):
            print("[OK] Metodo stop_dashboard_server() existe")
        else:
            print("[FAIL] ERROR: Metodo stop_dashboard_server() NO existe")
            return False
        
        # Verificar que on_closing llama a stop_dashboard_server
        import inspect
        source = inspect.getsource(TranscriptionProcessorApp.on_closing)
        if 'stop_dashboard_server' in source:
            print("[OK] on_closing() llama a stop_dashboard_server()")
        else:
            print("[FAIL] ERROR: on_closing() NO llama a stop_dashboard_server()")
            return False
        
        # Verificar queue_running = False en on_closing (directo o via metodo)
        if 'queue_running' in source and '= False' in source:
            print("[OK] on_closing() marca queue_running = False (directo)")
        elif '_stop_download_queue' in source:
            print("[OK] on_closing() llama a _stop_download_queue() que marca queue_running = False")
        else:
            print("[FAIL] ERROR: on_closing() NO marca queue_running = False")
        
        print("\n[SUCCESS] TEST 1 PASADO: Limpieza de dashboard implementada correctamente")
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")

def test_2_stop_dashboard_code():
    """Test 2: Verificar el código de stop_dashboard_server()."""
    print("\n" + "="*60)
    print("TEST 2: Codigo de stop_dashboard_server()")
    print("="*60)
    
    try:
        import inspect
        from gui_app import TranscriptionProcessorApp
        
        source = inspect.getsource(TranscriptionProcessorApp.stop_dashboard_server)
        
        checks = [
            ('terminate()', 'Llamada a terminate()'),
            ('wait(timeout', 'Timeout en wait()'),
            ('TimeoutExpired', 'Manejo de TimeoutExpired'),
            ('kill()', 'Fallback a kill()'),
            ('taskkill', 'Nuclear option con taskkill'),
        ]
        
        all_passed = True
        for pattern, desc in checks:
            if pattern in source:
                print(f"[OK] {desc}: OK")
            else:
                print(f"[FAIL] {desc}: FALTA")
                all_passed = False
        
        if all_passed:
            print("\n[SUCCESS] TEST 2 PASADO: Codigo robusto de limpieza implementado")
        else:
            print("\n[FAIL] TEST 2 FALLIDO: Faltan componentes de limpieza")
            
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")

def test_4_new_cleanup_methods():
    """Test 4: Verificar nuevos metodos de limpieza."""
    print("\n" + "="*60)
    print("TEST 4: Nuevos metodos de limpieza")
    print("="*60)
    
    try:
        from gui_app import TranscriptionProcessorApp
        
        methods = [
            '_stop_channel_monitor',
            '_stop_download_queue', 
            '_stop_scheduler',
            '_wait_for_threads',
            'check_orphan_processes',
            'monitor_child_processes'
        ]
        
        all_found = True
        for method in methods:
            if hasattr(TranscriptionProcessorApp, method):
                print(f"[OK] Metodo {method}() existe")
            else:
                print(f"[FAIL] Metodo {method}() NO existe")
                all_found = False
        
        # Verificar que se llaman en on_closing
        import inspect
        source = inspect.getsource(TranscriptionProcessorApp.on_closing)
        
        if '_stop_channel_monitor' in source:
            print("[OK] on_closing() llama a _stop_channel_monitor()")
        else:
            print("[FAIL] on_closing() NO llama a _stop_channel_monitor()")
            all_found = False
            
        if 'check_orphan_processes' in source:
            print("[FAIL] ADVERTENCIA: check_orphan_processes debe estar en __init__, no en on_closing")
        
        # Verificar que se llaman en __init__
        init_source = inspect.getsource(TranscriptionProcessorApp.__init__)
        if 'check_orphan_processes' in init_source:
            print("[OK] __init__() llama a check_orphan_processes()")
        else:
            print("[FAIL] __init__() NO llama a check_orphan_processes()")
            all_found = False
            
        if 'monitor_child_processes' in init_source:
            print("[OK] __init__() llama a monitor_child_processes()")
        else:
            print("[FAIL] __init__() NO llama a monitor_child_processes()")
            all_found = False
        
        if all_found:
            print("\n[SUCCESS] TEST 4 PASADO: Todos los metodos implementados y llamados")
        else:
            print("\n[FAIL] TEST 4 FALLIDO: Faltan metodos o llamadas")
            
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")

def test_3_manual_instructions():
    """Test 3: Instrucciones para prueba manual."""
    print("\n" + "="*60)
    print("TEST 3: Instrucciones de prueba manual")
    print("="*60)
    
    print("""
Para probar manualmente el fix de procesos huérfanos:

ESCENARIO 1: Dashboard activo
------------------------------
1. Ejecutar: python main.py
2. Ir a la pestaña Dashboard
3. Hacer clic en "Iniciar Servidor Web"
4. Verificar que el servidor está corriendo (http://localhost:8000)
5. Cerrar la aplicación (botón X o File > Exit)
6. Abrir Task Manager (Ctrl+Shift+Esc)
7. Verificar que NO hay procesos "python.exe" adicionales
8. Verificar que el puerto 8000 está libre:
   Abrir cmd y ejecutar: netstat -ano | findstr :8000

ESCENARIO 2: Descarga activa
----------------------------
1. Ejecutar: python main.py
2. Añadir URLs a la cola de descargas
3. Iniciar la descarga (Start Queue)
4. Mientras está descargando, cerrar la aplicación
5. Verificar que queue_running se marca como False
6. Verificar que NO hay procesos yt-dlp huérfanos

ESCENARIO 3: Dashboard + Descarga simultáneas
---------------------------------------------
1. Ejecutar: python main.py
2. Iniciar el servidor dashboard
3. Iniciar una descarga
4. Cerrar la aplicación
5. Verificar que ambos procesos se limpian correctamente

RESULTADO ESPERADO:
- Ningún proceso python.exe residual
- Puerto 8000 libre
- Sin mensajes de error al reiniciar la app
""")

def main():
    print("="*60)
    print("KDP Master Suite - Test de Limpieza de Procesos Huérfanos")
    print("="*60)
    
    results = []
    
    # Test 1: Verificar implementación
    results.append(("Test 1: Limpieza dashboard", test_1_dashboard_cleanup()))
    
    # Test 2: Verificar código
    results.append(("Test 2: Código robusto", test_2_stop_dashboard_code()))
    
    # Test 3: Nuevos métodos de limpieza
    results.append(("Test 3: Metodos nuevos", test_4_new_cleanup_methods()))
    
    # Test 4: Instrucciones
    results.append(("Test 4: Manual", test_3_manual_instructions()))
    
    print("\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n*** TODOS LOS TESTS AUTOMATICOS PASARON ***")
        print("Ahora ejecuta las pruebas manuales descritas en Test 4")
    else:
        print("\n*** ALGUNOS TESTS FALLARON - Revisa los errores above ***")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())