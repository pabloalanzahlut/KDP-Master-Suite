"""
Multi-Thread Coordinator
========================
Coordinador de tareas multi-thread para backup paralelo.
"""

import threading
import queue
import time
from typing import Callable, List, Optional, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future


@dataclass
class Task:
    task_id: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: int = 0


class MultiThreadCoordinator:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: List[Future] = []
        self._lock = threading.Lock()
        self._results: Dict[str, any] = {}
        self._task_queue = queue.PriorityQueue()

    def submit(self, task_id: str, func: Callable, *args, priority: int = 0, **kwargs) -> Future:
        future = self.executor.submit(func, *args, **kwargs)
        with self._lock:
            self.tasks.append(future)
            self._task_queue.put((priority, task_id, future))
        return future

    def wait_all(self, timeout: Optional[float] = None) -> Dict[str, any]:
        results = {}
        for task in self.tasks:
            try:
                result = task.result(timeout=timeout)
                results[task] = result
            except Exception as e:
                results[task] = {"error": str(e)}
        return results

    def get_active_count(self) -> int:
        return sum(1 for t in self.tasks if not t.done())

    def shutdown(self, wait: bool = True):
        self.executor.shutdown(wait=wait)

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "max_workers": self.max_workers,
                "total_tasks": len(self.tasks),
                "active": self.get_active_count(),
                "completed": sum(1 for t in self.tasks if t.done())
            }


_global_coordinator = None


def get_multi_thread_coordinator(max_workers: int = 4) -> MultiThreadCoordinator:
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = MultiThreadCoordinator(max_workers)
    return _global_coordinator