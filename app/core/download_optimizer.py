"""
Módulos P4: Optimización de Descarga y Priorización
- P4-34: Optimización de Orden de Cola
- P4-35: Detección de Videos "Pesados"
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class VideoPriority:
    """Prioridad calculada para un video."""
    video_id: str
    priority_score: float
    estimated_time_minutes: int
    recommended_position: int
    reason: str


class DownloadOptimizer:
    """Optimizador de orden de descarga."""

    HEAVY_VIDEO_THRESHOLD_MINUTES = 60
    PRIORITY_WEIGHTS = {
        'relevance': 0.35,
        'recency': 0.25,
        'duration': 0.20,
        'completeness': 0.20
    }

    def __init__(self):
        self._optimization_count = 0

    def calculate_priority(
        self,
        video: Dict,
        user_preferences: Optional[Dict] = None
    ) -> VideoPriority:
        """
        P4-34: Calcula prioridad de un video para procesamiento.
        Args:
            video: Datos del video
            user_preferences: Preferencias del usuario
        Returns:
            VideoPriority con score y posición recomendada
        """
        self._optimization_count += 1

        video_id = video.get('id', '')
        duration = video.get('duration_seconds', 600)
        duration_minutes = duration / 60

        relevance = (video.get('relevance_score', 50) or video.get('kdp_relevance_score', 50)) / 100

        published = video.get('published_at') or video.get('discovered_at')
        recency = 0.5
        if published:
            try:
                if isinstance(published, str):
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                else:
                    dt = published
                days_old = (datetime.now() - dt).days
                recency = max(0, 1 - (days_old / 365))
            except:
                pass

        if duration_minutes <= 10:
            duration_score = 1.0
        elif duration_minutes <= 30:
            duration_score = 0.7
        else:
            duration_score = 0.4

        completeness = 0.8
        if video.get('description') and len(video.get('description', '')) > 100:
            completeness = 1.0

        priority_score = (
            relevance * self.PRIORITY_WEIGHTS['relevance'] +
            recency * self.PRIORITY_WEIGHTS['recency'] +
            duration_score * self.PRIORITY_WEIGHTS['duration'] +
            completeness * self.PRIORITY_WEIGHTS['completeness']
        )

        reason = f"Relevancia: {relevance:.2f}, Reciente: {recency:.2f}, Duración: {duration_minutes:.0f}min"

        return VideoPriority(
            video_id=video_id,
            priority_score=round(priority_score, 3),
            estimated_time_minutes=int(duration_minutes),
            recommended_position=0,
            reason=reason
        )

    def optimize_queue_order(
        self,
        videos: List[Dict],
        user_preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Optimiza el orden de la cola de descargas.
        Args:
            videos: Lista de videos a ordenar
            user_preferences: Preferencias del usuario
        Returns:
            Lista de videos ordenada por prioridad
        """
        prioritized = []

        for video in videos:
            priority = self.calculate_priority(video, user_preferences)
            video_with_priority = video.copy()
            video_with_priority['_priority_score'] = priority.priority_score
            video_with_priority['_priority_reason'] = priority.reason
            prioritized.append(video_with_priority)

        prioritized.sort(key=lambda v: v['_priority_score'], reverse=True)

        for i, v in enumerate(prioritized):
            v['_recommended_position'] = i + 1

        return prioritized

    def is_heavy_video(self, video: Dict) -> bool:
        """
        P4-35: Detecta si un video es "pesado" (>1 hora).
        Args:
            video: Datos del video
        Returns:
            True si el video es considerado pesado
        """
        duration = video.get('duration_seconds', 0)
        duration_minutes = duration / 60
        return duration_minutes > self.HEAVY_VIDEO_THRESHOLD_MINUTES

    def suggest_alternatives(
        self,
        video: Dict,
        available_videos: List[Dict]
    ) -> List[Dict]:
        """Sugiere videos alternativos más eficientes."""
        alternatives = []

        for v in available_videos:
            if v.get('id') == video.get('id'):
                continue

            v_duration = v.get('duration_seconds', 600) / 60
            if v_duration <= 30:
                v_priority = self.calculate_priority(v)
                alternatives.append({
                    'video': v,
                    'priority': v_priority.priority_score,
                    'duration': v_duration
                })

        alternatives.sort(key=lambda x: x['priority'], reverse=True)
        return alternatives[:5]

    def estimate_total_time(self, videos: List[Dict]) -> Dict:
        """Estima tiempo total de procesamiento."""
        total_seconds = sum(v.get('duration_seconds', 600) for v in videos)
        heavy_count = sum(1 for v in videos if self.is_heavy_video(v))

        return {
            'total_videos': len(videos),
            'total_minutes': int(total_seconds / 60),
            'total_hours': round(total_seconds / 3600, 1),
            'heavy_videos': heavy_count,
            'light_videos': len(videos) - heavy_count,
            'estimated_processing_minutes': int(total_seconds / 60 * 0.5)
        }

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del optimizador."""
        return {
            "total_optimized": self._optimization_count,
            "model": "DownloadOptimizer v1.0"
        }


def create_download_optimizer() -> DownloadOptimizer:
    """Crea una instancia del optimizador de descargas."""
    return DownloadOptimizer()


_global_optimizer: Optional[DownloadOptimizer] = None


def get_download_optimizer() -> DownloadOptimizer:
    """Obtiene la instancia global del optimizador."""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = create_download_optimizer()
    return _global_optimizer