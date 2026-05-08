"""
KDP_MASTER - Portable Mode Logic
==============================
Funcionalidad: Detecta automáticamente si la app debe usar rutas locales o del sistema.

v2.9.2: FIX-ENCODING-001 - Forzar UTF-8 para evitar UnicodeEncodeError en consola Windows.
"""

import os
import sys
from pathlib import Path

# ==================== INICIO FIX-ENCODING-001: UTF-8 RECONFIGURE ====================
# [PROBLEMA] UnicodeEncodeError: 'charmap' codec can't encode emojis en consola cp1252
# [SOLUCIÓN] Forzar stdout/stderr a UTF-8 antes de cualquier print()
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fallback: continuar sin reconfigure
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
# ==================== FIN FIX-ENCODING-001 ====================

# === [INICIO FUNCIONALIDAD: PACKAGING ENTERPRISE (PORTABLE)] ===
def is_portable() -> bool:
    """
    Detecta si la app se ejecuta desde una unidad extraíble o contiene un flag portable.
    """
    base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(".").resolve()
    
    # Flag explícito
    if (base_dir / "portable.flag").exists():
        return True
        
    # Detección por tipo de unidad en Windows
    if sys.platform == 'win32':
        import ctypes
        drive = os.path.splitdrive(str(base_dir))[0]
        if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2: # DRIVE_REMOVABLE
            return True
            
    return False

print(f"[PORTABLE CHECK] Sistema: {'PORTABLE' if is_portable() else 'INSTALADO'}")
# ==================== [FIN FUNCIONALIDAD: PACKAGING ENTERPRISE (PORTABLE)] ====================