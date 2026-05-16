"""
Módulos IA P2-19: Análisis de Actualidad (Trending)
Determina si un tema es trending/pasajero o evergreen.
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysis:
    """Resultado del análisis de tendencia."""
    is_trending: bool
    trend_score: float
    is_evergreen: bool
    decay_rate: Optional[float]
    recommendation: str


class TrendAnalyzer:
    """Analizador de tendencias de temas."""

    TRENDING_KEYWORDS = [
        '2024', '2025', 'nuevo', 'nueva', 'latest', 'new',
        'actualizado', 'breaking', 'urgent', 'alerta',
        'viral', 'trending', 'populaire'
    ]

    EVERGREEN_KEYWORDS = [
        'básico', 'fundamentos', 'esencial', 'principiante',
        'tutorial completo', 'guía completa', 'masterclass',
        ' fundamentals', 'essential', 'complete guide',
        'introducción', 'introducción', ' basics'
    ]

    EXPIRY_DAYS = {
        'breaking': 7,
        'viral': 14,
        'actualizado': 30,
        '2024': 365,
        '2025': 365
    }

    def __init__(self):
        self._analysis_count = 0

    def analyze_trend(
        self,
        title: str,
        description: str = "",
        upload_date: Optional[str] = None,
        view_count: Optional[int] = None,
        like_count: Optional[int] = None
    ) -> TrendAnalysis:
        """
        P2-19: Analiza si un tema es trending o evergreen.
        Args:
            title: Título del video
            description: Descripción del video
            upload_date: Fecha de publicación (ISO format)
            view_count: Cantidad de vistas
            like_count: Cantidad de likes
        Returns:
            TrendAnalysis con resultado
        """
        self._analysis_count += 1

        content = f"{title.lower()} {description.lower()}"
        words = content.split()

        trend_score = 0.0
        trending_indicators = []
        evergreen_indicators = []

        for keyword in self.TRENDING_KEYWORDS:
            if keyword in content:
                trend_score += 0.2
                trending_indicators.append(keyword)

        for keyword in self.EVERGREEN_KEYWORDS:
            if keyword in content:
                trend_score -= 0.15
                evergreen_indicators.append(keyword)

        if view_count and like_count and view_count > 0:
            engagement = like_count / view_count
            if engagement > 0.1:
                trend_score += 0.1

        if upload_date:
            try:
                upload_dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                age_days = (datetime.now() - upload_dt).days

                for keyword, days in self.EXPIRY_DAYS.items():
                    if keyword in content:
                        if age_days > days:
                            trend_score += 0.3

                if age_days > 365 and trend_score > 0:
                    trend_score -= 0.2

            except Exception as e:
                logger.warning(f"Error parseando fecha: {e}")

        trend_score = max(-1.0, min(1.0, trend_score))

        is_trending = trend_score > 0.3
        is_evergreen = trend_score < 0.0 or len(evergreen_indicators) >= 2

        if is_trending:
            recommendation = "Tema trending - consumes pronto, puede quedar obsoleto"
        elif is_evergreen:
            recommendation = "Tema evergreen - mantiene valor a largo plazo"
        else:
            recommendation = "Tema neutral - valor estable"

        return TrendAnalysis(
            is_trending=is_trending,
            trend_score=round(trend_score, 2),
            is_evergreen=is_evergreen,
            decay_rate=None,
            recommendation=recommendation
        )

    def compare_topics(
        self,
        topics: List[Dict]
    ) -> List[Dict]:
        """Compara múltiples topics para determinar cuáles son trending."""
        results = []

        for topic in topics:
            analysis = self.analyze_trend(
                title=topic.get('title', ''),
                description=topic.get('description', ''),
                upload_date=topic.get('upload_date'),
                view_count=topic.get('view_count'),
                like_count=topic.get('like_count')
            )

            results.append({
                'topic': topic.get('title', '')[:50],
                'trend_score': analysis.trend_score,
                'is_trending': analysis.is_trending,
                'is_evergreen': analysis.is_evergreen,
                'recommendation': analysis.recommendation
            })

        results.sort(key=lambda x: x['trend_score'], reverse=True)
        return results

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del analizador."""
        return {
            "total_analyzed": self._analysis_count,
            "model": "TrendAnalyzer v1.0"
        }


def create_trend_analyzer() -> TrendAnalyzer:
    """Crea una instancia del analizador de tendencias."""
    return TrendAnalyzer()


_global_analyzer: Optional[TrendAnalyzer] = None


def get_trend_analyzer() -> TrendAnalyzer:
    """Obtiene la instancia global del analizador de tendencias."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = create_trend_analyzer()
    return _global_analyzer