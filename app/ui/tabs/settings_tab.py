"""
KDP Master - Settings Tab
=================
Pestaña centralizada de configuración.
"""

import os
import json
import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, app_instance):
        super().__init__(parent, fg_color="#2B2B2B")
        self.app = app_instance
        self.config_file = self.app.config_file if hasattr(self.app, 'config_file') else None
        
        self._create_ui()
        self._load_settings()
    
    def _create_ui(self):
        title = ctk.CTkLabel(
            self, 
            text="⚙️ Configuración"
        )
        title.pack(pady=(20, 10))
        
        scroll = ctk.CTkScrollableFrame(self, label_text="Opciones")
        scroll.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self._create_notification_section(scroll)
        self._create_general_section(scroll)
    
    def _create_notification_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="#2B2B2B")
        section.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(
            section, 
            text="🔔 Notificaciones", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        self.notify_enabled_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            section,
            text="Habilitar notificaciones",
            variable=self.notify_enabled_var,
            command=self._on_settings_changed
        ).pack(anchor="w", padx=20)
        
        self.notify_native_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            section,
            text="Notificaciones Windows nativas (Action Center)",
            variable=self.notify_native_var,
            command=self._on_settings_changed
        ).pack(anchor="w", padx=20, pady=(5, 0))
        
        self.notify_internal_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            section,
            text="Notificaciones internas (en app)",
            variable=self.notify_internal_var,
            command=self._on_settings_changed
        ).pack(anchor="w", padx=20, pady=(5, 0))
        
        ctk.CTkLabel(section, text="Silencio entre notificaciones (minutos):").pack(anchor="w", padx=20, pady=(10, 0))
        
        self.cooldown_var = ctk.IntVar(value=5)
        slider = ctk.CTkSlider(
            section,
            from_=0,
            to=30,
            number_of_steps=30,
            variable=self.cooldown_var,
            command=self._on_cooldown_changed
        )
        slider.pack(fill=ctk.X, padx=20, pady=5)
        
        self.cooldown_label = ctk.CTkLabel(section, text=f"{self.cooldown_var.get()} minutos")
        self.cooldown_label.pack(anchor="w", padx=20)
        
        self.notify_video_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            section,
            text="Notificar nuevos videos detectados",
            variable=self.notify_video_var,
            command=self._on_settings_changed
        ).pack(anchor="w", padx=20, pady=(10, 0))
        
        self.notify_processing_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            section,
            text="Notificar procesamiento completado",
            variable=self.notify_processing_var,
            command=self._on_settings_changed
        ).pack(anchor="w", padx=20, pady=(5, 0))
    
    def _create_general_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="#2B2B2B")
        section.pack(fill=ctk.X, pady=(15, 0))
        
        ctk.CTkLabel(
            section, 
            text="📁 Rutas", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(section, text="Directorio de entrada:").pack(anchor="w", padx=20)
        self.input_entry = ctk.CTkEntry(section, width=400)
        self.input_entry.pack(fill=ctk.X, padx=20, pady=2)
        
        btn_frame = ctk.CTkFrame(section, fg_color="#2B2B2B")
        btn_frame.pack(fill=ctk.X, padx=20, pady=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="Examinar...",
            command=self._browse_input_dir,
            width=100
        ).pack(side=ctk.LEFT)
        
        ctk.CTkLabel(section, text="Directorio de salida:").pack(anchor="w", padx=20, pady=(10, 0))
        
        self.output_entry = ctk.CTkEntry(section, width=400)
        self.output_entry.pack(fill=ctk.X, padx=20, pady=2)
        
        btn_frame2 = ctk.CTkFrame(section, fg_color="#2B2B2B")
        btn_frame2.pack(fill=ctk.X, padx=20, pady=(0, 10))
        
        ctk.CTkButton(
            btn_frame2,
            text="Examinar...",
            command=self._browse_output_dir,
            width=100
        ).pack(side=ctk.LEFT)
        
        ctk.CTkButton(
            section,
            text="💾 Guardar configuración",
            command=self._save_settings,
            fg_color="#10b981",
            hover_color="#059669"
        ).pack(pady=(20, 0))
    
    def _on_cooldown_changed(self, value):
        self.cooldown_label.configure(text=f"{int(value)} minutos")
    
    def _on_settings_changed(self):
        self._save_settings()
    
    def _load_settings(self):
        if not self.config_file or not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            notif = config.get("notifications", {})
            
            self.notify_enabled_var.set(notif.get("enabled", True))
            self.notify_native_var.set(notif.get("enable_native", False))
            self.notify_internal_var.set(notif.get("enable_internal", True))
            self.cooldown_var.set(notif.get("cooldown_minutes", 5))
            self.cooldown_label.configure(text=f"{self.cooldown_var.get()} minutos")
            self.notify_video_var.set(notif.get("notify_on_new_video", True))
            self.notify_processing_var.set(notif.get("notify_on_processing_complete", True))
            
            self.input_entry.delete(0, ctk.END)
            self.input_entry.insert(0, config.get("input_dir", ""))
            
            self.output_entry.delete(0, ctk.END)
            self.output_entry.insert(0, config.get("output_dir", ""))
            
        except Exception as e:
            print(f"Error cargando settings: {e}")
    
    def _save_settings(self):
        if not self.config_file:
            return
        
        try:
            existing = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            
            existing["notifications"] = {
                "enabled": self.notify_enabled_var.get(),
                "enable_native": self.notify_native_var.get(),
                "enable_internal": self.notify_internal_var.get(),
                "cooldown_minutes": self.cooldown_var.get(),
                "notify_on_new_video": self.notify_video_var.get(),
                "notify_on_processing_complete": self.notify_processing_var.get(),
            }
            
            existing["input_dir"] = self.input_entry.get()
            existing["output_dir"] = self.output_entry.get()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            
            if hasattr(self.app, 'notifier') and self.app.notifier:
                self.app.notifier.settings = {"notifications": existing["notifications"]}
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")
    
    def _browse_input_dir(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Seleccionar directorio de entrada")
        if path:
            self.input_entry.delete(0, ctk.END)
            self.input_entry.insert(0, path)
    
    def _browse_output_dir(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Seleccionar directorio de salida")
        if path:
            self.output_entry.delete(0, ctk.END)
            self.output_entry.insert(0, path)