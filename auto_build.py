#!/usr/bin/env python3
"""
KDP Master - Auto Build
=========================
Build automático post-guardado.
- Vigila cambios en gui_app.py, build_exe.py, app/**/*.py
- Espera 3 segundos debounce después del último guardado
- Ejecuta build_incremental automáticamente
- Notifica al finalizar

Uso:
    python auto_build.py              # Iniciar modo auto-build
    python auto_build.py --once        # Build único sin watcher
    python auto_build.py --stop       # Detener watcher activo
"""
import sys
import os
import time
import subprocess
import signal
import threading
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
WATCH_FILE = PROJECT_ROOT / ".auto_build.lock"

# Archivos a vigilia (patterns)
WATCH_PATTERNS = [
    "gui_app.py",
    "build_exe.py",
    "app/modules/monitoring/run_build.py",
]

# Extensiones a vigilia
WATCH_EXTENSIONS = [".py"]

# Debounce: tiempo de espera después del último cambio
DEBOUNCE_SECONDS = 3


class AutoBuildManager:
    def __init__(self):
        self.last_trigger = 0
        self.build_in_progress = False
        self.running = True
        self.lock_file = WATCH_FILE
        self._write_lock()
    
    def _write_lock(self):
        """Escribe archivo de lock"""
        with open(self.lock_file, 'w') as f:
            f.write(f"{os.getpid()}\n{datetime.now().isoformat()}")
    
    def _remove_lock(self):
        """Elimina archivo de lock"""
        if self.lock_file.exists():
            self.lock_file.unlink()
    
    def _should_trigger(self, file_path):
        """Determina si debe ejecutar build"""
        if self.build_in_progress:
            return False
        
        basename = os.path.basename(file_path)
        
        # Ignorar archivos del watcher
        if basename in ("auto_build.py", "watcher.py"):
            return False
        
        # Verificar patterns
        if any(pattern in file_path for pattern in WATCH_PATTERNS):
            return True
        
        # Verificar extensiones
        if any(file_path.endswith(ext) for ext in WATCH_EXTENSIONS):
            # Solo app/ y modules/
            if "/app/" in file_path or "\\app\\" in file_path or "/modules/" in file_path or "\\modules\\" in file_path:
                return True
        
        return False
    
    def _run_build(self):
        """Ejecuta build incremental"""
        if self.build_in_progress:
            return
        
        print(f"\n{'='*60}")
        print(f" AUTO-BUILD: Iniciando build incremental...")
        print(f"{'='*60}")
        
        self.build_in_progress = True
        
        try:
            result = subprocess.run(
                [sys.executable, "build_exe.py", "--incremental"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n✅ BUILD EXITOSO")
                print(f"   Output: {result.stdout[-500:]}")
                self._notify_success()
            else:
                print(f"\n❌ BUILD FALLÓ")
                print(f"   Error: {result.stderr[-300:]}")
                self._notify_error(result.stderr[-300:])
        
        except Exception as e:
            print(f"\n❌ EXCEPCIÓN: {e}")
            self._notify_error(str(e))
        
        finally:
            self.build_in_progress = False
            self.last_trigger = 0
    
    def _notify_success(self):
        """Notifica build exitoso (sonido)"""
        try:
            import winsound
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            print("\a")  # Bell
    
    def _notify_error(self, error_msg):
        """Notifica build fallido"""
        try:
            import winsound
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            print("\a")
        print(f"🔔 Revisa los errores en: build_info.json")
    
    def trigger_if_needed(self, file_path):
        """Dispara build si es necesario (con debounce)"""
        if not self._should_trigger(file_path):
            return
        
        now = time.time()
        
        # Resetear si hay nuevo cambio después del debounce
        if self.last_trigger > 0 and now - self.last_trigger < DEBOUNCE_SECONDS:
            self.last_trigger = now  # extender debounce
            print(f"⏳ Debounce extendido para: {os.path.basename(file_path)}")
            return
        
        # Nuevo trigger
        self.last_trigger = now
        
        # Ejecutar después del debounce
        def delayed_build():
            wait_time = DEBOUNCE_SECONDS
            for i in range(wait_time, 0, -1):
                if not self.running:
                    return
                time.sleep(1)
                if i > 1:
                    print(f"⏳ Build en {i}...")
            
            if self.running:
                self._run_build()
        
        thread = threading.Thread(target=delayed_build, daemon=True)
        thread.start()
    
    def stop(self):
        """Detiene el watcher"""
        self.running = False
        self._remove_lock()
        print("🛑 Auto-build detenido")


def main():
    parser = argparse.ArgumentParser(description='KDP Auto Build')
    parser.add_argument('--once', action='store_true', help='Build único sin watcher')
    parser.add_argument('--stop', action='store_true', help='Detener watcher activo')
    args = parser.parse_args()
    
    # --stop: Detener watcher anterior
    if args.stop:
        if WATCH_FILE.exists():
            with open(WATCH_FILE, 'r') as f:
                pid = int(f.readline().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"🛑 Watcher {pid} detenido")
            except ProcessLookupError:
                print("⚠️ Proceso no encontrado")
            WATCH_FILE.unlink()
            return
        else:
            print("ℹ️ No hay watcher activo")
            return
    
    # --once: Build único
    if args.once:
        print("🏗️ Ejecutando build único...")
        result = subprocess.run(
            [sys.executable, "build_exe.py", "--incremental"],
            cwd=str(PROJECT_ROOT)
        )
        sys.exit(result.returncode)
    
    # Modo watcher: vigila cambios
    print("="*60)
    print(" KDP MASTER - AUTO BUILD (Post-Guardado)")
    print("="*60)
    print(f"📂 Proyecto: {PROJECT_ROOT}")
    print(f"⏳ Debounce: {DEBOUNCE_SECONDS}s")
    print(f"📝 Archivos vigilados: {', '.join(WATCH_PATTERNS)}")
    print(f"   + app/**/*.py, modules/**/*.py")
    print("")
    print("Presiona Ctrl+C para detener")
    print("="*60)
    
    # Inicializar manager
    manager = AutoBuildManager()
    
    # Usar watchdog si está disponible, si no polling simple
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class BuildTriggerHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.is_directory:
                    return
                if event.src_path.endswith('.py'):
                    print(f"📝 Cambio detectado: {os.path.basename(event.src_path)}")
                    manager.trigger_if_needed(event.src_path)
            
            def on_created(self, event):
                if event.is_directory:
                    return
                if event.src_path.endswith('.py'):
                    print(f"🆕 Archivo creado: {os.path.basename(event.src_path)}")
                    manager.trigger_if_needed(event.src_path)
        
        handler = BuildTriggerHandler()
        observer = Observer()
        
        # Vigilar directorio raíz y subdirectorios clave
        observer.schedule(handler, path=str(PROJECT_ROOT / "app"), recursive=True)
        observer.schedule(handler, path=str(PROJECT_ROOT / "modules"), recursive=True)
        observer.schedule(handler, path=str(PROJECT_ROOT), recursive=False)
        
        observer.start()
        
        print("👀 Vigilmdo cambios en tiempo real...")
        
        try:
            while manager.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo...")
        finally:
            observer.stop()
            observer.join()
            manager.stop()
    
    except ImportError:
        # Fallback: polling simple
        print("⚠️ watchdog no instalado. Usando polling simple.")
        print("   Instala con: pip install watchdog")
        
        import hashlib
        
        def get_file_hash(path):
            with open(path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        
        # Monitorear archivos clave
        files_to_watch = [
            PROJECT_ROOT / "gui_app.py",
            PROJECT_ROOT / "build_exe.py",
            PROJECT_ROOT / "app" / "modules" / "monitoring" / "run_build.py",
        ]
        
        last_hashes = {f: get_file_hash(f) for f in files_to_watch if f.exists()}
        
        try:
            while manager.running:
                time.sleep(1)
                
                for f in files_to_watch:
                    if not f.exists():
                        continue
                    
                    current_hash = get_file_hash(f)
                    if f in last_hashes and current_hash != last_hashes[f]:
                        print(f"📝 Cambio detectado: {f.name}")
                        manager.trigger_if_needed(str(f))
                        last_hashes[f] = current_hash
        
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo...")
        finally:
            manager.stop()
    
    print("✨ Auto-build finalizado")


if __name__ == "__main__":
    # Fix Unicode para Windows/PowerShell
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    main()