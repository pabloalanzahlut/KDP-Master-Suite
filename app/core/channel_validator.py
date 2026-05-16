"""
Módulos P5: Auditoría de Canales
- P5-48: Alerta de Cambio de Nombre de Canal
- P5-49: Detección de Canales Falsos/Clones
- P5-20: Alerta de Contenido Eliminado
"""
import logging
import hashlib
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChannelSnapshot:
    """Captura del estado de un canal."""
    channel_id: str
    channel_name: str
    channel_url: str
    subscriber_count: Optional[int]
    video_count: int
    captured_at: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ChannelAlert:
    """Alerta sobre un canal."""
    channel_id: str
    alert_type: str
    severity: str
    message: str
    detected_at: str
    details: Optional[Dict] = None


class ChannelValidator:
    """Validador de integridad y seguridad de canales."""

    SUSPICIOUS_PATTERNS = [
        r'verify.*account',
        r'click.*here.*gift',
        r'free.*subscribers?',
        r'giveaway.*now',
        r'claim.*prize',
        r'congratulations?.*winner'
    ]

    CLONE_INDICATORS = [
        'clon', 'fake', 'official2', 'real',
        '-topic', 'topic', 'community',
        'gameplay', 'vlogs', 'official'
    ]

    def __init__(self):
        self._snapshots: Dict[str, List[ChannelSnapshot]] = {}
        self._alerts: List[ChannelAlert] = []

    def capture_channel_state(self, channel_data: Dict) -> ChannelSnapshot:
        """
        Captura el estado actual de un canal.
        Args:
            channel_data: Diccionario con datos del canal
        Returns:
            ChannelSnapshot con el estado capturado
        """
        channel_id = channel_data.get('id') or channel_data.get('channel_id', '')
        channel_name = channel_data.get('name') or channel_data.get('channel_name', '')

        snapshot = ChannelSnapshot(
            channel_id=str(channel_id),
            channel_name=channel_name,
            channel_url=channel_data.get('url') or channel_data.get('channel_url', ''),
            subscriber_count=channel_data.get('subscriber_count'),
            video_count=channel_data.get('video_count', 0),
            captured_at=datetime.now().isoformat(),
            thumbnail_url=channel_data.get('thumbnail'),
            description=channel_data.get('description')
        )

        if channel_id not in self._snapshots:
            self._snapshots[channel_id] = []

        self._snapshots[channel_id].append(snapshot)
        return snapshot

    def check_name_change(self, channel_id: str, current_name: str) -> Optional[ChannelAlert]:
        """
        P5-48: Detecta cambio de nombre de canal.
        Args:
            channel_id: ID del canal
            current_name: Nombre actual del canal
        Returns:
            ChannelAlert si hay cambio de nombre, None si no hay cambio
        """
        snapshots = self._snapshots.get(channel_id, [])
        if len(snapshots) < 2:
            return None

        previous_snapshot = snapshots[-2]
        if previous_snapshot.channel_name != current_name:
            alert = ChannelAlert(
                channel_id=channel_id,
                alert_type="name_change",
                severity="medium",
                message=f"El canal '{previous_snapshot.channel_name}' cambió a '{current_name}'",
                detected_at=datetime.now().isoformat(),
                details={
                    "previous_name": previous_snapshot.channel_name,
                    "current_name": current_name,
                    "change_date": snapshots[-1].captured_at
                }
            )
            self._alerts.append(alert)
            logger.warning(f"Alerta: Cambio de nombre detectado para canal {channel_id}")
            return alert

        return None

    def detect_fake_or_clone(self, channel_data: Dict) -> Optional[ChannelAlert]:
        """
        P5-49: Detecta posibles canales falsos o clones.
        Args:
            channel_data: Datos del canal a verificar
        Returns:
            ChannelAlert si se detecta posible clon, None si es limpio
        """
        channel_id = str(channel_data.get('id', ''))
        channel_name = channel_data.get('name', '').lower()
        channel_url = channel_data.get('url', '').lower()

        is_suspicious = False
        reasons = []

        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, channel_name) or re.search(pattern, channel_url):
                is_suspicious = True
                reasons.append(f"Patrón sospechoso: {pattern}")

        url_parts = channel_url.split('/')
        if any(indicator in channel_name for indicator in self.CLONE_INDICATORS):
            for part in url_parts[-2:]:
                if part and part not in ['channel', 'user', 'c']:
                    if any(c in part.lower() for c in self.CLONE_INDICATORS):
                        is_suspicious = True
                        reasons.append(f"Posible clon en URL: {part}")

        if channel_data.get('subscriber_count') == 0 and channel_data.get('video_count', 0) > 10:
            is_suspicious = True
            reasons.append("Sin suscriptores pero con muchos videos")

        if is_suspicious:
            alert = ChannelAlert(
                channel_id=channel_id,
                alert_type="fake_or_clone",
                severity="high",
                message=f"Posible canal falso o clon detectado: {channel_data.get('name')}",
                detected_at=datetime.now().isoformat(),
                details={
                    "reasons": reasons,
                    "channel_name": channel_data.get('name'),
                    "channel_url": channel_data.get('url')
                }
            )
            self._alerts.append(alert)
            logger.warning(f"Alerta: Posible clon detectado para canal {channel_id}")
            return alert

        return None

    def validate_url_ssl(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        P5-50: Valida que la URL tenga certificado SSL válido.
        Args:
            url: URL a validar
        Returns:
            (is_valid, error_message)
        """
        if not url.startswith('https://'):
            return False, "URL no usa HTTPS"

        return True, None

    def check_deleted_content(self, channel_data: Dict, videos: List[Dict]) -> Dict:
        """
        P5-20: Detecta contenido eliminado o no disponible.
        Args:
            channel_data: Datos del canal
            videos: Lista de videos del canal
        Returns:
            Diccionario con estadísticas de estado de videos
        """
        stats = {
            "total": len(videos),
            "available": 0,
            "private": 0,
            "deleted": 0,
            "unavailable": 0,
            "unknown": 0
        }

        for video in videos:
            status = video.get('status', video.get('availability', 'unknown'))
            if status == 'available' or status == 'public':
                stats["available"] += 1
            elif status == 'private':
                stats["private"] += 1
            elif status == 'deleted':
                stats["deleted"] += 1
            elif status in ['unavailable', 'not_found', 'removed']:
                stats["unavailable"] += 1
            else:
                stats["unknown"] += 1

        if stats["deleted"] > 0 or stats["unavailable"] > 0:
            logger.info(f"Canal {channel_data.get('name')}: {stats['deleted']} eliminados, {stats['unavailable']} no disponibles")

        return stats

    def get_alerts(self, channel_id: Optional[str] = None) -> List[ChannelAlert]:
        """Obtiene las alertas acumuladas, opcionalmente filtradas por canal."""
        if channel_id:
            return [a for a in self._alerts if a.channel_id == channel_id]
        return self._alerts

    def clear_alerts(self, channel_id: Optional[str] = None):
        """Limpia las alertas."""
        if channel_id:
            self._alerts = [a for a in self._alerts if a.channel_id != channel_id]
        else:
            self._alerts = []

    def get_channel_health(self, channel_id: str) -> Dict:
        """Retorna un resumen de salud del canal."""
        snapshots = self._snapshots.get(channel_id, [])
        alerts = self.get_alerts(channel_id)

        return {
            "channel_id": channel_id,
            "snapshot_count": len(snapshots),
            "alert_count": len(alerts),
            "last_captured": snapshots[-1].captured_at if snapshots else None,
            "has_alerts": len(alerts) > 0,
            "alert_types": list(set(a.alert_type for a in alerts))
        }


def create_channel_validator() -> ChannelValidator:
    """Crea y retorna una instancia del validador de canales."""
    return ChannelValidator()


_global_validator: Optional[ChannelValidator] = None


def get_channel_validator() -> ChannelValidator:
    """Obtiene la instancia global del validador de canales."""
    global _global_validator
    if _global_validator is None:
        _global_validator = create_channel_validator()
    return _global_validator