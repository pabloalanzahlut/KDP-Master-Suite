"""
KDP MASTER - Duplicate Concept Detector (Módulo 17)
==============================================
Detector de duplicados conceptuales usando embeddings.
"""

import os
import logging
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class DuplicateConceptDetector:
    """Módulo 17: Detector de duplicados conceptuales."""
    
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL = "nomic-embed-text"
    SIMILARITY_THRESHOLD = 0.85
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or self.DEFAULT_MODEL
        self.threshold = self.SIMILARITY_THRESHOLD
        self.known_topics: List[Dict[str, Any]] = []
    
    def set_threshold(self, threshold: float):
        """Configura umbral de similitud."""
        self.threshold = max(0.0, min(threshold, 1.0))
    
    def load_knowledge_base(self, kb_items: List[Dict[str, Any]]):
        """Carga base de conocimiento."""
        self.known_topics = kb_items
    
    async def compute_embedding(self, text: str) -> Optional[List[float]]:
        """Calcula embedding con Ollama."""
        try:
            import requests
            
            response = requests.post(
                f"{self.OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding')
            
            return None
        
        except Exception as e:
            logger.warning(f"Error computing embedding: {e}")
            return None
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similitud coseno."""
        if not a or not b:
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(x * x for x in b) ** 0.5
        
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        return dot_product / (mag_a * mag_b)
    
    async def check_duplicate(self, text: str, use_ollama: bool = True) -> Tuple[bool, str, float]:
        """
        Verifica duplicado conceptual.
        Returns: (is_duplicate, reason, similarity_score)
        """
        if not self.known_topics:
            return False, "Sin conocimiento previo", 0.0
        
        text_lower = text.lower()
        
        for topic in self.known_topics:
            topic_text = f"{topic.get('title', '')} {topic.get('description', '')}".lower()
            
            words1 = set(text_lower.split())
            words2 = set(topic_text.split())
            intersection = words1 & words2
            union = words1 | words2
            
            if union:
                jaccard = len(intersection) / len(union)
                if jaccard >= 0.6:
                    return True, f"High keyword overlap: {intersection}", jaccard
        
        if use_ollama:
            embedding = await self.compute_embedding(text)
            
            if embedding:
                best_score = 0.0
                best_topic = None
                
                for topic in self.known_topics:
                    topic_emb = topic.get('embedding')
                    if topic_emb:
                        score = self.cosine_similarity(embedding, topic_emb)
                        if score > best_score:
                            best_score = score
                            best_topic = topic
                
                if best_score >= self.threshold:
                    return True, f"Semantic similarity: {best_score:.2f}", best_score
        
        return False, "No duplicado", 0.0
    
    async def check_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Verifica batch de textos."""
        results = []
        
        for text in texts:
            is_dup, reason, score = await self.check_duplicate(text)
            results.append({
                'text': text[:50] + '...' if len(text) > 50 else text,
                'is_duplicate': is_dup,
                'reason': reason,
                'similarity': score
            })
        
        return results
    
    def check_keyword_overlap(self, text1: str, text2: str) -> float:
        """Verifica keyword overlap simple."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)


def create_duplicate_detector(model: Optional[str] = None) -> DuplicateConceptDetector:
    """Factory function."""
    return DuplicateConceptDetector(model)