#!/usr/bin/env python3
"""
Health Check - Monitoring
Endpoint de salud del sistema
"""
import os
import sys
import sqlite3
import json
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler


PROJECT_ROOT = Path(".").resolve()
DATA_DIR = PROJECT_ROOT / "data"


class HealthChecker:
    def __init__(self):
        self.checks = []
    
    def check_database(self):
        """Check database connectivity"""
        db_path = DATA_DIR / "channel_monitor.db"
        
        if not db_path.exists():
            return {"status": "FAIL", "message": "DB not found"}
        
        try:
            conn = sqlite3.connect(str(db_path), timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM channels")
            count = cursor.fetchone()[0]
            conn.close()
            
            return {"status": "OK", "message": f"{count} channels"}
        except Exception as e:
            return {"status": "FAIL", "message": str(e)}
    
    def check_transcriptions(self):
        """Check transcriptions directory"""
        transcriptions_dir = DATA_DIR / "transcriptions"
        
        if not transcriptions_dir.exists():
            return {"status": "FAIL", "message": "Transcriptions dir not found"}
        
        channels = len([d for d in transcriptions_dir.iterdir() if d.is_dir()])
        
        return {"status": "OK", "message": f"{channels} channels"}
    
    def check_ollama(self):
        """Check Ollama availability"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {"status": "OK", "message": f"{len(models)} models"}
            else:
                return {"status": "WARNING", "message": f"Status {response.status_code}"}
        except:
            return {"status": "WARNING", "message": "Not reachable"}
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            stat = shutil.disk_usage(PROJECT_ROOT)
            free_gb = stat.free / (1024**3)
            
            status = "OK" if free_gb > 1 else "WARNING"
            return {"status": status, "message": f"{free_gb:.1f} GB free"}
        except Exception as e:
            return {"status": "UNKNOWN", "message": str(e)}
    
    def check_data_size(self):
        """Check data directory size"""
        try:
            total = 0
            for root, dirs, files in os.walk(DATA_DIR):
                for f in files:
                    try:
                        total += Path(root, f).stat().st_size
                    except:
                        pass
            
            size_gb = total / (1024**3)
            return {"status": "OK", "message": f"{size_gb:.2f} GB"}
        except Exception as e:
            return {"status": "UNKNOWN", "message": str(e)}
    
    def run_all_checks(self):
        """Run all health checks"""
        self.checks = {
            "timestamp": datetime.now().isoformat(),
            "database": self.check_database(),
            "transcriptions": self.check_transcriptions(),
            "ollama": self.check_ollama(),
            "disk_space": self.check_disk_space(),
            "data_size": self.check_data_size()
        }
        
        # Determine overall status
        statuses = [c["status"] for c in self.checks.values() if isinstance(c, dict)]
        
        if any(s == "FAIL" for s in statuses):
            overall = "FAIL"
        elif any(s == "WARNING" for s in statuses):
            overall = "WARNING"
        else:
            overall = "OK"
        
        self.checks["overall_status"] = overall
        
        return self.checks
    
    def get_status(self):
        """Get status for HTTP response"""
        checks = self.run_all_checks()
        return {
            "status": checks["overall_status"],
            "checks": checks
        }


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health endpoint"""
    
    checker = HealthChecker()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path in ["/health", "/health.json"]:
            status = self.checker.get_status()
            
            self.send_response(200 if status["status"] != "FAIL" else 503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            self.wfile.write(json.dumps(status, indent=2).encode())
        
        elif self.path == "/health/ready":
            status = self.checker.get_status()
            
            ready = status["status"] in ["OK", "WARNING"]
            self.send_response(200 if ready else 503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            self.wfile.write(json.dumps({"ready": ready}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress logging"""
        pass


def start_server(port=8765):
    """Start health check server"""
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f" Health check server: http://localhost:{port}/health")
    print(f"   Ready endpoint: http://localhost:{port}/health/ready")
    print("\nPresiona Ctrl+C para detener")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n Servidor detenido")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Health Check")
    parser.add_argument("--server", action="store_true", help="Iniciar servidor HTTP")
    parser.add_argument("--port", type=int, default=8765, help="Puerto del servidor")
    parser.add_argument("--check", action="store_true", help="Ejecutar checks sin servidor")
    
    args = parser.parse_args()
    
    if args.server:
        start_server(args.port)
    elif args.check:
        checker = HealthChecker()
        status = checker.run_all_checks()
        print(json.dumps(status, indent=2))
    else:
        start_server()