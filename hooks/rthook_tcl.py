"""
rthook_tcl.py — Runtime Hook para Tcl/Tk
=============================================
Configura variables TCL_LIBRARY y TK_LIBRARY antes de cargar tkinter.
Esto previene el error: "Tcl data directory not found"

Estrategia: Múltiples intentos de búsqueda + fallback inteligente
"""
import os
import sys

def _setup_tcl_environment():
    """Configura TCL_LIBRARY/TK_LIBRARY para el ejecutable."""
    if not getattr(sys, 'frozen', False):
        return  # Solo para ejecutable
    
    base_path = sys._MEIPASS
    
    # 📌 ESTRATEGIA 1: Buscar en múltiples ubicaciones posibles
    search_paths = [
        base_path,                                    # raíz del exe
        os.path.join(base_path, '_internal'),         # _internal/
        os.path.join(base_path, 'app', '_internal'), # app/_internal/
    ]
    
    tcl_names = ['tcl8.6', 'tcl_data', '_tcl_data']
    tk_names = ['tk8.6', 'tk_data', '_tk_data']
    
    # Buscar TCL
    for search_base in search_paths:
        for name in tcl_names:
            tcl_path = os.path.join(search_base, name)
            if os.path.isdir(tcl_path):
                os.environ['TCL_LIBRARY'] = tcl_path
                break
        if 'TCL_LIBRARY' in os.environ:
            break
    
    # Buscar TK
    for search_base in search_paths:
        for name in tk_names:
            tk_path = os.path.join(search_base, name)
            if os.path.isdir(tk_path):
                os.environ['TK_LIBRARY'] = tk_path
                break
        if 'TK_LIBRARY' in os.environ:
            break
    
    # 📌 ESTRATEGIA 2: Fallback a Python del sistema
    if 'TCL_LIBRARY' not in os.environ:
        for prefix in [sys.prefix, os.environ.get('PYTHON_HOME', '')]:
            if prefix:
                candidates = [
                    os.path.join(prefix, 'tcl', 'tcl8.6'),
                    os.path.join(prefix, 'Library', 'tcl', 'tcl8.6'),
                ]
                for tcl_path in candidates:
                    if os.path.isdir(tcl_path):
                        os.environ['TCL_LIBRARY'] = tcl_path
                        break
    
    if 'TK_LIBRARY' not in os.environ:
        for prefix in [sys.prefix, os.environ.get('PYTHON_HOME', '')]:
            if prefix:
                candidates = [
                    os.path.join(prefix, 'tcl', 'tk8.6'),
                    os.path.join(prefix, 'Library', 'tcl', 'tk8.6'),
                ]
                for tk_path in candidates:
                    if os.path.isdir(tk_path):
                        os.environ['TK_LIBRARY'] = tk_path
                        break
    
    # 📌 ESTRATEGIA 3: Forzar uso de Tcl/Tk embebido en Python
    if 'TCL_LIBRARY' not in os.environ:
        # Usar las DLLs embebidas directamente
        internal_path = os.path.join(base_path, '_internal')
        if os.path.isdir(internal_path):
            tcl_dll = os.path.join(internal_path, 'tcl86t.dll')
            if os.path.exists(tcl_dll):
                # Agregar al PATH para que tkinter lo encuentre
                os.environ['PATH'] = internal_path + os.pathsep + os.environ.get('PATH', '')

_setup_tcl_environment()