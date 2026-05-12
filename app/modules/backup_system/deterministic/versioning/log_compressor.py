"""
Log Compressor
==============
Compresor de logs históricos de más de 7 días.
"""

import os
import gzip
import logging
from datetime import datetime, timedelta
from typing import List


class LogCompressor:
    """Compresor de logs."""

    def __init__(self, days_threshold: int = 7):
        self.days_threshold = days_threshold

    def compress_old_logs(self, log_dir: str) -> List[str]:
        compressed = []

        if not os.path.exists(log_dir):
            return compressed

        cutoff = datetime.now() - timedelta(days=self.days_threshold)

        for f in os.listdir(log_dir):
            if not f.endswith((".log", ".txt")):
                continue

            path = os.path.join(log_dir, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))

            if mtime < cutoff and not f.endswith(".gz"):
                try:
                    with open(path, 'rb') as fin:
                        with gzip.open(path + ".gz", 'wb') as fout:
                            fout.write(fin.read())
                    os.remove(path)
                    compressed.append(f)
                except Exception as e:
                    logging.error(f"Error compressing {f}: {e}")

        return compressed


def compress_logs(log_dir: str) -> List[str]:
    compressor = LogCompressor()
    return compressor.compress_old_logs(log_dir)