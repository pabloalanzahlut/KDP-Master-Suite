import requests
import time
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class KBUpdatePayload(BaseModel):
    """Esquema de validación pre-envío (Fase 4.6)."""
    source: str
    category: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

class WebhookDispatcher:
    """Despachador con reintentos y backoff exponencial (Fase 4.2)."""
    def __init__(self, url: Optional[str] = None):
        self.url = url
        self.max_retries = 3

    def dispatch(self, data: Dict[str, Any]) -> bool:
        if not self.url:
            return False

        try:
            # 4.6 Validación estricta con Pydantic
            payload = KBUpdatePayload(**data)
            json_data = payload.model_dump()
        except Exception as e:
            print(f"[WEBHOOK] Schema Validation Failed: {e}")
            return False

        # 4.2 Retry Logic con Backoff
        for attempt in range(self.max_retries):
            try:
                resp = requests.post(self.url, json=json_data, timeout=8)
                if resp.status_code in [200, 201, 204]:
                    return True
                print(f"[WEBHOOK] Attempt {attempt+1} failed with status {resp.status_code}")
            except requests.RequestException as e:
                wait = 2 ** attempt
                print(f"[WEBHOOK] Error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
        
        # 🛡️ Contingencia: En un sistema real aquí guardaríamos en pending_sync.json
        return False