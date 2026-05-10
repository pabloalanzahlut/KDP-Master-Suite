"""
KDP MASTER - Natural Ingest Engine (Módulo 21)
=============================================
Asistente de ingesta por lenguaje natural.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class NaturalIngestEngine:
    """Módulo 21: Ingesta por lenguaje natural."""
    
    COMMAND_PATTERNS = {
        r'añade.*videos?\s+.*(\d+).*': 'count',
        r'los\s+(\d+)\s+mejores': 'count',
        r'todos\s+los\s+videos': 'all',
        r'ultimos\s+(\d+)': 'recent',
        r'últimos\s+(\d+)': 'recent',
    }
    
    def __init__(self):
        self.default_channel = None
        self.topics: Dict[str, List[str]] = {}
    
    def set_default_channel(self, channel: str):
        """Configura canal por defecto."""
        self.default_channel = channel
    
    def add_topic(self, topic: str, keywords: List[str]):
        """Añade topic con keywords."""
        self.topics[topic.lower()] = keywords
    
    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        Parsea comando en lenguaje natural.
        """
        command_lower = command.lower().strip()
        
        result = {
            'action': 'unknown',
            'count': None,
            'topic': None,
            'channel': self.default_channel,
            'filters': {},
            'raw_command': command
        }
        
        if 'encola' in command_lower or 'añade' in command_lower:
            result['action'] = 'add'
        
        for pattern, action_type in self.COMMAND_PATTERNS.items():
            match = re.search(pattern, command_lower)
            if match:
                if action_type == 'count' and match.group(1):
                    result['count'] = int(match.group(1))
                elif action_type == 'all':
                    result['count'] = None
                elif action_type == 'recent':
                    result['count'] = int(match.group(1))
                    result['filters']['sort'] = 'date'
                break
        
        for topic, keywords in self.topics.items():
            if any(kw in command_lower for kw in keywords):
                result['topic'] = topic
                break
        
        channel_match = re.search(r'de\s+(.+?)(?:\s|$)', command_lower)
        if channel_match:
            result['channel'] = channel_match.group(1).strip()
        
        return result
    
    async def process_with_ollama(self, command: str, 
                              model: str = "llama3.1:8b") -> Dict[str, Any]:
        """Procesa comando complejo con Ollama."""
        prompt = f"""Parsea este comando de usuario y extrae la intención:

Comando: {command}

Responde en JSON:
{{
  "action": "add/search/filter",
  "count": numero o null,
  "topic": topic principal o null,
  "channel": nombre del canal o null,
  "filters": {{filtros adicionales}},
  "intention": "descripción de intención del usuario"
}}"""
        
        try:
            import requests
            import os
            
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                return {
                    'success': True,
                    'parsed': self._parse_json_from_text(response_text),
                    'raw_response': response_text
                }
            
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extrae JSON desde texto."""
        try:
            import json
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        
        return {}
    
    def generate_response(self, parsed: Dict[str, Any]) -> str:
        """Genera respuesta amigable."""
        action = parsed.get('action', 'unknown')
        
        if action == 'add':
            count = parsed.get('count', 'todos')
            topic = parsed.get('topic')
            channel = parsed.get('channel')
            
            msg = f"Entendido. Voy a"
            if count:
                msg += f" añadir los {count} mejores"
            else:
                msg += " añadir"
            
            if topic:
                msg += f" sobre {topic}"
            
            if channel:
                msg += f" de {channel}"
            else:
                msg += " videos"
            
            return msg
        
        return "Comando no reconocido. Intenta: 'Encola los 3 mejores videos sobre fiscalidad de este canal'"
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Valida si el comando es procesable."""
        if len(command) < 3:
            return False, "Comando muy corto"
        
        if len(command) > 500:
            return False, "Comando muy largo (máx 500 caracteres)"
        
        known_actions = ['encola', 'añade', 'busca', 'filtra', 'busca']
        if not any(action in command.lower() for action in known_actions):
            return False, "Acción no reconocida. Usa: encola, añade, busca o filtra"
        
        return True, "Válido"


def create_natural_ingest_engine() -> NaturalIngestEngine:
    """Factory function."""
    return NaturalIngestEngine()