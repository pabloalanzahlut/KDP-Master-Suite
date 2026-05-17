"""
P1-3: Scroll Infinito con Buffer
Carga los siguientes 100 videos automáticamente al llegar al final del scroll.
"""
import logging
from typing import List, Dict, Callable, Optional

logger = logging.getLogger(__name__)


class ScrollBuffer:
    """Buffer de scroll infinito para carga de videos."""

    DEFAULT_BUFFER_SIZE = 100

    def __init__(
        self,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        on_load_more: Optional[Callable] = None
    ):
        self.buffer_size = buffer_size
        self.on_load_more = on_load_more
        self._loaded_items: List = []
        self._current_index = 0
        self._has_more = True

    def set_items(self, items: List, reset: bool = True):
        """Establece los items a paginar."""
        if reset:
            self._loaded_items = []
            self._current_index = 0
        self._all_items = items
        self._has_more = len(items) > self.buffer_size

    def get_visible_items(self) -> List:
        """Retorna los items actualmente visibles."""
        end = min(self._current_index + self.buffer_size, len(self._loaded_items))
        return self._loaded_items[:end]

    def on_scroll_position(self, position: float):
        """
        Detecta cuando el usuario está cerca del final y carga más.
        Args:
            position: Posición del scroll (0.0 a 1.0)
        """
        if not self._has_more:
            return

        if position >= 0.9 and self.on_load_more:
            self.load_more()

    def load_more(self) -> int:
        """Carga más items del buffer."""
        start = self._current_index
        end = min(start + self.buffer_size, len(self._all_items))

        new_items = self._all_items[start:end]
        self._loaded_items.extend(new_items)
        self._current_index = end

        self._has_more = end < len(self._all_items)

        logger.debug(f"Cargados {len(new_items)} items. Total: {len(self._loaded_items)}/{len(self._all_items)}")
        return len(new_items)

    def reset(self):
        """Reinicia el buffer."""
        self._loaded_items = []
        self._current_index = 0
        self._has_more = True

    def has_more(self) -> bool:
        """Indica si hay más items por cargar."""
        return self._has_more

    def get_progress(self) -> float:
        """Retorna el progreso de carga (0.0 a 1.0)."""
        if not self._all_items:
            return 0.0
        return len(self._loaded_items) / len(self._all_items)


def get_scroll_buffer(buffer_size: int = 100) -> ScrollBuffer:
    return ScrollBuffer(buffer_size=buffer_size)