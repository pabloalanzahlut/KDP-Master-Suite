"""
Async I/O Handler
=================
Manejador de I/O asíncrono para operaciones de backup (fallback sin aiofiles).
"""

import threading
import concurrent.futures
from typing import Optional, List, Dict, Any
from pathlib import Path


class AsyncIOHandler:
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent)
        self._lock = threading.Lock()

    def read_file_async(self, file_path: str) -> Optional[bytes]:
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception:
            return None

    def write_file_async(self, file_path: str, data: bytes) -> bool:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(data)
            return True
        except Exception:
            return False

    def copy_file_async(self, src: str, dst: str) -> bool:
        data = self.read_file_async(src)
        if data:
            return self.write_file_async(dst, data)
        return False

    def batch_read_async(self, file_paths: List[str]) -> Dict[str, Optional[bytes]]:
        results = {}
        futures = {self.executor.submit(self.read_file_async, fp): fp for fp in file_paths}
        for future in concurrent.futures.as_completed(futures):
            fp = futures[future]
            results[fp] = future.result()
        return results

    def batch_write_async(self, file_data: Dict[str, bytes]) -> Dict[str, bool]:
        results = {}
        futures = {self.executor.submit(self.write_file_async, fp, data): fp for fp, data in file_data.items()}
        for future in concurrent.futures.as_completed(futures):
            fp = futures[future]
            results[fp] = future.result()
        return results

    def shutdown(self):
        self.executor.shutdown(wait=True)


def get_async_io_handler(max_concurrent: int = 10) -> AsyncIOHandler:
    return AsyncIOHandler(max_concurrent)