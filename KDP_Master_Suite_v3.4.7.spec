# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('.env.template', '.'), ('data', 'data'), ('knowledge', 'knowledge'), ('themes', 'themes'), ('docs', 'docs'), ('C:\\Program Files\\Python314\\tcl\\tcl8.6', '_tcl_data'), ('C:\\Program Files\\Python314\\tcl\\tk8.6', '_tk_data'), ('app', 'app'), ('modules', 'modules')]
binaries = [('C:\\Users\\Alan\\AppData\\Local\\Programs\\Python\\Python311\\python311.dll', '.')]
hiddenimports = ['google.genai', 'pycparser.lextab', 'pycparser.yacctab', '_tkinter', 'tkinter', 'pystray._win32', 'PIL._tkinter_finder', 'requests', 'sv_ttk', 'markdown2', 'weasyprint', 'winotify', 'pydantic', 'psutil', 'secrets', 'app.core.doc_updater', 'app.core.env_manager', 'sqlite3', 'cryptography', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.scrolledtext', 'logging.handlers', 'json', 'csv', 'zipfile', 'shutil', 'subprocess', 'threading', 'urllib.request', 'urllib.error', 'pathlib', 'datetime', 're', 'atexit', 'time', 'socket', 'webbrowser', 'http.server', 'hashlib', 'base64', 'json', 'urllib.parse', 'customtkinter', 'app.ui.tabs.settings_tab', 'app.modules.processing.integrate_knowledge', 'app.core.ollama_pool', 'modules.manual_analyzer']
tmp_ret = collect_all('tkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sv_ttk')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pydantic')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('psutil')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('cryptography')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KDP_Master_Suite_v3.4.7',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KDP_Master_Suite_v3.4.7',
)
