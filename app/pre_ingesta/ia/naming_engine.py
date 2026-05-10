"""
KDP MASTER - Naming Engine (Módulo 14)
===================================
Motor de naming semántico corporativo.
Genera nombres de archivo normalizados.
"""

import re
import os
from typing import Optional, Tuple


class NamingEngine:
    """Módulo 14: Motor de naming semántico corporativo."""
    
    STOP_WORDS = [
        'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'con',
        'para', 'por', 'sin', 'sobre', 'entre', 'y', 'o', 'a', 'al',
        'the', 'a', 'an', 'of', 'in', 'on', 'for', 'to', 'with', 'and', 'or'
    ]
    
    MAX_TITLE_LENGTH = 60
    
    def __init__(self):
        self.use_spanish = True
    
    def set_language(self, use_spanish: bool):
        """Configura idioma."""
        self.use_spanish = use_spanish
    
    def generate_filename(self, title: str, video_id: Optional[str] = None,
                   category: Optional[str] = None) -> str:
        """
        Genera nombre de archivo normalizado.
        """
        clean = self._clean_title(title)
        
        if category:
            clean = f"[{category}] {clean}"
        
        if video_id:
            clean = f"{clean}_{video_id}"
        
        return clean
    
    def _clean_title(self, title: str) -> str:
        """Limpia título para filename."""
        clean = title.strip()
        
        clean = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ]', '', clean)
        
        words = clean.split()
        words = [w for w in words if w.lower() not in self.STOP_WORDS or len(w) > 3]
        
        clean = '_'.join(words[:8])
        
        clean = re.sub(r'_+', '_', clean)
        
        if len(clean) > self.MAX_TITLE_LENGTH:
            clean = clean[:self.MAX_TITLE_LENGTH]
        
        return clean.strip('_')
    
    def extract_keywords(self, title: str, description: str = "",
                   max_keywords: int = 5) -> list:
        """Extrae keywords del contenido."""
        text = f"{title} {description}".lower()
        
        text = re.sub(r'[^\w\s]', ' ', text)
        
        words = text.split()
        words = [w for w in words if len(w) > 3 and w.lower() not in self.STOP_WORDS]
        
        from collections import Counter
        freq = Counter(words)
        
        keywords = [w for w, _ in freq.most_common(max_keywords)]
        
        return keywords
    
    def generate_descriptive_name(self, title: str, channel: str = "",
                         category: Optional[str] = None) -> Tuple[str, str]:
        """Genera nombre descriptivo + resumen."""
        filename = self.generate_filename(title, category=category)
        
        short_desc = title[:100] if title else "Sin descripción"
        
        return filename, short_desc


def create_naming_engine() -> NamingEngine:
    """Factory function."""
    return NamingEngine()