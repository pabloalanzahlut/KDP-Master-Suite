"""
Resource Optimizer
==================
Optimiza uso de recursos durante backup.
"""

from typing import Dict


class ResourceOptimizer:
    def __init__(self):
        self.max_threads = 4
        self.max_memory_mb = 512

    def optimize(self, system_stats: Dict) -> Dict:
        cpu = system_stats.get("cpu", 50)
        mem = system_stats.get("memory", 50)
        threads = max(1, self.max_threads - (cpu // 30))
        return {"recommended_threads": threads, "batch_size": 50 if mem < 70 else 100}


def get_resource_optimizer():
    return ResourceOptimizer()