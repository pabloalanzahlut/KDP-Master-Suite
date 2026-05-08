import os
import sys
import time
import atexit
import signal
import platform
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _import_portalocker():
    try:
        import portalocker
        return portalocker
    except ImportError:
        return None


class ApplicationLock:
    """
    Sistema de prevención de instancias múltiples robusto.
    Usa portalocker para atomicidad cross-platform (Windows/macOS/Linux).
    
    Características:
    - Lock atómico con O_EXCL
    - Validación de PID de proceso activo
    - Limpieza de locks huérfanos con confirmación
    - Registro automático de cleanup en atexit
    - Soporte para signal handlers (SIGTERM, SIGINT)
    """
    
    # [MODULE: ApplicationLock] START
    # [MODULE: ApplicationLock] END
    
    def __init__(self, lock_name="app.lock", timeout=1, base_dir=None):
        """
        Inicializa el gestor de lock.
        
        Args:
            lock_name: Nombre del archivo de lock
            timeout: Timeout en segundos para adquirir lock
            base_dir: Directorio base donde crear el lock (default: cwd)
        """
        self.lock_name = lock_name
        self.timeout = timeout
        self.base_dir = base_dir or self._get_base_dir()
        self.lock_path = os.path.join(self.base_dir, lock_name)
        self.lock_fd = None
        self._acquired = False
        self._pid = os.getpid()
        
        # Intentar importar portalocker
        self._portalocker = _import_portalocker()
        
    def _get_base_dir(self):
        """Obtiene el directorio base para el lock file."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))
    
    def acquire(self):
        """
        Intenta adquirir el lock de forma atómica.
        
        Returns:
            bool: True si se adquirió el lock, False si ya está en uso.
        """
        # Primero verificar locks huérfanos
        if os.path.exists(self.lock_path):
            if self.is_orphaned_lock():
                logger.warning(f"Lock huérfano detectado en {self.lock_path}")
                return False  # Dejar que el usuario decida
        
        if self._portalocker:
            return self._acquire_portalocker()
        else:
            return self._acquire_native()
    
    def _acquire_portalocker(self):
        """Adquirir lock usando portalocker (recomendado)."""
        try:
            self.lock_fd = open(self.lock_path, 'w')
            self._portalocker.lock(
                self.lock_fd.fileno(),
                self._portalocker.LOCK_EX | self._portalocker.LOCK_NB
            )
            self.lock_fd.write(str(self._pid))
            self.lock_fd.flush()
            self._acquired = True
            
            # Registrar cleanup automático
            atexit.register(self.release)
            
            # Registrar signal handlers
            self._register_signal_handlers()
            
            logger.info(f"Lock adquirido: {self.lock_path} (PID: {self._pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error al adquirir lock con portalocker: {e}")
            if self.lock_fd:
                try:
                    self.lock_fd.close()
                except:
                    pass
            self.lock_fd = None
            return False
    
    def _acquire_native(self):
        """Adquirir lock usando implementación nativa (fallback)."""
        try:
            # Windows: usar msvcrt
            if platform.system() == "Windows":
                return self._acquire_windows()
            # Linux/Mac: usar fcntl
            else:
                return self._acquire_fcntl()
        except Exception as e:
            logger.error(f"Error al adquirir lock nativo: {e}")
            return False
    
    def _acquire_windows(self):
        """Adquirir lock en Windows usando msvcrt."""
        import msvcrt
        try:
            # Crear archivo para lock
            self.lock_fd = open(self.lock_path, 'w')
            # Intentar lock exclusivo no bloqueante
            msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
            self.lock_fd.write(str(self._pid))
            self.lock_fd.flush()
            self._acquired = True
            
            atexit.register(self.release)
            self._register_signal_handlers()
            
            logger.info(f"Lock adquirido (Windows): {self.lock_path}")
            return True
        except (IOError, OSError):
            if self.lock_fd:
                try:
                    self.lock_fd.close()
                except:
                    pass
            self.lock_fd = None
            return False
    
    def _acquire_fcntl(self):
        """Adquirir lock en Linux/Mac usando fcntl."""
        import fcntl
        try:
            self.lock_fd = open(self.lock_path, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(self._pid))
            self.lock_fd.flush()
            self._acquired = True
            
            atexit.register(self.release)
            self._register_signal_handlers()
            
            logger.info(f"Lock adquirido (Unix): {self.lock_path}")
            return True
        except (IOError, OSError):
            if self.lock_fd:
                try:
                    self.lock_fd.close()
                except:
                    pass
            self.lock_fd = None
            return False
    
    def _register_signal_handlers(self):
        """Registrar handlers para señales de terminación."""
        def signal_handler(signum, frame):
            logger.info(f"Señal {signum} recibida, liberando lock...")
            self.release()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except:
            pass  # Platform no soporta signals
    
    def release(self):
        """
        Libera el lock y elimina el archivo.
        """
        if not self._acquired:
            return
        
        try:
            if self._portalocker:
                try:
                    self._portalocker.lock(self.lock_fd.fileno(), self._portalocker.LOCK_UN)
                except:
                    pass
            else:
                if platform.system() == "Windows":
                    import msvcrt
                    try:
                        msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass
                else:
                    import fcntl
                    try:
                        fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                    except:
                        pass
            
            if self.lock_fd:
                try:
                    self.lock_fd.close()
                except:
                    pass
            
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)
            
            logger.info(f"Lock liberado y eliminado: {self.lock_path}")
            
        except Exception as e:
            logger.error(f"Error al liberar lock: {e}")
        
        self._acquired = False
        self.lock_fd = None
    
    def is_orphaned_lock(self):
        """
        Verifica si el lock pertenece a un proceso huérfano (muerto).
        
        Returns:
            bool: True si el lock está huérfano (proceso dueño no existe).
        """
        if not os.path.exists(self.lock_path):
            return False
        
        try:
            with open(self.lock_path, 'r') as f:
                pid_str = f.read().strip()
            
            if not pid_str:
                return True  # Archivo vacío = huérfano
            
            pid = int(pid_str)
            
            # Verificar si el proceso existe
            if platform.system() == "Windows":
                return not self._process_exists_windows(pid)
            else:
                return self._process_exists_unix(pid) == False
            
        except (ValueError, FileNotFoundError):
            return True  # Archivo corrupto o no legible = huérfano
        except Exception as e:
            logger.warning(f"Error al verificar lock huérfano: {e}")
            return True
    
    def _process_exists_windows(self, pid):
        """Verifica si un proceso existe en Windows."""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback sin psutil
            import subprocess
            try:
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                return str(pid) in result.stdout
            except:
                return True  # Asumir que existe si no podemos verificar
    
    def _process_exists_unix(self, pid):
        """Verifica si un proceso existe en Unix."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def get_lock_info(self):
        """
        Obtiene información de debug del lock.
        
        Returns:
            dict: Información del lock actual.
        """
        info = {
            "lock_path": self.lock_path,
            "exists": os.path.exists(self.lock_path),
            "current_pid": self._pid,
            "acquired": self._acquired
        }
        
        if os.path.exists(self.lock_path):
            try:
                with open(self.lock_path, 'r') as f:
                    info["stored_pid"] = f.read().strip()
                    info["is_orphaned"] = self.is_orphaned_lock()
            except:
                info["stored_pid"] = "unknown"
                info["is_orphaned"] = True
        
        return info
    
    def force_cleanup(self):
        """
        Fuerza la limpieza del lock sin verificar si es huérfano.
        Útil para recuperación de errores.
        """
        try:
            if self.lock_fd:
                try:
                    self.lock_fd.close()
                except:
                    pass
            
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)
            
            logger.warning(f"Lock forzosamente eliminado: {self.lock_path}")
            return True
        except Exception as e:
            logger.error(f"Error en force cleanup: {e}")
            return False


def check_and_initialize_lock(lock_name="app.lock", base_dir=None):
    """
    Función helper para verificar y adquirir lock en inicio de aplicación.
    
    Args:
        lock_name: Nombre del archivo de lock
        base_dir: Directorio base
        
    Returns:
        tuple: (lock_instance, should_continue)
            - lock_instance: Instancia de ApplicationLock si se adquirió
            - should_continue: False si debe detenerse, True para continuar
    """
    lock = ApplicationLock(lock_name=lock_name, base_dir=base_dir)
    
    if not lock.acquire():
        return lock, False
    
    return lock, True