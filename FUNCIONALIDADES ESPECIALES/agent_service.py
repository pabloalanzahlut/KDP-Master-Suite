import logging
from datetime import datetime
from typing import List, Dict, Optional

class GEMAgentService:
    """
    Servicio para la gestión y ejecución de Agentes de IA (GEM Agents).
    Sigue el principio de Responsabilidad Única (SRP).
    """
    
    def __init__(self, db_manager, ai_provider):
        self.db = db_manager
        self.ai = ai_provider
        self.logger = logging.getLogger(__name__)

    # --- INICIO FUNCIONALIDAD US-030: EJECUCIÓN DE PROMPTS ---
    def execute_agent_prompt(self, agent_id: str, input_text: str, template_vars: Dict = None) -> Dict:
        """
        Ejecuta un prompt utilizando un agente específico y procesa la respuesta.
        """
        try:
            # 1. Obtener plantilla del agente
            template = self._get_agent_template(agent_id)
            
            # 2. Formatear prompt
            final_prompt = template.format(**(template_vars or {}), input=input_text)
            
            # 3. Llamada al proveedor de IA
            response = self.ai.generate_completion(final_prompt)
            
            # 4. Registrar en historial (US-031)
            self._save_to_history(agent_id, input_text, response)
            
            return {
                "status": "success",
                "content": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error ejecutando agente {agent_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    # --- FIN FUNCIONALIDAD US-030 ---

    # --- INICIO FUNCIONALIDAD US-031: HISTORIAL DE EJECUCIONES ---
    def _save_to_history(self, agent_id: str, prompt: str, result: str):
        """
        Persiste la ejecución en la base de datos para auditoría y consulta.
        """
        query = """
            INSERT INTO agent_history (agent_id, prompt_text, result_text, executed_at)
            VALUES (?, ?, ?, ?)
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (agent_id, prompt, result, datetime.now()))
        except Exception as e:
            self.logger.error(f"No se pudo guardar historial del agente: {e}")

    def get_agent_history(self, limit: int = 50) -> List[Dict]:
        """Recupera las últimas ejecuciones de agentes."""
        query = "SELECT * FROM agent_history ORDER BY executed_at DESC LIMIT ?"
        # Lógica de recuperación...
        return []
    # --- FIN FUNCIONALIDAD US-031 ---

    def _get_agent_template(self, agent_id: str) -> str:
        """Retorna la plantilla base para el agente."""
        templates = {
            "summarizer": "Resume el siguiente contenido de forma profesional: {input}",
            "kdp_expert": "Actúa como experto en KDP. Analiza este nicho: {input}",
            "seo_optimizer": "Genera 10 tags SEO para este título: {input}"
        }
        return templates.get(agent_id, "{input}")