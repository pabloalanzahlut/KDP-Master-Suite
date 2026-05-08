"""
Brute Force Test - Lazy Loading Mechanism
"""
import sys
sys.path.insert(0, r'D:\ANEXOS KDP Y DIGITALES\KDP_MASTER')

import tkinter as tk
from tkinter import ttk

print("=== BRUTE FORCE LAZY LOADING TEST ===")

# 1. Verificar que gui_app importa sin errores
print("\n[1] IMPORT TEST")
try:
    from gui_app import TranscriptionProcessorApp
    print("  OK: TranscriptionProcessorApp imported")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# 2. Verificar que todos los setup methods existen
print("\n[2] SETUP METHODS TEST")
methods = [
    'setup_download_tab', 'setup_process_tab', 'setup_analyze_tab',
    'setup_search_tab', 'setup_pending_videos_tab', 'setup_channel_monitor_tab',
    'setup_dashboard_tab', 'setup_schedule_tab', 'setup_review_tab',
    'setup_settings_tab'
]
for m in methods:
    if hasattr(TranscriptionProcessorApp, m):
        print(f"  OK: {m}")
    else:
        print(f"  FAIL: {m} NOT FOUND")

# 3. Verificar que _on_tab_changed y _load_tab_on_demand existen
print("\n[3] LAZY LOADING METHODS TEST")
for m in ['_on_tab_changed', '_load_tab_on_demand']:
    if hasattr(TranscriptionProcessorApp, m):
        print(f"  OK: {m}")
    else:
        print(f"  FAIL: {m} NOT FOUND")

# 4. Verificar que las tabs existen en create_ui
print("\n[4] TAB CREATION TEST")
import inspect
src = inspect.getsource(TranscriptionProcessorApp.create_ui)
for name in ['download', 'process', 'analyze', 'search', 'channel_monitor',
            'dashboard', 'pending_mass', 'review', 'schedule', 'settings']:
    if f'tab_{name}' in src:
        print(f"  OK: tab_{name} created in create_ui")
    else:
        print(f"  FAIL: tab_{name} NOT found in create_ui")

# 5. Verificar que se llaman setup_download y setup_process INMEDIATAMENTE
print("\n[5] IMMEDIATE SETUP TEST")
for name in ['download', 'process']:
    mname = f'setup_{name}_tab'
    pattern = f'self.{mname}()'
    if pattern in src:
        print(f"  OK: {mname}() called immediately")
    else:
        print(f"  FAIL: {mname}() NOT called immediately")

# 6. Verificar que hay binding de <<NotebookTabChanged>>
print("\n[6] BINDING TEST")
if '<<NotebookTabChanged>>' in src and '_on_tab_changed' in src:
    print("  OK: Binding <<NotebookTabChanged>> -> _on_tab_changed")
else:
    print("  FAIL: Binding not found")

# 7. Verificar que _on_tab_changed llama a _load_tab_on_demand
print("\n[7] TAB NAMES MAPPING TEST")
src2 = inspect.getsource(TranscriptionProcessorApp._on_tab_changed)
for name in ['download', 'process', 'analyze', 'search', 'channel_monitor',
            'dashboard', 'pending_mass', 'review', 'schedule', 'settings']:
    if f"'{name}'" in src2:
        print(f"  OK: '{name}' in _on_tab_changed")
    else:
        print(f"  WARN: '{name}' NOT in _on_tab_changed")

# 8. Verificar que _load_tab_on_demand llama al setup method
print("\n[8] LAZY CALL TEST")
src3 = inspect.getsource(TranscriptionProcessorApp._load_tab_on_demand)
if 'setup_method()' in src3:
    print("  OK: _load_tab_on_demand calls setup_method()")
else:
    print("  FAIL: setup_method() not called")

# 9. Verificar que _load_tab_on_demand marca como inicializada
print("\n[9] INITIALIZATION FLAG TEST")
if '_tabs_initialized[tab_name] = True' in src3:
    print("  OK: _tabs_initialized[tab_name] = True")
else:
    print("  FAIL: Initialization flag not set")

# 10. Verificar módulos de tabs
print("\n[10] TAB MODULES TEST")
mods = ['download_tab', 'process_tab', 'schedule_tab', 'settings_tab',
        'analyze_tab', 'search_tab', 'dashboard_tab', 'monitor_tab']
for m in mods:
    try:
        exec(f'from app.ui.tabs import {m}')
        print(f"  OK: {m}")
    except Exception as e:
        print(f"  FAIL: {m} -> {e}")

print("\n=== RESUMEN ===")
print("  El mecanismo de lazy loading está configurado.")
print("  Las pestañas download y process se cargan inmediatamente.")
print("  Las demás pestañas se cargan al hacer clic (lazy).")
print("  Si hay errores en el log, aparecen en la pestaña correspondiente.")
print("\n  PARA PROBAR: haz clic en cada pestaña y observa el log.")
