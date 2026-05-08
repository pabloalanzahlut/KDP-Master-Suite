import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuración centralizada de la aplicación"""
    
    # Rutas base
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUTS_DIR = BASE_DIR / "outputs"
    KNOWLEDGE_DIR = BASE_DIR / "knowledge"
    
    # Directorios de transcripciones
    TRANSCRIPTIONS_DIR = DATA_DIR / "transcriptions"
    PROCESSED_DIR = OUTPUTS_DIR / "transcriptions_processed"
    
    # Base de datos
    DB_PATH = DATA_DIR / "kdp_master.db"
    
    # Archivos de manuales
    MANUALS_DIR = KNOWLEDGE_DIR / "manuals"
    MATRIZ_MAESTRA_PATH = MANUALS_DIR / "MATRIZ MAESTRA.md"
    MANUAL_LEGALIDAD_PATH = MANUALS_DIR / "MANUAL_LEGALIDAD.md"
    MANUAL_FORMULAS_PATH = MANUALS_DIR / "MANUAL de FÓRMULAS.md"
    
    # Configuración de YouTube/yt-dlp
    YT_SLEEP_MIN = 2
    YT_SLEEP_MAX = 5
    YT_SLEEP_REQUESTS = 3
    YT_SLEEP_INTERVAL = 3
    YT_MAX_SLEEP_INTERVAL = 15
    
    # Límites
    MAX_VIDEOS_PER_SCAN = 1000
    MAX_CONCURRENT_DOWNLOADS = 3
    
    # API Keys (opcional)
    YOUTUBE_API_KEY: Optional[str] = None
    
    # Configuración de metadatos enriquecidos (v2.6.0)
    METADATA_ENRICHMENT_MODE = 'passive'  # 'passive', 'active', 'hybrid'
    METADATA_ENRICH_IF_MISSING_TAGS = True
    METADATA_ENRICH_SHORT_DESCRIPTIONS = True
    METADATA_SHORT_DESCRIPTION_THRESHOLD = 100
    METADATA_HIGH_VALUE_THRESHOLD = 8.0
    METADATA_MAX_API_CALLS_PER_DAY = 100
    METADATA_TRACK_QUOTA_USAGE = True
    
    # Configuración de Exportación KB
    EXPORT_MAX_FILE_SIZE_MB = 8
    EXPORT_MAX_TOTAL_SIZE_MB = 500
    EXPORT_TIMEOUT_SECONDS = 120
    EXPORT_ESTIMATED_IMAGE_SIZE_MB = 1.5

    # Configuración de Programación Horaria
    SCHEDULE_ENABLED = True
    SCHEDULE_CHECK_INTERVAL_SECONDS = 60
    SCHEDULE_MAX_TASKS_TOTAL = 20
    SCHEDULE_MAX_TASKS_ACTIVE = 10
    SCHEDULE_DEFAULT_INTERVAL_MINUTES = 60
    SCHEDULE_DEFAULT_DAILY_TIME = "03:00"
    SCHEDULE_DETECT_POLL_INTERVAL_MINUTES = 15
    SCHEDULE_NOTIFICATIONS_ENABLED = True
    SCHEDULE_MINIMIZE_TO_TRAY_ON_CLOSE = True
    
    @classmethod
    def initialize(cls):
        """Inicializa directorios si no existen"""
        directories = [
            cls.DATA_DIR,
            cls.OUTPUTS_DIR,
            cls.KNOWLEDGE_DIR,
            cls.TRANSCRIPTIONS_DIR,
            cls.PROCESSED_DIR,
            cls.MANUALS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_db_path(cls) -> Path:
        """Retorna la ruta absoluta de la base de datos"""
        return cls.DB_PATH
    
    @classmethod
    def get_transcriptions_dir(cls) -> Path:
        """Retorna el directorio de transcripciones"""
        return cls.TRANSCRIPTIONS_DIR
    
    @classmethod
    def get_processed_dir(cls) -> Path:
        """Retorna el directorio de archivos procesados"""
        return cls.PROCESSED_DIR
    
    @classmethod
    def get_manual_path(cls, manual_name: str) -> Path:
        """Retorna la ruta de un manual específico"""
        return cls.MANUALS_DIR / manual_name
    
    @classmethod
    def verify_manuals(cls) -> dict:
        """Verifica existencia de manuales requeridos"""
        manuals = {
            'MATRIZ_MAESTRA': cls.MATRIZ_MAESTRA_PATH.exists(),
            'MANUAL_LEGALIDAD': cls.MANUAL_LEGALIDAD_PATH.exists(),
            'MANUAL_FORMULAS': cls.MANUAL_FORMULAS_PATH.exists()
        }
        return manuals
    
    @classmethod
    def create_missing_manuals(cls):
        """Crea manuales básicos si no existen"""
        cls.initialize()
        
        if not cls.MATRIZ_MAESTRA_PATH.exists():
            with open(cls.MATRIZ_MAESTRA_PATH, 'w', encoding='utf-8') as f:
                f.write("""# MATRIZ MAESTRA - KDP Master Suite

## Configuración del Sistema
- Versión: 2.4.3
- Estado: Activo
- Fecha de creación: 2024

## Reglas Generales
1. No eliminar este archivo
2. El sistema lo usa para validar configuración
3. Contiene metadatos del proyecto

## Historial
- Inicialización completada
""")
        
        if not cls.MANUAL_LEGALIDAD_PATH.exists():
            with open(cls.MANUAL_LEGALIDAD_PATH, 'w', encoding='utf-8') as f:
                f.write("# MANUAL DE LEGALIDAD\n\nContenido del manual de legalidad.\n")
        
        if not cls.MANUAL_FORMULAS_PATH.exists():
            with open(cls.MANUAL_FORMULAS_PATH, 'w', encoding='utf-8') as f:
                f.write("# MANUAL DE FÓRMULAS\n\nContenido del manual de fórmulas.\n")
    
    @classmethod
    def get_yt_sleep_time(cls) -> int:
        """Retorna el tiempo de pausa entre requests a YouTube"""
        import random
        return random.randint(cls.YT_SLEEP_MIN, cls.YT_SLEEP_MAX)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valida que la configuración sea correcta"""
        try:
            assert isinstance(cls.BASE_DIR, Path)
            assert isinstance(cls.DATA_DIR, Path)
            assert isinstance(cls.DB_PATH, Path)
            assert cls.YT_SLEEP_REQUESTS > 0
            assert cls.MAX_CONCURRENT_DOWNLOADS > 0
            return True
        except (AssertionError, AttributeError) as e:
            print(f"❌ Error de validación de configuración: {e}")
            return False


Config.initialize()
Config.create_missing_manuals()