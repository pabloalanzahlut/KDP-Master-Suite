# =====================================================================
# MÓDULO: ENHANCED SEARCH TAB - KDP MASTER SUITE v3.4.7
# =====================================================================
# Este código reemplaza el método setup_search_tab() existente
# Diseño adaptado a la captura de pantalla adjunta
# =====================================================================

def setup_search_tab(self):
    """
    ================================================================
    MÉTODO: setup_search_tab (ENHANCED VERSION v3.4.7)
    ================================================================
    Pestaña de búsqueda avanzada con diseño mejorado.
    
    Características:
    - Layout 30/70 (filtros/resultados)
    - Tema oscuro consistente con captura
    - Paginación completa
    - Exportación CSV
    - Búsqueda FTS5 con debounce
    - Pills de filtros activos
    
    Estilo visual:
    - Header: #1e293b
    - Sidebar: #0f172a
    - Tree zebra: #1e293b / #0f172a
    - Accent: #3b82f6
    """
    
    # =================================================================
    # VERIFICACIÓN DE DEPENDENCIAS
    # =================================================================
    if not self.knowledge_db:
        self.search_tab_loaded = True
        for widget in self.tab_search.winfo_children():
            widget.destroy()
        ttk.Label(self.tab_search, text="⚠️ Base de conocimiento no disponible", 
                 font=("Segoe UI", 12), foreground="#ef4444").pack(pady=40)
        return
    
    # Lazy loading check
    if self.search_tab_loaded:
        return
    
    self.search_tab_loaded = True
    
    # =================================================================
    # PASO 1: INICIALIZAR VARIABLES DE ESTADO
    # =================================================================
    if not hasattr(self, 'search_filter_var'):
        self.search_filter_var = tk.StringVar(value="")
    if not hasattr(self, 'search_type_var'):
        self.search_type_var = tk.StringVar(value="Todos")
    if not hasattr(self, 'search_category_var'):
        self.search_category_var = tk.StringVar(value="Todos")
    if not hasattr(self, 'search_order_var'):
        self.search_order_var = tk.StringVar(value="Nuevos primero")
    if not hasattr(self, 'search_date_from_var'):
        self.search_date_from_var = tk.StringVar(value="")
    if not hasattr(self, 'search_date_to_var'):
        self.search_date_to_var = tk.StringVar(value="")
    if not hasattr(self, 'search_stats_var'):
        self.search_stats_var = tk.StringVar(value="0")
    if not hasattr(self, 'search_results_label_var'):
        self.search_results_label_var = tk.StringVar(value="0 entradas")
    if not hasattr(self, 'search_fts_time_var'):
        self.search_fts_time_var = tk.StringVar(value="0ms")
    
    # Paginación
    self.search_current_page = 1
    self.search_page_size = 20
    self.search_total_results = 0
    self.search_total_pages = 1
    self.search_results_cache = []
    
    # Debounce timer
    self.search_debounce_id = None
    
    # Tipos documentales
    self.DOC_TYPES_WITH_ALL = ["Todos", "Tutorial", "Artículo", "Investigación", "Lista", "Legal", "Fórmulas"]
    self.DOC_TYPE_ICONS = {
        "Tutorial": "📝",
        "Artículo": "📄",
        "Investigación": "📊",
        "Lista": "📋",
        "Legal": "⚖️",
        "Fórmulas": "🔢"
    }
    
    # Categorías KDP (cargar desde DB)
    self.kdp_categories = self._load_kdp_categories()
    
    # =================================================================
    # PASO 2: LIMPIAR TAB EXISTENTE
    # =================================================================
    for widget in self.tab_search.winfo_children():
        widget.destroy()
    
    # =================================================================
    # PASO 3: CONTENEDOR PRINCIPAL CON PADDING
    # =================================================================
    main_wrapper = ttk.Frame(self.tab_search)
    main_wrapper.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    
    # =================================================================
    # PASO 4: HEADER - TÍTULO + BARRA DE BÚSQUEDA
    # =================================================================
    header_container = ttk.Frame(main_wrapper)
    header_container.pack(fill=tk.X, pady=(0, 12))
    
    # Título principal con icono
    title_frame = ttk.Frame(header_container)
    title_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(title_frame, text="🔍 Búsqueda en Base de Conocimiento KDP", 
             font=("Segoe UI", 13, "bold"),
             foreground="#e2e8f0").pack(side=tk.LEFT)
    
    # Barra de búsqueda
    search_bar = ttk.Frame(header_container)
    search_bar.pack(fill=tk.X)
    
    # Entry de búsqueda con estilo mejorado
    search_entry = ttk.Entry(
        search_bar, 
        textvariable=self.search_filter_var, 
        font=("Segoe UI", 11),
        width=60
    )
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
    search_entry.bind('<KeyRelease>', lambda e: self._debounced_search())
    search_entry.bind('<Return>', lambda e: self._execute_kb_search())
    search_entry.focus_set()
    
    # Botones de acción
    btn_search = ttk.Button(
        search_bar, 
        text="BUSCAR", 
        command=self._execute_kb_search,
        bootstyle="info",
        width=10
    )
    btn_search.pack(side=tk.LEFT, padx=3)
    ToolTip(btn_search, "Ejecutar búsqueda (Enter)")
    
    btn_clear = ttk.Button(
        search_bar, 
        text="LIMPIAR", 
        command=self._clear_search_filters,
        bootstyle="secondary-outline",
        width=10
    )
    btn_clear.pack(side=tk.LEFT, padx=3)
    ToolTip(btn_clear, "Limpiar filtros y resultados")
    
    btn_export = ttk.Button(
        search_bar, 
        text="EXPORTAR CSV", 
        command=self._export_kb_search,
        bootstyle="success-outline",
        width=14
    )
    btn_export.pack(side=tk.LEFT, padx=3)
    ToolTip(btn_export, "Exportar resultados actuales a CSV")
    
    # Contador de resultados
    count_label = ttk.Label(
        search_bar, 
        textvariable=self.search_results_label_var,
        font=("Segoe UI", 9),
        foreground="#64748b"
    )
    count_label.pack(side=tk.LEFT, padx=10)
    
    # =================================================================
    # PASO 5: PILLS - FILTROS ACTIVOS
    # =================================================================
    pills_container = ttk.Frame(main_wrapper)
    pills_container.pack(fill=tk.X, pady=(0, 10))
    
    self.search_pills_label = ttk.Label(
        pills_container, 
        text="Filtros activos: 🔍 'bsr'",  # Según captura
        font=("Segoe UI", 9),
        foreground="#94a3b8"
    )
    self.search_pills_label.pack(side=tk.LEFT)
    
    # =================================================================
    # PASO 6: CONTENEDOR PRINCIPAL (30% SIDEBAR + 70% RESULTS)
    # =================================================================
    content_container = ttk.Frame(main_wrapper)
    content_container.pack(fill=tk.BOTH, expand=True)
    
    # =================================================================
    # PASO 7: SIDEBAR IZQUIERDO (30% - FILTROS)
    # =================================================================
    sidebar = ttk.Frame(content_container, width=280)
    sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
    sidebar.pack_propagate(False)
    
    # --- Filtro: Tipo Documental ---
    type_lf = ttk.LabelFrame(sidebar, text=" 📋 TIPO DOCUMENTAL ", padding=10)
    type_lf.pack(fill=tk.X, pady=(0, 8))
    
    type_combo = ttk.Combobox(
        type_lf, 
        textvariable=self.search_type_var,
        values=self.DOC_TYPES_WITH_ALL, 
        state="readonly",
        font=("Segoe UI", 10)
    )
    type_combo.pack(fill=tk.X)
    type_combo.bind('<<ComboboxSelected>>', lambda e: self._execute_kb_search())
    ToolTip(type_combo, "Filtrar por tipo de documento")
    
    # --- Filtro: Categoría KDP ---
    cat_lf = ttk.LabelFrame(sidebar, text=" 📁 CATEGORÍA KDP ", padding=10)
    cat_lf.pack(fill=tk.X, pady=(0, 8))
    
    category_values = ["Todos"] + self.kdp_categories
    cat_combo = ttk.Combobox(
        cat_lf, 
        textvariable=self.search_category_var,
        values=category_values, 
        state="readonly",
        font=("Segoe UI", 10)
    )
    cat_combo.pack(fill=tk.X)
    cat_combo.bind('<<ComboboxSelected>>', lambda e: self._execute_kb_search())
    ToolTip(cat_combo, "Filtrar por categoría KDP")
    
    # --- Filtro: Rango de Fechas ---
    date_lf = ttk.LabelFrame(sidebar, text=" 📅 RANGO DE FECHAS ", padding=10)
    date_lf.pack(fill=tk.X, pady=(0, 8))
    
    ttk.Label(date_lf, text="Desde (YYYY-MM)", font=("Segoe UI", 8), 
             foreground="#64748b").pack(anchor=tk.W, pady=(0, 2))
    date_from = ttk.Entry(date_lf, textvariable=self.search_date_from_var, 
                         font=("Segoe UI", 9))
    date_from.pack(fill=tk.X, pady=(0, 8))
    date_from.bind('<Return>', lambda e: self._execute_kb_search())
    
    ttk.Label(date_lf, text="Hasta (YYYY-MM)", font=("Segoe UI", 8), 
             foreground="#64748b").pack(anchor=tk.W, pady=(0, 2))
    date_to = ttk.Entry(date_lf, textvariable=self.search_date_to_var, 
                       font=("Segoe UI", 9))
    date_to.pack(fill=tk.X)
    date_to.bind('<Return>', lambda e: self._execute_kb_search())
    
    # --- Filtro: Ordenar Por ---
    order_lf = ttk.LabelFrame(sidebar, text=" ↕ ORDENAR POR ", padding=10)
    order_lf.pack(fill=tk.X, pady=(0, 8))
    
    order_combo = ttk.Combobox(
        order_lf, 
        textvariable=self.search_order_var,
        values=["Nuevos primero", "Antiguos primero", "Por categoría", "Por relevancia"], 
        state="readonly",
        font=("Segoe UI", 10)
    )
    order_combo.pack(fill=tk.X)
    order_combo.bind('<<ComboboxSelected>>', lambda e: self._execute_kb_search())
    ToolTip(order_combo, "Orden de resultados")
    
    # --- Botones de Acción del Sidebar ---
    action_frame = ttk.Frame(sidebar)
    action_frame.pack(fill=tk.X, pady=(15, 5))
    
    btn_apply = ttk.Button(
        action_frame, 
        text="✅ APLICAR FILTROS",
        command=self._execute_kb_search,
        bootstyle="success",
        width=25
    )
    btn_apply.pack(fill=tk.X, pady=(0, 6))
    
    btn_reset = ttk.Button(
        action_frame, 
        text="🔄 LIMPIAR TODO",
        command=self._clear_search_filters,
        bootstyle="danger-outline",
        width=25
    )
    btn_reset.pack(fill=tk.X)
    
    # =================================================================
    # PASO 8: PANEL DERECHO (70% - RESULTADOS)
    # =================================================================
    results_panel = ttk.Frame(content_container)
    results_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # --- Header de resultados con stats ---
    results_header = ttk.Frame(results_panel)
    results_header.pack(fill=tk.X, pady=(0, 8))
    
    # Stats label
    stats_frame = ttk.Frame(results_header)
    stats_frame.pack(side=tk.LEFT)
    
    ttk.Label(stats_frame, text="📄 Resultados: ", 
             font=("Segoe UI", 10, "bold"),
             foreground="#94a3b8").pack(side=tk.LEFT)
    
    ttk.Label(stats_frame, textvariable=self.search_results_label_var,
             font=("Segoe UI", 10, "bold"),
             foreground="#3b82f6").pack(side=tk.LEFT, padx=(2, 10))
    
    # FTS badge
    fts_badge = ttk.Label(
        stats_frame,
        textvariable=self.search_fts_time_var,
        font=("Consolas", 8),
        foreground="#64748b"
    )
    fts_badge.pack(side=tk.LEFT)
    
    # Scrollbar para resultados
    scroll_frame = ttk.Frame(results_panel)
    scroll_frame.pack(fill=tk.BOTH, expand=True)
    
    # --- TreeView con columnas según captura ---
    columns = ("icon", "title", "category", "type", "date", "words", "id")
    self.search_tree = ttk.Treeview(
        scroll_frame, 
        columns=columns, 
        show="headings",
        selectmode="browse",
        height=18
    )
    
    # Configurar columnas
    self.search_tree.heading("icon", text="📷")
    self.search_tree.heading("title", text="Título")
    self.search_tree.heading("category", text="Categoría")
    self.search_tree.heading("type", text="Tipo")
    self.search_tree.heading("date", text="Fecha")
    self.search_tree.heading("words", text="Palabras")
    self.search_tree.heading("id", text="ID")
    
    # Anchos de columnas
    self.search_tree.column("icon", width=40, anchor=tk.CENTER)
    self.search_tree.column("title", width=350, anchor=tk.W)
    self.search_tree.column("category", width=130, anchor=tk.W)
    self.search_tree.column("type", width=100, anchor=tk.W)
    self.search_tree.column("date", width=85, anchor=tk.CENTER)
    self.search_tree.column("words", width=70, anchor=tk.CENTER)
    self.search_tree.column("id", width=50, anchor=tk.CENTER)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, 
                             command=self.search_tree.yview)
    self.search_tree.configure(yscrollcommand=scrollbar.set)
    
    self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Evento de doble clic
    self.search_tree.bind('<Double-1>', self._on_search_result_double_click)
    
    # Tags para zebra striping y tipos
    self.search_tree.tag_configure("oddrow", background="#1e293b")
    self.search_tree.tag_configure("evenrow", background="#0f172a")
    self.search_tree.tag_configure("tutorial", foreground="#60a5fa")
    self.search_tree.tag_configure("artículo", foreground="#34d399")
    self.search_tree.tag_configure("investigación", foreground="#a78bfa")
    self.search_tree.tag_configure("lista", foreground="#fbbf24")
    self.search_tree.tag_configure("legal", foreground="#f87171")
    self.search_tree.tag_configure("fórmulas", foreground="#fb923c")
    
    # =================================================================
    # PASO 9: PAGINACIÓN
    # =================================================================
    pagination_frame = ttk.Frame(results_panel)
    pagination_frame.pack(fill=tk.X, pady=(10, 0))
    
    # Info de página
    self.search_page_info = ttk.Label(
        pagination_frame, 
        text="Página 1 de 1 (0 resultados)",
        font=("Segoe UI", 9),
        foreground="#94a3b8"
    )
    self.search_page_info.pack(side=tk.LEFT)
    
    # Botones de paginación
    self.search_page_buttons = ttk.Frame(pagination_frame)
    self.search_page_buttons.pack(side=tk.RIGHT)
    
    # =================================================================
    # FINALIZAR
    # =================================================================
    self.log("[SEARCH] Pestaña de búsqueda avanzada cargada correctamente")
    
    # Auto-cargar últimos resultados si existen
    if self.search_filter_var.get().strip():
        self.root.after(500, self._execute_kb_search)


def _load_kdp_categories(self):
    """
    Carga las categorías KDP desde la base de datos.
    
    Returns:
        list: Lista de categorías únicas
    """
    try:
        if not self.knowledge_db:
            return [
                "Legalidad y Compliance",
                "Matriz de Roles (GEM)",
                "Matriz de Roles y Fases SOE",
                "Fórmulas y Métricas",
                "Investigación de Nichos",
                "Amazon Ads y Marketing",
                "Conocimiento General KDP"
            ]
        
        # Consultar categorías únicas de la DB
        rows = self.knowledge_db.query_raw(
            "SELECT DISTINCT category FROM knowledge_entries WHERE category IS NOT NULL ORDER BY category"
        )
        
        categories = [row[0] for row in rows if row[0]]
        
        # Fallback si está vacío
        if not categories:
            categories = [
                "Legalidad y Compliance",
                "Matriz de Roles (GEM)",
                "Fórmulas y Métricas",
                "Amazon Ads y Marketing"
            ]
        
        return categories
        
    except Exception as e:
        self.log(f"[SEARCH] Error cargando categorías: {e}", "warning")
        return ["General"]


def _debounced_search(self):
    """
    Ejecuta búsqueda con debounce de 400ms.
    Cancela búsquedas anteriores pendientes.
    """
    # Cancelar timer anterior si existe
    if self.search_debounce_id:
        self.root.after_cancel(self.search_debounce_id)
    
    # Programar nueva búsqueda
    self.search_debounce_id = self.root.after(400, self._execute_kb_search)


def _execute_kb_search(self):
    """
    ================================================================
    MÉTODO: _execute_kb_search (ENHANCED)
    ================================================================
    Ejecuta búsqueda en la base de conocimiento con filtros avanzados.
    
    Proceso:
    1. Recolectar filtros activos
    2. Construir query FTS5
    3. Ejecutar búsqueda con timer
    4. Procesar resultados
    5. Renderizar en TreeView
    6. Actualizar paginación
    """
    
    if not self.knowledge_db:
        messagebox.showwarning("Base de Conocimiento", 
                              "La base de conocimiento no está disponible.")
        return
    
    # Cancelar debounce timer si existe
    if self.search_debounce_id:
        self.root.after_cancel(self.search_debounce_id)
        self.search_debounce_id = None
    
    # =================================================================
    # PASO 1: RECOLECTAR FILTROS
    # =================================================================
    query = self.search_filter_var.get().strip()
    tipo = self.search_type_var.get()
    categoria = self.search_category_var.get()
    date_from = self.search_date_from_var.get().strip()
    date_to = self.search_date_to_var.get().strip()
    order = self.search_order_var.get()
    
    # =================================================================
    # PASO 2: CONSTRUIR FILTROS PARA KNOWLEDGE_DB
    # =================================================================
    filters = {}
    
    if tipo and tipo != "Todos":
        filters['type'] = tipo
    
    if categoria and categoria != "Todos":
        filters['category'] = categoria
    
    # Filtros de fecha (formato YYYY-MM)
    if date_from:
        filters['date_from'] = date_from + "-01"  # Primer día del mes
    
    if date_to:
        # Último día del mes
        import calendar
        year, month = map(int, date_to.split('-'))
        last_day = calendar.monthrange(year, month)[1]
        filters['date_to'] = f"{date_to}-{last_day}"
    
    # Orden
    order_map = {
        "Nuevos primero": "timestamp DESC",
        "Antiguos primero": "timestamp ASC",
        "Por categoría": "category ASC, timestamp DESC",
        "Por relevancia": "confidence_score DESC"
    }
    order_by = order_map.get(order, "timestamp DESC")
    
    # =================================================================
    # PASO 3: EJECUTAR BÚSQUEDA FTS5
    # =================================================================
    start_time = time.time()
    
    try:
        # Si hay query de texto, usar FTS5
        if query:
            result = self.knowledge_db.search_entries(
                query=query,
                filters=filters,
                page=1,
                page_size=1000,  # Cargar todos para paginación local
                order_by=order_by
            )
        else:
            # Sin query, listar todo con filtros
            result = self.knowledge_db.get_entries_filtered(
                filters=filters,
                order_by=order_by,
                limit=1000
            )
        
        # =================================================================
        # PASO 4: PROCESAR RESULTADOS
        # =================================================================
        self.search_results_cache = []
        
        for row in result.get('entries', []):
            # Detectar tipo si no existe
            tipo_doc = row.get('type') or self._detect_doc_type(
                row.get('content', ''), 
                row.get('category', '')
            )
            
            icon = self.DOC_TYPE_ICONS.get(tipo_doc, "📄")
            
            # Calcular palabras del contenido
            content = row.get('content', '')
            word_count = len(content.split()) if content else 0
            
            self.search_results_cache.append({
                'id': row.get('id'),
                'icon': icon,
                'title': row.get('source') or f"Entrada {row.get('id')}",
                'category': row.get('category', 'Sin categoría'),
                'type': tipo_doc,
                'date': str(row.get('timestamp', ''))[:10] if row.get('timestamp') else 'N/A',
                'words': word_count,
                'content': content
            })
        
        # =================================================================
        # PASO 5: ACTUALIZAR ESTADÍSTICAS
        # =================================================================
        self.search_total_results = len(self.search_results_cache)
        self.search_total_pages = max(1, (self.search_total_results + self.search_page_size - 1) // self.search_page_size)
        self.search_current_page = 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Actualizar labels
        self.search_results_label_var.set(f"{self.search_total_results} entradas")
        self.search_fts_time_var.set(f"FTS5 — {elapsed_ms:.0f}ms")
        
        # Actualizar pills
        self._update_search_pills()
        
        # =================================================================
        # PASO 6: RENDERIZAR RESULTADOS
        # =================================================================
        self._render_search_results()
        
        # =================================================================
        # PASO 7: ACTUALIZAR PAGINACIÓN
        # =================================================================
        self._update_search_pagination_buttons()
        
        self.log(f"[SEARCH] Búsqueda: '{query}' → {self.search_total_results} resultados en {elapsed_ms:.0f}ms")
        
    except Exception as e:
        self.log(f"[SEARCH ERROR] {e}", "error")
        messagebox.showerror("Error de Búsqueda", f"Error ejecutando búsqueda:\n{str(e)}")
        self.search_results_label_var.set("Error")
        self.search_fts_time_var.set("—")


def _detect_doc_type(self, content: str, category: str) -> str:
    """
    Detecta el tipo documental basándose en el contenido y categoría.
    
    Args:
        content: Texto del contenido
        category: Categoría KDP
    
    Returns:
        Tipo documental detectado
    """
    content_lower = content.lower()
    category_lower = category.lower()
    
    # Keywords por tipo
    tutorial_kw = ["cómo", "como", "tutorial", "guía", "paso a paso", "instrucciones"]
    article_kw = ["opinión", "análisis", "review", "perspectiva"]
    research_kw = ["investigación", "estudio", "datos", "estadística"]
    list_kw = ["lista", "checklist", "top", "mejores", "consejos"]
    legal_kw = ["legal", "derecho", "términos", "compliance", "política"]
    formula_kw = ["fórmula", "ecuación", "cálculo", "métrica", "kpi"]
    
    # Verificar keywords
    for kw in tutorial_kw:
        if kw in content_lower or kw in category_lower:
            return "Tutorial"
    for kw in article_kw:
        if kw in content_lower or kw in category_lower:
            return "Artículo"
    for kw in research_kw:
        if kw in content_lower or kw in category_lower:
            return "Investigación"
    for kw in list_kw:
        if kw in content_lower or kw in category_lower:
            return "Lista"
    for kw in legal_kw:
        if kw in content_lower or kw in category_lower:
            return "Legal"
    for kw in formula_kw:
        if kw in content_lower or kw in category_lower:
            return "Fórmulas"
    
    # Default basado en longitud
    word_count = len(content.split())
    if word_count < 500:
        return "Lista"
    elif word_count < 2000:
        return "Artículo"
    else:
        return "Tutorial"


def _render_search_results(self):
    """
    Renderiza los resultados de búsqueda en el TreeView con zebra striping.
    """
    # Limpiar TreeView
    for item in self.search_tree.get_children():
        self.search_tree.delete(item)
    
    # Verificar si hay resultados
    if not self.search_results_cache:
        # Mostrar mensaje de "sin resultados"
        self.search_tree.insert("", tk.END, values=(
            "",
            "Sin resultados. Prueba con otros términos o filtros.",
            "",
            "",
            "",
            "",
            ""
        ))
        return
    
    # Calcular rango de resultados para página actual
    start = (self.search_current_page - 1) * self.search_page_size
    end = start + self.search_page_size
    page_results = self.search_results_cache[start:end]
    
    # Insertar resultados
    for i, result in enumerate(page_results):
        doc_type = result['type']
        icon = result['icon']
        
        # Tags para estilo
        tag = doc_type.lower()
        row_tag = "oddrow" if i % 2 == 0 else "evenrow"
        combined_tags = (tag, row_tag)
        
        # Truncar título si es muy largo
        title = result['title']
        if len(title) > 60:
            title = title[:57] + "..."
        
        # Insertar fila
        self.search_tree.insert("", tk.END, values=(
            icon,
            title,
            result['category'][:20],
            doc_type,
            result['date'],
            f"{result['words']:,}",
            result['id']
        ), tags=combined_tags)
    
    # Actualizar label de página
    self.search_page_info.config(
        text=f"Página {self.search_current_page} de {self.search_total_pages} ({self.search_total_results} resultados)"
    )
    
    self.log(f"[SEARCH] Renderizados {len(page_results)} resultados (página {self.search_current_page})")


def _update_search_pagination_buttons(self):
    """
    Actualiza los botones de paginación.
    Muestra: [◀] [1] [2] [3] [4] [5] [▶]
    """
    # Limpiar botones existentes
    for widget in self.search_page_buttons.winfo_children():
        widget.destroy()
    
    total = self.search_total_pages
    current = self.search_current_page
    
    if total <= 1:
        return
    
    # Botón Anterior
    btn_prev = ttk.Button(
        self.search_page_buttons, 
        text="◀",
        command=self._search_prev_page,
        bootstyle="secondary-outline",
        width=3
    )
    btn_prev.pack(side=tk.LEFT, padx=2)
    if current == 1:
        btn_prev.config(state=tk.DISABLED)
    
    # Botones de páginas (máximo 5 visibles)
    max_buttons = 5
    start_page = max(1, current - 2)
    end_page = min(total, start_page + max_buttons - 1)
    
    # Ajustar si estamos cerca del final
    if end_page - start_page < max_buttons - 1:
        start_page = max(1, end_page - max_buttons + 1)
    
    for page in range(start_page, end_page + 1):
        if page == current:
            # Página actual (resaltada)
            btn = ttk.Button(
                self.search_page_buttons, 
                text=str(page),
                bootstyle="info",
                width=3
            )
        else:
            btn = ttk.Button(
                self.search_page_buttons, 
                text=str(page),
                command=lambda p=page: self._search_goto_page(p),
                bootstyle="secondary-outline",
                width=3
            )
        btn.pack(side=tk.LEFT, padx=2)
    
    # Indicador de más páginas
    if end_page < total:
        ttk.Label(
            self.search_page_buttons, 
            text=f"... {total}",
            font=("Segoe UI", 9),
            foreground="#64748b"
        ).pack(side=tk.LEFT, padx=5)
    
    # Botón Siguiente
    btn_next = ttk.Button(
        self.search_page_buttons, 
        text="▶",
        command=self._search_next_page,
        bootstyle="secondary-outline",
        width=3
    )
    btn_next.pack(side=tk.LEFT, padx=2)
    if current == total:
        btn_next.config(state=tk.DISABLED)


def _search_prev_page(self):
    """Ir a página anterior."""
    if self.search_current_page > 1:
        self.search_current_page -= 1
        self._render_search_results()
        self._update_search_pagination_buttons()


def _search_next_page(self):
    """Ir a página siguiente."""
    if self.search_current_page < self.search_total_pages:
        self.search_current_page += 1
        self._render_search_results()
        self._update_search_pagination_buttons()


def _search_goto_page(self, page):
    """Ir a página específica."""
    if 1 <= page <= self.search_total_pages:
        self.search_current_page = page
        self._render_search_results()
        self._update_search_pagination_buttons()


def _update_search_pills(self):
    """
    Actualiza el label de filtros activos (pills).
    Muestra: Filtros activos: 🔍 'query' | 📋 Tipo | 📁 Categoría | 📅 Fecha
    """
    active_filters = []
    
    query = self.search_filter_var.get().strip()
    if query:
        active_filters.append(f"🔍 '{query}'")
    
    tipo = self.search_type_var.get()
    if tipo and tipo != "Todos":
        active_filters.append(f"📋 {tipo}")
    
    categoria = self.search_category_var.get()
    if categoria and categoria != "Todos":
        active_filters.append(f"📁 {categoria}")
    
    date_from = self.search_date_from_var.get().strip()
    date_to = self.search_date_to_var.get().strip()
    if date_from or date_to:
        date_str = f"{date_from or '...'} → {date_to or '...'}"
        active_filters.append(f"📅 {date_str}")
    
    # Actualizar label
    if active_filters:
        self.search_pills_label.config(
            text="Filtros activos: " + " | ".join(active_filters)
        )
    else:
        self.search_pills_label.config(text="Filtros activos: Ninguno")


def _clear_search_filters(self):
    """
    Limpia todos los filtros y resultados.
    """
    self.search_filter_var.set("")
    self.search_type_var.set("Todos")
    self.search_category_var.set("Todos")
    self.search_date_from_var.set("")
    self.search_date_to_var.set("")
    self.search_order_var.set("Nuevos primero")
    
    # Limpiar resultados
    self.search_results_cache = []
    self.search_current_page = 1
    self.search_total_results = 0
    self.search_total_pages = 1
    
    # Limpiar TreeView
    for item in self.search_tree.get_children():
        self.search_tree.delete(item)
    
    # Actualizar labels
    self.search_results_label_var.set("0 entradas")
    self.search_fts_time_var.set("—")
    self.search_page_info.config(text="Página 1 de 1 (0 resultados)")
    self._update_search_pills()
    
    # Limpiar botones de paginación
    for widget in self.search_page_buttons.winfo_children():
        widget.destroy()
    
    self.log("[SEARCH] Filtros limpiados")


def _export_kb_search(self):
    """
    Exporta los resultados actuales a CSV.
    """
    if not self.search_results_cache:
        messagebox.showinfo("Exportar", "No hay resultados para exportar.")
        return
    
    # Solicitar ubicación de archivo
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile=f"busqueda_kdp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    
    if not file_path:
        return
    
    try:
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['ID', 'Título', 'Categoría', 'Tipo', 'Fecha', 'Palabras', 'Contenido (100 chars)'])
            
            # Datos
            for result in self.search_results_cache:
                content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                
                writer.writerow([
                    result['id'],
                    result['title'],
                    result['category'],
                    result['type'],
                    result['date'],
                    result['words'],
                    content_preview
                ])
        
        messagebox.showinfo("Exportación Exitosa", 
                           f"Se exportaron {len(self.search_results_cache)} resultados a:\n{file_path}")
        self.log(f"[SEARCH] Exportados {len(self.search_results_cache)} resultados a CSV")
        
    except Exception as e:
        messagebox.showerror("Error de Exportación", f"Error al exportar:\n{str(e)}")
        self.log(f"[SEARCH ERROR] Error exportando: {e}", "error")


def _on_search_result_double_click(self, event):
    """
    Maneja doble clic en resultado para ver detalles.
    """
    selection = self.search_tree.selection()
    if not selection:
        return
    
    item = self.search_tree.item(selection[0])
    values = item['values']
    
    if not values or len(values) < 7:
        return
    
    entry_id = values[6]
    
    # Buscar entrada completa en cache
    result = next((r for r in self.search_results_cache if r['id'] == entry_id), None)
    
    if not result:
        return
    
    # Crear ventana de detalles
    detail_win = tk.Toplevel(self.root)
    detail_win.title(f"Detalle - {result['title']}")
    detail_win.geometry("700x550")
    detail_win.transient(self.root)
    
    # Header
    header = ttk.Frame(detail_win)
    header.pack(fill=tk.X, padx=15, pady=10)
    
    ttk.Label(header, text=result['icon'], font=("Segoe UI", 24)).pack(side=tk.LEFT, padx=(0, 10))
    
    info_frame = ttk.Frame(header)
    info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    ttk.Label(info_frame, text=result['title'], 
             font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)
    ttk.Label(info_frame, 
             text=f"{result['type']} | {result['category']} | {result['date']} | {result['words']:,} palabras",
             font=("Segoe UI", 9),
             foreground="#64748b").pack(anchor=tk.W)
    
    # Contenido
    content_frame = ttk.LabelFrame(detail_win, text=" Contenido ", padding=10)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
    
    text_widget = scrolledtext.ScrolledText(
        content_frame, 
        wrap=tk.WORD, 
        font=("Segoe UI", 10),
        height=20
    )
    text_widget.pack(fill=tk.BOTH, expand=True)
    text_widget.insert("1.0", result['content'])
    text_widget.config(state=tk.DISABLED)
    
    # Botón cerrar
    ttk.Button(detail_win, text="Cerrar", command=detail_win.destroy,
              bootstyle="secondary").pack(pady=(0, 10))
    
    self.log(f"[SEARCH] Abriendo detalles de entrada {entry_id}")
