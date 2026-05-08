#!/usr/bin/env python3
"""
Silent Install - Packaging Enterprise
Instalador silencioso sin prompts interactivos
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(".").resolve()
DIST_DIR = PROJECT_ROOT / "dist"


class SilentInstaller:
    def __init__(self):
        self.install_path = None
    
    def detect_portable_mode(self):
        """Detecta si está en modo portable"""
        # Check for portable marker
        portable_marker = PROJECT_ROOT / "portable.marker"
        
        if portable_marker.exists():
            return True
        
        # Check if running from removable media
        try:
            drive = os.path.splitdrive(PROJECT_ROOT)[0]
            # Check if USB drive (removable)
            if drive:
                import win32api
                try:
                    drive_type = win32api.GetDriveType(drive)
                    # DRIVE_REMOVABLE = 2
                    return drive_type == 2
                except:
                    pass
        except:
            pass
        
        return False
    
    def get_install_path(self):
        """Determina path de instalación"""
        if self.detect_portable_mode():
            return PROJECT_ROOT
        
        # Default: AppData/Local/KDP_Master
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        install_path = Path(local_appdata) / "KDP_Master_Suite"
        
        return install_path
    
    def copy_files(self):
        """Copia archivos de instalación"""
        if not Dist_DIR.exists():
            print(" Directorio dist no encontrado. Ejecuta build primero.")
            return False
        
        print(f" Instalando en: {self.install_path}")
        
        self.install_path.mkdir(parents=True, exist_ok=True)
        
        # Copy dist contents
        source = Dist_DIR / "KDP_Transcriptions"
        
        if not source.exists():
            print(f" Fuente no encontrada: {source}")
            return False
        
        # Use robocopy for better handling on Windows
        try:
            cmd = ["robocopy", str(source), str(self.install_path), "/E", "/NJH", "/NJS", "/NDL", "/NFL", "/NC", "/NS", "/NP"]
            result = subprocess.run(cmd, capture_output=True)
            # robocopy returns 0-7, 0 = no copy needed, 1-7 = success
            if result.returncode > 7:
                raise Exception(f"Robocopy failed with code {result.returncode}")
        except FileNotFoundError:
            # Fallback to shutil
            shutil.copytree(source, self.install_path, dirs_exist_ok=True)
        
        print(f" Archivos copiados a {self.install_path}")
        return True
    
    def create_shortcut(self):
        """Crea shortcut en escritorio"""
        try:
            import win32com.client
            import pythoncom
            
            pythoncom.CoInitialize()
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(
                os.path.join(os.environ["USERPROFILE"], "Desktop", "KDP Master Suite.lnk")
            )
            shortcut.TargetPath = str(self.install_path / "KDP_Transcriptions.exe")
            shortcut.WorkingDirectory = str(self.install_path)
            shortcut.Description = "KDP Master Suite"
            shortcut.Save()
            
            print(" Shortcut creado en escritorio")
            return True
        except Exception as e:
            print(f"! No se pudo crear shortcut: {e}")
            return False
    
    def create_start_menu_entry(self):
        """Crea entrada en Start Menu"""
        try:
            start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            start_menu.mkdir(parents=True, exist_ok=True)
            
            # Create a simple batch file launcher
            launcher = start_menu / "KDP Master Suite.bat"
            launcher.write_text(f'@echo off\n"{self.install_path}\\KDP_Transcriptions.exe"')
            
            print(" Entrada en Start Menu creada")
            return True
        except Exception as e:
            print(f"! No se pudo crear entrada: {e}")
            return False
    
    def install(self):
        """Ejecuta instalación silenciosa"""
        print("=" * 60)
        print(" SILENT INSTALL - KDP Master Suite")
        print("=" * 60)
        
        self.install_path = self.get_install_path()
        
        print(f" Modo: {'Portable' if self.detect_portable_mode() else 'Instalado'}")
        print(f" Destino: {self.install_path}")
        
        if not self.copy_files():
            return 1
        
        # Only create shortcuts for non-portable install
        if not self.detect_portable_mode():
            self.create_shortcut()
            self.create_start_menu_entry()
        
        print("\n Instalación completada silenciosamente")
        return 0
    
    def uninstall(self):
        """Desinstalación"""
        print(" Desinstalando...")
        
        if self.install_path and self.install_path.exists():
            shutil.rmtree(self.install_path)
            print(f" Eliminado: {self.install_path}")
        
        # Remove shortcuts
        desktop_shortcut = Path(os.environ["USERPROFILE"]) / "Desktop" / "KDP Master Suite.lnk"
        if desktop_shortcut.exists():
            desktop_shortcut.unlink()
        
        print(" Desinstalación completada")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Silent Installer")
    parser.add_argument("--install", action="store_true", help="Instalar silenciosamente")
    parser.add_argument("--uninstall", action="store_true", help="Desinstalar")
    parser.add_argument("--portable", action="store_true", help="Modo portable")
    
    args = parser.parse_args()
    
    installer = SilentInstaller()
    
    if args.uninstall:
        installer.uninstall()
    elif args.install:
        sys.exit(installer.install())
    else:
        print("Usa: --install o --uninstall")