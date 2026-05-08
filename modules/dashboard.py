# -*- coding: utf-8 -*-
"""
Real-time Dashboard Module for KDP Master Suite
Implements visual analytics using Matplotlib integrated with Tkinter.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random
import threading
import time

class DashboardView:
    def __init__(self, parent_frame, theme_manager=None):
        self.parent = parent_frame
        self.theme_manager = theme_manager
        self.is_running = False
        
        # Colors (Default dark)
        self.bg_color = "#0a0e1a"
        self.fg_color = "#f1f5f9"
        self.accent_color = "#3b82f6"
        
        if theme_manager:
            theme_manager.register_listener(self.update_theme)
            self.update_theme(theme_manager.colors)

        self.setup_ui()

    def update_theme(self, colors):
        self.bg_color = colors["bg_primary"]
        self.fg_color = colors["fg_primary"]
        self.accent_color = colors["accent"]
        # TODO: Trigger redraw of charts with new colors

    def setup_ui(self):
        # Grid layout for dashboard
        self.parent.columnconfigure(0, weight=1)
        self.parent.columnconfigure(1, weight=1)
        self.parent.rowconfigure(0, weight=1)
        self.parent.rowconfigure(1, weight=1)

        # Create Charts
        self.create_activity_chart(0, 0)
        self.create_status_pie_chart(0, 1)
        self.create_video_trend_chart(1, 0)
        self.create_processing_speed_chart(1, 1)

    def create_activity_chart(self, row, col):
        frame = ttk.LabelFrame(self.parent, text=" 📊 Actividad Diaria ", padding=10)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=self.bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.bg_color)
        
        # Mock Data
        days = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        values = [random.randint(10, 50) for _ in range(7)]
        
        bars = ax.bar(days, values, color=self.accent_color)
        ax.tick_params(colors=self.fg_color)
        for spine in ax.spines.values():
            spine.set_color(self.fg_color)
            
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_status_pie_chart(self, row, col):
        frame = ttk.LabelFrame(self.parent, text=" 🍩 Distribución de Estado ", padding=10)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=self.bg_color)
        ax = fig.add_subplot(111)
        
        labels = 'Completado', 'Pendiente', 'Fallido'
        sizes = [65, 30, 5]
        colors = ['#10b981', '#f59e0b', '#ef4444']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                shadow=False, startangle=90, colors=colors, textprops=dict(color=self.fg_color))
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_video_trend_chart(self, row, col):
        frame = ttk.LabelFrame(self.parent, text=" 📈 Tendencia de Videos ", padding=10)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=self.bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.bg_color)
        
        x = range(10)
        y = [random.randint(20, 40) + i for i in x]
        
        ax.plot(x, y, color='#a855f7', marker='o')
        ax.tick_params(colors=self.fg_color)
        for spine in ax.spines.values():
            spine.set_color(self.fg_color)
            
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_processing_speed_chart(self, row, col):
        frame = ttk.LabelFrame(self.parent, text=" ⚡ Velocidad de Procesamiento (MB/s) ", padding=10)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=self.bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.bg_color)
        
        x = range(20)
        y = [random.uniform(1.5, 3.5) for _ in x]
        
        ax.fill_between(x, y, color='#06b6d4', alpha=0.4)
        ax.plot(x, y, color='#06b6d4')
        
        ax.tick_params(colors=self.fg_color)
        for spine in ax.spines.values():
            spine.set_color(self.fg_color)
            
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def start_realtime_updates(self):
        self.is_running = True
        # threading.Thread(target=self._update_loop, daemon=True).start()

    def _update_loop(self):
        while self.is_running:
            time.sleep(5)
            # Update charts logic here
            pass
