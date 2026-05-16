"""
Data Masking
============
Enmascara datos sensibles.
"""

import re
from typing import Dict


class DataMasking:
    def mask(self, data: str) -> str:
        patterns = [r"\d{4}-\d{4}-\d{4}-\d{4}", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"]
        for p in patterns:
            data = re.sub(p, "***", data)
        return data


def get_data_masking():
    return DataMasking()