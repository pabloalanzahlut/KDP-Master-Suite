import pytest
from pathlib import Path
from app.core.config import Config

def test_validate_with_hardcoded_values():
    """Config con valores por defecto debe pasar validación"""
    assert Config.validate_config() is True

def test_youtube_limits_are_positive():
    """Valores de YT deben ser positivos"""
    assert Config.YT_SLEEP_REQUESTS > 0
    assert Config.MAX_CONCURRENT_DOWNLOADS > 0

def test_paths_resolve_to_absolute():
    """Rutas deben resolverse como absolutas"""
    assert Config.BASE_DIR.resolve().is_absolute()
    assert Config.DATA_DIR.resolve().is_absolute()
    assert Config.DB_PATH.resolve().is_absolute()

def test_directories_initialized():
    """Directorios base deben existir tras Config.initialize()"""
    Config.initialize()
    assert Config.DATA_DIR.exists()
    assert Config.OUTPUTS_DIR.exists()