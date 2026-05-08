"""
GUI Tab for Global Search
========================
Pestaña de búsqueda global para gui_app.py con indexador FTS5
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sqlite3
import threading

try:
    from app.services.file_indexer import FileIndexer
except ImportError:
    class FileIndexer:
        def __init__(self, db_manager=None):
            self.db = db_manager
            self.search_transcriptions = lambda q, l=50: []
            self.get_stats = lambda: {"total": 0, "by_type": {}}

def setup_search_tab(self):
    """Configura la pestaña de búsqueda."""
    self.file_indexer = FileIndexer()
    
    search_main = ttk.Frame(self.tab_search, padding=15)
    search_main.pack(fill=tk.BOTH, expand=True)

    control_frame = ttk.Frame(search_main)
    control_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(control_frame, text="🔍 Búsqueda Global:", font=("Inter", 11, "bold")).pack(side=tk.LEFT, padx=(0, 15))
    
    self.search_var = tk.StringVar()
    entry = ttk.Entry(control_frame, textvariable=self.search_var, width=60, font=("Inter", 11))
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    entry.bind('<Return>', lambda e: self.run_search())
    
    self.search_btn = ttk.Button(control_frame, text="🔍 EJECUTAR", command=self.run_search, style="Primary.TButton")
    self.search_btn.pack(side=tk.LEFT, padx=10)
    
    sync_frame = ttk.Frame(control_frame)
    sync_frame.pack(side=tk.LEFT, padx=20)
    
    self.sync_btn = ttk.Button(sync_frame, text="🔄 Sincronizar", command=self.sync_files, style="Secondary.TButton")
    self.sync_btn.pack(side=tk.LEFT, padx=2)
    
    self.search_status = ttk.Label(control_frame, text="", font=("Inter", 9), foreground="#94a3b8")
    self.search_status.pack(side=tk.RIGHT, padx=10)
    
    results_frame = ttk.LabelFrame(search_main, text=" 📄 Fragmentos de Conocimiento Encontrados ", padding=10)
    results_frame.pack(fill=tk.BOTH, expand=True)
    
    self.search_results = scrolledtext.ScrolledText(results_frame, height=15, font=('Inter', 10), padx=15, pady=15)
    self.search_results.pack(fill=tk.BOTH, expand=True)
    
    footer_search = ttk.Frame(search_main)
    footer_search.pack(fill=tk.X, pady=(10, 0))
    ttk.Label(footer_search, text="Tip: Usa palabras clave como 'seguridad', 'procedimiento' o 'error' para filtrar.", 
              font=("Inter", 8, "italic"), foreground="#94a3b8").pack(side=tk.LEFT)


def run_search(self):
    query = self.search_var.get().strip()
    if not query:
        return
    
    self.search_btn.config(state='disabled')
    self.search_status.config(text="Buscando...", foreground="#f59e0b")
    self.search_results.delete(1.0, tk.END)
    self.search_results.insert(tk.END, f"🔍 Buscando '{query}'...\n\n")
    
    def do_search():
        found_count = 0
        query_lower = query.lower()
        lines_to_insert = []
        
        # 1. Búsqueda en knowledge_base.db
        db_path = os.path.join(self.base_dir, "knowledge", "knowledge_base.db")
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT category, source, content FROM knowledge_entries WHERE content LIKE ?", ('%' + query + '%',))
                rows = cursor.fetchall()
                conn.close()
                
                if rows:
                    lines_to_insert.append(f"📊 Base de Datos: {len(rows)} resultado(s)\n{'='*50}\n\n")
                    for row in rows:
                        found_count += 1
                        snippet = row[2][:200]
                        idx = snippet.lower().find(query_lower)
                        if idx >= 0:
                            start = max(0, idx - 30)
                            end = min(len(snippet), idx + len(query) + 50)
                            snippet = "..." + snippet[start:end] + "..."
                        lines_to_insert.append(f"📂 [{row[0]}] → {row[1]}\n")
                        lines_to_insert.append(f"   {snippet}\n")
                        lines_to_insert.append(f"{'─'*40}\n\n")
                else:
                    lines_to_insert.append("📊 Base de Datos: 0 resultados (tabla vacía o sin coincidencias)\n\n")
            except Exception as e:
                lines_to_insert.append(f"📊 Base de Datos: Error — {e}\n\n")
        
        # 2. Búsqueda en archivos procesados (.txt en output_dir)
        out_path = self.output_dir.get()
        if os.path.exists(out_path):
            file_results = []
            for f in sorted(os.listdir(out_path)):
                if not f.endswith('.txt'):
                    continue
                try:
                    with open(os.path.join(out_path, f), 'r', encoding='utf-8', errors='replace') as file:
                        content = file.read()
                        if query_lower in content.lower():
                            idx = content.lower().find(query_lower)
                            start = max(0, idx - 50)
                            end = min(len(content), idx + len(query) + 100)
                            snippet = content[start:end].replace('\n', ' ').strip()
                            if start > 0:
                                snippet = "..." + snippet
                            if end < len(content):
                                snippet = snippet + "..."
                            file_results.append((f, snippet))
                except Exception as e:
                    file_results.append((f, f"Error leyendo: {e}"))
            
            if file_results:
                lines_to_insert.append(f"📄 Archivos Procesados: {len(file_results)} resultado(s)\n{'='*50}\n\n")
                for fname, snippet in file_results:
                    found_count += 1
                    lines_to_insert.append(f"📄 {fname}\n")
                    lines_to_insert.append(f"   {snippet}\n")
                    lines_to_insert.append(f"{'─'*40}\n\n")
            else:
                lines_to_insert.append("📄 Archivos Procesados: 0 resultados\n\n")
        else:
            lines_to_insert.append("📄 Directorio de salida no existe\n\n")
        
        # 3. Búsqueda en transcripciones (usando FTS5)
        try:
            fts_results = self.file_indexer.search_transcriptions(query, limit=30)
            if fts_results:
                lines_to_insert.append(f"🎬 Transcripciones (FTS5): {len(fts_results)} resultado(s)\n{'='*50}\n\n")
                for row in fts_results:
                    found_count += 1
                    lines_to_insert.append(f"🎬 {row.get('file_name', 'Unknown')}\n")
                    lines_to_insert.append(f"   {row.get('snippet', '')}\n")
                    lines_to_insert.append(f"{'─'*40}\n\n")
            else:
                lines_to_insert.append("🎬 Transcripciones (FTS5): 0 resultados\n\n")
        except Exception as e:
            lines_to_insert.append(f"🎬 Transcripciones: Error - {e}\n\n")
         
        # Resumen
        lines_to_insert.append(f"\n{'='*50}\n")
        lines_to_insert.append(f"✅ Total: {found_count} coincidencia(s) encontrada(s)")
        
        # Actualizar UI en hilo principal
        def update_ui():
            self.search_results.delete(1.0, tk.END)
            for line in lines_to_insert:
                self.search_results.insert(tk.END, line)
            self.search_results.see(1.0)
            self.search_btn.config(state='normal')
            self.search_status.config(text=f"{found_count} resultado(s)", foreground="#10b981" if found_count > 0 else "#94a3b8")
        
        self.root.after(0, update_ui)
    
    threading.Thread(target=do_search, daemon=True).start()


def sync_files(self):
    """Sincroniza archivos usando el indexador en background."""
    in_path = self.input_dir.get()
    out_path = self.output_dir.get()
    paths = [p for p in [in_path, out_path] if os.path.isdir(p)]
    
    if not paths:
        self.search_status.config(text="No hay directorios para indexar", foreground="#f59e0b")
        return
    
    self.sync_btn.config(state='disabled')
    self.search_status.config(text="Sincronizando...", foreground="#f59e0b")
    
    stats = self.file_indexer.get_stats()
    self.search_status.config(text=f"📁 {stats.get('total', 0)} archivos indexados", foreground="#10b981")
    
    def ui_callback(status, current, total, filename):
        def _update():
            if status == 'scanning':
                self.search_status.config(text=f"Escaneando {total} archivos...", foreground="#f59e0b")
            elif status == 'indexing':
                self.search_status.config(text=f"Indexando {current}/{total}: {filename}", foreground="#f59e0b")
            elif status == 'done':
                self.search_status.config(text=filename if filename else f"✅ {current} archivos indexados", foreground="#10b981")
                self.sync_btn.config(state='normal')
            elif status == 'error':
                self.search_status.config(text=f"Error: {filename}", foreground="#ef4444")
                self.sync_btn.config(state='normal')
        self.root.after(0, _update)
    
    self.file_indexer.init_background_scan(paths, ui_callback)
