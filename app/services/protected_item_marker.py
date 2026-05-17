"""
Protected Item Marker - Módulo 50
=================================
Sistema para marcar y proteger items importantes de la cola.

¿Para qué sirve esto?
====================
Imagina que tienes una canción favorita en tu playlist.
No quieres que cuando borres la playlist se elimine esa canción.
La marcas como "protegida" y nunca se borra.

Caso de uso real:
================
- Tienes 50 videos en cola
- 3 son "referencia" para un proyecto importante
- Quieres vaciar la cola pero SIN perder esos 3
- Los marcas como "Protegido" → No se borran nunca

Este módulo:
1. Permite MARCAR items como protegidos
2. Protege automáticamente items con metadata enriquecida
3. Muestra advertencia cuando hay items protegidos
4. Impide el borrado de items protegidos (excepto explícitamente)
"""

import logging
from typing import List, Any, Dict, Set, Optional
import threading

logger = logging.getLogger(__name__)


class ProtectedItemMarker:
    """
    Gestor de protección de items en la cola.
    
    Implementa sistema de marcado y protección de items importantes.
    """

    _lock = threading.Lock()

    def __init__(self):
        self._protected_indices: Set[int] = set()
        self._protected_urls: Set[str] = set()
        
        logger.info("ProtectedItemMarker inicializado")

    def mark_as_protected(self, items: List[Any], indices: List[int]) -> int:
        """
        Marca items como protegidos por índice.
        
        Args:
            items: Lista de items.
            indices: Índices de items a proteger.

        Returns:
            Número de items marcados.
        """
        with self._lock:
            count = 0
            for idx in indices:
                if 0 <= idx < len(items):
                    if hasattr(items[idx], 'is_protected'):
                        items[idx].is_protected = True
                    
                    self._protected_indices.add(idx)
                    
                    url = self._extract_url(items[idx])
                    if url:
                        self._protected_urls.add(url)
                    
                    count += 1
            
            logger.info(f"Protegidos {count} items por índice")
            return count

    def mark_by_url(self, items: List[Any], urls: List[str]) -> int:
        """
        Marca items como protegidos por URL.
        
        Args:
            items: Lista de items.
            urls: Lista de URLs a proteger.

        Returns:
            Número de items marcados.
        """
        with self._lock:
            urls_set = set(urls)
            count = 0
            
            for idx, item in enumerate(items):
                url = self._extract_url(item)
                if url in urls_set:
                    if hasattr(item, 'is_protected'):
                        item.is_protected = True
                    self._protected_indices.add(idx)
                    self._protected_urls.add(url)
                    count += 1
            
            logger.info(f"Protegidos {count} items por URL")
            return count

    def unmark_protected(self, items: List[Any], indices: List[int]) -> int:
        """
        Quita la protección de items.
        
        Args:
            items: Lista de items.
            indices: Índices a desproteger.

        Returns:
            Número de items desprotegidos.
        """
        with self._lock:
            count = 0
            for idx in indices:
                if 0 <= idx < len(items):
                    if hasattr(items[idx], 'is_protected'):
                        items[idx].is_protected = False
                    
                    self._protected_indices.discard(idx)
                    url = self._extract_url(items[idx])
                    if url:
                        self._protected_urls.discard(url)
                    
                    count += 1
            
            logger.info(f"Desprotegidos {count} items")
            return count

    def get_protected_items(self, items: List[Any]) -> List[Any]:
        """
        Obtiene lista de items protegidos.
        
        Args:
            items: Lista de items.

        Returns:
            Lista de items protegidos.
        """
        protected = []
        
        for idx, item in enumerate(items):
            is_protected = False
            
            if hasattr(item, 'is_protected') and item.is_protected:
                is_protected = True
            elif idx in self._protected_indices:
                is_protected = True
            elif hasattr(item, 'url') and item.url in self._protected_urls:
                is_protected = True
            elif isinstance(item, dict) and item.get('url') in self._protected_urls:
                is_protected = True
            
            if is_protected:
                protected.append(item)
        
        return protected

    def get_protected_count(self, items: List[Any]) -> int:
        """
        Obtiene el número de items protegidos.
        
        Args:
            items: Lista de items.

        Returns:
            Número de items protegidos.
        """
        return len(self.get_protected_items(items))

    def filter_protected(self, items: List[Any]) -> tuple[List[Any], List[Any]]:
        """
        Filtra items en protegidos y no protegidos.
        
        Args:
            items: Lista de items.

        Returns:
            Tupla (protegidos, no_protegidos).
        """
        protected = []
        not_protected = []
        
        for item in items:
            is_protected = (
                (hasattr(item, 'is_protected') and item.is_protected) or
                (hasattr(item, 'url') and item.url in self._protected_urls) or
                (isinstance(item, dict) and item.get('url') in self._protected_urls)
            )
            
            if is_protected:
                protected.append(item)
            else:
                not_protected.append(item)
        
        return protected, not_protected

    def auto_protect_enriched(self, items: List[Any]) -> int:
        """
        Protege automáticamente items con metadata enriquecida.
        
        Args:
            items: Lista de items.

        Returns:
            Número de items protegidos automáticamente.
        """
        count = 0
        
        for idx, item in enumerate(items):
            is_enriched = False
            
            if hasattr(item, 'metadata_enriched'):
                is_enriched = item.metadata_enriched
            elif isinstance(item, dict):
                is_enriched = item.get('metadata_enriched', False)
            
            if is_enriched:
                if hasattr(item, 'is_protected'):
                    item.is_protected = True
                self._protected_indices.add(idx)
                count += 1
        
        if count > 0:
            logger.info(f"Auto-protegidos {count} items con metadata enriquecida")
        
        return count

    def get_protection_status(self, items: List[Any]) -> Dict[str, Any]:
        """
        Obtiene estado de protección de la cola.
        
        Returns:
            Diccionario con información de protección.
        """
        total = len(items)
        protected_count = self.get_protected_count(items)
        
        return {
            "total_items": total,
            "protected_count": protected_count,
            "unprotected_count": total - protected_count,
            "protection_percentage": (protected_count / total * 100) if total > 0 else 0
        }

    def _extract_url(self, item: Any) -> str:
        """Extrae la URL de un item."""
        if hasattr(item, 'url'):
            return item.url
        elif isinstance(item, dict):
            return item.get('url', '')
        return ''

    def clear_all_protections(self):
        """Limpia todas las protecciones."""
        with self._lock:
            count = len(self._protected_indices)
            self._protected_indices.clear()
            self._protected_urls.clear()
            logger.info(f"Limpiadas {count} protecciones")


def create_protected_marker() -> ProtectedItemMarker:
    """Factory function."""
    return ProtectedItemMarker()