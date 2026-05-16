"""
Módulos P2: Gestión de Estado de Videos
- P2-13: Marcador de "Ya en Cola"
- P2-14: Filtro de "Vistos/Leídos"
- P2-15: Comparador de Timestamps
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class VideoState:
    """Estado de un video en el sistema."""
    video_id: str
    status: str
    added_to_queue_at: Optional[str]
    processed_at: Optional[str]
    viewed: bool
    viewed_at: Optional[str]
    read: bool
    read_at: Optional[str]
    metadata: Dict


class VideoStateManager:
    """Gestor de estado de videos para tracking de cola y visto/leído."""

    DEFAULT_STORAGE_FILE = "data/video_states.json"

    def __init__(self, storage_file: Optional[str] = None):
        self.storage_file = Path(storage_file) if storage_file else Path(self.DEFAULT_STORAGE_FILE)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._states: Dict[str, VideoState] = {}
        self._load_states()

    def _load_states(self):
        """Carga estados desde archivo."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for vid, state in data.items():
                        self._states[vid] = VideoState(**state)
                logger.info(f"Cargados {len(self._states)} estados de video")
            except Exception as e:
                logger.error(f"Error cargando estados: {e}")

    def _save_states(self):
        """Guarda estados a archivo."""
        try:
            data = {vid: asdict(state) for vid, state in self._states.items()}
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando estados: {e}")

    def mark_in_queue(self, video_id: str, metadata: Optional[Dict] = None):
        """P2-13: Marca un video como añadido a la cola."""
        now = datetime.now().isoformat()
        self._states[video_id] = VideoState(
            video_id=video_id,
            status="queued",
            added_to_queue_at=now,
            processed_at=None,
            viewed=False,
            viewed_at=None,
            read=False,
            read_at=None,
            metadata=metadata or {}
        )
        self._save_states()
        logger.debug(f"Video {video_id} marcado en cola")

    def mark_processed(self, video_id: str):
        """Marca un video como procesado."""
        now = datetime.now().isoformat()
        if video_id in self._states:
            self._states[video_id].status = "processed"
            self._states[video_id].processed_at = now
        else:
            self._states[video_id] = VideoState(
                video_id=video_id,
                status="processed",
                added_to_queue_at=now,
                processed_at=now,
                viewed=False,
                viewed_at=None,
                read=False,
                read_at=None,
                metadata={}
            )
        self._save_states()

    def mark_viewed(self, video_id: str):
        """P2-14: Marca un video como visto."""
        now = datetime.now().isoformat()
        if video_id not in self._states:
            self._states[video_id] = VideoState(
                video_id=video_id,
                status="unknown",
                added_to_queue_at=None,
                processed_at=None,
                viewed=True,
                viewed_at=now,
                read=False,
                read_at=None,
                metadata={}
            )
        else:
            self._states[video_id].viewed = True
            self._states[video_id].viewed_at = now
        self._save_states()

    def mark_read(self, video_id: str):
        """Marca la transcripción del video como leída."""
        now = datetime.now().isoformat()
        if video_id not in self._states:
            self._states[video_id] = VideoState(
                video_id=video_id,
                status="unknown",
                added_to_queue_at=None,
                processed_at=None,
                viewed=False,
                viewed_at=None,
                read=True,
                read_at=now,
                metadata={}
            )
        else:
            self._states[video_id].read = True
            self._states[video_id].read_at = now
        self._save_states()

    def is_in_queue(self, video_id: str) -> bool:
        """P2-13: Verifica si el video está en la cola."""
        state = self._states.get(video_id)
        return state is not None and state.status == "queued"

    def is_viewed(self, video_id: str) -> bool:
        """P2-14: Verifica si el video ha sido visto."""
        state = self._states.get(video_id)
        return state is not None and state.viewed

    def is_read(self, video_id: str) -> bool:
        """Verifica si la transcripción ha sido leída."""
        state = self._states.get(video_id)
        return state is not None and state.read

    def get_unviewed_count(self) -> int:
        """Retorna cantidad de videos no vistos."""
        return sum(1 for s in self._states.values() if not s.viewed)

    def get_unread_count(self) -> int:
        """Retorna cantidad de transcripciones no leídas."""
        return sum(1 for s in self._states.values() if not s.read)

    def get_queue_count(self) -> int:
        """Retorna cantidad de videos en cola."""
        return sum(1 for s in self._states.values() if s.status == "queued")

    def get_all_videos_in_queue(self) -> List[str]:
        """Retorna lista de IDs de videos en cola."""
        return [vid for vid, s in self._states.items() if s.status == "queued"]

    def get_all_viewed(self) -> List[str]:
        """Retorna lista de IDs de videos vistos."""
        return [vid for vid, s in self._states.items() if s.viewed]

    def get_all_read(self) -> List[str]:
        """Retorna lista de IDs de videos leídos."""
        return [vid for vid, s in self._states.items() if s.read]

    def clear_old_states(self, days: int = 30):
        """Limpia estados anteriores a N días."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        removed = 0

        for vid, state in list(self._states.items()):
            last_activity = state.viewed_at or state.read_at or state.processed_at or state.added_to_queue_at
            if last_activity:
                try:
                    dt = datetime.fromisoformat(last_activity)
                    if dt.timestamp() < cutoff:
                        del self._states[vid]
                        removed += 1
                except:
                    pass

        if removed > 0:
            self._save_states()
            logger.info(f"Limpiados {removed} estados antiguos")


_global_manager: Optional[VideoStateManager] = None


def get_video_state_manager() -> VideoStateManager:
    """Obtiene la instancia global del gestor de estados."""
    global _global_manager
    if _global_manager is None:
        _global_manager = VideoStateManager()
    return _global_manager