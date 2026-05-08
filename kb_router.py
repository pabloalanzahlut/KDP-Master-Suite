from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="KDP Master Suite - KB Gateway")

class HealthStatus(BaseModel):
    status: str
    ai_engine: str
    version: str

@app.get("/health", response_model=HealthStatus)
async def health():
    """Endpoint de observabilidad para microservicios externos (Fase 4.1)."""
    return {
        "status": "ok",
        "ai_engine": "ollama",
        "version": "3.4.7-ELITE"
    }

def run_api(port: int = 8000):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

if __name__ == "__main__":
    run_api()