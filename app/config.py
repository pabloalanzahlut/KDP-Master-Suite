import os
import logging
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Error fatal de configuración. Detiene la aplicación."""
    pass

@dataclass
class AppPaths:
    base_dir: Path
    db_path: Path
    transcriptions_dir: Path
    download_dir: Path
    processed_dir: Path
    knowledge_dir: Path
    exports_dir: Path

    @classmethod
    def load(cls) -> "AppPaths":
        base_dir = Path(os.getenv("KDP_BASE_DIR", ".")).resolve()
        
        db_path = base_dir / os.getenv("KDP_DB_PATH", "data/kdp_master.db")
        transcriptions_dir = base_dir / os.getenv("TRANSCRIPTIONS_DIR", "data/transcriptions")
        download_dir = base_dir / os.getenv("DOWNLOAD_DIR", "data/downloads")
        processed_dir = base_dir / os.getenv("PROCESSED_DIR", "outputs/transcriptions_processed")
        knowledge_dir = base_dir / os.getenv("KNOWLEDGE_DIR", "knowledge")
        exports_dir = base_dir / os.getenv("EXPORTS_DIR", "knowledge/exports")

        dirs_to_create = [
            db_path.parent, transcriptions_dir, download_dir, 
            processed_dir, knowledge_dir, exports_dir
        ]
        
        try:
            for d in dirs_to_create:
                d.mkdir(parents=True, exist_ok=True)
            logger.info("✅ Directorios verificados/creados.")
        except Exception as e:
            raise ConfigError(f"❌ Error al crear directorios: {e}")
        
        return cls(
            base_dir=base_dir, 
            db_path=db_path, 
            transcriptions_dir=transcriptions_dir,
            download_dir=download_dir,
            processed_dir=processed_dir,
            knowledge_dir=knowledge_dir,
            exports_dir=exports_dir
        )

@dataclass
class OllamaConfig:
    base_url: str
    model: str
    timeout: int
    batch_threshold: int
    max_tokens_input: int

    @classmethod
    def load(cls) -> "OllamaConfig":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
            logger.warning(f"⚠️ OLLAMA_BASE_URL ajustado a: {base_url}")

        model = os.getenv("OLLAMA_MODEL", "qwen3:8b")

        try:
            timeout = int(os.getenv("OLLAMA_TIMEOUT", "180"))
            if not (30 <= timeout <= 600): raise ValueError("Rango: 30-600")
        except ValueError: 
            timeout = 180

        try:
            threshold = int(os.getenv("BATCH_THRESHOLD", "10"))
            if threshold < 1: raise ValueError("Debe ser >= 1")
        except ValueError: 
            threshold = 10

        try:
            max_tokens_input = int(os.getenv("MAX_TOKENS_INPUT", "4000"))
            if max_tokens_input < 100: raise ValueError("Debe ser >= 100")
        except ValueError:
            max_tokens_input = 4000

        return cls(base_url=base_url, model=model, timeout=timeout, 
                   batch_threshold=threshold, max_tokens_input=max_tokens_input)

@dataclass
class GeneralConfig:
    log_level: str
    default_languages: List[str]
    ai_provider: str
    ai_api_key: Optional[str]

    @classmethod
    def load(cls) -> "GeneralConfig":
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in valid_levels:
            logger.warning(f"⚠️ LOG_LEVEL inválido '{log_level}', usando INFO")
            log_level = "INFO"

        langs_str = os.getenv("DEFAULT_LANGUAGES", "es,en")
        default_languages = [l.strip() for l in langs_str.split(",") if l.strip()]

        ai_provider = os.getenv("AI_PROVIDER", "ollama").lower()
        ai_api_key = os.getenv("AI_API_KEY", None)

        return cls(
            log_level=log_level,
            default_languages=default_languages,
            ai_provider=ai_provider,
            ai_api_key=ai_api_key
        )

class ConfigManager:
    _instance = None
    _is_loaded = False

    ollama: OllamaConfig
    paths: AppPaths
    general: GeneralConfig

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not ConfigManager._is_loaded:
            self._load_env_once()
            self.paths = AppPaths.load()
            self.ollama = OllamaConfig.load()
            self.general = GeneralConfig.load()
            
            ConfigManager._is_loaded = True
            logger.info("✅ Configuración cargada exitosamente.")

    def _load_env_once(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            pass

config = ConfigManager()