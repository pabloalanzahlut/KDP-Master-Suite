"""
KDP MASTER - Deduplicator (Módulo 3)
==================================
Deduplicador transversal en tiempo real.
"""

import json
import hashlib
import os
from typing import List, Tuple, Set, Dict, Optional
from datetime import datetime

from ..pre_ingesta.base import QueueItem


class DeduplicatorEngine:
    """Módulo 3: Deduplicador transversal en tiempo real."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._get_default_db_path()
        self.seen_hashes: Set[str] = set()
        self.seen_urls: Set[str] = set()
        self._load_cache()
    
    def _get_default_db_path(self) -> str:
        """Obtiene path por defecto."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'data', 'pre_ingesta_dedup.cache')
    
    def _load_cache(self):
        """Carga cache de hashes."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seen_hashes = set(data.get('hashes', []))
                    self.seen_urls = set(data.get('urls', []))
            except Exception:
                pass
    
    def _save_cache(self):
        """Guarda cache de hashes."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'hashes': list(self.seen_hashes),
                    'urls': list(self.seen_urls),
                    'updated': datetime.now().isoformat()
                }, f, ensure_ascii=False)
        except Exception:
            pass
    
    def _generate_hash(self, url: str) -> str:
        """Genera hash para URL."""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
    
    def check_duplicate(self, url: str) -> Tuple[bool, str]:
        """
        Verifica duplicado en tiempo real.
        Returns: (is_duplicate, status_message)
        """
        url_normalized = url.strip().lower()
        
        if url_normalized in self.seen_urls:
            return True, "URL ya existente en cache local"
        
        item_hash = self._generate_hash(url)
        if item_hash in self.seen_hashes:
            return True, "Hash ya existente en cache local"
        
        return False, "Único"
    
    def check_from_history(self, url: str, history_db_path: str) -> Tuple[bool, str]:
        """
        Verifica contra historial de procesados.
        """
        if not os.path.exists(history_db_path):
            return False, "Sin historial"
        
        try:
            import sqlite3
            conn = sqlite3.connect(history_db_path)
            cursor = conn.cursor()
            
            normalized = url.strip()
            cursor.execute("SELECT COUNT(*) FROM videos WHERE url = ? OR video_id = ?", 
                        (normalized, self._extract_video_id(url)))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                return True, "Ya procesado anteriormente"
            
            return False, "No encontrado en historial"
        except Exception:
            return False, "Error al consultar historial"
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extrae video ID de URL YouTube."""
        import re
        patterns = [
            r'(?:v=|/)([\w-]{11})',
            r'youtube\.com/shorts/([\w-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def mark_as_seen(self, item: QueueItem):
        """Marca item como visto."""
        self.seen_urls.add(item.url.strip().lower())
        
        item_hash = self._generate_hash(item.url)
        self.seen_hashes.add(item_hash)
        
        self._save_cache()
    
    def clear_cache(self):
        """Limpia cache."""
        self.seen_hashes.clear()
        self.seen_urls.clear()
        self._save_cache()
    
    def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas."""
        return {
            'cached_hashes': len(self.seen_hashes),
            'cached_urls': len(self.seen_urls)
        }


def create_deduplicator(db_path: Optional[str] = None) -> DeduplicatorEngine:
    """Factory function."""
    return DeduplicatorEngine(db_path)