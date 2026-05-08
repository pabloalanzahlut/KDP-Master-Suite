"""
Módulo de corrección de encoding UTF-8 para la aplicación.
[PROBLEMA] UnicodeEncodeError en ejecutable con consola cp1252
[SOLUCIÓN] Forzar UTF-8 en stdout/stderr para toda la app
"""

import sys
import os


def apply_encoding_fix():
    """Aplica la corrección de encoding UTF-8 a stdout y stderr."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    if sys.stderr.encoding != 'utf-8':
        try:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def setup_project_root():
    """Agrega el directorio raíz del proyecto a sys.path."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)
    project_root = os.path.dirname(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root


if __name__ == "__main__":
    apply_encoding_fix()