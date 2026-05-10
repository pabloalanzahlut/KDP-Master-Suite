"""
KDP MASTER - Value Predictor (Módulo 22)
=======================================
Predictor de valor de transcripción.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ValuePredictor:
    """Módulo 22: Predictor de valor de transcripción."""
    
    HIGH_VALUE_INDICATORS = [
        'tutorial', 'curso', 'guía', 'completo', 'avanzado',
        'estrategia', 'sistema', 'método', ' paso a paso',
        'práctico', 'ejemplos', 'caso de estudio'
    ]
    
    LOW_VALUE_INDICATORS = [
        'intro', 'outro', 'trailer', 'sponsor', 'promoción',
        'short', 'reels', 'vlog', 'daily', 'vlog'
    ]
    
    def __init__(self):
        self.model = "llama3.1:8b"
    
    def set_model(self, model: str):
        """Configura modelo."""
        self.model = model
    
    def predict(self, title: str, description: str = "",
               duration: int = 0, tags: List[str] = None,
               has_transcript: bool = False) -> Dict[str, Any]:
        """
        Predice valor de transcripción.
        """
        score = 0.0
        indicators = []
        
        text = f"{title} {description}".lower()
        
        for indicator in self.HIGH_VALUE_INDICATORS:
            if indicator.lower() in text:
                score += 1.5
                indicators.append(f"+{indicator}")
        
        for indicator in self.LOW_VALUE_INDICATORS:
            if indicator.lower() in text:
                score -= 1.0
                indicators.append(f"-{indicator}")
        
        if duration > 600:
            score += 1.0
            indicators.append("+duración_larga")
        elif duration < 120:
            score -= 0.5
            indicators.append("-duración_corta")
        
        if has_transcript:
            score += 0.5
            indicators.append("+transcript_available")
        
        if tags:
            tag_score = min(len(tags) * 0.1, 1.0)
            score += tag_score
            indicators.append(f"+{len(tags)}_tags")
        
        normalized_score = max(min(score / 10.0, 1.0), 0.0)
        
        if normalized_score >= 0.7:
            value_level = "alto"
        elif normalized_score >= 0.4:
            value_level = "medio"
        else:
            value_level = "bajo"
        
        return {
            'value_score': round(normalized_score, 2),
            'raw_score': round(score, 2),
            'value_level': value_level,
            'indicators': indicators,
            'estimated_quality': self._estimate_quality(normalized_score),
            'recommended_action': 'process' if normalized_score > 0.3 else 'skip'
        }
    
    def _estimate_quality(self, score: float) -> str:
        """Estima calidad esperada."""
        if score >= 0.8:
            return "Excelente - Manual completo esperado"
        elif score >= 0.6:
            return "Bueno - Contenido sustancial"
        elif score >= 0.4:
            return "Regular - Contenido básico"
        else:
            return "Bajo - Probablemente contenido banal"
    
    async def predict_with_ollama(self, title: str, description: str = "",
                             duration: int = 0) -> Dict[str, Any]:
        """Predice usando Ollama."""
        prompt = f"""Evalúa el valor potenciales de transcripción de este video:

Título: {title}
Descripción: {description[:300] if description else 'Sin descripción'}
Duración: {duration} segundos

Responde en JSON:
{{
  "value_score": 0.0-1.0,
  "value_level": "alto/medio/bajo",
  "quality_expected": "descripción de calidad esperada",
  "recommended_action": "process/skip"
}}"""
        
        try:
            import requests
            import os
            
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                parsed = self._parse_json_from_text(response_text)
                parsed['method'] = 'ollama'
                parsed['success'] = True
                return parsed
            
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_json_from_text(self, text: str) -> Dict[str, Any]:
        """Parsea JSON desde texto."""
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
    
    def predict_batch(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predice para batch."""
        results = []
        
        for video in videos:
            result = self.predict(
                title=video.get('title', ''),
                description=video.get('description', ''),
                duration=video.get('duration', 0),
                tags=video.get('tags', [])
            )
            result['video_id'] = video.get('id')
            results.append(result)
        
        results.sort(key=lambda x: x['value_score'], reverse=True)
        
        return results


def create_value_predictor() -> ValuePredictor:
    """Factory function."""
    return ValuePredictor()