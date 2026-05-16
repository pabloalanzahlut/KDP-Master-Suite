"""
Módulos IA P6-58: Alerta de Declive de Calidad
Detecta cuando los últimos videos de un canal son de menor calidad.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class QualityDeclineAnalysis:
    """Resultado del análisis de declive de calidad."""
    has_decline: bool
    decline_percentage: float
    avg_previous_score: float
    avg_recent_score: float
    trend: str
    recommendation: str


class QualityDeclineDetector:
    """Detector de declive de calidad en canales."""

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._analysis_count = 0

    def analyze_quality_trend(
        self,
        videos: List[Dict],
        min_videos: int = 15
    ) -> QualityDeclineAnalysis:
        """
        P6-58: Analiza si hay declive de calidad en los últimos videos.
        Args:
            videos: Lista de videos del canal
            min_videos: Mínimo de videos para análisis válido
        Returns:
            QualityDeclineAnalysis con resultado
        """
        self._analysis_count += 1

        if len(videos) < min_videos:
            return QualityDeclineAnalysis(
                has_decline=False,
                decline_percentage=0.0,
                avg_previous_score=0.0,
                avg_recent_score=0.0,
                trend="insuficiente_datos",
                recommendation="Se necesitan más videos para análisis de tendencia"
            )

        sorted_videos = sorted(
            videos,
            key=lambda v: v.get('published_at', v.get('discovered_at', ''))
        )

        window = min(self.window_size, len(sorted_videos) // 3)
        if window < 3:
            window = 3

        previous_videos = sorted_videos[:-window]
        recent_videos = sorted_videos[-window:]

        previous_score = self._calculate_avg_quality(previous_videos)
        recent_score = self._calculate_avg_quality(recent_videos)

        if previous_score > 0:
            decline_percentage = ((previous_score - recent_score) / previous_score) * 100
        else:
            decline_percentage = 0

        has_decline = decline_percentage > 15 and recent_score < previous_score

        if decline_percentage > 25:
            trend = "declive_significativo"
            recommendation = "El canal muestra un declive significativo de calidad. Considera reducir seguimiento."
        elif decline_percentage > 15:
            trend = "declive_moderado"
            recommendation = "Ligero declive de calidad. Monitorear más videos."
        elif decline_percentage > 0:
            trend = "estable"
            recommendation = "Calidad estable con variaciones normales."
        else:
            trend = "mejorando"
            recommendation = "El canal está mejorando su calidad."

        return QualityDeclineAnalysis(
            has_decline=has_decline,
            decline_percentage=round(decline_percentage, 1),
            avg_previous_score=round(previous_score, 2),
            avg_recent_score=round(recent_score, 2),
            trend=trend,
            recommendation=recommendation
        )

    def _calculate_avg_quality(self, videos: List[Dict]) -> float:
        """Calcula el promedio de calidad de una lista de videos."""
        if not videos:
            return 0.0

        total = 0
        count = 0

        for video in videos:
            score = (
                video.get('relevance_score', 50) or
                video.get('kdp_relevance_score', 50) or
                video.get('quality_score', 50) or
                50
            )
            total += score
            count += 1

        return (total / count) if count > 0 else 50.0

    def get_quality_scores_timeline(self, videos: List[Dict]) -> List[Dict]:
        """Retorna línea de tiempo de scores de calidad."""
        sorted_videos = sorted(
            videos,
            key=lambda v: v.get('published_at', v.get('discovered_at', ''))
        )

        timeline = []

        for video in sorted_videos:
            date = video.get('published_at', video.get('discovered_at', 'Unknown'))
            score = (
                video.get('relevance_score', 50) or
                video.get('kdp_relevance_score', 50) or
                video.get('quality_score', 50) or
                50
            )
            timeline.append({
                'video_id': video.get('id', ''),
                'title': video.get('title', '')[:30],
                'date': date,
                'quality_score': score
            })

        return timeline

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del detector."""
        return {
            "total_analyzed": self._analysis_count,
            "window_size": self.window_size,
            "model": "QualityDeclineDetector v1.0"
        }


def create_quality_decline_detector(window_size: int = 10) -> QualityDeclineDetector:
    """Crea una instancia del detector de declive de calidad."""
    return QualityDeclineDetector(window_size)


_global_detector: Optional[QualityDeclineDetector] = None


def get_quality_decline_detector() -> QualityDeclineDetector:
    """Obtiene la instancia global del detector de declive."""
    global _global_detector
    if _global_detector is None:
        _global_detector = create_quality_decline_detector()
    return _global_detector