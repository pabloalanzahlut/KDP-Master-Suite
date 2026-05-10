"""
KDP MASTER - Relevance Analyzer (Módulo 13)
==========================================
Analista de relevancia estratégica.
Usa Ollama para analizar título y metadatos.
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class RelevanceAnalyzer:
    """Módulo 13: Analista de relevancia estratégica."""
    
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL = "llama3.1:8b"
    
    NICHE_KEYWORDS = [
        "inversión", "finanzas", "criptomonedas", "bolsa", " trading ",
        " fiscalidad ", "impuestos", "jubilación", "pensiones",
        "ahorro", "riqueza", "income", "passive income", "money"
    ]
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or self.DEFAULT_MODEL
        self.niche_keywords = self.NICHE_KEYWORDS
    
    def set_niche_keywords(self, keywords: list):
        """Configura keywords del nicho."""
        self.niche_keywords = keywords
    
    def calculate_relevance(self, title: str, description: str = "",
                       channel_name: str = "", tags: list = None) -> Tuple[float, str, list]:
        """
        Calcula relevancia estratégica (1-10).
        Returns: (score, explanation, matched_keywords)
        """
        matched = []
        text_combined = f"{title} {description} {channel_name}".lower()
        
        for keyword in self.niche_keywords:
            if keyword.lower() in text_combined:
                matched.append(keyword)
        
        base_score = min(len(matched) * 2.5, 10.0)
        
        if tags:
            tag_bonus = min(len([t for t in tags if any(k in t.lower() for k in self.niche_keywords)]) * 0.5, 2.0)
            base_score += tag_bonus
        
        score = max(min(base_score, 10.0), 1.0)
        
        explanation = f"Keywords coincidentes: {', '.join(matched[:5]) if matched else 'Ninguna'}"
        
        return score, explanation, matched
    
    async def analyze_with_ollama(self, title: str, description: str = "",
                         channel_name: str = "", context: str = "") -> Dict[str, Any]:
        """
        Analiza con Ollama para insights más profundos.
        """
        prompt = f"""Analiza la relevancia estratégica de este video para un nicho de inversiones/finanzas:
        
Título: {title}
Descripción: {description}
Canal: {channel_name}

Responde en JSON:
{{
  "relevance_score": 1-10,
  "strategic_value": "alto/medio/bajo",
  "target_audience": "audiencia principal",
  "content_type": "educativo/promocional/entretenimiento",
  "monetization_potential": "alto/medio/bajo",
  "key_insights": ["insight1", "insight2"]
}}"""
        
        try:
            import requests
            
            response = requests.post(
                f"{self.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'raw_response': result.get('response', ''),
                    'model': self.model
                }
            
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        
        except Exception as e:
            logger.warning(f"Ollama no disponible: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze(self, video_metadata: Dict[str, Any], use_ollama: bool = False) -> Dict[str, Any]:
        """
        Análisis completo de relevancia.
        """
        title = video_metadata.get('title', '')
        description = video_metadata.get('description', '')
        channel = video_metadata.get('channel', video_metadata.get('uploader', ''))
        tags = video_metadata.get('tags', [])
        
        score, explanation, matched = self.calculate_relevance(
            title, description, channel, tags
        )
        
        result = {
            'relevance_score': score,
            'strategic_score': score * 1.0,
            'explanation': explanation,
            'matched_keywords': matched,
            'analysis_method': 'keyword_matching'
        }
        
        if use_ollama:
            ollama_result = self.analyze_with_ollama(title, description, channel)
            if ollama_result.get('success'):
                result['ollama_analysis'] = ollama_result
                result['analysis_method'] = 'hybrid'
        
        return result


def create_relevance_analyzer(model: Optional[str] = None) -> RelevanceAnalyzer:
    """Factory function."""
    return RelevanceAnalyzer(model)