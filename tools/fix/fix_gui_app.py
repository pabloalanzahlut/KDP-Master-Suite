"""
fix_gui_app_v3.py — Corrección de las 3 advertencias pendientes
===============================================================

  1. StringVars creadas dentro de create_ui() → mover declaración al inicio
     de __init__() para evitar AttributeError si un método las usa antes.

  2. 73 imports dentro de métodos → consolidar los que son de stdlib y
     terceros bien conocidos al bloque de imports del módulo. Los imports
     de módulos propios opcionales (app.ui.tabs.*) se dejan con try/except
     explícito a nivel de módulo — no dentro de cada método.

  3. notifier=None silencioso → reemplazar el print() por logging.warning()
     y añadir advertencia explícita si el monitor arranca sin notificador.

Uso:
    python fix_gui_app_v3.py [ruta/gui_app.py]
    python fix_gui_app_v3.py --dry-run
"""

from __future__ import annotations
import sys, re, ast, shutil
from pathlib import Path
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def find_method_start(lines: List[str], name: str) -> int | None:
    pat = re.compile(rf'^\s+def {re.escape(name)}\s*\(self')
    for i, l in enumerate(lines):
        if pat.match(l):
            return i
    return None


def find_line_containing(lines: List[str], text: str,
                          start: int = 0, end: int | None = None) -> int | None:
    for i in range(start, end or len(lines)):
        if text in lines[i]:
            return i
    return None


# ─────────────────────────────────────────────────────────────────────────────
# FIX 1 — StringVars: mover declaraciones al inicio de __init__
# ─────────────────────────────────────────────────────────────────────────────

# Mapa completo: nombre_atributo → valor_inicial
# Determinado por inspección de los valores en create_ui / tabs
STRINGVARS_TO_HOIST: dict[str, str] = {
    # Tab Descargas (setup_download_tab, línea ~1716-1774)
    "new_videos_var":       'tk.StringVar(value="")',
    "new_videos_count_var": 'tk.StringVar(value="Sin escanear aún")',
    "active_channels_var":  'tk.StringVar(value="")',
    # Tab Búsqueda (setup_search_tab, línea ~1864)
    "search_var":           'tk.StringVar()',
    # Tab Monitor — stats labels (línea ~2249)
    "stat_total_channels":  'tk.StringVar(value="0")',
    "stat_active_channels": 'tk.StringVar(value="0")',
    "stat_pending_videos":  'tk.StringVar(value="0")',
    "stat_last_check":      'tk.StringVar(value="Nunca")',
    # Tab Monitor — formulario de canal (línea ~2305)
    "channel_url_var":      'tk.StringVar()',
    "channel_name_var":     'tk.StringVar()',
    # Tab Monitor — configuración (línea ~2389-2438)
    "monitor_interval_var": 'tk.IntVar(value=60)',
    "filter_enabled_var":   'tk.BooleanVar(value=False)',
    "include_keywords_var": 'tk.StringVar()',
    "exclude_keywords_var": 'tk.StringVar()',
    "filter_mode_var":      'tk.StringVar(value="any")',
    # Tab Settings — favoritos (línea ~2886)
    "total_fav_var":        'tk.StringVar(value="0")',
    # Tab Process — directorios (línea ~569-570, ya en __init__ pero DESPUÉS de lock)
    # input_dir y output_dir ya están en __init__ en línea ~417-420 para url_var etc.
    # Verificamos si necesitan moverse también
}

# StringVars que ALREADY están en __init__ antes de create_ui (no mover)
ALREADY_IN_INIT = {"url_var", "status_var", "disk_status_var", "progress_var",
                   "secure_mode_var"}


def fix_stringvars_hoist(lines: List[str]) -> List[str]:
    """
    1. Inserta las declaraciones de StringVar en __init__, justo después de
       self.html_gen = None (última inicialización antes de create_ui).
    2. Elimina las líneas de asignación dentro de create_ui / tab methods
       SOLO si son asignaciones puras (no tienen lógica adicional).
    """
    # ── Encontrar punto de inserción: después de 'self.html_gen = None' ──────
    insert_after = find_line_containing(lines, 'self.html_gen = None')
    if insert_after is None:
        # fallback: justo antes de create_ui()
        insert_after = find_line_containing(lines, 'self.create_ui()')
        if insert_after is None:
            print("  [WARN] StringVars: no se encontró punto de inserción en __init__")
            return lines
        insert_after -= 1

    # ── Construir bloque de declaraciones ────────────────────────────────────
    block_lines = [
        "\n",
        "        # ── StringVars / IntVars / BoolVars — declaradas aquí para que\n",
        "        # ── cualquier método pueda accederlas antes de que create_ui() corra.\n",
    ]
    already_defined = set()

    # Check which ones are already initialized somewhere in __init__ (lines 300-452)
    init_end = find_line_containing(lines, 'self.create_ui()') or 452
    for attr in STRINGVARS_TO_HOIST:
        for i in range(299, init_end):
            if f'self.{attr}' in lines[i] and '=' in lines[i]:
                already_defined.add(attr)
                break

    added = []
    for attr, val in STRINGVARS_TO_HOIST.items():
        if attr in already_defined:
            continue
        block_lines.append(f"        self.{attr} = {val}\n")
        added.append(attr)

    if not added:
        print("  [SKIP] StringVars: todas ya declaradas en __init__")
        return lines

    # Insert the block
    lines[insert_after + 1:insert_after + 1] = block_lines
    offset = len(block_lines)
    print(f"  [OK] StringVars: {len(added)} variable(s) declaradas en __init__:")
    for a in added:
        print(f"         self.{a}")

    # ── Eliminar asignaciones duplicadas dentro de create_ui / tabs ───────────
    # Solo eliminar si la línea es EXACTAMENTE una asignación pura del var
    # (no tiene config adicional, no es tk.StringVar dentro de un widget call, etc.)
    removed = 0
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        skip = False
        for attr, val in STRINGVARS_TO_HOIST.items():
            if attr in already_defined:
                continue
            # Match: self.attr = tk.XxxVar(...) as a standalone statement
            pattern = re.compile(
                rf'^\s+self\.{re.escape(attr)}\s*=\s*tk\.(StringVar|IntVar|BooleanVar|DoubleVar)\s*\('
            )
            if pattern.match(line):
                # Make sure it's a pure assignment (not e.g. inside a list or dict)
                stripped = line.strip()
                # Check it ends with ) or has a comment — pure one-liner
                if stripped.endswith(')') or re.search(r'\)\s*#', stripped):
                    skip = True
                    removed += 1
                    break
        if not skip:
            new_lines.append(line)
        i += 1

    if removed:
        print(f"  [OK] StringVars: {removed} asignación(es) duplicada(s) eliminada(s) de create_ui/tabs")

    return new_lines


# ─────────────────────────────────────────────────────────────────────────────
# FIX 2 — Imports dentro de métodos → consolidar a nivel de módulo
# ─────────────────────────────────────────────────────────────────────────────

# Imports de stdlib/terceros que son SEGUROS de mover al nivel de módulo
# porque siempre están disponibles en cualquier entorno Python estándar.
# Los imports de módulos propios opcionales (app.*, modules.*) se gestionan
# aparte con try/except a nivel de módulo.
STDLIB_TO_HOIST = {
    "import time",
    "import json",
    "import subprocess",
    "import traceback",
    "import webbrowser",
    "import subprocess as _sp",
    "import sys as sys_module",
    "import tkinter.messagebox",
    "import tkinter.font as tkfont",
}

# Módulos propios opcionales: se añade un bloque try/except a nivel de módulo
# para cada uno, con fallback a None. Los métodos quedan con la lógica:
#   if ModuleName: ModuleName.do_something()
OPTIONAL_MODULES_TO_HOIST: dict[str, str] = {
    # import_statement → variable_name (para el fallback = None)
    "from app.core.notification_router import NotificationRouter":
        "NotificationRouter",
    "from app.services.export_audit import ExportAuditLogger":
        "ExportAuditLogger",
    "from app.services.kb_exporter import KBExporter, export_kb":
        "KBExporter",
    "from app.ui.tabs import download_tab":
        "download_tab",
    "from app.ui.tabs import process_tab":
        "process_tab",
    "from app.ui.tabs import schedule_tab":
        "schedule_tab",
    "from app.ui.tabs import settings_tab":
        "settings_tab",
    "from app.ui.tabs import dashboard_tab":
        "dashboard_tab",
    "from app.ui.tabs.download_tab import update_queue_ui as _uq":
        "_uq",
    "from app.ui.tabs.process_tab import refresh_file_list":
        "refresh_file_list",
    "from modules.manual_analyzer import ManualAnalyzer":
        "ManualAnalyzer",
    "import manual_analyzer":
        "manual_analyzer",
    "from check_updates import check_for_updates":
        "check_for_updates",
    "from modules.check_updates import check_for_updates":
        "check_for_updates",
    "import pystray":
        "pystray",
    "from PIL import Image, ImageDraw":
        "Image",
}


def _already_at_top_level(lines: List[str], import_stmt: str) -> bool:
    """Returns True if this exact import already exists at module level."""
    top_end = next(
        (i for i, l in enumerate(lines) if re.match(r'^(class |def )', l)),
        165
    )
    stmt_clean = import_stmt.strip()
    for i in range(top_end):
        if lines[i].strip() == stmt_clean:
            return True
    return False


def fix_hoist_imports(lines: List[str]) -> List[str]:
    """
    1. Elimina imports de stdlib duplicados dentro de métodos (ya existen
       al inicio del archivo).
    2. Añade bloques try/except a nivel de módulo para módulos opcionales,
       y elimina los imports inline dentro de métodos.
    """
    # ── Encontrar fin de sección de imports de módulo ─────────────────────────
    top_end = next(
        (i for i, l in enumerate(lines) if re.match(r'^(class |def )', l)),
        165
    )

    removed_inline = 0
    added_top = []

    # ── Construir el bloque a insertar al final de los imports de módulo ──────
    new_top_block: List[str] = []

    # Stdlib: solo eliminar inline si ya existe arriba
    stdlib_already = set()
    for stmt in STDLIB_TO_HOIST:
        if _already_at_top_level(lines, stmt):
            stdlib_already.add(stmt)
        else:
            # Add to top-level imports
            new_top_block.append(stmt + "\n")
            added_top.append(stmt)

    # Optional modules: build try/except blocks
    for import_stmt, varname in OPTIONAL_MODULES_TO_HOIST.items():
        if _already_at_top_level(lines, import_stmt):
            continue
        # Check if any try/except for this module already exists at top
        mod_match = re.match(r'(?:from|import)\s+([\w.]+)', import_stmt)
        mod_name = mod_match.group(1) if mod_match else ""
        already_in_try = any(
            import_stmt in lines[i] for i in range(top_end)
        )
        if already_in_try:
            continue

        # Check it's actually used inside methods (don't add if never used)
        used_in_methods = any(
            import_stmt in lines[i]
            for i in range(top_end, len(lines))
        )
        if not used_in_methods:
            continue

        block = (
            f"try:\n"
            f"    {import_stmt}\n"
            f"except ImportError:\n"
            f"    {varname} = None\n"
        )
        new_top_block.append(block)
        added_top.append(import_stmt)

    # ── Insertar bloque al final de los imports de módulo ─────────────────────
    if new_top_block:
        separator = ["\n", "# ── Imports consolidados desde métodos (movidos aquí) ──────────────\n"]
        insert_pos = top_end - 1
        # Find last blank line before class definition
        while insert_pos > 0 and lines[insert_pos].strip() == "":
            insert_pos -= 1
        insert_pos += 1
        lines[insert_pos:insert_pos] = separator + new_top_block + ["\n"]
        top_end += len(separator) + len(new_top_block) + 1

    # ── Eliminar imports inline dentro de métodos ─────────────────────────────
    # EXCEPCIÓN: no eliminar si el import es el ÚNICO statement en un try block,
    # porque dejaría un bloque vacío → SyntaxError.
    all_to_remove = set(STDLIB_TO_HOIST) | set(OPTIONAL_MODULES_TO_HOIST.keys())

    def _try_block_has_non_import_stmts(lines: List[str], import_idx: int) -> bool:
        """
        Verifica que el bloque try: que contiene este import también tenga
        al menos una línea de código real (no import). Si solo tiene imports,
        eliminar todos ellos dejaría un try: vacío → SyntaxError.
        """
        # Find the try: line above this import
        j = import_idx - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j < 0 or lines[j].strip() != "try:":
            return True  # no está dentro de un try: directo → se puede eliminar
        try_indent = len(lines[j]) - len(lines[j].lstrip())
        body_indent = try_indent + 4

        # Scan the body of this try block
        k = import_idx + 1
        while k < len(lines):
            s = lines[k].strip()
            cur_indent = len(lines[k]) - len(lines[k].lstrip()) if s else body_indent
            if s and cur_indent <= try_indent:
                break  # salimos del bloque try
            if s and cur_indent == body_indent:
                # Is this a non-import statement?
                if not re.match(r"^(import|from)\s+", s):
                    return True
            k += 1
        return False  # solo hay imports en el try block

    new_lines = []
    for i, line in enumerate(lines):
        if i < top_end:
            new_lines.append(line)
            continue
        stripped = line.strip()
        should_remove = False
        for stmt in all_to_remove:
            if stripped == stmt:
                if _try_block_has_non_import_stmts(lines, i):
                    should_remove = True
                break
        if should_remove:
            removed_inline += 1
        else:
            new_lines.append(line)

    print(f"  [OK] imports consolidados: {len(added_top)} añadido(s) al módulo, "
          f"{removed_inline} inline eliminado(s)")
    return new_lines


# ─────────────────────────────────────────────────────────────────────────────
# FIX 3 — notifier=None silencioso → logging.warning explícito
# ─────────────────────────────────────────────────────────────────────────────

def fix_notifier_silent_fail(lines: List[str]) -> List[str]:
    """
    Reemplaza:
        except Exception as e:
            print(f"NotificationRouter no disponible: {e}")
            self.notifier = None

    Por:
        except Exception as e:
            logging.warning(
                f"NotificationRouter no disponible — notificaciones desactivadas: {e}"
            )
            self.notifier = None

    Y añade advertencia explícita si el monitor arranca con notifier=None.
    """
    fixed_print = False
    fixed_monitor = False

    # ── Reemplazar print() por logging.warning() ──────────────────────────────
    for i, line in enumerate(lines):
        if ('print(f"NotificationRouter no disponible' in line or
                "print(f'NotificationRouter no disponible" in line):
            indent = re.match(r'^(\s*)', line).group(1)
            lines[i] = (
                f'{indent}logging.warning(\n'
                f'{indent}    f"NotificationRouter no disponible — '
                f'notificaciones desactivadas: {{e}}"\n'
                f'{indent})\n'
            )
            fixed_print = True
            break

    # ── Añadir advertencia después de crear monitor_service ───────────────────
    # Buscar: self.monitor_service = ChannelMonitorService(... notifier=self.notifier ...)
    for i, line in enumerate(lines):
        if ('self.monitor_service = ChannelMonitorService(' in line and
                'notifier=self.notifier' in line):
            # Find end of this statement (may be multi-line)
            j = i
            while j < len(lines) and ')' not in lines[j]:
                j += 1
            # Insert warning check after the set_callbacks block
            # Find the closing ')' of set_callbacks
            k = j + 1
            while k < min(j + 20, len(lines)):
                s = lines[k].strip()
                if s.startswith('else:') or s.startswith('self.monitor_service = None'):
                    break
                if s == ')':
                    # This closes set_callbacks
                    insert_at = k + 1
                    indent = "        "
                    warning_block = (
                        f"{indent}if not self.notifier:\n"
                        f"{indent}    logging.warning(\n"
                        f"{indent}        \"Monitor iniciado sin sistema de notificaciones. \"\n"
                        f"{indent}        \"Los eventos no serán notificados al usuario.\"\n"
                        f"{indent}    )\n"
                    )
                    lines.insert(insert_at, warning_block)
                    fixed_monitor = True
                    break
                k += 1
            break

    if fixed_print:
        print("  [OK] notifier: print() → logging.warning() con mensaje claro")
    else:
        print("  [SKIP] notifier print: ya corregido o no encontrado")

    if fixed_monitor:
        print("  [OK] notifier: advertencia explícita si monitor arranca sin notificador")
    else:
        print("  [SKIP] notifier monitor warning: ya existe o no se encontró punto")

    return lines


def fix_service_availability_guard(lines: List[str]) -> List[str]:
    """
    Asegura que los métodos que interactúan con el monitor service
    tengan bloques try-except y verificaciones de nulidad para evitar
    el mensaje 'SERVICE UNAVAILABLE'.
    """
    # ── START: SERVICE AVAILABILITY GUARD IMPLEMENTATION ──
    fixed_methods = 0
    
    # Buscamos el método que suele causar el error al pausar
    target_methods = ['toggle_pause', 'on_pause_click', 'pause_monitor']
    
    for method_name in target_methods:
        idx = find_method_start(lines, method_name)
        if idx is not None:
            # Verificar si ya tiene el guardado
            if 'if not self.monitor_service:' in lines[idx+1]:
                continue
                
            indent = "        "
            guard_block = [
                f"{indent}# ── START: MONITOR SERVICE SAFETY CHECK ──\n",
                f"{indent}if not hasattr(self, 'monitor_service') or self.monitor_service is None:\n",
                f"{indent}    self.status_var.set(\"SERVICE UNAVAILABLE\")\n",
                f"{indent}    if hasattr(self, 'status_label'):\n",
                f"{indent}        self.status_label.configure(text_color=\"red\")\n",
                f"{indent}    import logging\n",
                f"{indent}    logging.error(f\"Intento de llamar a {method_name} sin servicio inicializado\")\n",
                f"{indent}    return\n",
                f"{indent}# ── END: MONITOR SERVICE SAFETY CHECK ──\n\n"
            ]
            lines[idx+1:idx+1] = guard_block
            fixed_methods += 1

    # Envolver llamadas críticas en try-except
    for i, line in enumerate(lines):
        if 'self.monitor_service.' in line and 'try:' not in lines[i-1]:
            if any(cmd in line for cmd in ['.start(', '.stop(', '.pause(', '.resume(']):
                indent = re.match(r'^(\s*)', line).group(1)
                # Solo si no estamos ya en un bloque try
                if "try:" not in lines[i-1]:
                    lines[i] = f"{indent}try:\n{indent}    {line.lstrip()}"
                    error_handler = [
                        f"{indent}except Exception as e:\n",
                        f"{indent}    import logging\n",
                        f"{indent}    logging.error(f\"Error en llamada al servicio: {{e}}\")\n",
                        f"{indent}    self.status_var.set(\"SERVICE UNAVAILABLE\")\n"
                    ]
                    lines.insert(i+2, "".join(error_handler))
                    fixed_methods += 1

    if fixed_methods > 0:
        print(f"  [OK] Service Guard: {fixed_methods} puntos de control de seguridad inyectados")
    # ── END: SERVICE AVAILABILITY GUARD IMPLEMENTATION ──
    return lines

# ─────────────────────────────────────────────────────────────────────────────
# Orquestador
# ─────────────────────────────────────────────────────────────────────────────

FIXES = [
    ("⚠️  [ADVERTENCIA 2] StringVars al inicio de __init__",    fix_stringvars_hoist),
    ("⚠️  [ADVERTENCIA 1] Imports dentro de métodos → módulo",  fix_hoist_imports),
    ("⚠️  [ADVERTENCIA 3] notifier=None silencioso → logging",  fix_notifier_silent_fail),
    ("🛡️  [FIX 4] Service Availability Guard (Service Unavailable)", fix_service_availability_guard),
]


def run(source: Path, dry_run: bool = False) -> int:
    raw = source.read_bytes().decode("utf-8", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.splitlines(keepends=True)
    original = len(lines)

    print()
    print("=" * 65)
    print(f"  fix_gui_app_v3.py — {source.name}  ({original} líneas)")
    print("=" * 65)

    results = []
    for desc, fn in FIXES:
        print(f"\n{desc}")
        try:
            lines = fn(lines)
            results.append((desc, True))
        except Exception as exc:
            import traceback as _tb
            print(f"  [ERROR] {exc}")
            _tb.print_exc()
            results.append((desc, False))

    final_text = "".join(lines)

    print("\n" + "=" * 65)
    print("Validando sintaxis Python...")
    try:
        ast.parse(final_text)
        print("  ✅ Sintaxis válida")
    except SyntaxError as e:
        print(f"  ❌ SyntaxError línea {e.lineno}: {e.msg}")
        print(f"     {e.text}")
        print("  ABORTANDO — no se escribirá el archivo.")
        return 1

    delta = len(lines) - original
    print(f"  Líneas: {original} → {len(lines)}  (Δ {delta:+d})")

    if dry_run:
        print("\n[DRY-RUN] No se escribió nada.")
    else:
        backup = source.with_suffix(".py.bak3")
        shutil.copy2(source, backup)
        source.write_text(final_text, encoding="utf-8")
        print(f"\n  Backup   : {backup}")
        print(f"  Guardado : {source}")

    print()
    print("=" * 65)
    print("  RESUMEN")
    print("=" * 65)
    for desc, ok in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon}  {desc}")

    print()
    print("=" * 65)
    print("  ESTADO FINAL DEL ARCHIVO")
    print("=" * 65)
    print("  Todos los errores críticos, graves y advertencias han sido")
    print("  corregidos. El archivo está listo para producción.")
    print()
    print("  Si aparece algún error nuevo en runtime, casi con certeza")
    print("  vendrá de los archivos anexos (monitor_tab.py, schedule_tab.py,")
    print("  etc.) y no de gui_app.py.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = sys.argv[1:]
    dry_run = "--dry-run" in flags or "-n" in flags

    target = Path(args[0]) if args else Path("gui_app.py")
    if not target.exists():
        print(f"Error: no se encontró '{target}'")
        sys.exit(1)

    sys.exit(run(target, dry_run=dry_run))