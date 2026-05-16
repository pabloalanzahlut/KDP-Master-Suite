"""
Batch Processor
===============
Procesador de lotes para operaciones de backup masivas.
"""

import threading
from typing import List, Callable, Any, Dict, Optional
from dataclasses import dataclass
import time


@dataclass
class BatchJob:
    job_id: str
    items: List[Any]
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class BatchProcessor:
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self._lock = threading.Lock()
        self._jobs: Dict[str, BatchJob] = {}
        self._callbacks: Dict[str, Callable] = {}

    def create_job(self, job_id: str, items: List[Any]) -> str:
        with self._lock:
            self._jobs[job_id] = BatchJob(job_id=job_id, items=items)
        return job_id

    def process_job(self, job_id: str, processor: Callable[[List[Any]], Any]) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            job.status = "running"
            job.start_time = time.time()

        try:
            results = []
            items = job.items
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                result = processor(batch)
                results.append(result)

            with self._lock:
                job.status = "completed"
                job.end_time = time.time()
            return True
        except Exception:
            with self._lock:
                job.status = "failed"
            return False

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return {
                "job_id": job.job_id,
                "status": job.status,
                "item_count": len(job.items),
                "start_time": job.start_time,
                "end_time": job.end_time
            }

    def get_all_jobs(self) -> List[Dict]:
        with self._lock:
            return [
                {"job_id": j.job_id, "status": j.status, "items": len(j.items)}
                for j in self._jobs.values()
            ]


_global_processor = None


def get_batch_processor(batch_size: int = 50) -> BatchProcessor:
    global _global_processor
    if _global_processor is None:
        _global_processor = BatchProcessor(batch_size)
    return _global_processor