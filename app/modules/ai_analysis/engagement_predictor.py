"""
Módulos IA P2-17: Predictor de Engagement Real
Analiza ratio views/likes/comentarios para identificar contenido valorado.
"""
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EngagementAnalysis:
    """Análisis de engagement de un video."""
    view_count: int
    like_count: int
    comment_count: int
    engagement_ratio: float
    quality_score: float
    is_valued_content: bool
    recommendation: str


class EngagementPredictor:
    """Predictor de engagement real."""

    HIGH_ENGAGEMENT_THRESHOLD = 0.05
    LOW_ENGAGEMENT_THRESHOLD = 0.01

    def __init__(self):
        self._analysis_count = 0

    def analyze_engagement(
        self,
        video: Dict
    ) -> EngagementAnalysis:
        """
        P2-17: Analiza el engagement real de un video.
        Args:
            video: Datos del video con view_count, like_count, comment_count
        Returns:
            EngagementAnalysis con resultado
        """
        self._analysis_count += 1

        view_count = video.get('view_count', 0) or 0
        like_count = video.get('like_count', 0) or 0
        comment_count = video.get('comment_count', 0) or 0

        if view_count == 0:
            return EngagementAnalysis(
                view_count=0,
                like_count=0,
                comment_count=0,
                engagement_ratio=0.0,
                quality_score=0.0,
                is_valued_content=False,
                recommendation="Sin datos de views - imposible evaluar"
            )

        base_engagement = (like_count + comment_count * 2) / view_count

        like_ratio = like_count / view_count if view_count > 0 else 0
        comment_ratio = comment_count / view_count if view_count > 0 else 0

        if like_ratio > 0.1:
            quality_score = 0.9
        elif like_ratio > 0.05:
            quality_score = 0.7
        else:
            quality_score = 0.5

        if comment_ratio > 0.01:
            quality_score += 0.1

        if view_count > 1000000:
            quality_score += 0.1
        elif view_count > 100000:
            quality_score += 0.05

        quality_score = min(quality_score, 1.0)

        is_valued = base_engagement >= self.HIGH_ENGAGEMENT_THRESHOLD

        if is_valued:
            recommendation = "Contenido de alta calidad - alto engagement"
        elif base_engagement >= self.LOW_ENGAGEMENT_THRESHOLD:
            recommendation = "Contenido promedio - engagement normal"
        else:
            recommendation = "Contenido de bajo engagement - puede ser irrelevante"

        return EngagementAnalysis(
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            engagement_ratio=round(base_engagement, 4),
            quality_score=round(quality_score, 2),
            is_valued_content=is_valued,
            recommendation=recommendation
        )

    def rank_by_engagement(
        self,
        videos: list
    ) -> list:
        """Ranking de videos por engagement."""
        analyzed = [(v, self.analyze_engagement(v)) for v in videos]
        return [v[0] for v in sorted(analyzed, key=lambda x: x[1].engagement_ratio, reverse=True)]

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del predictor."""
        return {
            "total_analyzed": self._analysis_count,
            "model": "EngagementPredictor v1.0"
        }


def create_engagement_predictor() -> EngagementPredictor:
    """Crea una instancia del predictor de engagement."""
    return EngagementPredictor()


_global_predictor: Optional[EngagementPredictor] = None


def get_engagement_predictor() -> EngagementPredictor:
    """Obtiene la instancia global del predictor."""
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = create_engagement_predictor()
    return _global_predictor