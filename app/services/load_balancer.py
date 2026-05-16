"""
Módulos P4-38: Balanceo de Carga por Canal
Distribuye descargas equitativamente entre canales.
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ChannelLoad:
    """Carga de un canal."""
    channel_id: str
    active_downloads: int
    last_download: Optional[datetime]
    priority: int


class LoadBalancer:
    """Balanceador de carga entre canales."""

    MAX_DOWNLOADS_PER_CHANNEL = 3
    COOLDOWN_SECONDS = 60

    def __init__(self):
        self._channel_loads: Dict[str, ChannelLoad] = {}
        self._balance_count = 0

    def register_download_start(self, channel_id: str):
        """Registra inicio de descarga."""
        now = datetime.now()
        if channel_id not in self._channel_loads:
            self._channel_loads[channel_id] = ChannelLoad(
                channel_id=channel_id,
                active_downloads=0,
                last_download=None,
                priority=3
            )
        self._channel_loads[channel_id].active_downloads += 1
        self._channel_loads[channel_id].last_download = now

    def register_download_end(self, channel_id: str):
        """Registra fin de descarga."""
        if channel_id in self._channel_loads:
            self._channel_loads[channel_id].active_downloads = max(
                0,
                self._channel_loads[channel_id].active_downloads - 1
            )

    def can_download_from(
        self,
        channel_id: str,
        max_per_channel: int = MAX_DOWNLOADS_PER_CHANNEL
    ) -> bool:
        """
        P4-38: Determina si se puede iniciar descarga desde un canal.
        Args:
            channel_id: ID del canal
            max_per_channel: Máximo de descargas simultáneas por canal
        Returns:
            True si el canal puede aceptar más descargas
        """
        if channel_id not in self._channel_loads:
            return True

        load = self._channel_loads[channel_id]

        if load.active_downloads >= max_per_channel:
            return False

        if load.last_download:
            time_since_last = (datetime.now() - load.last_download).total_seconds()
            if time_since_last < self.COOLDOWN_SECONDS:
                return False

        return True

    def get_least_loaded_channel(
        self,
        channels: List[str],
        max_per_channel: int = MAX_DOWNLOADS_PER_CHANNEL
    ) -> Optional[str]:
        """Obtiene el canal con menor carga."""
        candidates = [c for c in channels if self.can_download_from(c, max_per_channel)]

        if not candidates:
            return None

        candidates.sort(
            key=lambda c: (
                self._channel_loads.get(c, ChannelLoad(c, 0, None, 3)).active_downloads,
                -self._channel_loads.get(c, ChannelLoad(c, 0, None, 3)).priority
            )
        )

        return candidates[0]

    def set_channel_priority(self, channel_id: str, priority: int):
        """Establece prioridad de un canal (1-5)."""
        if channel_id not in self._channel_loads:
            self._channel_loads[channel_id] = ChannelLoad(
                channel_id=channel_id,
                active_downloads=0,
                last_download=None,
                priority=priority
            )
        else:
            self._channel_loads[channel_id].priority = priority

    def get_channel_status(self, channel_id: str) -> Dict:
        """Obtiene estado de carga de un canal."""
        load = self._channel_loads.get(channel_id)
        if not load:
            return {
                "channel_id": channel_id,
                "active_downloads": 0,
                "can_download": True,
                "priority": 3
            }

        return {
            "channel_id": channel_id,
            "active_downloads": load.active_downloads,
            "can_download": self.can_download_from(channel_id),
            "priority": load.priority,
            "last_download": load.last_download.isoformat() if load.last_download else None
        }

    def get_all_status(self) -> Dict[str, Dict]:
        """Obtiene estado de todos los canales."""
        return {cid: self.get_channel_status(cid) for cid in self._channel_loads.keys()}

    def reset(self):
        """Reinicia el balanceador."""
        self._channel_loads.clear()

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del balanceador."""
        return {
            "tracked_channels": len(self._channel_loads),
            "model": "LoadBalancer v1.0"
        }


def create_load_balancer() -> LoadBalancer:
    """Crea una instancia del balanceador de carga."""
    return LoadBalancer()


_global_balancer: Optional[LoadBalancer] = None


def get_load_balancer() -> LoadBalancer:
    """Obtiene la instancia global del balanceador."""
    global _global_balancer
    if _global_balancer is None:
        _global_balancer = create_load_balancer()
    return _global_balancer