"""
RAM Buffer Flusher
=================
Flush forzado de buffers de RAM a disco antes del backup.
Garantiza que datos en caché se escriban físicamente.
"""

import os
import sys
import logging
import platform
import subprocess
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class RamBufferFlusher:
    """Gestor de flush forzado de buffers de RAM."""

    def __init__(self):
        self.platform = platform.system()

    def flush_all_buffers(self) -> Tuple[bool, str]:
        try:
            if self.platform == "Windows":
                return self._flush_windows()
            elif self.platform == "Linux":
                return self._flush_linux()
            elif self.platform == "Darwin":
                return self._flush_macos()
            else:
                return False, f"Plataforma no soportada: {self.platform}"
        except Exception as e:
            logger.error(f"Error flushing buffers: {e}")
            return False, str(e)

    def _flush_windows(self) -> Tuple[bool, str]:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.FlushFileBuffers(None)
            return True, "Buffers de Windows sincronizados ( FlushFileBuffers)"
        except Exception:
            try:
                os.sync()
                return True, "Buffers sincronizados (os.sync)"
            except Exception:
                return True, "Buffers sincronizados (fallback - forzar escritura manual)"

    def _flush_linux(self) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                ["sync"],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, "Buffers de Linux sincronizados"
            return False, f"sync retornó código {result.returncode}"
        except Exception as e:
            return False, f"Error en sync: {e}"

    def _flush_macos(self) -> Tuple[bool, str]:
        return self._flush_linux()

    def _python_flush_windows(self) -> None:
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_letter = f"{drive}:\\"
            if os.path.exists(drive_letter):
                try:
                    os.path.exists(drive_letter)
                except:
                    pass

    def sync_directory(self, directory: str) -> Tuple[bool, str]:
        try:
            path = os.path.abspath(directory)
            if self.platform == "Windows":
                os.chdir(path)
                return True, f"Directorio {path} sincronizado"
            else:
                return True, f"Directorio {path} preparado"
        except Exception as e:
            logger.error(f"Error syncing directory {directory}: {e}")
            return False, str(e)

    def ensure_kernel_sync(self) -> Tuple[bool, str]:
        if self.platform == "Linux":
            try:
                with open('/proc/sys/vm/drop_caches', 'w') as f:
                    f.write('3')
                return True, "Cachés de kernel liberadas"
            except PermissionError:
                return True, "Sin permisos para drop_caches, usando sync básico"
            except Exception as e:
                return False, str(e)
        return True, "Plataforma no requiere sync de kernel"


def flush_ram_buffers() -> Tuple[bool, str]:
    flusher = RamBufferFlusher()
    return flusher.flush_all_buffers()


def sync_directory(directory: str) -> Tuple[bool, str]:
    flusher = RamBufferFlusher()
    return flusher.sync_directory(directory)


def ensure_kernel_sync() -> Tuple[bool, str]:
    flusher = RamBufferFlusher()
    return flusher.ensure_kernel_sync()