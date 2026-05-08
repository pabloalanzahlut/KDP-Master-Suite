# -*- coding: utf-8 -*-
"""
Core UI Framework for KDP Knowledge Integrator
Provides Theme Management, Animation Engine, and Icon Abstraction.
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import threading
import time
import math

class ThemeManager:
    """
    Manages application themes (colors, fonts) and applies them dynamically.
    """
    
    DEFAULT_THEMES = {
        "dark": {
            "bg_primary": "#0a0e1a",
            "bg_secondary": "#1e293b",
            "bg_tertiary": "#334155",
            "fg_primary": "#f1f5f9",
            "fg_secondary": "#cbd5e1",
            "accent": "#3b82f6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#06b6d4"
        },
        "light": {
            "bg_primary": "#f8fafc",
            "bg_secondary": "#ffffff",
            "bg_tertiary": "#e2e8f0",
            "fg_primary": "#0f172a",
            "fg_secondary": "#475569",
            "accent": "#3b82f6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#06b6d4"
        }
    }

    def __init__(self, app_root):
        self.root = app_root
        self.current_theme_name = "dark"
        self.colors = self.DEFAULT_THEMES["dark"]
        self.listeners = []

    def load_theme(self, theme_name):
        """Loads a theme by name (built-in or from file)."""
        if theme_name in self.DEFAULT_THEMES:
            self.colors = self.DEFAULT_THEMES[theme_name]
            self.current_theme_name = theme_name
            self.apply_theme()
        else:
            # TODO: Load from JSON file in themes/ dir
            pass

    def apply_theme(self):
        """Applies current theme colors to ttk.Style."""
        style = ttk.Style()
        colors = self.colors
        
        # Configure standard TTK styles
        style.configure("TFrame", background=colors["bg_primary"])
        style.configure("TLabel", background=colors["bg_primary"], foreground=colors["fg_primary"])
        style.configure("TButton", background=colors["bg_tertiary"], foreground=colors["fg_primary"])
        
        # Special classes
        style.configure("Card.TFrame", background=colors["bg_secondary"], relief="raised")
        style.configure("Header.TLabel", foreground=colors["accent"], font=("Segoe UI", 22, "bold"))
        
        # Notify components
        for callback in self.listeners:
            try:
                callback(colors)
            except Exception as e:
                print(f"Error updating theme listener: {e}")

        # Update Root background
        self.root.configure(bg=colors["bg_primary"])

    def register_listener(self, callback):
        """Register a function to be called when theme changes."""
        self.listeners.append(callback)

    def get_color(self, name):
        return self.colors.get(name, "#000000")


class AnimationEngine:
    """
    Provides smooth animations for Tkinter widgets using the event loop.
    """
    
    @staticmethod
    def fade_in(widget, duration=500, step=0.05):
        """Fades in a widget (alpha 0 -> 1). Only works for Toplevel windows easily."""
        # Note: Normal frames doesn't support alpha easily without hacks. 
        # This is best for Toast Notifications or modal windows.
        try:
            widget.attributes("-alpha", 0.0)
            widget.deiconify()
            
            def _fade(current_alpha):
                if current_alpha < 1.0:
                    current_alpha += step
                    widget.attributes("-alpha", current_alpha)
                    delay = int(duration * step)
                    widget.after(delay, lambda: _fade(current_alpha))
            
            _fade(0.0)
        except Exception:
            widget.deiconify() # Fallback

    @staticmethod
    def animate_color(widget, prop, start_hex, end_hex, duration=300):
        """Interpolates color property of a widget."""
        # Simple linear interpolation for hex colors
        def hex_to_rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
        def rgb_to_hex(rgb): return '#%02x%02x%02x' % rgb
        
        start_rgb = hex_to_rgb(start_hex)
        end_rgb = hex_to_rgb(end_hex)
        
        steps = 10
        delay = int(duration / steps)
        
        def _step(i):
            if i > steps: return
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * (i / steps))
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * (i / steps))
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * (i / steps))
            color = rgb_to_hex((r, g, b))
            try:
                widget.configure(**{prop: color})
                widget.after(delay, lambda: _step(i + 1))
            except:
                pass # Widget might be destroyed
        
        _step(0)


class IconManager:
    """
    Manages application icons, supporting Unicode fallbacks and future SVG rendering.
    """
    
    ICONS = {
        "dashboard": "📊",
        "download": "📥",
        "process": "⚙️",
        "intelligence": "🧠",
        "search": "🔍",
        "monitor": "📺",
        "settings": "🔧",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "refresh": "🔄",
        "delete": "🗑️",
        "add": "➕",
        "play": "▶️",
        "pause": "⏸️"
    }

    @staticmethod
    def get(name):
        return IconManager.ICONS.get(name, "❓")


class ResponsiveManager:
    """
    Handles responsive layout adjustments based on window size.
    Implements 'Compact Mode' for smaller screens.
    """
    BREAKPOINT_COMPACT = 1366
    
    def __init__(self, root):
        self.root = root
        self.is_compact = False
        self.listeners = []
        self._bind_events()
        
    def _bind_events(self):
        self.root.bind("<Configure>", self._on_resize)
        
    def _on_resize(self, event):
        # Filter out events not from the main window (e.g. internal widgets)
        if event.widget == self.root:
            width = event.width
            new_state = width < self.BREAKPOINT_COMPACT
            
            if new_state != self.is_compact:
                self.is_compact = new_state
                self._notify_listeners()
                
    def register_listener(self, callback):
        """Register a callback(is_compact: bool) to be called on mode change."""
        self.listeners.append(callback)
        
    def _notify_listeners(self):
        for callback in self.listeners:
            try:
                callback(self.is_compact)
            except Exception as e:
                print(f"Error in responsive listener: {e}")


class BindingManager:
    """
    Manages configurable keyboard shortcuts.
    Loads bindings from a JSON file and allows dynamic rebinding.
    """
    DEFAULT_BINDINGS = {
        "refresh": "<F5>",
        "docs": "<F1>",
        "quit": "<Control-q>",
        "settings": "<Control-comma>",
        "search": "<Control-f>",
        "toggle_theme": "<Control-t>"
    }
    
    def __init__(self, root, config_path="keybindings.json"):
        self.root = root
        self.config_path = config_path
        self.bindings = self.DEFAULT_BINDINGS.copy()
        self.actions = {}  # Map action_name -> function
        self._load_config()
        
    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_bindings = json.load(f)
                    self.bindings.update(user_bindings)
            except Exception as e:
                print(f"Error loading keybindings: {e}")
                
    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.bindings, f, indent=4)
        except Exception as e:
            print(f"Error saving keybindings: {e}")
            
    def register_action(self, action_name, callback):
        """Register a function to an action name."""
        self.actions[action_name] = callback
        # Bind immediately if key exists
        if action_name in self.bindings:
            self._apply_binding(action_name, self.bindings[action_name])
            
    def _apply_binding(self, action_name, key_sequence):
        # Unbind old if necessary (complex in Tkinter, skipping for now)
        try:
            self.root.bind(key_sequence, lambda event: self._trigger_action(action_name, event))
        except Exception as e:
            print(f"Error binding {key_sequence}: {e}")
            
    def _trigger_action(self, action_name, event):
        if action_name in self.actions:
            self.actions[action_name]()
            
    def rebind(self, action_name, new_key):
        """Update a binding dynamically."""
        self.bindings[action_name] = new_key
        self._apply_binding(action_name, new_key)
        self.save_config()

# Global UI Context (to be initialized by App)

ui_context = {
    "theme": None,
    "anim": AnimationEngine(),
    "icons": IconManager(),
    "responsive": None, # Initialized in App
    "bindings": None    # Initialized in App
}
