"""
KDP MASTER - Keypoints Extractor (Módulo 18)
==========================================
Extractor de key-points pre-descarga.
"""

from typing import Dict, Any, List, Optional


class KeypointsExtractor:
    """Módulo 18: Extractor de key-points."""
    
    def __init__(self):
        self.max_points = 3
    
    def set_max_points(self, max_points: int):
        """Configura máximo de puntos."""
        self.max_points = max(1, min(max_points, 10))
    
    async def extract_with_ollama(self, title: str, description: str = "",
                             model: str = "llama3.1:8b") -> Dict[str, Any]:
        """Extrae key-points usando Ollama."""
        prompt = f"""Basado en el siguiente contenido, extrae los 3 puntos clave más importantes:

Título: {title}
Descripción: {description[:500] if description else 'Sin descripción'}

Responde en formato:
PUNTO1: [punto clave 1]
PUNTO2: [punto clave 2]
PUNTO3: [punto clave 3]"""
        
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
                
                points = self._parse_points(response_text)
                
                return {
                    'success': True,
                    'points': points,
                    'raw_response': response_text
                }
            
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_points(self, text: str) -> List[str]:
        """Parsea puntos desde texto."""
        lines = text.strip().split('\n')
        points = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('PUNTO') or line.startswith('Punto'):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    points.append(parts[1].strip())
        
        if not points:
            points = [line.strip() for line in lines if len(line.strip()) > 20]
        
        return points[:self.max_points]
    
    def extract_from_metadata(self, title: str, description: str = "",
                          tags: List[str] = None) -> List[str]:
        """Extrae key-points desde metadata sin IA."""
        points = []
        
        if title:
            points.append(f"Título: {title[:80]}")
        
        if description:
            sentences = description.split('.')
            for sentence in sentences[:self.max_points]:
                sentence = sentence.strip()
                if len(sentence) > 20:
                    points.append(sentence[:100])
        
        if tags and len(points) < self.max_points:
            for tag in tags[:self.max_points - len(points)]:
                points.append(f"Etiqueta: {tag}")
        
        return points[:self.max_points]
    
    def extract_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrae desde batch."""
        results = []
        
        for item in items:
            title = item.get('title', '')
            description = item.get('description', '')
            tags = item.get('tags', [])
            
            points = self.extract_from_metadata(title, description, tags)
            
            results.append({
                'video_id': item.get('id'),
                'key_points': points
            })
        
        return results


def create_keypoints_extractor() -> KeypointsExtractor:
    """Factory function."""
    return KeypointsExtractor()