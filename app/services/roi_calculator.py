"""
Módulos IA P6-55: ROI de Tiempo de Visualización
Calcula el valor obtenido vs tiempo invertido en ver videos.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ROIMetric:
    """Métrica de ROI para un video."""
    video_id: str
    title: str
    duration_minutes: float
    value_score: float
    time_investment_hours: float
    roi_score: float
    recommendation: str


class ROICalculator:
    """Calculador de ROI de tiempo de visualización."""

    VALUE_WEIGHTS = {
        'relevance': 0.35,
        'practicality': 0.30,
        'depth': 0.20,
        'completeness': 0.15
    }

    def __init__(self):
        self._calculation_count = 0

    def calculate_roi(
        self,
        video: Dict,
        user_level: str = "intermediate"
    ) -> ROIMetric:
        """
        P6-55: Calcula el ROI de tiempo para un video.
        Args:
            video: Datos del video
            user_level: Nivel del usuario
        Returns:
            ROIMetric con análisis
        """
        self._calculation_count += 1

        title = video.get('title', '')
        duration = video.get('duration_seconds', 600)
        duration_minutes = duration / 60
        time_investment_hours = duration_minutes / 60

        relevance = video.get('relevance_score', video.get('kdp_relevance_score', 50)) / 100
        practicality = self._estimate_practicality(video)
        depth = self._estimate_depth(video, user_level)
        completeness = self._estimate_completeness(video)

        value_score = (
            relevance * self.VALUE_WEIGHTS['relevance'] +
            practicality * self.VALUE_WEIGHTS['practicality'] +
            depth * self.VALUE_WEIGHTS['depth'] +
            completeness * self.VALUE_WEIGHTS['completeness']
        )

        if time_investment_hours > 0:
            roi_score = value_score / time_investment_hours
        else:
            roi_score = 0

        roi_score = min(roi_score, 10.0)

        if roi_score > 2.0:
            recommendation = "Excelente inversión de tiempo"
        elif roi_score > 1.0:
            recommendation = "Buena inversión de tiempo"
        elif roi_score > 0.5:
            recommendation = "Inversión moderada de tiempo"
        else:
            recommendation = "Bajo ROI - considerar skipping"

        return ROIMetric(
            video_id=video.get('id', ''),
            title=title[:50],
            duration_minutes=round(duration_minutes, 1),
            value_score=round(value_score, 2),
            time_investment_hours=round(time_investment_hours, 2),
            roi_score=round(roi_score, 2),
            recommendation=recommendation
        )

    def calculate_batch_roi(
        self,
        videos: List[Dict],
        user_level: str = "intermediate"
    ) -> Dict:
        """Calcula ROI para una lista de videos."""
        roi_metrics = [self.calculate_roi(v, user_level) for v in videos]

        total_time = sum(m.time_investment_hours for m in roi_metrics)
        avg_value = sum(m.value_score for m in roi_metrics) / len(roi_metrics) if videos else 0

        total_roi = total_time > 0 and avg_value / total_time or 0

        sorted_by_roi = sorted(roi_metrics, key=lambda x: x.roi_score, reverse=True)

        return {
            "total_videos": len(videos),
            "total_time_hours": round(total_time, 2),
            "average_value_score": round(avg_value, 2),
            "average_roi": round(total_roi, 2),
            "best_roi": sorted_by_roi[0].__dict__ if sorted_by_roi else None,
            "worst_roi": sorted_by_roi[-1].__dict__ if sorted_by_roi else None,
            "recommendations": [m.recommendation for m in sorted_by_roi[:3]]
        }

    def _estimate_practicality(self, video: Dict) -> float:
        """Estima qué tan práctico es el contenido."""
        description = video.get('description', '').lower()
        title = video.get('title', '').lower()

        practical_keywords = [
            'ejemplo', 'ejemplos', 'práctica', 'practicar',
            'example', 'practice', 'how to', 'step by step',
            'tutorial', 'demo', 'caso de estudio', 'case study'
        ]

        score = 0.5
        for kw in practical_keywords:
            if kw in description or kw in title:
                score += 0.1

        return min(score, 1.0)

    def _estimate_depth(self, video: Dict, user_level: str) -> float:
        """Estima la profundidad del contenido."""
        title = video.get('title', '').lower()
        duration = video.get('duration_seconds', 600)

        score = 0.5

        deep_keywords = ['completo', 'avanzado', 'masterclass', 'full', 'advanced', 'complete guide']
        basic_keywords = ['básico', 'intro', 'quick', 'brief', 'resumen']

        for kw in deep_keywords:
            if kw in title:
                score += 0.2

        for kw in basic_keywords:
            if kw in title:
                score -= 0.2

        if duration > 3600:
            score += 0.15

        return max(0.0, min(score, 1.0))

    def _estimate_completeness(self, video: Dict) -> float:
        """Estima qué tan completo es el contenido."""
        description = video.get('description', '')

        score = 0.5

        if description and len(description) > 200:
            score += 0.2
        if description and len(description) > 500:
            score += 0.1

        tags = video.get('tags', [])
        if tags and len(tags) > 3:
            score += 0.1

        return min(score, 1.0)

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del calculador."""
        return {
            "total_calculated": self._calculation_count,
            "model": "ROICalculator v1.0"
        }


def create_roi_calculator() -> ROICalculator:
    """Crea una instancia del calculador de ROI."""
    return ROICalculator()


_global_calculator: Optional[ROICalculator] = None


def get_roi_calculator() -> ROICalculator:
    """Obtiene la instancia global del calculador de ROI."""
    global _global_calculator
    if _global_calculator is None:
        _global_calculator = create_roi_calculator()
    return _global_calculator