"""
build_exe.py — KDP Master Suite · Build Script
================================================
Genera el ejecutable portable de KDP Master Suite usando PyInstaller.

Principios aplicados:
  - Separación de responsabilidades: cada función hace una sola cosa
  - Fail-fast: cualquier paso crítico que falle aborta el build con mensaje claro
  - Idempotencia: se puede ejecutar varias veces sin efectos acumulativos
  - Trazabilidad: log detallado de cada paso con timestamps
  - Configuración centralizada: todas las constantes en un único lugar (BuildConfig)
  - No side-effects globales: las dependencias se instalan en el entorno virtual
    del proyecto, nunca se toca el entorno global del sistema

Uso:
    python build_exe.py               # build estándar (onedir)
    python build_exe.py --onefile     # un solo .exe (más lento al arrancar)
    python build_exe.py --debug       # activa consola y verbose de PyInstaller
    python build_exe.py --skip-deps   # omite verificación de dependencias
    python build_exe.py --clean-only  # solo limpia artefactos anteriores y sale
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

def _setup_logging() -> logging.Logger:
    fmt = "[%(asctime)s] %(levelname)-8s %(message)s"
    datefmt = "%H:%M:%S"
    logging.basicConfig(level=logging.INFO, format=fmt, datefmt=datefmt)
    return logging.getLogger("builder")

log = _setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# Configuración centralizada
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BuildConfig:
    """
    Fuente única de verdad para todos los parámetros del build.
    Modifica aquí; no disperses constantes por el resto del script.
    """

    # ── Identidad del ejecutable ──────────────────────────────────────────────
    app_name:    str = "KDP_Transcriptions"
    app_version: str = "2.4.3"
    entry_point: str = "gui_app.py"          # relativo a base_dir
    icon_file:   str = "assets/icon.ico"     # relativo a base_dir; None → sin ícono

    # ── Dependencias con versiones pinneadas ──────────────────────────────────
    # Formato: "paquete==versión" o "paquete>=mínimo,<máximo"
    required_packages: list[str] = field(default_factory=lambda: [
        "pyinstaller>=6.0",
        "pydantic==2.10.6",
        "pydantic-core==2.27.2",
        "sv-ttk",
        "Pillow",
    ])

    # ── Módulos de la app que PyInstaller no detecta automáticamente ──────────
    # Regla: incluir solo los que usan importación dinámica (importlib, try/except)
    hidden_imports: list[str] = field(default_factory=lambda: [
        # Stdlib usados dinámicamente
        "tkinter",
        "tkinter.ttk",
        "tkinter.scrolledtext",
        "tkinter.font",
        "sqlite3",
        # Tema visual
        "sv_ttk",
        # App — capa de servicios
        "app.core.config",
        "app.core.utils",
        "app.core.notification_router",
        "app.core.plugin_manager",
        "app.core.ui_framework",
        "app.database.db_manager",
        "app.database.knowledge_db",
        "app.services.download_service",
        "app.services.processing_service",
        "app.services.monitor_service",
        "app.services.processed_videos_tracker",
        "app.services.manual_content_merger",
        "app.services.knowledge_integrator",
        "app.services.export_audit",
        "app.services.kb_exporter",
        # App — tabs UI (importados con from app.ui.tabs import X en runtime)
        "app.ui.tabs.download_tab",
        "app.ui.tabs.process_tab",
        "app.ui.tabs.monitor_tab",
        "app.ui.tabs.schedule_tab",
        # Módulos raíz (fallback imports cuando app.* no está disponible)
        "check_kb_health",
        "check_updates",
        "check_for_updates",
        "convert_to_pdf",
        "export_kb",
        "generate_category_report",
        "generate_role_graph",
        "install_ffmpeg",
        "integrate_knowledge",
        "manual_content_merger",
        "monitor_service",
        "processed_videos_tracker",
        "security",
        "services",
        "validate_config",
        # Módulos bajo 'modules/'
        "modules.check_updates",
        "modules.convert_to_pdf",
        "modules.dashboard",
        "modules.export_kb",
        "modules.integrate_knowledge",
        "modules.manual_analyzer",
        "modules.security",
        # Terceros opcionales (no abortar si no están instalados)
        "markdown",
        "markdown2",
        "flask",
        "flask.json",
        "openai",
        "google.generativeai",
        "weasyprint",
        "graphviz",
        "PIL",
        "PIL.Image",
    ])

    # ── Paquetes de los que se necesitan todos sus datos de runtime ───────────
    collect_all: list[str] = field(default_factory=lambda: [
        "sv_ttk",
        "matplotlib",
    ])

    # ── Archivos/carpetas de datos de la app a incluir en el bundle ───────────
    # Formato: (origen_relativo_a_base_dir, destino_dentro_del_exe)
    data_files: list[tuple[str, str]] = field(default_factory=lambda: [
        ("app/ui",         "app/ui"),
        ("app/core",       "app/core"),
        ("app/database",   "app/database"),
        ("app/services",   "app/services"),
        ("modules",        "modules"),
        ("assets",         "assets"),
    ])

    # ── Excluir módulos pesados que nunca se usan en runtime ──────────────────
    excludes: list[str] = field(default_factory=lambda: [
        "pytest",
        "sphinx",
        "black",
        "mypy",
        "ruff",
        "ipython",
        "jupyter",
        "notebook",
        "unittest",
        "doctest",
        "pdb",
        "test",
        "tests",
        "xmlrunner",
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Resultado de una operación (patrón Result / Either)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Result:
    ok: bool
    message: str
    detail: str = ""

    @staticmethod
    def success(message: str) -> "Result":
        return Result(ok=True, message=message)

    @staticmethod
    def failure(message: str, detail: str = "") -> "Result":
        return Result(ok=False, message=message, detail=detail)


# ─────────────────────────────────────────────────────────────────────────────
# Paso 1 — Verificación del entorno
# ─────────────────────────────────────────────────────────────────────────────

def verify_environment(cfg: BuildConfig, base_dir: Path) -> Result:
    """
    Comprueba que el entorno de Python y el proyecto sean válidos
    antes de empezar a construir.
    """
    # Python mínimo
    if sys.version_info < (3, 9):
        return Result.failure(
            f"Python 3.9+ requerido, se detectó {sys.version}",
            "Actualiza tu instalación de Python."
        )

    # Script de entrada
    entry = base_dir / cfg.entry_point
    if not entry.exists():
        return Result.failure(
            f"Archivo de entrada no encontrado: {entry}",
            "Asegúrate de ejecutar build_exe.py desde la raíz del proyecto."
        )

    # PyInstaller disponible
    if importlib.util.find_spec("PyInstaller") is None:
        return Result.failure(
            "PyInstaller no está instalado.",
            f"Ejecuta: {sys.executable} -m pip install pyinstaller>=6.0"
        )

    log.info("Entorno verificado — Python %s.%s.%s", *sys.version_info[:3])
    return Result.success("Entorno OK")


# ─────────────────────────────────────────────────────────────────────────────
# Paso 2 — Verificación / instalación de dependencias
# ─────────────────────────────────────────────────────────────────────────────

def _package_installed(spec: str) -> bool:
    """Devuelve True si el paquete que satisface `spec` ya está instalado."""
    # Extraer nombre base (sin operadores de versión)
    name = spec.split("=")[0].split(">")[0].split("<")[0].split("!")[0].strip()
    # pip show es más fiable que importlib para nombres con guiones vs. guiones bajos
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", name],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return False
    # Verificar versión si está especificada (comprobación básica de ==)
    if "==" in spec:
        required_version = spec.split("==")[1].strip()
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                installed = line.split(":", 1)[1].strip()
                return installed == required_version
    return True


def ensure_dependencies(cfg: BuildConfig) -> Result:
    """
    Instala solo los paquetes que faltan o tienen versión incorrecta.
    No toca paquetes que ya cumplen los requisitos.
    """
    to_install = []
    for spec in cfg.required_packages:
        if _package_installed(spec):
            log.info("  ✓ %-35s ya instalado", spec)
        else:
            log.warning("  ✗ %-35s FALTANTE → se instalará", spec)
            to_install.append(spec)

    if not to_install:
        log.info("Todas las dependencias satisfechas.")
        return Result.success("Dependencias OK")

    log.info("Instalando %d paquete(s)...", len(to_install))
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade"] + to_install,
        capture_output=False,   # mostrar output en tiempo real
    )
    if proc.returncode != 0:
        return Result.failure(
            "Falló la instalación de dependencias.",
            f"Paquetes problemáticos: {to_install}"
        )

    log.info("Dependencias instaladas correctamente.")
    return Result.success("Dependencias instaladas")


# ─────────────────────────────────────────────────────────────────────────────
# Paso 3 — Limpieza de artefactos anteriores
# ─────────────────────────────────────────────────────────────────────────────

def clean_artifacts(base_dir: Path, cfg: BuildConfig) -> Result:
    """
    Elimina directorios 'build/', 'dist/' y el archivo .spec anterior.
    Garantiza que el build parte de cero sin basura acumulada.
    """
    targets = [
        base_dir / "build",
        base_dir / "dist",
        base_dir / f"{cfg.app_name}.spec",
    ]
    for target in targets:
        if target.exists():
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                    log.info("  Eliminado directorio: %s", target)
                else:
                    target.unlink()
                    log.info("  Eliminado archivo:    %s", target)
            except OSError as exc:
                return Result.failure(
                    f"No se pudo limpiar: {target}",
                    str(exc)
                )
    return Result.success("Limpieza completada")


# ─────────────────────────────────────────────────────────────────────────────
# Paso 4 — Construcción del ejecutable
# ─────────────────────────────────────────────────────────────────────────────

def _find_tcl_tk_data() -> list[tuple[Path, str]]:
    """
    Localiza los directorios de datos de Tcl y Tk en el entorno Python actual.

    Problema que resuelve:
        PyInstaller no siempre copia los datos de Tcl/Tk al bundle, lo que
        produce en runtime:
            FileNotFoundError: Tcl data directory "..._internal/tcl_data" not found.
        Esto ocurre especialmente en Windows con instalaciones de python.org
        o con entornos virtuales.

    Estrategia de búsqueda (en orden de fiabilidad):
        1. Variables de entorno TCL_LIBRARY / TK_LIBRARY (más explícito)
        2. Atributos del interprete Tcl embebido en tkinter (_fix_paths)
        3. Rutas convencionales relativas a sys.prefix
        4. Busqueda junto a la DLL de Python (Windows)

    Retorna lista de (ruta_origen, nombre_destino_en_bundle).
    Lista vacia si no se puede determinar (no fatal; se loguea warning).
    """
    import tkinter as tk

    candidates: list[tuple[Path, str]] = []

    def _add_if_valid(path_str: "str | None", dest: str) -> bool:
        if not path_str:
            return False
        p = Path(path_str)
        if p.is_dir():
            candidates.append((p, dest))
            log.info("  Tcl/Tk encontrado: %s -> %s", p, dest)
            return True
        return False

    # Estrategia 1: variables de entorno (mas explicito, el usuario puede forzarlas)
    _add_if_valid(os.environ.get("TCL_LIBRARY"), "tcl_data")
    _add_if_valid(os.environ.get("TK_LIBRARY"),  "tk_data")
    if len(candidates) == 2:
        return candidates

    # Estrategia 2: preguntar al interprete Tcl embebido en tkinter
    try:
        root = tk.Tk()
        root.withdraw()
        tcl_lib = root.tk.exprstring("$tcl_library")
        tk_lib  = root.tk.exprstring("$tk_library")
        root.destroy()
        _add_if_valid(tcl_lib, "tcl_data")
        _add_if_valid(tk_lib,  "tk_data")
        if len(candidates) == 2:
            return candidates
    except Exception as exc:
        log.debug("Estrategia 2 (Tcl/Tk via tkinter) fallo: %s", exc)

    # Estrategia 3: rutas convencionales relativas a sys.prefix
    prefix = Path(sys.prefix)
    found_tcl = any(d == "tcl_data" for _, d in candidates)
    found_tk  = any(d == "tk_data"  for _, d in candidates)
    conventional = [
        # Windows python.org
        ("tcl/tcl8.6",         "tcl_data"),
        ("tcl/tk8.6",          "tk_data"),
        ("Lib/tcl8.6",         "tcl_data"),
        ("Lib/tk8.6",          "tk_data"),
        # Linux / macOS
        ("lib/tcl8.6",         "tcl_data"),
        ("lib/tk8.6",          "tk_data"),
        # Conda
        ("Library/lib/tcl8.6", "tcl_data"),
        ("Library/lib/tk8.6",  "tk_data"),
    ]
    for rel, dest in conventional:
        if dest == "tcl_data" and found_tcl:
            continue
        if dest == "tk_data" and found_tk:
            continue
        if _add_if_valid(str(prefix / rel), dest):
            if dest == "tcl_data":
                found_tcl = True
            else:
                found_tk = True

    # Estrategia 4: buscar junto al ejecutable de Python (Windows, carpeta de DLLs)
    if sys.platform == "win32" and not (found_tcl and found_tk):
        dll_dir = Path(sys.executable).parent
        for pattern, dest in [("tcl8*", "tcl_data"), ("tk8*", "tk_data")]:
            if (dest == "tcl_data" and found_tcl) or (dest == "tk_data" and found_tk):
                continue
            for match in dll_dir.glob(pattern):
                if match.is_dir() and _add_if_valid(str(match), dest):
                    break

    if not candidates:
        log.warning(
            "No se encontraron datos de Tcl/Tk. "
            "El ejecutable puede fallar con: "
            "FileNotFoundError: Tcl data directory not found. "
            "Solucion: define TCL_LIBRARY y TK_LIBRARY antes de ejecutar el build. "
            "Ejemplo (Windows): "
            "set TCL_LIBRARY=C:\\Python312\\tcl\\tcl8.6 | "
            "set TK_LIBRARY=C:\\Python312\\tcl\\tk8.6"
        )

    return candidates


def _build_add_data_args(cfg: BuildConfig, base_dir: Path) -> list[str]:
    """
    Construye los argumentos --add-data para:
      1. Archivos de la app definidos en BuildConfig.data_files
      2. Datos de Tcl/Tk detectados automaticamente

    Solo incluye rutas que existen en disco; omite las demas silenciosamente.
    """
    sep = ";" if sys.platform == "win32" else ":"
    args = []

    # Datos de la app
    for src_rel, dst in cfg.data_files:
        src = base_dir / src_rel
        if src.exists():
            args.append(f"--add-data={src}{sep}{dst}")
            log.debug("  + app data: %s -> %s", src_rel, dst)
        else:
            log.debug("  - omitido (no existe): %s", src_rel)

    # Datos de Tcl/Tk (critico para tkinter en Windows)
    log.info("Localizando datos de Tcl/Tk...")
    for tcl_src, tcl_dst in _find_tcl_tk_data():
        args.append(f"--add-data={tcl_src}{sep}{tcl_dst}")

    return args


def build_executable(
    cfg: BuildConfig,
    base_dir: Path,
    onefile: bool = False,
    debug: bool = False,
) -> Result:
    """
    Invoca PyInstaller con los parámetros construidos a partir de BuildConfig.
    """
    import PyInstaller.__main__ as pyi

    dist_path = base_dir / "dist"
    work_path = base_dir / "build"
    entry     = base_dir / cfg.entry_point

    # ── Argumentos base ───────────────────────────────────────────────────────
    args: list[str] = [
        str(entry),
        f"--name={cfg.app_name}",
        f"--distpath={dist_path}",
        f"--workpath={work_path}",
        f"--specpath={base_dir}",
        "--noupx",          # UPX puede disparar falsos positivos en antivirus
        "--clean",
        "--noconfirm",
    ]

    # ── Modo: onefile vs onedir ───────────────────────────────────────────────
    if onefile:
        args.append("--onefile")
        log.info("Modo: --onefile (un solo .exe, inicio más lento)")
    else:
        args.append("--onedir")
        log.info("Modo: --onedir (carpeta con dependencias, inicio más rápido)")

    # ── Consola / ventana ─────────────────────────────────────────────────────
    if debug:
        args.append("--console")
        args.append("--log-level=DEBUG")
        log.info("Modo debug: consola activada")
    else:
        args.append("--windowed")
        args.append("--log-level=WARN")

    # ── Ícono ─────────────────────────────────────────────────────────────────
    icon_path = base_dir / cfg.icon_file
    if icon_path.exists():
        args.append(f"--icon={icon_path}")
        log.info("Ícono: %s", icon_path)
    else:
        log.warning("Ícono no encontrado (%s) — se usará el ícono por defecto", icon_path)

    # ── Hidden imports ────────────────────────────────────────────────────────
    for mod in cfg.hidden_imports:
        args.append(f"--hidden-import={mod}")

    # ── Collect-all ───────────────────────────────────────────────────────────
    for pkg in cfg.collect_all:
        args.append(f"--collect-all={pkg}")

    # ── Datos de la app ───────────────────────────────────────────────────────
    args.extend(_build_add_data_args(cfg, base_dir))

    # ── Excludes ─────────────────────────────────────────────────────────────
    for exc in cfg.excludes:
        args.append(f"--exclude-module={exc}")

    # ── Versión info en Windows ───────────────────────────────────────────────
    version_file = base_dir / "version_info.txt"
    if version_file.exists():
        args.append(f"--version-file={version_file}")

    # ── Ejecutar PyInstaller ──────────────────────────────────────────────────
    log.info("Lanzando PyInstaller con %d argumentos...", len(args))
    try:
        pyi.run(args)
    except SystemExit as exc:
        # PyInstaller usa sys.exit() para reportar errores
        if exc.code != 0:
            return Result.failure(
                f"PyInstaller terminó con código de error: {exc.code}",
                "Revisa el log anterior para más detalles."
            )

    # ── Verificar que el artefacto fue generado ───────────────────────────────
    if onefile:
        exe_name = cfg.app_name + (".exe" if sys.platform == "win32" else "")
        artifact = dist_path / exe_name
    else:
        artifact = dist_path / cfg.app_name

    if not artifact.exists():
        return Result.failure(
            "PyInstaller no generó el artefacto esperado.",
            f"Buscado en: {artifact}"
        )

    size_mb = _dir_size_mb(artifact) if artifact.is_dir() else artifact.stat().st_size / 1e6
    log.info("Artefacto generado: %s (%.1f MB)", artifact, size_mb)
    return Result.success(str(artifact))


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────

def _dir_size_mb(path: Path) -> float:
    """Calcula el tamaño total de un directorio en MB."""
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6


def _print_summary(steps: list[tuple[str, Result]], elapsed: float) -> None:
    """Imprime un resumen tabulado de todos los pasos del build."""
    print()
    print("=" * 60)
    print("  RESUMEN DEL BUILD")
    print("=" * 60)
    all_ok = True
    for step_name, result in steps:
        icon = "✅" if result.ok else "❌"
        print(f"  {icon}  {step_name:<38} {result.message}")
        if not result.ok and result.detail:
            print(f"       {'':38} → {result.detail}")
        if not result.ok:
            all_ok = False
    print("-" * 60)
    print(f"  Tiempo total: {elapsed:.1f}s")
    if all_ok:
        print("  Estado: BUILD EXITOSO")
    else:
        print("  Estado: BUILD FALLIDO")
    print("=" * 60)
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Orquestador principal
# ─────────────────────────────────────────────────────────────────────────────

def run_build(
    onefile: bool = False,
    debug: bool = False,
    skip_deps: bool = False,
    clean_only: bool = False,
) -> int:
    """
    Orquesta los pasos del build en orden.
    Retorna 0 en éxito, 1 en fallo.
    Principio: cada paso recibe solo lo que necesita y devuelve un Result.
    Si un paso crítico falla, se aborta inmediatamente (fail-fast).
    """
    t_start = time.monotonic()
    base_dir = Path(__file__).resolve().parent
    cfg = BuildConfig()
    steps: list[tuple[str, Result]] = []

    print()
    print("=" * 60)
    print(f"  KDP MASTER SUITE — Builder v{cfg.app_version}")
    print(f"  Python  : {sys.version.split()[0]}")
    print(f"  Base    : {base_dir}")
    print(f"  Modo    : {'onefile' if onefile else 'onedir'}"
          + (" + debug" if debug else ""))
    print("=" * 60)
    print()

    # ── Paso 1: verificar entorno ────────────────────────────────────────────
    log.info("▶ Paso 1/4 — Verificando entorno...")
    r = verify_environment(cfg, base_dir)
    steps.append(("Verificación de entorno", r))
    if not r.ok:
        log.error(r.message)
        if r.detail:
            log.error(r.detail)
        _print_summary(steps, time.monotonic() - t_start)
        return 1

    # ── Paso 2: limpiar artefactos anteriores ────────────────────────────────
    log.info("▶ Paso 2/4 — Limpiando artefactos anteriores...")
    r = clean_artifacts(base_dir, cfg)
    steps.append(("Limpieza de artefactos", r))
    if not r.ok:
        log.error(r.message)
        _print_summary(steps, time.monotonic() - t_start)
        return 1

    if clean_only:
        log.info("--clean-only: build omitido.")
        _print_summary(steps, time.monotonic() - t_start)
        return 0

    # ── Paso 3: dependencias ─────────────────────────────────────────────────
    if skip_deps:
        log.info("▶ Paso 3/4 — Dependencias omitidas (--skip-deps)")
        steps.append(("Verificación de dependencias", Result.success("omitido")))
    else:
        log.info("▶ Paso 3/4 — Verificando dependencias...")
        r = ensure_dependencies(cfg)
        steps.append(("Verificación de dependencias", r))
        if not r.ok:
            log.error(r.message)
            if r.detail:
                log.error(r.detail)
            _print_summary(steps, time.monotonic() - t_start)
            return 1

    # ── Paso 4: compilar ─────────────────────────────────────────────────────
    log.info("▶ Paso 4/4 — Construyendo ejecutable...")
    r = build_executable(cfg, base_dir, onefile=onefile, debug=debug)
    steps.append(("Construcción del ejecutable", r))
    if not r.ok:
        log.error(r.message)
        if r.detail:
            log.error(r.detail)
        _print_summary(steps, time.monotonic() - t_start)
        return 1

    # ── Éxito ────────────────────────────────────────────────────────────────
    dist_path = base_dir / "dist"
    log.info("Ejecutable listo en: %s", dist_path)
    _print_summary(steps, time.monotonic() - t_start)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Entry point con CLI
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="KDP Master Suite — Build Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Genera un único .exe (inicio más lento por descompresión).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activa consola y log verbose de PyInstaller.",
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Omite la verificación/instalación de dependencias.",
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Solo elimina artefactos anteriores y sale.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run_build(
        onefile=args.onefile,
        debug=args.debug,
        skip_deps=args.skip_deps,
        clean_only=args.clean_only,
    ))