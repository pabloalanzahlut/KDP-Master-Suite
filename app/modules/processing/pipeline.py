#!/usr/bin/env python3
"""
Pipeline Orchestrator - CI/CD Master
Orquesta todos los módulos de automatización
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


PROJECT_ROOT = Path('.').resolve()
TOOLS_DIR = PROJECT_ROOT / "tools"


class PipelineOrchestrator:
    def __init__(self) -> None:
        self.start_time = datetime.now()
        self.results: Dict[str, Any] = {
            "pipeline": "KDP_Master_CI_CD",
            "start_time": self.start_time.isoformat(),
            "steps": [],
            "status": "PENDING"
        }
        self.exit_code = 0
    
    def run_step(self, name: str, script_path: str, args: Optional[List[str]] = None) -> None:
        """Ejecuta un paso del pipeline"""
        print(f"\n{'='*60}")
        print(f"> {name}")
        print(f"{'='*60}")

        # Use absolute path and list format (no shell)
        abs_path = script_path.resolve()
        cmd = [sys.executable, str(abs_path)]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            step_result = {
                "step": name,
                "script": str(script_path),
                "exit_code": result.returncode,
                "status": "SUCCESS" if result.returncode == 0 else "FAIL",
                "output": result.stdout[-2000:] if result.stdout else ""
            }
            
            self.results["steps"].append(step_result)
            
            if result.returncode != 0:
                print(f" FALLÓ: {name}")
                print(result.stderr[-500:] if result.stderr else "")
                self.exit_code = result.returncode
                return False
            
            print(f" {name} completado")
            return True
            
        except Exception as e:
            print(f" ERROR: {name} - {e}")
            self.results["steps"].append({
                "step": name,
                "status": "ERROR",
                "error": str(e)
            })
            self.exit_code = 1
            return False
    
    def run_full_pipeline(self):
        """Ejecuta pipeline completo"""
        print("="*60)
        print(" KDP MASTER SUITE - CI/CD PIPELINE")
        print("="*60)
        print(f"Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Integrity Check
        if not self.run_step("1. Integrity Check", 
            TOOLS_DIR / "backup" / "integrity_check.py"):
            print("! Integrity check falló, continuando...")
        
        # Step 2: Run Tests
        if not self.run_step("2. Test Suite",
            TOOLS_DIR / "ci_cd" / "run_tests.py"):
            print("! Tests fallaron, continuando...")
        
        # Step 3: Run Build
        if not self.run_step("3. Build Pipeline",
            TOOLS_DIR / "ci_cd" / "run_build.py"):
            print(" Build falló, deteniendo pipeline")
            self._finish_pipeline()
            return self.exit_code
        
        # Step 4: Smoke Test
        if not self.run_step("4. Smoke Test",
            TOOLS_DIR / "ci_cd" / "smoke_test.py"):
            print("! Smoke test falló, revisando...")
        
        # Step 5: Checksum
        if not self.run_step("5. Generate Checksums",
            TOOLS_DIR / "packaging" / "checksum.py",
            ["--generate"]):
            print("! Checksum falló")
        
        # Step 6: Version Bump
        if not self.run_step("6. Version Bump",
            TOOLS_DIR / "scripts" / "version.py",
            ["--bump", "patch"]):
            print("! Version bump falló")
        
        # Step 7: Backup (optional, after successful build)
        if self.exit_code == 0:
            if not self.run_step("7. Backup",
                TOOLS_DIR / "backup" / "backup_manager.py",
                ["--backup"]):
                print("! Backup falló")
        
        self._finish_pipeline()
        
        return self.exit_code
    
    def run_quick_build(self):
        """Build rápido sin tests"""
        print("="*60)
        print(" QUICK BUILD - Sin Tests")
        print("="*60)
        
        # Step 1: Build
        if not self.run_step("Build Pipeline",
            TOOLS_DIR / "ci_cd" / "run_build.py"):
            self._finish_pipeline()
            return self.exit_code
        
        # Step 2: Smoke Test
        self.run_step("Smoke Test",
            TOOLS_DIR / "ci_cd" / "smoke_test.py")
        
        # Step 3: Checksum
        self.run_step("Generate Checksums",
            TOOLS_DIR / "packaging" / "checksum.py",
            ["--generate"])
        
        self._finish_pipeline()
        
        return self.exit_code
    
    def run_health_check(self):
        """Ejecuta health check"""
        print("="*60)
        print(" HEALTH CHECK")
        print("="*60)
        
        self.run_step("Health Check",
            TOOLS_DIR / "scripts" / "health_check.py",
            ["--check"])
        
        self._finish_pipeline()
        return self.exit_code
    
    def _finish_pipeline(self):
        """Finaliza pipeline y guarda resultados"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.results["end_time"] = end_time.isoformat()
        self.results["duration_seconds"] = duration
        self.results["status"] = "SUCCESS" if self.exit_code == 0 else "FAIL"
        
        # Save results
        results_file = PROJECT_ROOT / "logs" / f"pipeline_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{'='*60}")
        print(" RESUMEN DEL PIPELINE")
        print(f"{'='*60}")
        print(f"Estado: {' SUCCESS' if self.exit_code == 0 else ' FAIL'}")
        print(f"Duración: {duration:.1f} segundos")
        print(f"Pasos: {len(self.results['steps'])}")
        
        for step in self.results["steps"]:
            icon = "" if step.get("status") == "SUCCESS" else ""
            print(f"  {icon} {step['step']}")
        
        print(f"\n Resultados: {results_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline Orchestrator")
    parser.add_argument("--full", action="store_true", help="Pipeline completo (tests + build)")
    parser.add_argument("--quick", action="store_true", help="Build rápido")
    parser.add_argument("--build", action="store_true", help="Solo build")
    parser.add_argument("--test", action="store_true", help="Solo tests")
    parser.add_argument("--health", action="store_true", help="Health check")
    parser.add_argument("--backup", action="store_true", help="Solo backup")
    
    args = parser.parse_args()
    
    orchestrator = PipelineOrchestrator()
    
    if args.full:
        sys.exit(orchestrator.run_full_pipeline())
    elif args.quick:
        sys.exit(orchestrator.run_quick_build())
    elif args.build:
        sys.exit(orchestrator.run_step("Build", TOOLS_DIR / "ci_cd" / "run_build.py"))
    elif args.test:
        sys.exit(orchestrator.run_step("Tests", TOOLS_DIR / "ci_cd" / "run_tests.py"))
    elif args.health:
        sys.exit(orchestrator.run_health_check())
    elif args.backup:
        sys.exit(orchestrator.run_step("Backup", TOOLS_DIR / "backup" / "backup_manager.py", ["--backup"]))
    else:
        print("Usa: --full, --quick, --build, --test, --health, o --backup")