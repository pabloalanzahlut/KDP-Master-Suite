#!/usr/bin/env python3
"""
Build Pipeline - CI/CD
Build centralizado con versionado y checksum
"""
import os
import sys
import shutil
import hashlib
import subprocess
import shlex
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(".").resolve()
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
SPEC_FILE = PROJECT_ROOT / "KDP_Master_Suite_v3.4.7.spec"
VERSION_FILE = PROJECT_ROOT / "VERSION.txt"


class BuildPipeline:
    def __init__(self, clean_first=False, extra_pyinstaller_args=""):
        self.clean_first = clean_first
        self.extra_pyinstaller_args = shlex.split(extra_pyinstaller_args, posix=(os.name != 'nt')) if extra_pyinstaller_args else []
        self.build_info = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version.split()[0],
            "steps": [],
            "artifacts": [],
            "status": "PENDING"
        }
    
    def load_version(self):
        """Carga o genera version"""
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text().strip()
        
        version = datetime.now().strftime("%Y.%m.%d")
        VERSION_FILE.write_text(version)
        return version
    
    def clean_build_dirs(self):
        """Limpia directorios de build"""
        print(" Limpiando directorios de build...")
        
        dirs_to_clean = [BUILD_DIR, DIST_DIR, PROJECT_ROOT / "__pycache__"]
        
        for d in dirs_to_clean:
            if d.exists():
                shutil.rmtree(d)
                print(f"   Eliminado: {d}")
        
        # Clean pycache recursively
        for root, dirs, files in os.walk(PROJECT_ROOT):
            if "__pycache__" in dirs:
                pycache = Path(root) / "__pycache__"
                shutil.rmtree(pycache)
        
        self.build_info["steps"].append({"step": "clean", "status": "SUCCESS"})
        print(" Limpieza completada")
    
    def run_pyinstaller(self):
        """Ejecuta PyInstaller"""
        print(" Ejecutando PyInstaller...")
        
        if not SPEC_FILE.exists():
            print(f" SPEC file no encontrado: {SPEC_FILE}")
            self.build_info["steps"].append({"step": "pyinstaller", "status": "FAIL", "error": "SPEC not found"})
            return False
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(SPEC_FILE),
            "--clean",
            "--noconfirm"
        ]
        cmd.extend(self.extra_pyinstaller_args)
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        
        success = result.returncode == 0
        
        if success:
            self.build_info["steps"].append({"step": "pyinstaller", "status": "SUCCESS"})
            print(" PyInstaller completado")
        else:
            self.build_info["steps"].append({"step": "pyinstaller", "status": "FAIL", "error": result.stderr[-500:]})
            print(f" PyInstaller falló: {result.stderr[-300:]}")
        
        return success
    
    def find_artifacts(self):
        """Encuentra artefactos generados"""
        print(" Localizando artefactos...")
        
        artifacts = []
        
        # Find exe
        exe_paths = list(DIST_DIR.rglob("*.exe"))
        for exe in exe_paths:
            size = exe.stat().st_size
            artifacts.append({
                "type": "exe",
                "path": str(exe.relative_to(PROJECT_ROOT)),
                "size_bytes": size,
                "size_mb": round(size / 1024 / 1024, 2)
            })
            print(f"   {exe.name} ({artifacts[-1]['size_mb']} MB)")
        
        # Find main exe
        main_exe = DIST_DIR / "KDP_Transcriptions" / "KDP_Transcriptions.exe"
        if main_exe.exists():
            self.build_info["main_exe"] = str(main_exe.relative_to(PROJECT_ROOT))
        
        self.build_info["artifacts"] = artifacts
        return len(artifacts) > 0
    
    def generate_checksum(self):
        """Genera checksum SHA256"""
        print(" Generando checksums...")
        
        checksums = []
        
        for artifact in self.build_info["artifacts"]:
            if artifact["type"] == "exe":
                path = PROJECT_ROOT / artifact["path"]
                if path.exists():
                    sha256 = hashlib.sha256()
                    with open(path, 'rb') as f:
                        for chunk in iter(lambda: f.read(8192), b''):
                            sha256.update(chunk)
                    
                    checksum_file = path.with_suffix('.sha256')
                    checksum_file.write_text(sha256.hexdigest())
                    
                    artifact["sha256"] = sha256.hexdigest()
                    checksums.append({"file": artifact["path"], "sha256": sha256.hexdigest()[:16] + "..."})
                    print(f"   {artifact['path']}: {checksums[-1]['sha256']}")
        
        return checksums
    
    def save_build_info(self):
        """Guarda información del build"""
        info_file = PROJECT_ROOT / "build_info.json"
        
        self.build_info["version"] = self.load_version()
        self.build_info["status"] = "SUCCESS"
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(self.build_info, f, indent=2)
        
        print(f"\n Build info: {info_file}")
    
    def run(self):
        """Ejecuta el pipeline completo"""
        version = self.load_version()
        print("=" * 60)
        print(f" BUILD PIPELINE - KDP Master Suite v{version}")
        print("=" * 60)
        
        if self.clean_first:
            self.clean_build_dirs()
        
        if not self.run_pyinstaller():
            self.build_info["status"] = "FAIL"
            self.save_build_info()
            return 1
        
        if not self.find_artifacts():
            print(" No se encontraron artefactos")
            self.build_info["status"] = "FAIL"
            self.save_build_info()
            return 1
        
        self.generate_checksum()
        self.save_build_info()
        
        print("\n" + "=" * 60)
        print(" RESUMEN DEL BUILD")
        print("=" * 60)
        print(f"Versión: {version}")
        print(f"Estado:  SUCCESS")
        print(f"Artefactos: {len(self.build_info['artifacts'])}")
        for a in self.build_info['artifacts']:
            print(f"  - {a['path']} ({a['size_mb']} MB)")
        
        return 0


if __name__ == "__main__":
    pipeline = BuildPipeline(clean_first=True)
    sys.exit(pipeline.run())