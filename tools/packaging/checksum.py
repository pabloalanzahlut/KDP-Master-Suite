#!/usr/bin/env python3
"""
Checksum Generator - Packaging
Genera SHA256 checksums para verificación
"""
import os
import hashlib
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(".").resolve()
DIST_DIR = PROJECT_ROOT / "dist"


class ChecksumGenerator:
    def __init__(self):
        self.algorithms = ["sha256", "sha512"]
    
    def calculate_hash(self, file_path, algorithm="sha256"):
        """Calcula hash de archivo"""
        if algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "sha512":
            hasher = hashlib.sha512()
        else:
            raise ValueError(f"Algorithm not supported: {algorithm}")
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def generate_checksums(self, output_format="txt"):
        """Genera checksums para el build"""
        print("=" * 60)
        print(" CHECKSUM GENERATOR")
        print("=" * 60)
        
        checksums = []
        
        # Find all .exe files
        exe_files = list(DIST_DIR.rglob("*.exe"))
        
        if not exe_files:
            print(" No se encontraron archivos .exe")
            return False
        
        print(f" Encontrados {len(exe_files)} archivos .exe")
        
        for exe in exe_files:
            print(f"\n Procesando: {exe.name}")
            
            rel_path = exe.relative_to(DIST_DIR)
            size = exe.stat().st_size
            
            checksum_data = {
                "file": str(rel_path),
                "size_bytes": size,
                "size_mb": round(size / 1024 / 1024, 2),
                "sha256": self.calculate_hash(exe, "sha256"),
                "sha512": self.calculate_hash(exe, "sha512")
            }
            
            checksums.append(checksum_data)
            
            print(f"   {rel_path}")
            print(f"   {checksum_data['size_mb']} MB")
            print(f"   SHA256: {checksum_data['sha256'][:16]}...")
        
        # Save checksums
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == "json":
            output_file = PROJECT_ROOT / f"checksums_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(checksums, f, indent=2)
        else:
            output_file = PROJECT_ROOT / f"checksums_{timestamp}.txt"
            with open(output_file, 'w') as f:
                f.write("# KDP Master Suite Checksums\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                
                for cs in checksums:
                    f.write(f"{cs['sha256']}  {cs['file']}\n")
        
        # Also save latest as convenient reference
        latest_txt = PROJECT_ROOT / "checksums_latest.txt"
        latest_json = PROJECT_ROOT / "checksums_latest.json"
        
        with open(latest_txt, 'w') as f:
            f.write("# KDP Master Suite Checksums (Latest)\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            for cs in checksums:
                f.write(f"{cs['sha256']}  {cs['file']}\n")
        
        with open(latest_json, 'w') as f:
            json.dump(checksums, f, indent=2)
        
        print(f"\n Checksums guardados:")
        print(f"   {output_file}")
        print(f"   {latest_txt} (reference)")
        
        return True
    
    def verify_checksums(self, checksum_file=None):
        """Verifica checksums contra archivo"""
        if checksum_file is None:
            checksum_file = PROJECT_ROOT / "checksums_latest.txt"
        
        if not checksum_file.exists():
            print(f" Archivo de checksums no encontrado: {checksum_file}")
            return False
        
        print(f" Verificando: {checksum_file}")
        
        with open(checksum_file, 'r') as f:
            lines = f.readlines()
        
        errors = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) < 2:
                continue
            
            expected_hash = parts[0]
            file_path = " ".join(parts[1:])
            
            full_path = DIST_DIR / file_path
            
            if not full_path.exists():
                errors.append(f"Archivo no encontrado: {file_path}")
                continue
            
            actual_hash = self.calculate_hash(full_path)
            
            if actual_hash != expected_hash:
                errors.append(f"Mismatch: {file_path}")
            else:
                print(f"   {file_path}")
        
        if errors:
            print(f"\n {len(errors)} errores:")
            for e in errors:
                print(f"  - {e}")
            return False
        
        print("\n Todos los checksums verificados")
        return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Checksum Generator")
    parser.add_argument("--generate", action="store_true", help="Generar checksums")
    parser.add_argument("--verify", action="store_true", help="Verificar checksums")
    parser.add_argument("--format", choices=["txt", "json"], default="txt", help="Formato de salida")
    
    args = parser.parse_args()
    
    generator = ChecksumGenerator()
    
    if args.generate:
        generator.generate_checksums(args.format)
    elif args.verify:
        generator.verify_checksums()
    else:
        print("Usa: --generate o --verify")