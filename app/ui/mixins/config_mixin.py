"""
Config Mixin
Gestión de configuración y validación del sistema.
"""

import logging
import os
import json
import tkinter as tk
from tkinter import messagebox


class ConfigMixin:
    """Mixin para funcionalidades de configuración."""

    def load_config(self):
        """Carga la configuración desde el archivo JSON."""
        config_file = getattr(self, 'config_file', None)
        if not config_file:
            config_file = os.path.join(getattr(self, 'base_dir', '.'), 'settings.json')
        
        defaults = {
            "input_dir": getattr(self, 'input_dir', tk.StringVar(value="data/transcriptions")).get(),
            "output_dir": getattr(self, 'output_dir', tk.StringVar(value="outputs/processed")).get(),
            "blacklist": [],
            "channels": [],
            "ai_provider": "none",
            "ai_api_key": "",
            "ai_system_prompt": "Clasifica el texto según categorías KDP...",
            "theme": "dark",
            "max_downloads_per_channel": 3,
            "monitor_interval": 60,
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception as e:
                self.log(f"[WARN] Error cargando config: {e}")
        
        if hasattr(self, 'input_dir'):
            self.input_dir.set(defaults.get("input_dir", ""))
        if hasattr(self, 'output_dir'):
            self.output_dir.set(defaults.get("output_dir", ""))
        if hasattr(self, 'blacklist'):
            self.blacklist = defaults.get("blacklist", [])
        if hasattr(self, 'channels'):
            self.channels = defaults.get("channels", [])
        if hasattr(self, 'current_theme'):
            self.current_theme = defaults.get("theme", "dark")
        
        self.log("[CONFIG] Configuración cargada.")

    def save_config(self):
        """Guarda la configuración actual al archivo JSON."""
        config_file = getattr(self, 'config_file', None)
        if not config_file:
            config_file = os.path.join(getattr(self, 'base_dir', '.'), 'settings.json')
        
        config = {
            "input_dir": getattr(self, 'input_dir', tk.StringVar()).get(),
            "output_dir": getattr(self, 'output_dir', tk.StringVar()).get(),
            "blacklist": getattr(self, 'blacklist', []),
            "channels": getattr(self, 'channels', []),
            "theme": getattr(self, 'current_theme', 'dark'),
        }
        
        if hasattr(self, 'ai_provider'):
            config["ai_provider"] = self.ai_provider
        if hasattr(self, 'api_key'):
            config["ai_api_key"] = self.api_key
        if hasattr(self, 'ai_system_prompt'):
            config["ai_system_prompt"] = self.ai_system_prompt
        if hasattr(self, 'max_downloads_per_channel'):
            config["max_downloads_per_channel"] = self.max_downloads_per_channel
        if hasattr(self, 'monitor_interval_var'):
            config["monitor_interval"] = self.monitor_interval_var.get()
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            self.log("[CONFIG] Configuración guardada.")
        except Exception as e:
            self.log(f"[ERROR] Error guardando config: {e}", "error")

    def validate_configuration(self):
        """Valida la configuración del sistema."""
        errors = []
        warnings = []
        
        if hasattr(self, 'input_dir'):
            input_dir = self.input_dir.get()
            if not os.path.exists(input_dir):
                try:
                    os.makedirs(input_dir, exist_ok=True)
                    warnings.append(f"Directorio de entrada creado: {input_dir}")
                except Exception as e:
                    errors.append(f"No se pudo crear directorio de entrada: {e}")
        
        if hasattr(self, 'output_dir'):
            output_dir = self.output_dir.get()
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    warnings.append(f"Directorio de salida creado: {output_dir}")
                except Exception as e:
                    errors.append(f"No se pudo crear directorio de salida: {e}")
        
        if hasattr(self, 'db_manager') and self.db_manager:
            try:
                if not self.db_manager.check_integrity():
                    errors.append("Integridad de base de datos comprometida")
            except Exception as e:
                warnings.append(f"Error verificando DB: {e}")
        
        for w in warnings:
            self.log(f"[WARN] {w}")
        
        if errors:
            error_msg = "\n".join(errors)
            self.log(f"[ERROR] Errores de configuración:\n{error_msg}", "error")
            return False
        
        self.log("[CONFIG] Validación completada.")
        return True

    def reset_to_defaults(self):
        """Restablece la configuración a valores predeterminados."""
        if messagebox.askyesno("Confirmar", "¿Restablecer configuración a valores predeterminados?"):
            self.input_dir.set("data/transcriptions")
            self.output_dir.set("outputs/processed")
            self.blacklist = []
            self.channels = []
            self.save_config()
            self.log("[CONFIG] Configuración restablecida.")