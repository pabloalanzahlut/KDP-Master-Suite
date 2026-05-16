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

    # MÓDULO: Panel de Curación Inteligente
    setup_curation_panel(self)


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


# ==================== MÓDULOS DE CURACIÓN INTELIGENTE ====================

def setup_curation_panel(self):
    """Configura el panel de curación inteligente en analyze_tab."""
    try:
        from app.services.curation_metrics_service import create_curation_metrics_service
        from app.services.recommendation_engine import create_recommendation_engine
        from app.services.topic_grouper import create_topic_grouper

        # Crear servicios
        self.curation_metrics = create_curation_metrics_service(
            db_manager=getattr(self, 'db_manager', None)
        )
        self.recommendation_engine = create_recommendation_engine()
        self.topic_grouper = create_topic_grouper()

        # Panel de Curación
        curation_frame = ttk.LabelFrame(self.tab_analyze, text=" 🎯 Panel de Curación Inteligente ", padding=15)
        curation_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Fila 1: Métricas de salud
        health_frame = ttk.Frame(curation_frame)
        health_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(health_frame, text="📊 Analizar Salud del Canal",
                  command=self.analyze_channel_health).pack(side=tk.LEFT, padx=2)

        ttk.Button(health_frame, text="🏷️ Agrupar por Tema",
                  command=self.group_videos_by_topic).pack(side=tk.LEFT, padx=2)

        ttk.Button(health_frame, text="🔍 Recomendaciones",
                  command=self.show_recommendations).pack(side=tk.LEFT, padx=2)

        ttk.Button(health_frame, text="📈 Dashboard",
                  command=self.show_curation_dashboard).pack(side=tk.LEFT, padx=2)

        # Panel de resultados de curación
        self.curation_result_text = scrolledtext.ScrolledText(
            curation_frame, height=12, font=('Consolas', 9)
        )
        self.curation_result_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    except Exception as e:
        print(f"Error configurando panel de curación: {e}")


def analyze_channel_health(self):
    """Analiza la salud del canal y muestra métricas."""
    if not hasattr(self, 'curation_metrics'):
        self.curation_result_text.insert(tk.END, "\n⚠️ Servicio de métricas no disponible\n")
        return

    self.curation_result_text.delete(1.0, tk.END)
    self.curation_result_text.insert(tk.END, "📊 ANALIZANDO SALUD DEL CANAL...\n\n")

    try:
        health = self.curation_metrics.get_channel_health_score()

        self.curation_result_text.insert(tk.END, f"   Health Score: {health.get('health_score', 0)}/100\n")
        self.curation_result_text.insert(tk.END, f"   Total Videos: {health.get('total_videos', 0)}\n")
        self.curation_result_text.insert(tk.END, f"   Avg Relevance: {health.get('avg_relevance', 0)}/100\n")
        self.curation_result_text.insert(tk.END, f"   Último Scan: {health.get('last_scan', 'N/A')}\n\n")

        # Distribución
        dist = health.get('quality_distribution', {})
        self.curation_result_text.insert(tk.END, "📈 DISTRIBUCIÓN DE CALIDAD:\n")
        self.curation_result_text.insert(tk.END, f"   Crítico (90-100): {dist.get('critical', 0)}\n")
        self.curation_result_text.insert(tk.END, f"   Alto (70-89): {dist.get('high', 0)}\n")
        self.curation_result_text.insert(tk.END, f"   Medio (50-69): {dist.get('medium', 0)}\n")
        self.curation_result_text.insert(tk.END, f"   Bajo (30-49): {dist.get('low', 0)}\n")
        self.curation_result_text.insert(tk.END, f"   Trivial (0-29): {dist.get('trivial', 0)}\n\n")

        # Recomendaciones
        self.curation_result_text.insert(tk.END, "💡 RECOMENDACIONES:\n")
        for rec in health.get('recommendations', []):
            self.curation_result_text.insert(tk.END, f"   • {rec}\n")

        self.curation_result_text.insert(tk.END, "\n✅ Análisis completado\n")

    except Exception as e:
        self.curation_result_text.insert(tk.END, f"\n❌ Error: {e}\n")


def group_videos_by_topic(self):
    """Agrupa videos por tema y muestra resumen."""
    if not hasattr(self, 'topic_grouper'):
        self.curation_result_text.insert(tk.END, "\n⚠️ Servicio de grouping no disponible\n")
        return

    self.curation_result_text.delete(1.0, tk.END)
    self.curation_result_text.insert(tk.END, "🏷️ AGRUPANDO VIDEOS POR TEMA...\n\n")

    try:
        # Obtener videos de la DB
        videos = []
        if hasattr(self, 'db_manager') and self.db_manager:
            channels = self.db_manager.get_all_channels()
            for ch in channels:
                ch_videos = self.db_manager.get_videos_by_channel(ch['id'])
                for v in ch_videos:
                    v['channel_name'] = ch.get('channel_name', '')
                    videos.append(v)

        if not videos:
            self.curation_result_text.insert(tk.END, "   No hay videos para agrupar\n")
            return

        # Clasificar topics
        from app.services.topic_grouper import TopicGrouper
        grouper = TopicGrouper()
        summary = grouper.get_topic_summary(videos)

        self.curation_result_text.insert(tk.END, f"📊 Total Videos: {summary['total_videos']}\n")
        self.curation_result_text.insert(tk.END, f"🏷️ Temas Detectados: {summary['topics_count']}\n\n")

        self.curation_result_text.insert(tk.END, "📋 RESUMEN POR TEMA:\n")
        for topic_info in summary['topics']:
            pct = topic_info['percentage']
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            self.curation_result_text.insert(
                tk.END,
                f"   {topic_info['topic']:15} [{bar}] {topic_info['count']:3} ({pct}%)\n"
            )

        # Batches optimizados
        optimized = grouper.optimize_batch_order(videos)
        self.curation_result_text.insert(tk.END, f"\n✅ {len(optimized)} videos optimizados para procesamiento\n")

    except Exception as e:
        self.curation_result_text.insert(tk.END, f"\n❌ Error: {e}\n")


def show_recommendations(self):
    """Muestra recomendaciones para videos."""
    if not hasattr(self, 'recommendation_engine'):
        self.curation_result_text.insert(tk.END, "\n⚠️ Servicio de recomendaciones no disponible\n")
        return

    self.curation_result_text.delete(1.0, tk.END)
    self.curation_result_text.insert(tk.END, "🔍 GENERANDO RECOMENDACIONES...\n\n")

    try:
        # Obtener videos recientes
        videos = []
        if hasattr(self, 'db_manager') and self.db_manager:
            channels = self.db_manager.get_all_channels()
            for ch in channels:
                ch_videos = self.db_manager.get_videos_by_channel(ch['id'])[:10]
                for v in ch_videos:
                    v['channel_name'] = ch.get('channel_name', '')
                    videos.append(v)

        if len(videos) < 2:
            self.curation_result_text.insert(tk.END, "   Se necesitan al menos 2 videos para recomendaciones\n")
            return

        # Seleccionar video de referencia (primero)
        ref_video = videos[0]
        ref_title = ref_video.get('title', 'Unknown')

        # Encontrar relacionados
        related = self.recommendation_engine.find_related_videos(
            target_title=ref_title,
            target_description='',
            video_pool=videos,
            limit=5
        )

        self.curation_result_text.insert(tk.END, f"📌 VIDEO REFERENCIA:\n   {ref_title[:60]}\n\n")
        self.curation_result_text.insert(tk.END, "🔗 VIDEOS RELACIONADOS:\n")

        for item in related:
            vid = item['video']
            title = vid.get('title', 'Unknown')[:50]
            score = item['combined_score']
            marker = "📺" if item.get('is_series_next') else "  "
            self.curation_result_text.insert(
                tk.END,
                f"   {marker} [{score:.2f}] {title}\n"
            )

        self.curation_result_text.insert(tk.END, "\n✅ Recomendaciones generadas\n")

    except Exception as e:
        self.curation_result_text.insert(tk.END, f"\n❌ Error: {e}\n")


def show_curation_dashboard(self):
    """Muestra ventana de dashboard visual con gráficos de curación."""
    if not hasattr(self, 'curation_metrics'):
        messagebox.showwarning("⚠️", "Servicio de métricas no disponible")
        return
    
    dashboard = tk.Toplevel(self.root)
    dashboard.title("📊 Dashboard de Curación KDP")
    dashboard.geometry("800x600")
    
    main_frame = ttk.Frame(dashboard, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="🎯 Dashboard de Curación Inteligente", 
               font=("Segoe UI", 14, "bold")).pack(pady=(0, 15))
    
    stats_frame = ttk.LabelFrame(main_frame, text="📈 Estadísticas del Canal", padding=15)
    stats_frame.pack(fill=tk.X, pady=(0, 10))
    
    try:
        stats = self.curation_metrics.get_channel_health_score()
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        ttk.Label(stats_grid, text=f"Total Videos: {stats.get('total_videos', 0)}", 
                  font=("Segoe UI", 11)).grid(row=0, column=0, padx=20, pady=5, sticky=tk.W)
        ttk.Label(stats_grid, text=f"Health Score: {stats.get('health_score', 0)}/100", 
                  font=("Segoe UI", 11)).grid(row=0, column=1, padx=20, pady=5, sticky=tk.W)
        ttk.Label(stats_grid, text=f"Avg Relevance: {stats.get('avg_relevance', 0):.1f}/100", 
                  font=("Segoe UI", 11)).grid(row=0, column=2, padx=20, pady=5, sticky=tk.W)
        
        dist = stats.get('quality_distribution', {})
        dist_frame = ttk.LabelFrame(main_frame, text="📊 Distribución de Calidad", padding=15)
        dist_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        colors = {'critical': '#ef4444', 'high': '#22c55e', 'medium': '#eab308', 'low': '#94a3b8'}
        labels = {'critical': '🔴 Crítico (>90)', 'high': '🟢 Alto (70-90)', 
                  'medium': '🟡 Medio (40-70)', 'low': '⚪ Bajo (<40)'}
        
        for key in ['critical', 'high', 'medium', 'low']:
            count = dist.get(key, 0)
            color = colors.get(key, '#ccc')
            label = labels.get(key, key)
            
            row_frame = ttk.Frame(dist_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(row_frame, text=label, width=20, anchor=tk.W).pack(side=tk.LEFT)
            
            bar_canvas = tk.Canvas(row_frame, height=20, width=300, bg="#f1f5f9", highlightthickness=0)
            bar_canvas.pack(side=tk.LEFT, padx=10)
            
            max_val = max(dist.get('critical', 1), dist.get('high', 1), 
                         dist.get('medium', 1), dist.get('low', 1), 1)
            bar_width = (count / max_val) * 280 if max_val > 0 else 0
            bar_canvas.create_rectangle(2, 2, 2 + bar_width, 18, fill=color, outline="")
            
            ttk.Label(row_frame, text=f"{count} videos", width=10).pack(side=tk.LEFT)
        
        topics_frame = ttk.LabelFrame(main_frame, text="🏷️ Topics Detectados", padding=15)
        topics_frame.pack(fill=tk.BOTH, expand=True)
        
        topics_list = ttk.Frame(topics_frame)
        topics_list.pack(fill=tk.BOTH, expand=True)
        
        if hasattr(self, 'topic_grouper') and self.topic_grouper:
            topic_canvas = tk.Canvas(topics_list)
            topic_scroll = ttk.Scrollbar(topics_list, orient="vertical", command=topic_canvas.yview)
            topic_canvas.configure(yscrollcommand=topic_scroll.set)
            
            topic_frame = ttk.Frame(topic_canvas)
            topic_canvas.create_window((0, 0), window=topic_frame, anchor=tk.NW)
            
            topic_frame.bind("<Configure>", lambda e: topic_canvas.configure(scrollregion=topic_canvas.bbox("all")))
            
            topic_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            topic_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for i, topic in enumerate(['KDP Publishing', 'Amazon KDP', 'Self Publishing', 
                                       'Book Marketing', 'Ebook Creation', 'Passive Income']):
                ttk.Label(topic_frame, text=f"📁 {topic}", font=("Segoe UI", 10)).pack(anchor=tk.W, pady=2)
        else:
            ttk.Label(topics_list, text="Agrupar videos por tema para ver topics").pack()
            
    except Exception as e:
        ttk.Label(main_frame, text=f"Error cargando dashboard: {e}", foreground="red").pack()
    
    ttk.Button(main_frame, text="Cerrar", command=dashboard.destroy).pack(pady=10)
