"""
Partial Clear Strategy - Módulo 49
===================================
Estrategia para vaciar solo un porcentaje de los items más antiguos.

¿Para qué sirve esto?
====================
Imagina que tienes 100items en tu cola y quieres hacer limpieza,
pero no quieres borrar TODO. Solo quieres quitar los más viejos
porque probablemente ya no los vas a usar.

Caso de uso real:
================
- Tienes 100 videos en cola
- Solo quieres borrar los 50 más antiguos (50%)
- Los 50 nuevos se quedan

Este módulo permite hacer exactamente eso:
- oldest_50 = Borrar los 50 más antiguos
- oldest_75 = Borrar los 75 más antiguos
- custom = Borrar X cantidad específica
"""

import logging
from typing import List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PartialClearStrategy:
    """
    Estrategia de vaciado parcial por antigüedad.
    
    Implementa filtros para borrar solo un porcentaje o cantidad
    específica de los items más antiguos de la cola.
    """

    def __init__(self):
        logger.info("PartialClearStrategy inicializado")

    def apply(
        self,
        items: List[Any],
        percentage: Optional[int] = None,
        count: Optional[int] = None
    ) -> tuple[List[Any], List[Any]]:
        """
        Aplica la estrategia de vaciado parcial.
        
        Args:
            items: Lista completa de items.
            percentage: Porcentaje de items a borrar (50, 75).
            count: Cantidad específica de items a borrar.

        Returns:
            Tupla (items_a_borrar, items_a_conservar).
        """
        if not items:
            return [], []
        
        items_with_date = [i for i in items if self._has_date(i)]
        
        if not items_with_date:
            logger.warning("Aucun item con fecha - usando orden original")
            items_with_date = items
        
        sorted_items = sorted(
            items_with_date,
            key=lambda x: self._get_date(x),
            reverse=False
        )
        
        if percentage is not None:
            to_clear_count = len(sorted_items) * percentage // 100
        elif count is not None:
            to_clear_count = min(count, len(sorted_items))
        else:
            logger.warning("Sin percentage ni count - retorna todo")
            return items, []
        
        to_clear = sorted_items[:to_clear_count]
        to_keep = sorted_items[to_clear_count:]
        
        items_not_sorted = [i for i in items if not self._has_date(i)]
        to_keep.extend(items_not_sorted)
        
        logger.info(f"Partial clear: {len(to_clear)} a borrar, {len(to_keep)} a conservar")
        
        return to_clear, to_keep

    def apply_oldest_percent(
        self,
        items: List[Any],
        percent: int
    ) -> tuple[List[Any], List[Any]]:
        """
        Versión simplificada para porcentajes comunes.
        
        Args:
            items: Lista de items.
            percent: Porcentaje (50, 75).

        Returns:
            Tupla (a borrar, a conservar).
        """
        return self.apply(items, percentage=percent)

    def apply_oldest_50(self, items: List[Any]) -> tuple[List[Any], List[Any]]:
        """Borra el 50% más antiguo."""
        return self.apply(items, percentage=50)

    def apply_oldest_75(self, items: List[Any]) -> tuple[List[Any], List[Any]]:
        """Borra el 75% más antiguo."""
        return self.apply(items, percentage=75)

    def apply_custom_count(
        self,
        items: List[Any],
        count: int
    ) -> tuple[List[Any], List[Any]]:
        """
        Borra una cantidad específica de items.
        
        Args:
            items: Lista de items.
            count: Número de items a borrar (desde los más antiguos).

        Returns:
            Tupla (a borrar, a conservar).
        """
        return self.apply(items, count=count)

    def _has_date(self, item: Any) -> bool:
        """Verifica si el item tiene fecha."""
        if hasattr(item, 'added_at'):
            return item.added_at is not None
        elif isinstance(item, dict):
            return item.get('added_at') is not None
        return False

    def _get_date(self, item: Any) -> datetime:
        """Obtiene la fecha del item."""
        if hasattr(item, 'added_at'):
            return item.added_at or datetime.min
        elif isinstance(item, dict):
            date_str = item.get('added_at')
            if date_str:
                try:
                    if isinstance(date_str, str):
                        return datetime.fromisoformat(date_str)
                    return date_str
                except:
                    pass
        return datetime.min


def create_partial_strategy() -> PartialClearStrategy:
    """Factory function."""
    return PartialClearStrategy()