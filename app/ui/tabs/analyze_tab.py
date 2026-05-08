"""
GUI Tab for Knowledge Intelligence
==================================
Pestaña de inteligencia SynthLearn para gui_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import threading

# Importar componentes
from app.ui.components.tooltips import ToolTip


def setup_analyze_tab(self):
    """Configura la pestaña de inteligencia."""
    if not self.integrator:
        ttk.Label(self.tab_analyze, text="❌ Módulo Integrador no encontrado.").pack(pady=40)
        return

    header = ttk.Frame(self.tab_analyze)
    header.pack(fill=tk.X, pady=10)
    ttk.Label(header, text="🧠 Centro de Inteligencia SynthLearn", style="Header.TLabel").pack(side=tk.LEFT)
    
    btn_frame = ttk.Frame(self.tab_analyze)
    btn_frame.pack(fill=tk.X, pady=10)
    
    intel_btn = ttk.Button(btn_frame, text="🧠 Integrar Conocimiento", command=self.run_analysis, style="Primary.TButton")
    intel_btn.pack(side=tk.LEFT, padx=5, ipady=5)
    ToolTip(intel_btn, "Escanea archivos procesados y los categoriza")
    
    if hasattr(self, 'html_gen') and self.html_gen:
        html_btn = ttk.Button(btn_frame, text="🌐 Exportar Índice Web", command=self.generate_html, style="Success.TButton")
        html_btn.pack(side=tk.LEFT, padx=5, ipady=5)

    report_frame = ttk.LabelFrame(self.tab_analyze, text=" 📊 Reporte de Integración ", padding=10)
    report_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    self.analysis_text = scrolledtext.ScrolledText(report_frame, height=15, font=('Consolas', 10))
    self.analysis_text.pack(fill=tk.BOTH, expand=True)


def run_analysis(self):
    self.analysis_text.delete(1.0, tk.END)
    self.analysis_text.insert(tk.END, "Iniciando Integración...\n")
    
    out_path = self.output_dir.get()
    if not os.path.exists(out_path): 
        return
    
    files = [f for f in os.listdir(out_path) if f.endswith('.txt')]
    if not files:
        self.analysis_text.insert(tk.END, "Sin archivos para integrar.\n")
        return

    def async_integration():
        for f in files:
            try:
                with open(os.path.join(out_path, f), 'r', encoding='utf-8') as file:
                    content = file.read()
                    result = self.integrator.analyze_text(content, source_filename=f)
                    
                    def update_ui(file_name=f, res=result):
                        self.analysis_text.insert(tk.END, f"\n📄 Procesando: {file_name}\n")
                        for msg in res.get("integrated", []):
                            self.analysis_text.insert(tk.END, f"   ✅ {msg}\n")
                        self.analysis_text.insert(tk.END, "-"*30 + "\n")
                        self.analysis_text.see(tk.END)
                    self.root.after(0, update_ui)
            except Exception as e:
                self.logger.error(f"Error analizando {f}: {e}")
        self.root.after(0, lambda: messagebox.showinfo("Éxito", "Integración Finalizada"))

    threading.Thread(target=async_integration, daemon=True).start()


def generate_html(self):
    if not hasattr(self, 'html_gen') or not self.html_gen: return
    success, msg = self.html_gen.generate()
    if success: messagebox.showinfo("Éxito", "Índice generado.")
    else: messagebox.showerror("Error", msg)
