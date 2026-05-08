import sys
import time
import subprocess
import os

# Intentar importar watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ Error: Necesitas instalar 'watchdog' para usar el modo desarrollo.")
    print("   Ejecuta: pip install watchdog")
    sys.exit(1)

# Intentar importar sistema de lock
try:
    from app.lock_manager import ApplicationLock
    LOCK_AVAILABLE = True
except ImportError:
    try:
        from lock_manager import ApplicationLock
        LOCK_AVAILABLE = True
    except ImportError:
        ApplicationLock = None
        LOCK_AVAILABLE = False

class DevRunner(FileSystemEventHandler):
    def __init__(self, target_script):
        self.target_script = target_script
        self.process = None
        self.last_restart = 0
        self.restart()

    def restart(self):
        # Detener proceso anterior si existe
        if self.process:
            print("\n🔄 Cambio detectado. Reiniciando aplicación...")
            try:
                self.process.terminate()
                # Darle un momento para cerrar
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("Nota: El proceso anterior ya estaba cerrado")

        # Verificar y limpiar locks huérfanos si es necesario
        if LOCK_AVAILABLE:
            lock_check = ApplicationLock(lock_name="app.lock", base_dir=".")
            if os.path.exists(lock_check.lock_path):
                if lock_check.is_orphaned_lock():
                    print("🧹 Lock huérfano detectado y eliminado")
                    lock_check.force_cleanup()

        print(f"🚀 Ejecutando {self.target_script}...")
        # Ejecutar en un nuevo proceso
        self.process = subprocess.Popen([sys.executable, self.target_script])

    def on_modified(self, event):
        # Observar solo archivos Python
        if event.src_path.endswith(".py"):
            # Evitar reinicios si modificamos este mismo script
            if os.path.basename(event.src_path) == os.path.basename(__file__):
                return
                
            # Debounce: Evitar múltiples reinicios si el editor guarda varias veces rápido
            if time.time() - self.last_restart < 1.5:
                return
            
            self.last_restart = time.time()
            print(f"📝 Cambios en: {os.path.basename(event.src_path)}")
            self.restart()

if __name__ == "__main__":
    script_to_run = "gui_app.py"
    
    if not os.path.exists(script_to_run):
        print(f"❌ Error crítico: No se encontró el punto de entrada '{script_to_run}'")
        sys.exit(1)

    print("==================================================")
    print("💎 KDP Master Suite - DEV HOT-RELOAD MODE")
    print("==================================================")
    
    event_handler = DevRunner(script_to_run)
    observer = Observer()
    
    # Observar recursivamente todos los archivos en la carpeta actual
    observer.schedule(event_handler, path=".", recursive=True)
    observer.start()

    print(f"👀 Observando cambios en tiempo real...")
    print(f"   (Presiona Ctrl+C para finalizar la sesión Dev)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo monitor de desarrollo...")
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()
    print("✨ Sesión de desarrollo finalizada.")
