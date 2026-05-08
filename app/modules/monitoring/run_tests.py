"""
KDP_MASTER - Test Runner Automatizado
=====================================
Funcionalidad: Ejecuta la suite de pruebas y genera reportes de cobertura.
"""

import subprocess
import sys
import os
from pathlib import Path

# === [INICIO FUNCIONALIDAD: TEST RUNNER AUTOMATIZADO] ===
def run_quality_pipeline():
    """Ejecuta pytest con reporte de cobertura e informe HTML."""
    print("🚀 Iniciando Pipeline de Pruebas Unitarias...")
    
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    # Comandos para reporte de cobertura técnica
    commands = [
        sys.executable, "-m", "pytest",
        "--cov=app",
        "--cov-report=html:reports/coverage_html",
        "--cov-report=term-missing",
        "tests/"
    ]

    try:
        result = subprocess.run(commands, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error crítico en Test Runner: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if run_quality_pipeline() else 1)
# === [FIN FUNCIONALIDAD: TEST RUNNER AUTOMATIZADO] ===