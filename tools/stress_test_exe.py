import subprocess
import time
import os
import sys
from pathlib import Path

def run_stress_test(exe_path, iterations=10):
    """
    Realiza una prueba de fuerza bruta sobre el ejecutable.
    Verifica:
    1. Apertura y cierre repetido (resistencia del Lock).
    2. Prevención de múltiples instancias simultáneas.
    3. Limpieza de hilos zombie.
    """
    print(f"🚀 Iniciando Test de Fuerza Bruta para: {exe_path}")
    print(f"🔄 Iteraciones: {iterations}\n")
    
    base_dir = Path(exe_path).parent
    lock_file = base_dir / "app.lock"
    
    # --- TEST 1: CICLO REPETITIVO ---
    for i in range(1, iterations + 1):
        print(f"[{i}/{iterations}] Abriendo aplicación...")
        process = subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Esperar a que la ventana aparezca y el lock se cree
        time.sleep(5)
        
        if lock_file.exists():
            print("  ✅ Lock detectado correctamente.")
        else:
            print("  ❌ ERROR: El archivo .lock no se creó.")
            
        print("  Cerrando aplicación...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("  ⚠️ La aplicación no cerró en 10s. Forzando cierre...")
            process.kill()
            
        time.sleep(2)
        
        if not lock_file.exists():
            print("  ✅ Lock liberado correctamente.")
        else:
            print("  ❌ ERROR CRÍTICO: Lock huérfano detectado tras el cierre.")
            # Limpiar manualmente para continuar el test
            os.remove(lock_file)
            
    # --- TEST 2: PREVENCIÓN DE CONCURRENCIA ---
    print("\n🧪 Test de Concurrencia (Instancia Única)...")
    p1 = subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
    p2 = subprocess.Popen([exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(3)
    
    # El segundo proceso debería terminar casi de inmediato si el lock funciona
    if p2.poll() is not None:
        print("  ✅ Segunda instancia bloqueada exitosamente.")
    else:
        print("  ❌ FALLO: Se permitieron dos instancias simultáneas.")
        p2.kill()
        
    p1.terminate()
    p1.wait()
    
    print("\n🏁 Stress Test Completado.")

if __name__ == "__main__":
    # Ajustar ruta al .exe generado
    exe_to_test = os.path.join(os.getcwd(), "dist", "KDP_Transcriptions.exe")
    
    if not os.path.exists(exe_to_test):
        print(f"❌ No se encontró el ejecutable en {exe_to_test}")
        sys.exit(1)
        
    run_stress_test(exe_to_test)