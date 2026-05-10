"""
KDP MASTER - Bulk Processor (Módulo 5)
==================================
Módulo de importación masiva (Bulk Ingest).
"""

import re
import json
from typing import List, Tuple, Optional
from datetime import datetime

from ..pre_ingesta.base import QueueItem


class BulkIngestProcessor:
    """Módulo 5: Procesador de importación masiva."""
    
    URL_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]{11}',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]{11}',
        r'(?:https?://)?(?:www\.)?youtube\.com/@[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/c/[\w-]+',
    ]
    
    def parse_input(self, raw_input: str) -> List[str]:
        """
        Parsea input masivo y extrae URLs limpieza.
        Soporta: comas, saltos de línea, mixed content.
        """
        urls = []
        
        raw_input = raw_input.strip()
        
        separators = ['\n', ',', ';', '|', ' ']
        for sep in separators:
            if sep in raw_input:
                parts = raw_input.split(sep)
                raw_input = ' '.join(parts)
        
        urls = re.findall(r'(https?://)?(?:www\.)?youtube\.com/[^\s<>"\'&]+', raw_input, re.IGNORECASE)
        
        cleaned_urls = []
        for url in urls:
            if not url.startswith('http'):
                url = 'https://' + url
            
            if self._is_valid_youtube_url(url):
                cleaned_urls.append(url)
        
        unique_urls = list(dict.fromkeys(cleaned_urls))
        
        return unique_urls
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Valida que sea URL de YouTube."""
        for pattern in self.URL_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def process_batch(self, raw_input: str, source: str = "bulk") -> Tuple[List[QueueItem], List[str]]:
        """
        Procesa batch completo y retorna items + errors.
        """
        urls = self.parse_input(raw_input)
        items = []
        errors = []
        
        for url in urls:
            try:
                item = QueueItem(url=url, source=source)
                items.append(item)
            except Exception as e:
                errors.append(f"Error creando item para {url}: {str(e)}")
        
        return items, errors
    
    def validate_urls(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Valida lista de URLs.
        Returns: (valid_urls, invalid_urls)
        """
        valid = []
        invalid = []
        
        for url in urls:
            if self._is_valid_youtube_url(url):
                valid.append(url)
            else:
                invalid.append(url)
        
        return valid, invalid
    
    def get_stats(self, raw_input: str) -> dict:
        """Obtiene estadísticas del input."""
        urls = self.parse_input(raw_input)
        return {
            'total_found': len(urls),
            'unique_count': len(set(urls)),
            'estimated_duration_minutes': len(urls) * 10,
            'estimated_size_mb': len(urls) * 150
        }


def create_bulk_processor() -> BulkIngestProcessor:
    """Factory function."""
    return BulkIngestProcessor()