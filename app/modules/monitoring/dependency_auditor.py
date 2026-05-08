"""
KDP_MASTER - Dependency Auditor
===============================
Funcionalidad: Escaneo de vulnerabilidades y verificación de versiones.
"""

import subprocess
import sys

# === [INICIO FUNCIONALIDAD: AUDITORÍA DE DEPENDENCIAS] ===
def audit_dependencies():
    """Ejecuta escaneo de seguridad en las librerías instaladas."""
    print("🔍 Iniciando Auditoría de Seguridad (Safety)...")
    try:
        # Verificar vulnerabilidades conocidas
        result = subprocess.run([sys.executable, "-m", "safety", "check"], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️ ADVERTENCIA: Se encontraron vulnerabilidades en las dependencias:")
            print(result.stdout)
        else:
            print("✅ No se detectaron vulnerabilidades conocidas.")

        # Verificar paquetes desactualizados
        print("\n📦 Verificando paquetes desactualizados...")
        subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"])
        
        return True
    except FileNotFoundError:
        print("❌ Error: Se requiere 'safety'. Instálelo con 'pip install safety'.")
        return False

if __name__ == "__main__":
    audit_dependencies()
# === [FIN FUNCIONALIDAD: AUDITORÍA DE DEPENDENCIAS] ===