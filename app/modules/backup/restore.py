#!/usr/bin/env python3
"""
Restore Script - Recovery
Recuperación desde backups
"""
import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(".").resolve()
BACKUP_DIR = PROJECT_ROOT / "backups"


class RestoreManager:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
    
    def list_backups(self):
        """Lista backups disponibles"""
        print("=" * 60)
        print(" BACKUPS DISPONIBLES")
        print("=" * 60)
        
        if not self.backup_dir.exists():
            print(" No hay directorio de backups")
            return []
        
        backups = sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not backups:
            print("No hay backups disponibles")
            return []
        
        for i, backup in enumerate(backups, 1):
            manifest_file = backup / "manifest.json"
            size_mb = sum(f.stat().st_size for f in backup.rglob("*") if f.is_file()) / 1024 / 1024
            
            print(f"\n{i}.  {backup.name}")
            print(f"   Tamaño: {size_mb:.1f} MB")
            
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    print(f"   Archivos: {manifest.get('included_files', 'N/A')}")
                    print(f"   Fecha: {manifest.get('timestamp', 'N/A')}")
        
        return backups
    
    def select_backup(self, index=None):
        """Selecciona backup por índice"""
        backups = self.list_backups()
        
        if not backups:
            return None
        
        if index is None:
            # Default: most recent
            return backups[0]
        
        try:
            return backups[index - 1]
        except IndexError:
            print(f" Índice inválido. Rango: 1-{len(backups)}")
            return None
    
    def restore(self, backup_path=None, dry_run=False):
        """Restaura desde backup"""
        if backup_path is None:
            backup_path = self.select_backup()
            if backup_path is None:
                return False
        
        print(f"\n Restaurando desde: {backup_path.name}")
        
        if dry_run:
            print(" MODO DRY-RUN (sin cambios)")
        
        # Get manifest
        manifest_file = backup_path / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
                print(f"   Archivos a restaurar: {manifest.get('included_files', 'N/A')}")
        
        # Restore each item
        restored = []
        errors = []
        
        for item in backup_path.iterdir():
            if item.name == "manifest.json":
                continue
            
            dest = PROJECT_ROOT / item.name
            
            try:
                if not dry_run:
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
                
                restored.append(item.name)
                
            except Exception as e:
                errors.append(f"{item.name}: {e}")
        
        print(f"\n Restauración completada")
        print(f"   Restaurados: {len(restored)}")
        
        if errors:
            print(f"   Errores: {len(errors)}")
            for e in errors:
                print(f"     - {e}")
        
        if dry_run:
            print("\n DRY-RUN completado. No se hicieron cambios.")
        
        return len(errors) == 0
    
    def restore_specific(self, backup_name, items=None):
        """Restaura items específicos"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            print(f" Backup no encontrado: {backup_name}")
            return False
        
        print(f" Restaurando items específicos de: {backup_name}")
        
        if items is None:
            return self.restore(backup_path)
        
        for item_name in items:
            source = backup_path / item_name
            dest = PROJECT_ROOT / item_name
            
            if not source.exists():
                print(f"  ! No encontrado: {item_name}")
                continue
            
            try:
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                
                shutil.copytree(source, dest) if source.is_dir() else shutil.copy2(source, dest)
                print(f"   {item_name}")
                
            except Exception as e:
                print(f"   {item_name}: {e}")
        
        return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore Manager")
    parser.add_argument("--list", action="store_true", help="Listar backups")
    parser.add_argument("--restore", type=int, nargs="?", const=1, help="Restaurar backup (índice)")
    parser.add_argument("--latest", action="store_true", help="Restaurar más reciente")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulación")
    parser.add_argument("--name", type=str, help="Restaurar por nombre de backup")
    
    args = parser.parse_args()
    
    manager = RestoreManager()
    
    if args.list:
        manager.list_backups()
    elif args.restore:
        manager.restore(dry_run=args.dry_run)
    elif args.latest:
        manager.restore(dry_run=args.dry_run)
    elif args.name:
        manager.restore_specific(args.name)
    else:
        print("Usa: --list, --restore, --latest, o --name")