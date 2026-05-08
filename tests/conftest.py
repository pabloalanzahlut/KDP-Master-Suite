import pytest
import os

@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Limpia entorno para tests aislados"""
    for k in list(os.environ.keys()):
        if k.startswith(("OLLAMA_", "KDP_", "AI_", "LOG_")):
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LOG_LEVEL", "WARNING")