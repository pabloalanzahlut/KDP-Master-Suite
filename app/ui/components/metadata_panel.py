"""
KDP Master - Metadata Panel Component
=======================================
Panel para mostrar metadatos enriquecidos de entradas de la KB.
"""

import tkinter as tk
from tkinter import ttk


class MetadataPanel(ttk.Frame):
    """Panel para mostrar metadatos de una entrada de la KB."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_widgets()
        self.current_entry = None
    
    def _create_widgets(self):
        """Crea los widgets del panel."""
        title_label = ttk.Label(
            self, 
            text="📊 Metadatos",
            font=("Segoe UI", 11, "bold")
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fields = {}
        
        field_configs = [
            ("duration", "⏱️ Duración", "-"),
            ("views", "👁️ Vistas", "-"),
            ("likes", "👍 Likes", "-"),
            ("is_short", "🎬 Short", "-"),
            ("upload_date", "📅 Fecha", "-"),
            ("channel", "📺 Canal", "-"),
            ("keywords", "🏷️ Keywords", "-"),
            ("enriched", "✨ Enriquecido", "-")
        ]
        
        for key, label, default in field_configs:
            row = ttk.Frame(self.content_frame)
            row.pack(fill=tk.X, pady=2)
            
            ttk.Label(
                row, 
                text=label,
                font=("Segoe UI", 9)
            ).pack(side=tk.LEFT)
            
            value_label = ttk.Label(
                row, 
                text=default,
                font=("Segoe UI", 9, "bold"),
                foreground="#10b981"
            )
            value_label.pack(side=tk.RIGHT)
            
            self.fields[key] = value_label
        
        self.empty_label = ttk.Label(
            self.content_frame,
            text="Seleccione una entrada\npara ver metadatos",
            font=("Segoe UI", 9),
            foreground="#666"
        )
        self.empty_label.pack(pady=20)
    
    def show_entry(self, entry_data: dict):
        """Muestra los metadatos de una entrada."""
        self.current_entry = entry_data
        self.empty_label.pack_forget()
        
        metadata = entry_data.get('metadata_json', {})
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        duration = entry_data.get('duration_seconds')
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            self.fields['duration'].config(text=f"{minutes:02d}:{seconds:02d}")
        else:
            self.fields['duration'].config(text="-")
        
        views = entry_data.get('view_count', 0)
        self.fields['views'].config(text=f"{views:,}" if views else "-")
        
        likes = entry_data.get('like_count', 0)
        self.fields['likes'].config(text=f"{likes:,}" if likes else "-")
        
        is_short = entry_data.get('is_short', False)
        self.fields['is_short'].config(text="Sí" if is_short else "No")
        
        upload_date = entry_data.get('upload_date', '-')
        self.fields['upload_date'].config(text=upload_date[:10] if upload_date and upload_date != 'None' else "-")
        
        channel = entry_data.get('channel_name', '-')
        self.fields['channel'].config(text=channel[:20] if channel else "-")
        
        keywords = entry_data.get('keywords', '')
        if keywords:
            if isinstance(keywords, str):
                import json
                try:
                    kw_list = json.loads(keywords)
                    keywords = ', '.join(kw_list[:5])
                except:
                    keywords = keywords[:30]
            else:
                keywords = ', '.join(str(k) for k in keywords[:5])
            self.fields['keywords'].config(text=f"{keywords[:25]}...")
        else:
            self.fields['keywords'].config(text="-")
        
        enriched = entry_data.get('enriched_via_api', False)
        self.fields['enriched'].config(
            text="API" if enriched else "Pasivo",
            foreground="#10b981" if enriched else "#666"
        )
    
    def clear(self):
        """Limpia el panel."""
        self.current_entry = None
        self.empty_label.pack(pady=20)
        
        for key, label in self.fields.items():
            if key == 'enriched':
                label.config(text="-", foreground="#666")
            else:
                label.config(text="-")


class MetadataDashboard(ttk.Frame):
    """Dashboard de estadísticas de enriquecimiento de metadatos."""
    
    def __init__(self, parent, db_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.db_manager = db_manager
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea los widgets del dashboard."""
        title = ttk.Label(
            self,
            text="📈 Dashboard de Enriquecimiento",
            font=("Segoe UI", 12, "bold")
        )
        title.pack(pady=(0, 15))
        
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_labels = {}
        
        stats_config = [
            ("total_entries", "Total Entradas", "0"),
            ("with_metadata", "Con Metadatos", "0"),
            ("with_keywords", "Con Keywords", "0"),
            ("enriched_api", "Enriquec. API", "0"),
            ("shorts_count", "Total Shorts", "0"),
            ("avg_duration", "Duración Prom.", "0:00")
        ]
        
        for i, (key, label, default) in enumerate(stats_config):
            row = i // 2
            col = i % 2
            
            card = ttk.LabelFrame(stats_frame, text=label, padding=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            value_label = ttk.Label(
                card,
                text=default,
                font=("Segoe UI", 16, "bold"),
                foreground="#3b82f6"
            )
            value_label.pack()
            
            self.stats_labels[key] = value_label
        
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        
        refresh_btn = ttk.Button(
            self,
            text="🔄 Actualizar",
            command=self.refresh_stats
        )
        refresh_btn.pack(pady=10)
    
    def refresh_stats(self):
        """Actualiza las estadísticas del dashboard."""
        if not self.db_manager:
            return
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries")
            total = cursor.fetchone()['count']
            self.stats_labels['total_entries'].config(text=str(total))
            
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries WHERE metadata_json IS NOT NULL AND metadata_json != ''")
            with_meta = cursor.fetchone()['count']
            self.stats_labels['with_metadata'].config(text=str(with_meta))
            
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries WHERE keywords IS NOT NULL AND keywords != ''")
            with_kw = cursor.fetchone()['count']
            self.stats_labels['with_keywords'].config(text=str(with_kw))
            
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries WHERE enriched_via_api = 1")
            enriched = cursor.fetchone()['count']
            self.stats_labels['enriched_api'].config(text=str(enriched))
            
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries WHERE is_short = 1")
            shorts = cursor.fetchone()['count']
            self.stats_labels['shorts_count'].config(text=str(shorts))
            
            cursor.execute("SELECT AVG(duration_seconds) as avg FROM knowledge_entries WHERE duration_seconds IS NOT NULL")
            avg_dur = cursor.fetchone()['avg']
            if avg_dur:
                mins = int(avg_dur) // 60
                secs = int(avg_dur) % 60
                self.stats_labels['avg_duration'].config(text=f"{mins}:{secs:02d}")
            
            conn.close()
        except Exception as e:
            print(f"Error refresh stats: {e}")