"""
GUI Tab for Knowledge Intelligence
==================================
Pestaña de inteligencia SynthLearn para gui_app.py
Incluye clasificación IA con scoring de relevancia KDP
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import threading

from app.ui.components.tooltips import ToolTip


def setup_analyze_tab(self):
    """Configura la pestaña de inteligencia."""
    if not self.integrator:
        ttk.Label(self.tab_analyze, text="❌ Módulo Integrador no encontrado.").pack(pady=40)
        return

    header = ttk.Frame(self.tab_analyze)
    header.pack(fill=tk.X, pady=10)
    ttk.Label(header, text="🧠 Centro de Inteligencia SynthLearn", style="Header.TLabel").pack(side=tk.LEFT)
    
    # Contenedor principal con dos columnas
    main_container = ttk.Frame(self.tab_analyze)
    main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Columna izquierda: Clasificación IA
    left_frame = ttk.LabelFrame(main_container, text=" 🎯 Clasificación IA de Videos ", padding=10)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    # Input de título
    ttk.Label(left_frame, text="Título del video:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 3))
    self.classify_title_entry = ttk.Entry(left_frame, width=60, font=("Segoe UI", 10))
    self.classify_title_entry.pack(fill=tk.X, pady=(0, 10))
    
    # Input de descripción
    ttk.Label(left_frame, text="Descripción (opcional):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 3))
    self.classify_desc_text = scrolledtext.ScrolledText(left_frame, height=4, width=60, font=("Segoe UI", 9))
    self.classify_desc_text.pack(fill=tk.X, pady=(0, 10))
    
    # Botón clasificar
    btn_classify_frame = ttk.Frame(left_frame)
    btn_classify_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(btn_classify_frame, text="🔍 Clasificar Video", 
               command=self.classify_single_video, style="Primary.TButton").pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_classify_frame, text="🗑️ Limpiar", 
               command=self.clear_classification).pack(side=tk.LEFT, padx=2)
    
    # Panel de resultados de clasificación
    self.classify_result_frame = ttk.LabelFrame(left_frame, text=" 📊 Resultado de Clasificación ", padding=10)
    self.classify_result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    # Grid de resultados
    result_grid = ttk.Frame(self.classify_result_frame)
    result_grid.pack(fill=tk.X)
    
    # Categoría principal
    ttk.Label(result_grid, text="Categoría:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky=tk.W, pady=3)
    self.result_category_lbl = ttk.Label(result_grid, text="--", font=("Segoe UI", 10, "bold"), foreground="#3b82f6")
    self.result_category_lbl.grid(row=0, column=1, sticky=tk.W, padx=10, pady=3)
    
    # Confidence
    ttk.Label(result_grid, text="Confianza:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, pady=3)
    self.result_confidence_lbl = ttk.Label(result_grid, text="--%", font=("Segoe UI", 10, "bold"), foreground="#10b981")
    self.result_confidence_lbl.grid(row=1, column=1, sticky=tk.W, padx=10, pady=3)
    
    # Barra de confianza
    self.confidence_bar = ttk.Progressbar(result_grid, length=150, mode='determinate', maximum=100)
    self.confidence_bar.grid(row=1, column=2, sticky=tk.W, padx=10, pady=3)
    
    # Subcategorías
    ttk.Label(result_grid, text="Subcategorías:", font=("Segoe UI", 9)).grid(row=2, column=0, sticky=tk.W, pady=3)
    self.result_subcategories_lbl = ttk.Label(result_grid, text="--", font=("Segoe UI", 9), foreground="#64748b")
    self.result_subcategories_lbl.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=10, pady=3)
    
    # Keywords detectados
    ttk.Label(result_grid, text="Keywords:", font=("Segoe UI", 9)).grid(row=3, column=0, sticky=tk.W, pady=3)
    self.result_keywords_lbl = ttk.Label(result_grid, text="--", font=("Segoe UI", 9), foreground="#8b5cf6")
    self.result_keywords_lbl.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=10, pady=3)
    
    # Relevance Score
    ttk.Label(result_grid, text="Relevance KDP:", font=("Segoe UI", 9)).grid(row=4, column=0, sticky=tk.W, pady=3)
    self.result_relevance_lbl = ttk.Label(result_grid, text="--/100", font=("Segoe UI", 10, "bold"), foreground="#f59e0b")
    self.result_relevance_lbl.grid(row=4, column=1, sticky=tk.W, padx=10, pady=3)
    
    # Recomendación
    ttk.Label(result_grid, text="Recomendación:", font=("Segoe UI", 9)).grid(row=5, column=0, sticky=tk.W, pady=3)
    self.result_action_lbl = ttk.Label(result_grid, text="--", font=("Segoe UI", 10, "bold"))
    self.result_action_lbl.grid(row=5, column=1, columnspan=2, sticky=tk.W, padx=10, pady=3)
    
    # Lista de categorías disponibles
    categories_frame = ttk.LabelFrame(left_frame, text=" 📋 Categorías KDP Disponibles ", padding=10)
    categories_frame.pack(fill=tk.X, pady=(15, 0))
    
    self.categories_listbox = tk.Listbox(categories_frame, height=6, font=("Segoe UI", 9), selectmode=tk.SINGLE)
    self.categories_listbox.pack(fill=tk.X)
    
    categories = self._get_kdp_categories()
    for cat in categories:
        self.categories_listbox.insert(tk.END, f"• {cat}")
    
    # Columna derecha: Reporte de integración
    right_frame = ttk.LabelFrame(main_container, text=" 📊 Reporte de Integración ", padding=10)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
    
    btn_frame = ttk.Frame(right_frame)
    btn_frame.pack(fill=tk.X, pady=(0, 10))
    
    intel_btn = ttk.Button(btn_frame, text="🧠 Integrar Conocimiento", command=self.run_analysis, style="Primary.TButton")
    intel_btn.pack(side=tk.LEFT, padx=5)
    ToolTip(intel_btn, "Escanea archivos procesados y los categoriza")
    
    if hasattr(self, 'html_gen') and self.html_gen:
        html_btn = ttk.Button(btn_frame, text="🌐 Exportar Índice Web", command=self.generate_html, style="Success.TButton")
        html_btn.pack(side=tk.LEFT, padx=5)
    
    self.analysis_text = scrolledtext.ScrolledText(right_frame, height=10, font=('Consolas', 10))
    self.analysis_text.pack(fill=tk.BOTH, expand=True)


def classify_single_video(self):
    """Clasifica un video usando IA."""
    title = self.classify_title_entry.get().strip()
    if not title:
        messagebox.showwarning("Campo vacío", "Ingresa un título para clasificar.")
        return
    
    description = self.classify_desc_text.get(1.0, tk.END).strip()
    
    try:
        from app.pre_ingesta.ia.category_classifier import create_category_classifier
        from app.services.kdp_scoring_service import create_scoring_service
        
        classifier = create_category_classifier()
        scoring_service = create_scoring_service()
        
        # Clasificación de categoría
        category, confidence, subcategories = classifier.classify(title, description)
        
        # Scoring de relevancia
        score_result = scoring_service.score_video(title, description)
        
        # Actualizar UI con resultados
        self.result_category_lbl.config(text=self._format_category_name(category))
        
        confidence_pct = int(confidence * 100)
        self.result_confidence_lbl.config(text=f"{confidence_pct}%")
        self.confidence_bar['value'] = confidence_pct
        
        self.result_subcategories_lbl.config(text=", ".join(subcategories) if subcategories else "Ninguna detectada")
        
        self.result_keywords_lbl.config(text=", ".join(score_result.detected_keywords[:5]) if score_result.detected_keywords else "Ninguno")
        
        self.result_relevance_lbl.config(text=f"{score_result.kdp_relevance_score}/100")
        
        # Color según relevancia
        if score_result.kdp_relevance_score >= 70:
            self.result_relevance_lbl.config(foreground="#10b981")
        elif score_result.kdp_relevance_score >= 50:
            self.result_relevance_lbl.config(foreground="#f59e0b")
        else:
            self.result_relevance_lbl.config(foreground="#ef4444")
        
        # Acción recomendada
        action_map = {
            "download": "✅ DESCARGAR",
            "review": "🔍 REVISAR",
            "watch_later": "📺 VER DESPUÉS",
            "skip": "⏭️ SALTAR"
        }
        action_text = action_map.get(score_result.recommended_action, "--")
        self.result_action_lbl.config(text=action_text)
        
        # Color según acción
        color_map = {
            "download": "#10b981",
            "review": "#f59e0b",
            "watch_later": "#3b82f6",
            "skip": "#ef4444"
        }
        self.result_action_lbl.config(foreground=color_map.get(score_result.recommended_action, "#000000"))
        
        # Log
        self.analysis_text.insert(tk.END, f"\n🔍 Clasificado: {title[:50]}...\n")
        self.analysis_text.insert(tk.END, f"   Categoría: {category} ({confidence_pct}%)\n")
        self.analysis_text.insert(tk.END, f"   Relevance: {score_result.kdp_relevance_score}/100 - {action_text}\n")
        self.analysis_text.insert(tk.END, "-"*50 + "\n")
        self.analysis_text.see(tk.END)
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo clasificar: {e}")
        self.logger.error(f"Error en clasificación: {e}")


def clear_classification(self):
    """Limpia los campos de clasificación."""
    self.classify_title_entry.delete(0, tk.END)
    self.classify_desc_text.delete(1.0, tk.END)
    self.result_category_lbl.config(text="--")
    self.result_confidence_lbl.config(text="--%")
    self.confidence_bar['value'] = 0
    self.result_subcategories_lbl.config(text="--")
    self.result_keywords_lbl.config(text="--")
    self.result_relevance_lbl.config(text="--/100", foreground="#f59e0b")
    self.result_action_lbl.config(text="--", foreground="#000000")


def _get_kdp_categories(self):
    """Obtiene lista de categorías KDP disponibles."""
    from app.pre_ingesta.ia.category_classifier import CategoryClassifier
    return CategoryClassifier().get_available_categories()


def _format_category_name(self, category: str) -> str:
    """Formatea el nombre de categoría para mostrar."""
    return category.replace("_", " ").title()


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
