#!/usr/bin/env python3
"""
Backup Manager - Persistencia
Backup incremental con rotación
"""
import os
import shutil
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(".").resolve()
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "backups"
CONFIG_FILE = PROJECT_ROOT / "tools" / "backup" / "backup_config.json"


class BackupManager:
    def __init__(self, max_backups=10):
        self.max_backups = max_backups
        self.config = self._load_config()
    
    def _load_config(self):
        """Carga configuración de backup"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        
        return {
            "max_backups": 10,
            "include_dirs": ["data", "themes"],
            "exclude_patterns": ["__pycache__", "*.pyc", ".git", "*.zip"],
            "last_backup": None
        }
    
    def _save_config(self):
        """Guarda configuración"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def generate_backup_name(self):
        """Genera nombre de backup"""
        return f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def calculate_hash(self, file_path):
        """Calcula hash de archivo"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def backup_data(self):
        """Ejecuta backup incremental"""
        print("=" * 60)
        print(" BACKUP MANAGER - Persistencia")
        print("=" * 60)
        
        BACKUP_DIR.mkdir(exist_ok=True)
        
        backup_name = self.generate_backup_name()
        backup_path = BACKUP_DIR / backup_name
        
        print(f" Creando backup: {backup_name}")
        
        included_files = []
        skipped_files = []
        
        for include_dir in self.config.get("include_dirs", []):
            source = PROJECT_ROOT / include_dir
            
            if not source.exists():
                print(f"  ! Directorio no existe: {include_dir}")
                continue
            
            dest = backup_path / include_dir
            dest.mkdir(parents=True, exist_ok=True)
            
            for root, dirs, files in os.walk(source):
                # Filter excluded patterns
                dirs[:] = [d for d in dirs if not any(p in d for p in self.config.get("exclude_patterns", []))]
                
                for file in files:
                    if any(p in file for p in self.config.get("exclude_patterns", [])):
                        continue
                    
                    src_file = Path(root) / file
                    rel_path = src_file.relative_to(PROJECT_ROOT)
                    dst_file = backup_path / rel_path
                    
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(src_file, dst_file)
                        included_files.append(str(rel_path))
                    except Exception as e:
                        skipped_files.append(str(rel_path))
        
        # Generate manifest
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "backup_name": backup_name,
            "included_files": len(included_files),
            "skipped_files": len(skipped_files),
            "file_list": included_files[:100]  # First 100 for brevity
        }
        
        manifest_file = backup_path / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Rotación de backups
        self._rotate_backups()
        
        self.config["last_backup"] = datetime.now().isoformat()
        self._save_config()
        
        print(f"\n Backup completado: {len(included_files)} archivos")
        print(f" Ubicación: {backup_path}")
        
        return True
    
    def _rotate_backups(self):
        """Rota backups manteniendo solo N"""
        if not BACKUP_DIR.exists():
            return

        # Only include directories, not .zip files
        backups = sorted([d for d in BACKUP_DIR.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)

        if len(backups) > self.max_backups:
            to_delete = backups[self.max_backups:]

            print(f" Eliminando {len(to_delete)} backups antiguos...")

            for backup in to_delete:
                shutil.rmtree(backup)
                print(f"   Eliminado: {backup.name}")
    
    def list_backups(self):
        """Lista backups disponibles"""
        print("=" * 60)
        print(" BACKUPS DISPONIBLES")
        print("=" * 60)
        
        if not BACKUP_DIR.exists() or not any(BACKUP_DIR.iterdir()):
            print("No hay backups disponibles")
            return []
        
        backups = sorted(BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        
        result = []
        for backup in backups:
            manifest_file = backup / "manifest.json"
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    print(f"   {backup.name}")
                    print(f"     Archivos: {manifest.get('included_files', 'N/A')}")
                    print(f"     Fecha: {manifest.get('timestamp', 'N/A')}")
                    result.append(str(backup))
            else:
                print(f"   {backup.name} (sin manifest)")
        
        return result
    
    def restore_backup(self, backup_name=None):
        """Restaura desde backup"""
        if not BACKUP_DIR.exists():
            print(" No hay directorio de backups")
            return False
        
        if backup_name is None:
            backups = sorted(BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            if not backups:
                print(" No hay backups disponibles")
                return False
            backup_path = backups[0]
        else:
            backup_path = BACKUP_DIR / backup_name
            if not backup_path.exists():
                print(f" Backup no encontrado: {backup_name}")
                return False
        
        print(f" Restaurando desde: {backup_path.name}")
        
        for item in backup_path.iterdir():
            if item.name == "manifest.json":
                continue
            
            dest = PROJECT_ROOT / item.name
            
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        
        print(" Restauración completada")
        return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup Manager")
    parser.add_argument("--backup", action="store_true", help="Crear backup")
    parser.add_argument("--restore", type=str, nargs="?", const="latest", help="Restaurar backup")
    parser.add_argument("--list", action="store_true", help="Listar backups")
    parser.add_argument("--max", type=int, default=10, help="Máximo de backups a mantener")
    
    args = parser.parse_args()
    
    manager = BackupManager(max_backups=args.max)
    
    if args.backup:
        manager.backup_data()
    elif args.list:
        manager.list_backups()
    elif args.restore:
        manager.restore_backup(args.restore if args.restore != "latest" else None)
    else:
        print("Usa: --backup, --list, o --restore")