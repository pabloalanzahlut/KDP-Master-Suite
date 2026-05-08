"""
KDP_MASTER - Smoke Test Suite
=============================
Funcionalidad: Verifica que el entorno sea estable después de un despliegue o build.
"""

import os
import sys
import sqlite3
from pathlib import Path

# === [INICIO FUNCIONALIDAD: SMOKE TESTING] ===
def verify_system_health():
    """Verificaciones de 'Humo' para asegurar que la app no colapse al iniciar."""
    print("🔍 Ejecutando Smoke Test (ISO 25010)...")
    
    root = Path(__file__).parent.parent.parent
    critical_dirs = ["app/services", "data", "knowledge/manuals"]
    critical_files = ["gui_app.py", "dashboard_server.py"]
    
    # 1. Validar integridad de carpetas
    for d in critical_dirs:
        if not (root / d).exists():
            print(f"❌ FALLO: Directorio crítico no encontrado: {d}")
            return False

    # 2. Validar presencia de archivos fuente
    for f in critical_files:
        if not (root / f).exists():
            print(f"❌ FALLO: Script base faltante: {f}")
            return False

    # 3. Validar acceso a Persistencia (DB)
    try:
        db_path = root / "data" / "channel_monitor.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.execute("SELECT 1")
            conn.close()
    except Exception as e:
        print(f"❌ FALLO: Error de acceso a Base de Datos: {e}")
        return False

    print("✅ Smoke Test: PASSED (Entorno estable)")
    return True

if __name__ == "__main__":
    sys.exit(0 if verify_system_health() else 1)
# === [FIN FUNCIONALIDAD: SMOKE TESTING] ===