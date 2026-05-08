"""
Dashboard Mixin
Gestión del servidor de dashboard y métricas.
"""

import logging
import threading
import tkinter as tk


class DashboardMixin:
    """Mixin para funcionalidades de dashboard y métricas."""

    def start_dashboard_server(self, callback_ui=None):
        """Inicia el servidor del dashboard web."""
        if getattr(self, 'dashboard_active', False):
            return True, "Dashboard ya está activo"
        
        try:
            import dashboard_server as ds
            
            port = getattr(self, 'settings', {}).get('dashboard_port', 8050)
            
            def run_server():
                try:
                    ds.app.run(port=port, debug=False, use_reloader=False)
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"[DASHBOARD] Error: {e}"))
            
            self.dashboard_server_thread = threading.Thread(target=run_server, daemon=True)
            self.dashboard_server_thread.start()
            self.dashboard_active = True
            
            self.log(f"[DASHBOARD] Servidor iniciado en puerto {port}")
            return True, f"Puerto {port}"
        except ImportError:
            return False, "Módulo dashboard no disponible"
        except Exception as e:
            return False, f"Error al iniciar: {str(e)}"

    def stop_dashboard_server(self):
        """Detiene el servidor del dashboard."""
        if not getattr(self, 'dashboard_active', False):
            return True, "Dashboard ya detenido"
        
        try:
            import dashboard_server as ds
            if hasattr(ds, '_server') and ds._server:
                ds._server.shutdown()
                ds._server.server_close()
                ds._server = None
            
            self.dashboard_server_thread = None
            self.dashboard_active = False
            return True, "Servidor detenido"
        except Exception as e:
            return False, f"Error al detener: {str(e)}"

    def _auto_start_dashboard_thread(self):
        """Hilo para auto-inicio del dashboard sin bloquear UI."""
        import time
        time.sleep(3)
        try:
            success, msg = self.start_dashboard_server()
            if success:
                self.root.after(0, lambda: self.log(f"✅ Dashboard iniciado automáticamente: {msg}"))
            else:
                self.root.after(0, lambda: self.log(f"⚠️ Auto-inicio dashboard: {msg}"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Error auto-inicio dashboard: {e}"))

    def update_dashboard_metrics(self):
        """Actualiza las métricas del dashboard."""
        if not hasattr(self, 'metrics'):
            self.metrics = {"processed": 0, "errors": 0, "cache_hits": 0, "start_time": 0}
        
        metrics = getattr(self, 'metrics', {})
        
        if hasattr(self, 'db_manager') and self.db_manager:
            try:
                stats = self.db_manager.get_stats()
                metrics.update(stats)
            except Exception:
                pass
        
        return metrics

    def get_system_status(self):
        """Obtiene el estado actual del sistema."""
        status = {
            "app_running": True,
            "dashboard_active": getattr(self, 'dashboard_active', False),
            "queue_running": getattr(self, 'queue_running', False),
            "queue_paused": getattr(self, 'queue_paused', False),
            "monitor_active": getattr(self, 'monitor_var', tk.BooleanVar()).get() if hasattr(self, 'monitor_var') else False,
        }
        
        if hasattr(self, 'metrics'):
            status["metrics"] = self.metrics
        
        return status

    def open_dashboard(self):
        """Abre el dashboard en el navegador."""
        port = getattr(self, 'settings', {}).get('dashboard_port', 8050)
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")
        self.log(f"[DASHBOARD] Abriendo en navegador...")