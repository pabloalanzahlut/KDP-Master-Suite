"""
GUI Tab for Processing
======================
Pestaña de procesamiento de transcripciones para gui_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, Menu, scrolledtext, filedialog
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

from app.ui.components.notifications import ToastNotification
from app.ui.components.tooltips import ToolTip
from app.ui.components.progress_panel import ProgressPanel, BatchProgressManager
from app.services.processing_service import ProcessingService


def setup_process_tab(self):
    """Configura la pestaña de procesamiento."""
    paned = ttk.PanedWindow(self.tab_process, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, pady=5)

    left_frame = ttk.Frame(paned)
    paned.add(left_frame, weight=3)

    paths_frame = ttk.LabelFrame(left_frame, text=" 📂 Directorios de Trabajo ", padding=10)
    paths_frame.pack(fill=tk.X, pady=(0, 10))
    paths_frame.columnconfigure(1, weight=1)
    
    ttk.Label(paths_frame, text="📥 Entrada:", font=("Inter", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
    ttk.Entry(paths_frame, textvariable=self.input_dir, font=("Inter", 9)).grid(row=0, column=1, sticky=tk.EW, padx=5)
    ttk.Button(paths_frame, text="🔍 Buscar", width=8, command=self.browse_input).grid(row=0, column=2, padx=2)
    
    ttk.Label(paths_frame, text="📤 Salida:", font=("Inter", 9, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
    ttk.Entry(paths_frame, textvariable=self.output_dir, font=("Inter", 9)).grid(row=1, column=1, sticky=tk.EW, padx=5)
    ttk.Button(paths_frame, text="🔍 Buscar", width=8, command=self.browse_output).grid(row=1, column=2, padx=2)

    list_frame = ttk.LabelFrame(left_frame, text=" 📑 Repositorio de Archivos Detectados ", padding=10)
    list_frame.pack(fill=tk.BOTH, expand=True)

    toolbar = ttk.Frame(list_frame)
    toolbar.pack(fill=tk.X, pady=(0, 10))
    ttk.Button(toolbar, text="🔄 Sincronizar Lista", command=self.refresh_file_list, style="Primary.TButton").pack(side=tk.LEFT)
    ttk.Button(toolbar, text="✅ Seleccionar Todo", command=self.select_all_files).pack(side=tk.LEFT, padx=5)
    
    tree_container = ttk.Frame(list_frame)
    tree_container.pack(fill=tk.BOTH, expand=True)
    tree_scroll = ttk.Scrollbar(tree_container)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    columns = ('archivo', 'tipo', 'tamano')
    self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', selectmode='extended', yscrollcommand=tree_scroll.set)
    self.tree.heading('archivo', text='📄 Nombre del Archivo')
    self.tree.heading('tipo', text='📁 Tipo')
    self.tree.heading('tamano', text='⚖️ Tamaño')
    self.tree.column('archivo', width=450)
    self.tree.column('tipo', width=100, anchor='center')
    self.tree.column('tamano', width=100, anchor='e')
    self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.config(command=self.tree.yview)
    
    self.file_context_menu = Menu(self.root, tearoff=0)
    self.file_context_menu.add_command(label="✅ Seleccionar Todo", command=self.select_all_files)
    self.file_context_menu.add_separator()
    self.file_context_menu.add_command(label="🚀 Procesar Selección", command=self.start_processing)
    self.file_context_menu.add_command(label="📂 Abrir en Navegador", command=lambda: self.open_file_location())
    self.file_context_menu.add_separator()
    self.file_context_menu.add_command(label="🗑️ Eliminar Permanente", command=self.delete_selected_file)

    def show_file_menu(event):
        try:
            item = self.tree.identify_row(event.y)
            if item:
                if item not in self.tree.selection():
                    self.tree.selection_set(item)
            self.file_context_menu.post(event.x_root, event.y_root)
        finally:
            try:
                self.file_context_menu.grab_release()
            except Exception:
                pass
    self.tree.bind("<Button-3>", show_file_menu)
    self.tree.bind('<<TreeviewSelect>>', self.display_metadata)
    
    right_frame = ttk.Frame(paned, padding=(10, 0, 0, 0))
    paned.add(right_frame, weight=1)
    
    progress_section = ttk.LabelFrame(right_frame, text=" 📊 Progreso del Batch ", padding=10)
    progress_section.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    self.progress_panel = ProgressPanel(progress_section, max_visible=8, on_retry=self.retry_process_file)
    self.progress_panel.pack(fill=tk.BOTH, expand=True)
    
    self.batch_manager = BatchProgressManager(
        self.progress_panel,
        global_progress_callback=lambda pct: self.root.after(0, lambda: self.progress_var.set(pct))
    )
    
    action_panel = ttk.LabelFrame(right_frame, text=" ⚡ Acciones del Sistema ", padding=15)
    action_panel.pack(fill=tk.X, pady=(0, 15))
    
    proc_btn = ttk.Button(action_panel, text="🚀 INICIAR LIMPIEZA", command=self.start_processing, style="Success.TButton")
    proc_btn.pack(fill=tk.X, pady=(0, 10), ipady=15)
    
    ttk.Button(action_panel, text="📂 Abrir Resultados", command=lambda: self.open_folder(self.output_dir.get())).pack(fill=tk.X, pady=5)
    ttk.Button(action_panel, text="🗑️ Eliminar Seleccionados", command=self.delete_selected_file, style="Danger.TButton").pack(fill=tk.X, pady=5)

    meta_frame = ttk.LabelFrame(right_frame, text=" 🛡️ Metadatos e Inspección ", padding=10)
    meta_frame.pack(fill=tk.BOTH, expand=True)
    self.metadata_text = scrolledtext.ScrolledText(meta_frame, height=12, font=('Consolas', 9), state='disabled', wrap=tk.WORD)
    self.metadata_text.pack(fill=tk.BOTH, expand=True)


# ========== INICIO: REFRESCAR LISTA ARCHIVOS ==========
def _ensure_directories_exist(self):
    """Crea carpetas necesarias si no existen."""
    input_path = self.input_dir.get()
    output_path = self.output_dir.get()
    if not os.path.isabs(input_path):
        input_path = os.path.abspath(os.path.join(self.base_dir, input_path))
    if not os.path.isabs(output_path):
        output_path = os.path.abspath(os.path.join(self.base_dir, output_path))
    os.makedirs(input_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)
    return input_path, output_path


def refresh_file_list(self):
    """Actualiza la lista de archivos detectados en subdirectorios."""
    # 1. Asegurar carpetas existen
    path, _ = _ensure_directories_exist(self)
    
    self.tree.delete(*self.tree.get_children())
    self.files_to_process = []
    
    if not path:
        self.tree.insert('', tk.END, values=("⚠️ No configurado", "", ""))
        return
    
    # 2. Buscar recursivamente
    extensions = {'.vtt', '.srt', '.txt'}
    try:
        found_files = []
        for ext in extensions:
            for filepath in Path(path).rglob(f"*{ext}"):
                if filepath.is_file():
                    rel_path = filepath.relative_to(path)
                    found_files.append((str(filepath), str(rel_path)))
        
        if not found_files:
            self.tree.insert('', tk.END, values=("📂 Carpeta vacía", "", ""))
        else:
            # 3. Ordenar por fecha reciente
            found_files.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
            
            # 4. Insertar en treeview
            for filepath, rel_path in found_files:
                size_kb = os.path.getsize(filepath) / 1024
                display_name = rel_path.replace(os.sep, '/')
                ext = Path(filepath).suffix
                self.tree.insert('', tk.END, values=(display_name, ext, f"{size_kb:.1f} KB"))
                self.files_to_process.append(rel_path)
    except Exception as e:
        self.tree.insert('', tk.END, values=("❌ Error al leer", "", str(e)))
# ========== FIN: REFRESCAR LISTA ARCHIVOS ==========


def start_processing(self):
    selected_items = self.tree.selection()
    if not selected_items:
        messagebox.showwarning("Atención", "No hay archivos seleccionados.")
        return
    
    files_to_process = [self.tree.item(item)['values'][0] for item in selected_items]
    self.progress_var.set(0)
    
    input_dir = self.input_dir.get()
    if not os.path.isabs(input_dir):
        input_dir = os.path.abspath(os.path.join(self.base_dir, input_dir))
    
    output_dir = self.output_dir.get()
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(os.path.join(self.base_dir, output_dir))
    
    processing_service = ProcessingService()
    
    weights = {}
    for f in files_to_process:
        fpath = os.path.join(input_dir, f)
        weights[f] = os.path.getsize(fpath) if os.path.exists(fpath) else 1
    
    self.batch_manager.set_files(files_to_process, weights)
    
    def log_to_gui(message, level='info'):
        self.root.after(0, lambda: self.logger.error(message) if level == 'error' else self.logger.info(message))

    def individual_progress_callback(filename, percent, state, eta=None, speed=None):
        speed_str = None
        if speed:
            if speed > 1024*1024:
                speed_str = f"{speed/1024/1024:.1f}MB"
            elif speed > 1024:
                speed_str = f"{speed/1024:.1f}KB"
            else:
                speed_str = f"{speed:.0f}B"
        self.root.after(0, lambda: self.batch_manager.update_file(filename, percent, state, eta, speed_str))

    def run():
        try:
            count = processing_service.process_files(
                input_dir=input_dir,
                output_dir=output_dir,
                files_to_process=files_to_process,
                progress_callback=lambda v: self.root.after(0, lambda: self.progress_var.set(v)),
                log_callback=log_to_gui,
                individual_progress_callback=individual_progress_callback
            )
            
            failed = self.batch_manager.get_failed_files()
            completed = self.batch_manager.get_completed_count()
            total = self.batch_manager.get_total_count()
            
            self.root.after(0, lambda: [
                self._show_batch_summary(completed, total, count, failed),
                self.refresh_file_list()
            ])
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error procesando: {e}"))

    import threading
    threading.Thread(target=run, daemon=True).start()


def _show_batch_summary(self, completed, total, successful, failed):
    if not failed:
        messagebox.showinfo("Éxito", f"✅ Batch completado.\n\n📊 {completed}/{total} archivos procesados\n✅ {successful} archivos únicos generados.")
    else:
        msg = f"⚠️ Batch completado con errores.\n\n📊 {completed}/{total} archivos procesados\n✅ {successful} archivos únicos\n❌ {len(failed)} fallidos:\n" + "\n".join(f"  • {f}" for f in failed[:5])
        if len(failed) > 5:
            msg += f"\n  ... y {len(failed)-5} más"
        messagebox.showwarning("Completado con errores", msg)


def retry_process_file(self, filename):
    input_dir = self.input_dir.get()
    if not os.path.isabs(input_dir):
        input_dir = os.path.abspath(os.path.join(self.base_dir, input_dir))
    
    output_dir = self.output_dir.get()
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(os.path.join(self.base_dir, output_dir))
    
    processing_service = ProcessingService()
    
    def log_to_gui(message, level='info'):
        self.root.after(0, lambda: self.logger.error(message) if level == 'error' else self.logger.info(message))

    def individual_progress_callback(filename, percent, state, eta=None, speed=None):
        speed_str = None
        if speed:
            if speed > 1024*1024:
                speed_str = f"{speed/1024/1024:.1f}MB"
            elif speed > 1024:
                speed_str = f"{speed/1024:.1f}KB"
            else:
                speed_str = f"{speed:.0f}B"
        self.root.after(0, lambda: self.batch_manager.update_file(filename, percent, state, eta, speed_str))

    def run():
        try:
            processing_service.process_files(
                input_dir=input_dir,
                output_dir=output_dir,
                files_to_process=[filename],
                log_callback=log_to_gui,
                individual_progress_callback=individual_progress_callback
            )
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error reintentando {filename}: {e}"))

    import threading
    threading.Thread(target=run, daemon=True).start()


def display_metadata(self, event):
    selection = self.tree.selection()
    if not selection: return
    filename = self.tree.item(selection[0])['values'][0]
    filepath = os.path.join(self.input_dir.get(), filename)
    json_path = os.path.splitext(filepath)[0] + ".info.json"
    
    info = "No hay metadatos disponibles."
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                info = f"📌 TÍTULO: {data.get('title', 'N/A')}\n"
                info += f"👤 CANAL: {data.get('uploader', 'N/A')}\n"
                info += f"⏱️ DURACIÓN: {data.get('duration_string', 'N/A')}\n"
                info += f"👁️ VISTAS: {data.get('view_count', 0):,}\n"
                info += f"📅 FECHA: {data.get('upload_date', 'N/A')}"
        except Exception as e:
            info = f"Error leyendo metadatos: {e}"
    
    self.metadata_text.configure(state='normal')
    self.metadata_text.delete('1.0', tk.END)
    self.metadata_text.insert(tk.END, info)
    self.metadata_text.configure(state='disabled')


def browse_input(self):
    current = self.input_dir.get()
    if not current or not os.path.isdir(current):
        current = os.getcwd()
    d = filedialog.askdirectory(initialdir=current)
    if d:
        self.input_dir.set(d)
        self.refresh_file_list()


def browse_output(self):
    current = self.output_dir.get()
    if not current or not os.path.isdir(current):
        current = os.getcwd()
    d = filedialog.askdirectory(initialdir=current)
    if d:
        self.output_dir.set(d)


def delete_selected_file(self):
    selection = self.tree.selection()
    if not selection: return
    if messagebox.askyesno("Eliminar", "¿Seguro que desea eliminar estos archivos?"):
        deleted = 0
        errors = 0
        for item in selection:
            filename = self.tree.item(item)['values'][0]
            try:
                os.remove(os.path.join(self.input_dir.get(), filename))
                deleted += 1
            except Exception as e:
                errors += 1
                self.logger.error(f"No se pudo eliminar {filename}: {e}")
        self.refresh_file_list()
        if errors > 0:
            ToastNotification.show(self.root, f"🗑️ {deleted} eliminados, {errors} errores", "warning")
        else:
            ToastNotification.show(self.root, f"🗑️ {deleted} archivo(s) eliminado(s)", "success")


def open_file_location(self):
    selection = self.tree.selection()
    if not selection: return
    filename = self.tree.item(selection[0])['values'][0]
    path = os.path.abspath(os.path.join(self.input_dir.get(), filename))
    if os.path.exists(path):
        subprocess.Popen(f'explorer /select,"{path}"')
