"""
Cost Estimator
==============
Estima costo computational de backup.
"""

from typing import Dict


class CostEstimator:
    def estimate(self, file_count: int, size_mb: float) -> Dict:
        cpu_cost = file_count * 0.01
        io_cost = size_mb * 0.001
        total = cpu_cost + io_cost
        return {"cpu_cost": round(cpu_cost, 2), "io_cost": round(io_cost, 2), "total_cost": round(total, 2)}


def get_cost_estimator():
    return CostEstimator()