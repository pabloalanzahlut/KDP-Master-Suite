"""
Buffer Manager
==============
Gestor de buffers para operaciones de I/O optimizadas.
"""

import threading
from typing import Any, Optional
from collections import deque
from dataclasses import dataclass


@dataclass
class Buffer:
    data: Any
    size: int


class BufferManager:
    def __init__(self, max_size: int = 100, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._buffer = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._current_memory = 0

    def put(self, data: Any, size: int) -> bool:
        with self._lock:
            if self._current_memory + size > self.max_memory_bytes:
                return False
            self._buffer.append(Buffer(data=data, size=size))
            self._current_memory += size
            return True

    def get(self) -> Optional[Any]:
        with self._lock:
            if not self._buffer:
                return None
            buffer = self._buffer.popleft()
            self._current_memory -= buffer.size
            return buffer.data

    def clear(self):
        with self._lock:
            self._buffer.clear()
            self._current_memory = 0

    def get_size(self) -> int:
        with self._lock:
            return len(self._buffer)


def get_buffer_manager(max_size: int = 100, max_memory_mb: int = 100) -> BufferManager:
    return BufferManager(max_size, max_memory_mb)