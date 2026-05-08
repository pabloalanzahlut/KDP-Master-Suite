# --- INICIO FUNCIONALIDAD US-030 & US-031: LOGICA DE AGENTES ---
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

class AgentManager:
    """
    Gestiona la ejecución de prompts y la persistencia de resultados.
    Implementa el patrón Service para desacoplar la UI del motor de IA.
    """
    def __init__(self, db_path: str, ai_provider):
        self.db_path = db_path
        self.ai_provider = ai_provider # Inyección de dependencia (Ollama o Gemini)

    def execute_agent_prompt(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """
        Ejecuta un prompt, mide el rendimiento y guarda en el historial.
        """
        start_time = time.time()
        
        try:
            # US-030: Ejecución contra el proveedor de IA
            response_text = self.ai_provider.generate(prompt)
            execution_time = int((time.time() - start_time) * 1000)
            
            result = {
                "status": "success",
                "response": response_text,
                "execution_time": execution_time
            }
            
            # US-031: Guardado automático en historial
            self._log_execution(agent_name, prompt, response_text, execution_time)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _log_execution(self, agent_name: str, prompt: str, response: str, duration: int):
        """Persiste la ejecución en la BD."""
        query = """
            INSERT INTO agent_history (agent_name, prompt, response, execution_time_ms)
            VALUES (?, ?, ?, ?)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (agent_name, prompt, response, duration))
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to log agent history: {e}")

    def get_history(self, limit: int = 50):
        """Recupera el historial reciente para la UI."""
        query = "SELECT * FROM agent_history ORDER BY timestamp DESC LIMIT ?"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                return [dict(row) for row in conn.execute(query, (limit,)).fetchall()]
        except sqlite3.Error:
            return []

# --- FIN FUNCIONALIDAD US-030 & US-031 ---