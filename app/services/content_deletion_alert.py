"""
P5-20: Alerta de Contenido Eliminado
Notifica cuando videos de la lista fueron eliminados de YouTube.
"""
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DeletionAlert:
    """Alerta de video eliminado."""
    video_id: str
    video_title: str
    detected_at: str
    previous_status: str


class ContentDeletionAlert:
    """Monitor de contenido eliminado."""

    def __init__(self):
        self._known_video_ids: Set[str] = set()
        self._alerts: List[DeletionAlert] = []
        self._last_check: Optional[str] = None

    def register_videos(self, video_ids: List[str]):
        """Registra videos para monitorear."""
        self._known_video_ids.update(video_ids)
        logger.info(f"Monitoreando {len(self._known_video_ids)} videos")

    def check_deletions(
        self,
        current_videos: List[Dict],
        missing_check: bool = True
    ) -> List[DeletionAlert]:
        """
        Detecta videos eliminados.
        Args:
            current_videos: Videos que aún existen
            missing_check: Si True, verifica IDs faltantes
        Returns:
            Lista de DeletionAlert
        """
        self._last_check = datetime.now().isoformat()

        current_ids = {v.get('id') for v in current_videos if v.get('id')}

        if not missing_check:
            return []

        deleted_ids = self._known_video_ids - current_ids

        new_alerts = []
        for vid in deleted_ids:
            alert = DeletionAlert(
                video_id=vid,
                video_title="Desconocido",
                detected_at=self._last_check,
                previous_status="unknown"
            )
            new_alerts.append(alert)
            self._alerts.append(alert)

        if new_alerts:
            logger.warning(f"Detectados {len(new_alerts)} videos eliminados")

        return new_alerts

    def add_video(self, video_id: str):
        """Agrega un video al monitoreo."""
        self._known_video_ids.add(video_id)

    def remove_video(self, video_id: str):
        """Remueve un video del monitoreo."""
        self._known_video_ids.discard(video_id)

    def get_alerts(self, since: Optional[str] = None) -> List[DeletionAlert]:
        """Obtiene alertas, opcionalmente filtradas por fecha."""
        if since:
            return [a for a in self._alerts if a.detected_at >= since]
        return self._alerts

    def get_alert_count(self) -> int:
        """Retorna cantidad de alertas."""
        return len(self._alerts)

    def clear_alerts(self):
        """Limpia todas las alertas."""
        self._alerts.clear()

    def export_alerts(self, format: str = 'text') -> str:
        """Exporta alertas en formato specified."""
        if format == 'text':
            lines = [f"- {a.video_id} ({a.detected_at})" for a in self._alerts]
            return "\n".join(lines) if lines else "Sin alertas"
        elif format == 'json':
            import json
            return json.dumps([a.__dict__ for a in self._alerts], indent=2)
        return str(self._alerts)


def create_deletion_alert() -> ContentDeletionAlert:
    return ContentDeletionAlert()


_global_alert: Optional[ContentDeletionAlert] = None


def get_deletion_alert() -> ContentDeletionAlert:
    global _global_alert
    if _global_alert is None:
        _global_alert = create_deletion_alert()
    return _global_alert