"""
KDP MASTER - Metadata Tagger (Módulo 6)
===================================
Asignador de metadatos de sesión.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..pre_ingesta.base import QueueItem


class MetadataTagger:
    """Módulo 6: Asignador de metadatos de sesión."""
    
    AVAILABLE_TAGS = [
        'fiscalidad', 'inversiones', 'criptomonedas', 'bolsa', 'banking',
        'marketing', 'seo', 'negocios', 'emprendimiento', 'productividad',
        'tecnología', 'desarrollo', 'python', 'ia', 'machine_learning',
        'finanzas_personales', 'ahorro', 'jubilación', 'pensiones',
        'impuestos', '-legal', 'contabilidad', 'empresa', 'autónomo',
        'bienes_raíces', 'alquiler', 'reforma', 'decoración'
    ]
    
    def __init__(self):
        self.session_tags: Dict[str, Any] = {}
        self.project_labels: List[str] = []
    
    def set_session_tags(self, tags: Dict[str, Any]):
        """Configura tags de sesión."""
        self.session_tags = tags
    
    def set_project_label(self, label: str):
        """Configura label de proyecto."""
        if label not in self.project_labels:
            self.project_labels.append(label)
    
    def tag_item(self, item: QueueItem, video_metadata: Optional[Dict[str, Any]] = None) -> QueueItem:
        """Aplica tags al item."""
        for key, value in self.session_tags.items():
            item.metadata_tags[key] = value
        
        if self.project_labels:
            item.project_label = self.project_labels[0]
        
        if video_metadata:
            tags = video_metadata.get('tags', [])
            categories = video_metadata.get('categories', [])
            
            detected_tags = self._detect_tags_from_metadata(tags, categories)
            item.metadata_tags['detected_tags'] = detected_tags
        
        item.updated_at = datetime.now().isoformat()
        
        return item
    
    def _detect_tags_from_metadata(self, tags: List[str], categories: List[str]) -> List[str]:
        """Detecta tags desde metadata del video."""
        detected = []
        
        all_terms = [t.lower() for t in tags + categories]
        
        for available_tag in self.AVAILABLE_TAGS:
            for term in all_terms:
                if available_tag in term.lower() or term.lower() in available_tag:
                    if available_tag not in detected:
                        detected.append(available_tag)
        
        return detected[:5]
    
    def suggest_tags(self, title: str, description: str = "") -> List[str]:
        """Sugiere tags basándose en título y descripción."""
        text = f"{title} {description}".lower()
        suggestions = []
        
        for tag in self.AVAILABLE_TAGS:
            if tag in text:
                suggestions.append(tag)
        
        return suggestions[:5]
    
    def get_available_tags(self) -> List[str]:
        """Retorna tags disponibles."""
        return self.AVAILABLE_TAGS.copy()


def create_metadata_tagger() -> MetadataTagger:
    """Factory function."""
    return MetadataTagger()