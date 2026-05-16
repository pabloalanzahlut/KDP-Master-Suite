"""
Módulos IA P1-6: Análisis de Sentimiento del Título
Analiza el sentimiento del título (positivo, negativo, urgente).
"""
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SentimentAnalysis:
    """Resultado del análisis de sentimiento."""
    sentiment: str
    intensity: float
    urgency_level: str
    confidence: float
    indicators: list


class SentimentAnalyzer:
    """Analizador de sentimiento de títulos."""

    POSITIVE_WORDS = [
        'increíble', 'excelente', 'fantástico', 'maravilloso', 'genial', 'awesome',
        'amazing', 'great', 'best', 'perfect', 'love', 'gratis', 'free', 'nuevo',
        'revelación', 'descubrimiento', 'secreto', 'hack', 'truco', 'consejo'
    ]

    NEGATIVE_WORDS = [
        'error', 'fail', 'fallo', 'problema', 'cuidado', 'peligro', 'warning',
        'avoid', 'mistake', 'wrong', 'bad', 'terrible', 'no funciona', 'no sirve'
    ]

    URGENT_WORDS = [
        'urgente', 'urgent', 'ahora', 'now', 'inmediato', 'immediate',
        'alerta', 'alert', 'importante', 'important', 'última hora', 'breaking'
    ]

    CLICKBAIT_POSITIVE = [
        'no vas a creer', 'you won\'t believe', 'increíble que',
        'esto cambia todo', 'resultado inesperado', 'shocking', 'asombroso'
    ]

    def __init__(self):
        self._analysis_count = 0

    def analyze_sentiment(
        self,
        title: str
    ) -> SentimentAnalysis:
        """
        P1-6: Analiza el sentimiento de un título.
        Args:
            title: Título del video
        Returns:
            SentimentAnalysis con resultado
        """
        self._analysis_count += 1

        title_lower = title.lower()
        indicators = []

        positive_count = sum(1 for w in self.POSITIVE_WORDS if w in title_lower)
        negative_count = sum(1 for w in self.NEGATIVE_WORDS if w in title_lower)
        urgent_count = sum(1 for w in self.URGENT_WORDS if w in title_lower)

        if positive_count > negative_count:
            sentiment = 'positive'
            intensity = min(positive_count * 0.2, 1.0)
            if any(cb in title_lower for cb in self.CLICKBAIT_POSITIVE):
                indicators.append('clickbait_positive')
        elif negative_count > positive_count:
            sentiment = 'negative'
            intensity = min(negative_count * 0.2, 1.0)
        else:
            sentiment = 'neutral'
            intensity = 0.3

        if urgent_count > 0:
            urgency_level = 'high' if urgent_count >= 2 else 'medium'
        elif sentiment == 'positive' and positive_count >= 2:
            urgency_level = 'medium'
        else:
            urgency_level = 'low'

        confidence = min(0.5 + (positive_count + negative_count) * 0.1, 1.0)

        return SentimentAnalysis(
            sentiment=sentiment,
            intensity=round(intensity, 2),
            urgency_level=urgency_level,
            confidence=round(confidence, 2),
            indicators=indicators
        )

    def detect_urgency(self, title: str) -> str:
        """Detecta nivel de urgencia."""
        analysis = self.analyze_sentiment(title)
        return analysis.urgency_level

    def is_clickbait(self, title: str) -> bool:
        """Detecta si el título es clickbait."""
        title_lower = title.lower()
        return any(cb in title_lower for cb in self.CLICKBAIT_POSITIVE)

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del analizador."""
        return {
            "total_analyzed": self._analysis_count,
            "model": "SentimentAnalyzer v1.0"
        }


def create_sentiment_analyzer() -> SentimentAnalyzer:
    """Crea una instancia del analizador."""
    return SentimentAnalyzer()


_global_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Obtiene la instancia global."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = create_sentiment_analyzer()
    return _global_analyzer