"""
Queue Snapshot Manager
=====================
Sincronizador de estado de colas (Queue Snapshot).
Guarda imagen JSON exacta del estado de la cola en el momento del backup.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple

logger = logging.getLogger(__name__)


class QueueSnapshotManager:
    """Gestor de instantáneas del estado de colas."""

    def __init__(self, state_dir: str = None):
        self.state_dir = state_dir or os.path.join(os.getcwd(), "data")
        self.snapshot_file = os.path.join(self.state_dir, "queue_snapshot.json")

    def capture_queue_state(self, queue_data: Dict = None) -> Tuple[bool, str]:
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "queue_state": queue_data or self._get_default_state()
            }

            temp_file = self.snapshot_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)

            os.replace(temp_file, self.snapshot_file)
            logger.info(f"Queue snapshot captured: {self.snapshot_file}")
            return True, f"Snapshot: {snapshot['timestamp']}"

        except Exception as e:
            logger.error(f"Error capturing queue state: {e}")
            return False, str(e)

    def _get_default_state(self) -> Dict:
        return {
            "download_queue": [],
            "processing_queue": [],
            "completed": [],
            "failed": [],
            "total_items": 0
        }

    def load_queue_snapshot(self) -> Optional[Dict]:
        if not os.path.exists(self.snapshot_file):
            return None

        try:
            with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading snapshot: {e}")
            return None

    def get_snapshot_info(self) -> Optional[Dict]:
        snapshot = self.load_queue_snapshot()
        if snapshot:
            return {
                "timestamp": snapshot.get("timestamp"),
                "version": snapshot.get("version"),
                "items": snapshot.get("queue_state", {}).get("total_items", 0)
            }
        return None


def capture_queue_snapshot(queue_data: Dict = None) -> Tuple[bool, str]:
    manager = QueueSnapshotManager()
    return manager.capture_queue_state(queue_data)


def load_snapshot() -> Optional[Dict]:
    manager = QueueSnapshotManager()
    return manager.load_queue_snapshot()