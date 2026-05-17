"""
Queue Trash Bin - Módulo 48
===========================
Sistema de papelera temporal para recuperación de items borrados (Undo).

¿Para qué sirve esto?
====================
Es exactamente como la papelera de reciclaje de Windows.
Cuando borras un archivo, no desaparece inmediatamente.
Va a la papelera y puedes recuperarlo durante un tiempo.

Caso de uso real:
================
- Borras un documento de Word por error → Vas a la papelera → Lo restauras
- Vacías la papelera → Ya no hay vuelta atrás

Aquí funciona igual:
1. Vacías la cola → Los items van a la papelera
2. Tienes 60 segundos para presionar "♻️ Restaurar"
3. Pasados los 60 segundos → Se eliminan permanentemente

Este módulo implementa ese comportamiento.
"""

import logging
import time
from collections import deque
from datetime import datetime
from typing import List, Optional, Any, Dict

logger = logging.getLogger(__name__)


class QueueTrashBin:
    """
    Papelera temporal para items borrados de la cola.
    
    Proporciona funcionalidad de "Deshacer" (Undo) después de un vaciado.
    Los items se mantienen temporalmente y luego se eliminan permanentemente.
    """

    def __init__(self, timeout_seconds: int = 60):
        """
        Inicializa la papelera.
        
        Args:
            timeout_seconds: Tiempo en segundos antes de eliminar permanentemente.
                           Default: 60 segundos.
        """
        self._items = deque()
        self._timeout_seconds = timeout_seconds
        self._last_clear_time: Optional[float] = None
        self._last_clear_items: List[Any] = []
        
        logger.info(f"QueueTrashBin inicializado: timeout={timeout_seconds}s")

    def add_items(self, items: List[Any]):
        """
        Añade items a la papelera (después de un vaciado).
        
        Args:
            items: Lista de items a guardar temporalmente.
        """
        self._items.clear()
        self._items.extend(items)
        self._last_clear_time = time.time()
        self._last_clear_items = items
        
        logger.info(f"Añadidos {len(items)} items a la papelera")

    def get_items(self) -> List[Any]:
        """
        Recupera los items de la papelera si está dentro del timeout.
        
        Returns:
            Lista de items o lista vacía si expiró el timeout.
        """
        if self._last_clear_time is None:
            return []
        
        elapsed = time.time() - self._last_clear_time
        
        if elapsed > self._timeout_seconds:
            logger.info(f"Timeout expirado ({elapsed:.1f}s > {self._timeout_seconds}s)")
            self.clear()
            return []
        
        remaining = self._timeout_seconds - elapsed
        logger.info(f"Undo disponible: {remaining:.1f}s restantes")
        
        return list(self._items)

    def is_available(self) -> bool:
        """
        Verifica si la papelera tiene items recuperables.
        
        Returns:
            True si hay items dentro del timeout.
        """
        return len(self._items) > 0 and self.get_items() is not None

    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la papelera.
        
        Returns:
            Diccionario con información de estado.
        """
        has_items = len(self._items) > 0
        
        if not has_items or self._last_clear_time is None:
            return {
                "has_items": False,
                "items_count": 0,
                "remaining_seconds": 0,
                "is_expired": True
            }
        
        elapsed = time.time() - self._last_clear_time
        remaining = max(0, self._timeout_seconds - elapsed)
        is_expired = elapsed > self._timeout_seconds
        
        return {
            "has_items": True,
            "items_count": len(self._items),
            "remaining_seconds": remaining,
            "is_expired": is_expired,
            "last_clear_time": self._last_clear_time
        }

    def clear(self):
        """Elimina permanentemente todos los items de la papelera."""
        count = len(self._items)
        self._items.clear()
        self._last_clear_time = None
        self._last_clear_items = []
        
        logger.info(f" Papelera vaciada: {count} items eliminados permanentemente")

    def restore(self) -> Optional[List[Any]]:
        """
        Recupera los items y limpia la papelera.
        
        Returns:
            Lista de items restaurados o None si expiró.
        """
        items = self.get_items()
        
        if items:
            self.clear()
            logger.info(f" Restaurados {len(items)} items desde la papelera")
            return items
        
        return None

    def peek(self) -> List[Any]:
        """
        Mira los items sin quitarlos de la papelera.
        
        Returns:
            Lista de items en la papelera.
        """
        return list(self._items)

    def set_timeout(self, seconds: int):
        """
        Cambia el timeout de la papelera.
        
        Args:
            seconds: Nuevo timeout en segundos.
        """
        self._timeout_seconds = seconds
        logger.info(f"Timeout de papelera actualizado: {seconds}s")


def create_trash_bin(timeout_seconds: int = 60) -> QueueTrashBin:
    """
    Factory function para crear una instancia de QueueTrashBin.
    """
    return QueueTrashBin(timeout_seconds=timeout_seconds)