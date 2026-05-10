"""
KDP MASTER - Batch Grouper (Módulo 19)
===================================
Smart batch grouping usando embeddings.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class BatchGrouper:
    """Módulo 19: Smart batch grouping."""
    
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL = "nomic-embed-text"
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or self.DEFAULT_MODEL
        self.groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    async def compute_embedding(self, text: str) -> Optional[List[float]]:
        """Calcula embedding."""
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
    
    async def group_by_similarity(self, items: List[Dict[str, Any]], 
                              threshold: float = 0.7) -> List[List[Dict[str, Any]]]:
        """Agrupa items por similitud semántica."""
        if not items:
            return []
        
        for i, item in enumerate(items):
            text = f"{item.get('title', '')} {item.get('description', '')}"
            item['_embedding_text'] = text
        
        embeddings = {}
        for item in items:
            emb = await self.compute_embedding(item['_embedding_text'])
            if emb:
                embeddings[item.get('id', item.get('url', f'idx_{items.index(item)}'))] = emb
        
        groups = []
        assigned = set()
        
        for item in items:
            item_id = item.get('id', item.get('url', f'idx_{items.index(item)}'))
            
            if item_id in assigned:
                continue
            
            current_group = [item]
            assigned.add(item_id)
            
            item_emb = embeddings.get(item_id)
            if not item_emb:
                continue
            
            for other in items:
                other_id = other.get('id', other.get('url', f'idx_{items.index(other)}'))
                
                if other_id in assigned:
                    continue
                
                other_emb = embeddings.get(other_id)
                if not other_emb:
                    continue
                
                similarity = self.cosine_similarity(item_emb, other_emb)
                
                if similarity >= threshold:
                    current_group.append(other_id)
                    assigned.add(other_id)
            
            groups.append(current_group)
        
        return groups
    
    def group_by_category(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupa por categoría."""
        grouped = defaultdict(list)
        
        for item in items:
            category = item.get('category', 'unknown')
            grouped[category].append(item)
        
        return dict(grouped)
    
    def optimize_order(self, items: List[Dict[str, Any]], 
                   priorities: List[str] = None) -> List[Dict[str, Any]]:
        """Optimiza orden considerando similaridad y prioridad."""
        if not priorities:
            priorities = ['high', 'medium', 'low']
        
        priority_map = {p: i for i, p in enumerate(priorities)}
        
        sorted_items = sorted(
            items,
            key=lambda x: (
                priority_map.get(x.get('priority', 'medium'), 
                x.get('created_at', '')
            ),
            reverse=True
        )
        
        return sorted_items
    
    def get_group_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de grupos."""
        return {
            'total_groups': len(self.groups),
            'total_items': sum(len(g) for g in self.groups.values())
        }


def create_batch_grouper(model: Optional[str] = None) -> BatchGrouper:
    """Factory function."""
    return BatchGrouper(model)