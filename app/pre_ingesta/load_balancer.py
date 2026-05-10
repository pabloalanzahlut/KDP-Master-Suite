"""
KDP MASTER - Load Balancer (Módulo 12)
===================================
Balanceador de carga de cola.
"""

import threading
import time
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from ..pre_ingesta.base import QueueItem, QueuePriority


class LoadBalancer:
    """Módulo 12: Balanceador de carga de cola."""
    
    DEFAULT_MAX_WORKERS = 2
    DEFAULT_QUEUE_SIZE = 10
    
    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.lock = threading.Lock()
        self.paused = False
        self.stopped = False
    
    def distribute(self, items: List[QueueItem], processor: Callable[[QueueItem], bool]) -> dict:
        """
        Distribuye procesamiento entre hilos.
        Returns: stats
        """
        results = {
            'total': len(items),
            'completed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        if not items:
            return results
        
        with self.lock:
            if self.stopped:
                return results
            
            self.paused = False
        
        sorted_items = self._sort_by_priority(items)
        
        futures = []
        for item in sorted_items:
            if self._should_process():
                future = self.executor.submit(self._process_item, item, processor)
                futures.append(future)
            else:
                results['skipped'] += 1
        
        for future in as_completed(futures):
            if self.stopped:
                break
            
            try:
                success = future.result()
                with self.lock:
                    self.completed_tasks += 1
                    if success:
                        results['completed'] += 1
                    else:
                        results['failed'] += 1
            except Exception:
                with self.lock:
                    self.failed_tasks += 1
                    results['failed'] += 1
        
        return results
    
    def _sort_by_priority(self, items: List[QueueItem]) -> List[QueueItem]:
        """Ordena por prioridad."""
        priority_map = {QueuePriority.ALTA: 3, QueuePriority.MEDIA: 2, QueuePriority.BAJA: 1}
        return sorted(items, key=lambda x: priority_map.get(x.priority, 0), reverse=True)
    
    def _should_process(self) -> bool:
        """Verifica si debe procesar."""
        with self.lock:
            return self.active_tasks < self.max_workers and not self.paused and not self.stopped
    
    def _process_item(self, item: QueueItem, processor: Callable) -> bool:
        """Procesa un item individual."""
        try:
            with self.lock:
                self.active_tasks += 1
            
            result = processor(item)
            
            return result
        
        finally:
            with self.lock:
                self.active_tasks -= 1
    
    def pause(self):
        """Pausa procesamiento."""
        with self.lock:
            self.paused = True
    
    def resume(self):
        """Reanuda procesamiento."""
        with self.lock:
            self.paused = False
    
    def stop(self):
        """Detiene procesamiento."""
        with self.lock:
            self.stopped = True
            self.paused = False
    
    def reset(self):
        """Resetea estado."""
        with self.lock:
            self.paused = False
            self.stopped = False
            self.active_tasks = 0
    
    def get_status(self) -> dict:
        """Obtiene estado actual."""
        with self.lock:
            return {
                'active_tasks': self.active_tasks,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'paused': self.paused,
                'stopped': self.stopped,
                'max_workers': self.max_workers
            }
    
    def shutdown(self, wait: bool = True):
        """Cierra executor."""
        self.stop()
        self.executor.shutdown(wait=wait)


def create_load_balancer(max_workers: int = DEFAULT_MAX_WORKERS) -> LoadBalancer:
    """Factory function."""
    return LoadBalancer(max_workers)