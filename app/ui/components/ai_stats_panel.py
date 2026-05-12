"""
AI Stats Panel Component
========================
Panel UI para mostrar estadísticas de módulos IA.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any
from datetime import datetime


class AIStatsPanel(tk.Frame):
    """
    Panel de estadísticas de IA.
    Muestra métricas de módulos IA y estado del sistema.
    """

    def __init__(self, parent, orchestrator=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._orchestrator = orchestrator
        self._refresh_interval = 5000
        self._setup_ui()
        self._start_auto_refresh()

    def _setup_ui(self):
        """Configura la interfaz del panel."""
        self.configure(bg='#1e1e1e')

        title_frame = tk.Frame(self, bg='#1e1e1e')
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        title = tk.Label(
            title_frame,
            text="🤖 Panel de Estadísticas IA",
            font=('Segoe UI', 12, 'bold'),
            fg='white',
            bg='#1e1e1e'
        )
        title.pack(side=tk.LEFT)

        refresh_btn = tk.Button(
            title_frame,
            text="🔄",
            command=self.refresh_stats,
            bg='#2d2d2d',
            fg='white',
            bd=0,
            padx=10,
            pady=2,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.RIGHT)

        separator = tk.Frame(self, height=1, bg='#3d3d3d')
        separator.pack(fill=tk.X, padx=10, pady=5)

        content_frame = tk.Frame(self, bg='#1e1e1e')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._stats_labels = {}

        stats_grid = [
            ('Ollama Status', 'ollama_status', 'circle'),
            ('Videos Analizados', 'total_analyzed', 'number'),
            ('Tiempo Promedio', 'avg_time_ms', 'text'),
            ('Tiempo Total', 'total_time_ms', 'text'),
            ('Módulos Activos', 'modules_active', 'number'),
        ]

        for i, (label, key, style) in enumerate(stats_grid):
            row = i // 2
            col = (i % 2) * 2

            label_widget = tk.Label(
                content_frame,
                text=f"{label}:",
                font=('Segoe UI', 9),
                fg='#888888',
                bg='#1e1e1e',
                anchor='w'
            )
            label_widget.grid(row=row, column=col, sticky='w', padx=(0, 5), pady=2)

            value_widget = tk.Label(
                content_frame,
                text="--",
                font=('Segoe UI', 9, 'bold'),
                fg='white',
                bg='#1e1e1e',
                anchor='w'
            )
            value_widget.grid(row=row, column=col+1, sticky='w', pady=2)

            self._stats_labels[key] = value_widget

        modules_frame = tk.LabelFrame(
            self,
            text="Módulos IA Activos",
            font=('Segoe UI', 9),
            fg='#888888',
            bg='#1e1e1e',
            padx=10,
            pady=5
        )
        modules_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self._modules_listbox = tk.Listbox(
            modules_frame,
            font=('Consolas', 8),
            bg='#2d2d2d',
            fg='#00ff00',
            bd=0,
            highlightthickness=0,
            selectbackground='#3d3d3d'
        )
        self._modules_listbox.pack(fill=tk.BOTH, expand=True)

        actions_frame = tk.Frame(self, bg='#1e1e1e')
        actions_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        self._enable_btn = tk.Button(
            actions_frame,
            text="✅ Habilitar IA",
            command=self._on_enable,
            bg='#1a5f1a',
            fg='white',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            font=('Segoe UI', 9)
        )
        self._enable_btn.pack(side=tk.LEFT, padx=(0, 5))

        self._disable_btn = tk.Button(
            actions_frame,
            text="❌ Deshabilitar IA",
            command=self._on_disable,
            bg='#5f1a1a',
            fg='white',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            font=('Segoe UI', 9)
        )
        self._disable_btn.pack(side=tk.LEFT)

    def set_orchestrator(self, orchestrator):
        """Setea el orquestador IA."""
        self._orchestrator = orchestrator
        self.refresh_stats()

    def refresh_stats(self):
        """Actualiza las estadísticas."""
        if not self._orchestrator:
            self._update_label('ollama_status', '⭕ No configurado', '#888888')
            return

        ollama_available = self._orchestrator.is_available()
        if ollama_available:
            self._update_label('ollama_status', '🟢 Conectado', '#00ff00')
        else:
            self._update_label('ollama_status', '🔴 Desconectado (fallback)', '#ff6b6b')

        stats = self._orchestrator.get_stats()

        self._update_label('total_analyzed', str(stats.get('total_analyzed', 0)))

        avg_time = stats.get('avg_time_ms', 0)
        if avg_time > 0:
            self._update_label('avg_time_ms', f"{avg_time:.0f}ms")
        else:
            self._update_label('avg_time_ms', "--")

        total_time = stats.get('total_time_ms', 0)
        if total_time > 0:
            self._update_label('total_time_ms', f"{total_time/1000:.1f}s")
        else:
            self._update_label('total_time_ms', "--")

        modules_called = stats.get('modules_called', {})
        self._update_label('modules_active', str(len(modules_called)))

        self._modules_listbox.delete(0, tk.END)
        for module, count in sorted(modules_called.items(), key=lambda x: x[1], reverse=True):
            self._modules_listbox.insert(tk.END, f"  {module:20} {count:>5} llamadas")

    def _update_label(self, key: str, value: str, color: str = 'white'):
        """Actualiza un label de estadísticas."""
        if key in self._stats_labels:
            self._stats_labels[key].config(text=value, fg=color)

    def _on_enable(self):
        """Callback para habilitar IA."""
        if self._orchestrator:
            self._orchestrator.config.enable_density = True
            self._orchestrator.config.enable_noise = True
            self._orchestrator.config.enable_type_classify = True
            self.refresh_stats()

    def _on_disable(self):
        """Callback para deshabilitar IA."""
        if self._orchestrator:
            self._orchestrator.config.enable_density = False
            self._orchestrator.config.enable_noise = False
            self._orchestrator.config.enable_type_classify = False
            self.refresh_stats()

    def _start_auto_refresh(self):
        """Inicia auto-refresh de estadísticas."""
        self.after(self._refresh_interval, self._auto_refresh)

    def _auto_refresh(self):
        """Auto-refresh periódica."""
        self.refresh_stats()
        self._start_auto_refresh()


def create_ai_stats_panel(parent, orchestrator=None) -> AIStatsPanel:
    """Factory function para crear el panel."""
    return AIStatsPanel(parent, orchestrator)