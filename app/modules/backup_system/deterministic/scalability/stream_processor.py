"""
Stream Processor
================
Procesador de streams para backup de grandes archivos.
"""

import threading
import time
from typing import Callable, Optional, Iterator, Any
from dataclasses import dataclass


@dataclass
class StreamChunk:
    data: bytes
    chunk_id: int
    size: int
    timestamp: float


class StreamProcessor:
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
        self._lock = threading.Lock()
        self._callbacks: list = []

    def process_file(self, file_path: str, callback: Callable[[bytes], None]) -> bool:
        try:
            with open(file_path, "rb") as f:
                chunk_id = 0
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    callback(chunk)
                    chunk_id += 1
            return True
        except Exception:
            return False

    def process_iterator(self, data_iterator: Iterator, callback: Callable[[bytes], None]) -> int:
        count = 0
        for chunk in data_iterator:
            callback(chunk)
            count += 1
        return count

    def register_callback(self, callback: Callable[[StreamChunk], None]):
        self._callbacks.append(callback)

    def notify_chunk(self, chunk: StreamChunk):
        for cb in self._callbacks:
            try:
                cb(chunk)
            except Exception:
                pass


_global_processor = None


def get_stream_processor(chunk_size: int = 8192) -> StreamProcessor:
    global _global_processor
    if _global_processor is None:
        _global_processor = StreamProcessor(chunk_size)
    return _global_processor