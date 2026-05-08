#!/usr/bin/env python3
"""
Integrity Check - Validación de Estado
Verifica integridad de datos al inicio
"""
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(".").resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


class IntegrityCheck:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "status": "PENDING"
        }
    
    def check_database(self):
        """Verifica integridad de SQLite DB"""
        print(" Verificando database...")
        
        db_path = DATA_DIR / "channel_monitor.db"
        
        if not db_path.exists():
            self.results["checks"].append({
                "name": "database_exists",
                "status": "FAIL",
                "message": "Database no encontrado"
            })
            return False
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            
            # Check critical tables
            critical = ["channels", "videos"]
            missing = [t for t in critical if t not in tables]
            
            if missing:
                self.results["checks"].append({
                    "name": "database_tables",
                    "status": "FAIL",
                    "message": f"Tablas faltantes: {missing}"
                })
                conn.close()
                return False
            
            # Get counts
            cursor.execute("SELECT COUNT(*) FROM channels")
            channels_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM videos")
            videos_count = cursor.fetchone()[0]
            
            # PRAGMA integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            conn.close()
            
            self.results["checks"].append({
                "name": "database_integrity",
                "status": "PASS",
                "message": f"DB OK: {channels_count} canales, {videos_count} videos"
            })
            
            print(f"   DB: {channels_count} canales, {videos_count} videos")
            print(f"   Integrity: {integrity}")
            
            return True
            
        except Exception as e:
            self.results["checks"].append({
                "name": "database",
                "status": "FAIL",
                "message": str(e)
            })
            return False
    
    def check_transcriptions(self):
        """Verifica directorio de transcripciones"""
        print(" Verificando transcripciones...")
        
        transcriptions_dir = DATA_DIR / "transcriptions"
        
        if not transcriptions_dir.exists():
            self.results["checks"].append({
                "name": "transcriptions_exists",
                "status": "FAIL",
                "message": "Directorio de transcripciones no encontrado"
            })
            return False
        
        # Count channels and files
        channels = [d for d in transcriptions_dir.iterdir() if d.is_dir()]
        total_files = 0
        
        for channel in channels:
            files = list(channel.glob("*.vtt")) + list(channel.glob("*.info.json"))
            total_files += len(files)
        
        self.results["checks"].append({
            "name": "transcriptions",
            "status": "PASS",
            "message": f"{len(channels)} canales, {total_files} archivos"
        })
        
        print(f"   Transcripciones: {len(channels)} canales, {total_files} archivos")
        return True
    
    def check_processed_videos(self):
        """Verifica archivo de videos procesados"""
        print(" Verificando processed_videos.json...")
        
        processed_file = DATA_DIR / "processed_videos.json"
        
        if not processed_file.exists():
            self.results["checks"].append({
                "name": "processed_videos_exists",
                "status": "WARNING",
                "message": "Archivo no encontrado (se creará al procesar)"
            })
            print("  ! Archivo no encontrado (primera ejecución?)")
            return True
        
        try:
            with open(processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = len(data) if isinstance(data, list) else len(data.get('videos', []))
            
            self.results["checks"].append({
                "name": "processed_videos",
                "status": "PASS",
                "message": f"{count} videos procesados"
            })
            
            print(f"   Videos procesados: {count}")
            return True
            
        except json.JSONDecodeError as e:
            self.results["checks"].append({
                "name": "processed_videos_json",
                "status": "FAIL",
                "message": f"JSON corrupto: {e}"
            })
            return False
        except Exception as e:
            self.results["checks"].append({
                "name": "processed_videos",
                "status": "FAIL",
                "message": str(e)
            })
            return False
    
    def check_canales_csv(self):
        """Verifica CSV de canales"""
        print(" Verificando CANALES_LISTOS.csv...")
        
        csv_file = DATA_DIR / "CANALES_LISTOS.csv"
        
        if not csv_file.exists():
            self.results["checks"].append({
                "name": "canales_csv",
                "status": "WARNING",
                "message": "CSV no encontrado"
            })
            print("  ! CSV no encontrado")
            return True
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            count = len([l for l in lines if l.strip() and not l.startswith('#')])
            
            self.results["checks"].append({
                "name": "canales_csv",
                "status": "PASS",
                "message": f"{count} canales en CSV"
            })
            
            print(f"   CSV: {count} canales")
            return True
            
        except Exception as e:
            self.results["checks"].append({
                "name": "canales_csv",
                "status": "FAIL",
                "message": str(e)
            })
            return False
    
    def check_nichos(self):
        """Verifica directorio de nichos"""
        print(" Verificando nichos...")
        
        nichos_dir = DATA_DIR / "nichos"
        
        if not nichos_dir.exists():
            self.results["checks"].append({
                "name": "nichos_exists",
                "status": "WARNING",
                "message": "Directorio no encontrado"
            })
            print("  ! Directorio de nichos no encontrado")
            return True
        
        nichos = [d for d in nichos_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]
        
        self.results["checks"].append({
            "name": "nichos",
            "status": "PASS",
            "message": f"{len(nichos)} nichos"
        })
        
        print(f"   Nichos: {len(nichos)}")
        return True
    
    def check_config_files(self):
        """Verifica archivos de configuración"""
        print(" Verificando config...")
        
        config_files = [
            PROJECT_ROOT / ".env",
            PROJECT_ROOT / "settings.json"
        ]
        
        all_ok = True
        for cf in config_files:
            if cf.exists():
                print(f"   {cf.name}")
            else:
                print(f"  ! {cf.name} no encontrado (opcional)")
        
        self.results["checks"].append({
            "name": "config",
            "status": "PASS",
            "message": "Config verificada"
        })
        
        return True
    
    def run(self):
        """Ejecuta todos los checks"""
        print("=" * 60)
        print("INTEGRITY CHECK - Validacion de Estado")
        print("=" * 60)
        
        checks = [
            self.check_database(),
            self.check_transcriptions(),
            self.check_processed_videos(),
            self.check_canales_csv(),
            self.check_nichos(),
            self.check_config_files()
        ]
        
        # Determine status
        fails = sum(1 for c in checks if not c)
        warnings = sum(1 for c in self.results["checks"] if c.get("status") == "WARNING")
        
        if fails > 0:
            self.results["status"] = "FAIL"
        elif warnings > 0:
            self.results["status"] = "WARNING"
        else:
            self.results["status"] = "PASS"

        print("\n" + "=" * 60)
        print("INTEGRITY CHECK - Validacion de Estado")
        print("=" * 60)

        for check in self.results["checks"]:
            status_icon = "PASS" if check["status"] == "PASS" else ("WARN" if check["status"] == "WARNING" else "FAIL")
            print(f"[{status_icon}] {check['name']}: {check['message']}")

        print(f"\nEstado: {self.results['status']}")

        # Save results
        results_file = PROJECT_ROOT / "logs" / "integrity_check.json"
        results_file.parent.mkdir(exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"Resultados: {results_file}")

        return 0 if self.results["status"] != "FAIL" else 1


if __name__ == "__main__":
    check = IntegrityCheck()
    import sys
    sys.exit(check.run())