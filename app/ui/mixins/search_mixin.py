"""
Search Mixin
Gestión de búsquedas y filtros en la base de conocimiento.
"""

import logging
import tkinter as tk


class SearchMixin:
    """Mixin para funcionalidades de búsqueda."""

    def run_search(self):
        """Ejecuta la búsqueda en la base de conocimiento."""
        if hasattr(self, 'search_tab') and self.search_tab:
            try:
                self.search_tab.run_search(self)
            except Exception as e:
                self.log(f"[ERROR] Error en búsqueda: {e}", "error")
        else:
            query = getattr(self, 'search_var', tk.StringVar()).get().strip()
            if not query:
                self.log("[WARN] Ingrese un término de búsqueda.")
                return
            self.log(f"[SEARCH] Búsqueda: {query}")

    def run_indexed_search(self):
        """Ejecuta búsqueda indexada usando FTS5."""
        query = getattr(self, 'search_var', tk.StringVar()).get().strip()
        if not query:
            return
        
        if hasattr(self, 'knowledge_db') and self.knowledge_db:
            try:
                import time
                start_time = time.time()
                results = self.knowledge_db.search(query)
                elapsed = (time.time() - start_time) * 1000
                self.log(f"[SEARCH] {len(results)} resultados en {elapsed:.2f}ms")
                return results
            except Exception as e:
                self.log(f"[ERROR] Búsqueda indexada fallida: {e}", "error")
        return []

    def clear_search(self):
        """Limpia los resultados de búsqueda."""
        if hasattr(self, 'search_tab') and self.search_tab:
            try:
                self.search_tab.clear_search(self)
            except Exception:
                pass
        if hasattr(self, 'search_var'):
            self.search_var.set("")

    def export_search_results(self):
        """Exporta los resultados de búsqueda a archivo."""
        if hasattr(self, 'search_tab') and self.search_tab:
            try:
                self.search_tab.export_search_results(self)
            except Exception as e:
                self.log(f"[ERROR] Error al exportar resultados: {e}", "error")

    def toggle_search_filter(self):
        """Alterna los filtros de búsqueda avanzada."""
        if hasattr(self, 'filter_enabled_var'):
            self.filter_enabled_var.set(not self.filter_enabled_var.get())
            self.log(f"[FILTER] Filtros {'activados' if self.filter_enabled_var.get() else 'desactivados'}")