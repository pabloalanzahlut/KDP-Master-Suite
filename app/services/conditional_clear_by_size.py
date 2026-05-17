"""
Conditional Clear by Size - Módulo 51
=====================================
Filtro de vaciado condicional por tamaño de archivo o duración de video.

¿Para qué sirve esto?
====================
Imagina que quieres hacer limpieza pero solo quieres borrar
los videos "pesados" que ocupan mucho espacio, o los videos
largos que probablemente ya viste y no necesitas.

Caso de uso real:
================
- Tienes 100 videos en cola
- Solo quieres borrar los que pesen más de 100MB → Se borran solo esos
- Los videos cortos se quedan

O:
- Solo quieres borrar videos de más de 60 minutos → Los largos se van
- Los shorts se quedan

Este módulo permite esos filtros condicionales.
"""

import logging
from typing import List, Any, Tuple, Dict, Optional

logger = logging.getLogger(__name__)


class ConditionalClearBySize:
    """
    Filtro de vaciado por tamaño de archivo o duración de video.
    
    Implementa estrategias de filtrado basadas en:
    - Tamaño de archivo (MB/GB)
    - Duración del video (minutos/horas)
    - Combinaciones de ambos
    """

    def __init__(self):
        logger.info("ConditionalClearBySize inicializado")

    def filter_by_size(
        self,
        items: List[Any],
        min_mb: float = 0,
        max_mb: float = float('inf')
    ) -> Tuple[List[Any], List[Any]]:
        """
        Filtra items por tamaño de archivo.
        
        Args:
            items: Lista de items.
            min_mb: Tamaño mínimo en MB.
            max_mb: Tamaño máximo en MB.

        Returns:
            Tupla (items que cumplen el filtro, items que no).
        """
        matched = []
        not_matched = []
        
        for item in items:
            size_mb = self._extract_size(item)
            
            if min_mb <= size_mb <= max_mb:
                matched.append(item)
            else:
                not_matched.append(item)
        
        logger.info(f"Filtrado por tamaño: {len(matched)}匹配的, {len(not_matched)} no coincidieron")
        
        return matched, not_matched

    def filter_by_duration(
        self,
        items: List[Any],
        min_seconds: int = 0,
        max_seconds: int = float('inf')
    ) -> Tuple[List[Any], List[Any]]:
        """
        Filtra items por duración.
        
        Args:
            items: Lista de items.
            min_seconds: Duración mínima en segundos.
            max_seconds: Duración máxima en segundos.

        Returns:
            Tupla (items que cumplen el filtro, items que no).
        """
        matched = []
        not_matched = []
        
        for item in items:
            duration = self._extract_duration(item)
            
            if min_seconds <= duration <= max_seconds:
                matched.append(item)
            else:
                not_matched.append(item)
        
        logger.info(f"Filtrado por duración: {len(matched)}匹配的, {len(not_matched)} no coincidieron")
        
        return matched, not_matched

    def filter_by_duration_range(
        self,
        items: List[Any],
        category: str
    ) -> Tuple[List[Any], List[Any]]:
        """
        Filtra por categorías comunes de duración.
        
        Args:
            items: Lista de items.
            category: Categoría ('shorts', 'medium', 'long', 'very_long').

        Returns:
            Tupla (items de esa categoría, items de otras).
        """
        category_ranges = {
            'shorts': (0, 60),
            'medium': (60, 600),
            'long': (600, 3600),
            'very_long': (3600, float('inf'))
        }
        
        if category not in category_ranges:
            logger.warning(f"Categoría desconocida: {category}")
            return [], items
        
        min_s, max_s = category_ranges[category]
        return self.filter_by_duration(items, min_s, max_s)

    def filter_above_threshold(
        self,
        items: List[Any],
        threshold_mb: float,
        sort_by: str = "size"
    ) -> List[Any]:
        """
        Filtra items que superan un umbral, ordenados por tamaño/duración.
        
        Args:
            items: Lista de items.
            threshold_mb: Umbral de tamaño en MB.
            sort_by: Ordenar por ('size' o 'duration').

        Returns:
            Lista de items que superan el umbral, ordenada.
        """
        filtered = []
        
        for item in items:
            size_mb = self._extract_size(item)
            if size_mb >= threshold_mb:
                filtered.append(item)
        
        if sort_by == "size":
            filtered.sort(key=lambda x: self._extract_size(x), reverse=True)
        elif sort_by == "duration":
            filtered.sort(key=lambda x: self._extract_duration(x), reverse=True)
        
        logger.info(f"Filtrados {len(filtered)} items sobre {threshold_mb}MB")
        
        return filtered

    def get_size_distribution(self, items: List[Any]) -> Dict[str, Any]:
        """
        Obtiene distribución de tamaños en la cola.
        
        Returns:
            Diccionario con estadísticas de tamaño.
        """
        if not items:
            return {
                "total": 0,
                "total_mb": 0,
                "avg_mb": 0,
                "min_mb": 0,
                "max_mb": 0
            }
        
        sizes = [self._extract_size(item) for item in items]
        
        return {
            "total": len(items),
            "total_mb": sum(sizes),
            "avg_mb": sum(sizes) / len(sizes),
            "min_mb": min(sizes),
            "max_mb": max(sizes),
            "distribution": self._categorize_sizes(sizes)
        }

    def get_duration_distribution(self, items: List[Any]) -> Dict[str, Any]:
        """
        Obtiene distribución de duraciones en la cola.
        
        Returns:
            Diccionario con estadísticas de duración.
        """
        if not items:
            return {
                "total": 0,
                "total_minutes": 0,
                "avg_minutes": 0
            }
        
        durations = [self._extract_duration(item) for item in items]
        
        return {
            "total": len(items),
            "total_minutes": sum(durations) / 60,
            "avg_minutes": (sum(durations) / len(durations)) / 60,
            "distribution": self._categorize_durations(durations)
        }

    def _extract_size(self, item: Any) -> float:
        """Extrae el tamaño en MB de un item."""
        if hasattr(item, 'file_size_mb'):
            return float(item.file_size_mb)
        elif isinstance(item, dict):
            return float(item.get('file_size_mb', 0))
        return 0

    def _extract_duration(self, item: Any) -> int:
        """Extrae la duración en segundos de un item."""
        if hasattr(item, 'duration_seconds'):
            return int(item.duration_seconds)
        elif isinstance(item, dict):
            return int(item.get('duration_seconds', 0))
        return 0

    def _categorize_sizes(self, sizes: List[float]) -> Dict[str, int]:
        """Categoriza tamaños en rangos."""
        categories = {
            'tiny (<10MB)': 0,
            'small (10-50MB)': 0,
            'medium (50-200MB)': 0,
            'large (200-500MB)': 0,
            'very_large (>500MB)': 0
        }
        
        for size in sizes:
            if size < 10:
                categories['tiny (<10MB)'] += 1
            elif size < 50:
                categories['small (10-50MB)'] += 1
            elif size < 200:
                categories['medium (50-200MB)'] += 1
            elif size < 500:
                categories['large (200-500MB)'] += 1
            else:
                categories['very_large (>500MB)'] += 1
        
        return categories

    def _categorize_durations(self, durations: List[int]) -> Dict[str, int]:
        """Categoriza duraciones en rangos."""
        categories = {
            'shorts (<1min)': 0,
            'short (1-10min)': 0,
            'medium (10-30min)': 0,
            'long (30-60min)': 0,
            'very_long (>60min)': 0
        }
        
        for d in durations:
            if d < 60:
                categories['shorts (<1min)'] += 1
            elif d < 600:
                categories['short (1-10min)'] += 1
            elif d < 1800:
                categories['medium (10-30min)'] += 1
            elif d < 3600:
                categories['long (30-60min)'] += 1
            else:
                categories['very_long (>60min)'] += 1
        
        return categories


def create_size_conditional() -> ConditionalClearBySize:
    """Factory function."""
    return ConditionalClearBySize()