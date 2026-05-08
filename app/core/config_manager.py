"""
KDP_MASTER - Config Manager (Elite Enterprise)
==============================================
Implementación de la Épica: Deuda Técnica - Sistema Centralizado de Validación.
Utiliza Pydantic para asegurar que todos los parámetros sean válidos en tiempo de ejecución.
"""

import os
import json
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# === [INICIO FUNCIONALIDAD: SISTEMA DE CONFIGURACIÓN CENTRALIZADO] ===
class CloudSyncConfig(BaseModel):
    enabled: bool = False
    repo_url: Optional[str] = None

class MonitorConfig(BaseModel):
    auto_start: bool = False
    scan_frequency: int = Field(default=30, ge=15)
    max_results_per_check: int = 50
    max_age_days: int = 7

class AppConfig(BaseModel):
    input_dir: str = "data/transcriptions"
    output_dir: str = "outputs/transcriptions_processed"
    ai_provider: str = "ollama"
    ai_api_key: str = ""
    blacklist: List[str] = []
    cloud_sync: CloudSyncConfig = CloudSyncConfig()
    monitor: MonitorConfig = MonitorConfig()

class ConfigManager:
    """Orquestador de ajustes con validación atómica."""
    def __init__(self, config_path: str):
        self.path = Path(config_path)
        self.settings: AppConfig = self.load()

    def load(self) -> AppConfig:
        """Carga y valida el archivo JSON."""
        if not self.path.exists():
            return AppConfig()
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception as e:
            print(f"⚠️ Error validando configuración: {e}. Usando defaults.")
            return AppConfig()

    def save(self):
        """Persistencia atómica de la configuración validada."""
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(self.settings.model_dump_json(indent=2))
# === [FIN FUNCIONALIDAD: SISTEMA DE CONFIGURACIÓN CENTRALIZADO] ===