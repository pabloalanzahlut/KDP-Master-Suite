"""
Disk Space Predictor
====================
Predice espacio en disco necesario.
"""

import shutil
from typing import Dict


class DiskSpacePredictor:
    def predict(self, total_size_mb: float, compression_ratio: float = 0.6) -> Dict:
        needed = total_size_mb * compression_ratio
        stat = shutil.disk_usage("/")
        available_mb = stat.free / (1024 ** 2)
        return {"needed_mb": round(needed, 2), "available_mb": round(available_mb, 2), "sufficient": available_mb > needed}


def get_disk_space_predictor():
    return DiskSpacePredictor()