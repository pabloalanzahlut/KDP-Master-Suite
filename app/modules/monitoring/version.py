#!/usr/bin/env python3
"""
Version Manager - Semver Auto-Increment
Gestión de versionado semántico
"""
import os
import re
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(".").resolve()
VERSION_FILE = PROJECT_ROOT / "VERSION.txt"


class VersionManager:
    def __init__(self):
        self.version_file = VERSION_FILE
        self.release_notes_file = PROJECT_ROOT / "RELEASE_NOTES.md"
    
    def get_current_version(self):
        """Obtiene versión actual"""
        if self.version_file.exists():
            return self.version_file.read_text().strip()
        return "0.0.0"
    
    def parse_version(self, version):
        """Parsea version string a tuple"""
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
        if match:
            return tuple(int(x) for x in match.groups())
        return (0, 0, 0)
    
    def bump_version(self, part="patch"):
        """Incrementa version según parte"""
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        
        self.version_file.write_text(new_version)
        
        print(f" Version: {current} → {new_version}")
        
        return new_version
    
    def set_version(self, version):
        """Establece versión específica"""
        self.version_file.write_text(version)
        print(f" Version establecida: {version}")
        return version
    
    def get_version_info(self):
        """Retorna información de versión"""
        version = self.get_current_version()
        
        # Get git info if available
        git_info = {}
        try:
            git_dir = PROJECT_ROOT / ".git"
            if git_dir.exists():
                head_file = git_dir / "HEAD"
                if head_file.exists():
                    git_info["branch"] = head_file.read_text().strip().split(" ")[-1]
        except:
            pass
        
        return {
            "version": version,
            "major": self.parse_version(version)[0],
            "minor": self.parse_version(version)[1],
            "patch": self.parse_version(version)[2],
            "timestamp": datetime.now().isoformat(),
            "git": git_info
        }
    
    def tag_release(self, message=None):
        """Etiqueta release (preparado para git)"""
        version = self.get_current_version()
        
        if message is None:
            message = f"Release v{version}"
        
        # Prepara comando git tag
        tag_command = f'git tag -a v{version} -m "{message}"'
        
        print(f" Release tag: v{version}")
        print(f"   Comando: {tag_command}")
        
        return version


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Version Manager")
    parser.add_argument("--current", action="store_true", help="Ver versión actual")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default="patch", help="Incrementar versión")
    parser.add_argument("--set", type=str, help="Establecer versión específica")
    parser.add_argument("--info", action="store_true", help="Ver información completa")
    parser.add_argument("--tag", action="store_true", help="Etiquetar release")
    
    args = parser.parse_args()
    
    vm = VersionManager()
    
    if args.current:
        print(f"Versión actual: {vm.get_current_version()}")
    elif args.set:
        vm.set_version(args.set)
    elif args.info:
        import json
        print(json.dumps(vm.get_version_info(), indent=2))
    elif args.tag:
        vm.tag_release()
    else:
        vm.bump_version(args.bump)