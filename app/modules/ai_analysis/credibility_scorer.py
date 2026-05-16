"""
Módulos IA P2-15: Análisis de Credibilidad de Fuente
Score basado en historial del canal.
"""
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CredibilityScore:
    """Score de credibilidad de una fuente."""
    channel_id: str
    credibility_score: float
    risk_level: str
    factors: Dict[str, float]
    recommendation: str


class CredibilityScorer:
    """Analizador de credibilidad de fuentes."""

    HIGH_RISK_THRESHOLD = 0.4
    LOW_RISK_THRESHOLD = 0.7

    CREDIBILITY_POSITIVE = {
        'verified': 0.3,
        'high_subscribers': 0.2,
        'consistent_upload': 0.15,
        'old_channel': 0.1,
        'high_engagement': 0.15
    }

    CREDIBILITY_NEGATIVE = {
        'no_verified': -0.1,
        'low_subscribers': -0.15,
        'inconsistent_upload': -0.1,
        'new_channel': -0.1,
        'low_engagement': -0.15,
        'suspicious_name': -0.2
    }

    def __init__(self):
        self._analysis_count = 0

    def analyze_credibility(
        self,
        channel_data: Dict,
        video_history: list = None
    ) -> CredibilityScore:
        """
        P2-15: Analiza la credibilidad de una fuente.
        Args:
            channel_data: Datos del canal
            video_history: Historial de videos del canal
        Returns:
            CredibilityScore con análisis
        """
        self._analysis_count += 1

        channel_id = str(channel_data.get('id', ''))
        channel_name = channel_data.get('name', '').lower()
        subscriber_count = channel_data.get('subscriber_count', 0) or 0

        factors = {}
        score = 0.5

        if channel_data.get('verified'):
            score += self.CREDIBILITY_POSITIVE['verified']
            factors['verified'] = self.CREDIBILITY_POSITIVE['verified']

        if subscriber_count > 100000:
            score += self.CREDIBILITY_POSITIVE['high_subscribers']
            factors['high_subscribers'] = self.CREDIBILITY_POSITIVE['high_subscribers']
        elif subscriber_count < 1000:
            score += self.CREDIBILITY_NEGATIVE['low_subscribers']
            factors['low_subscribers'] = self.CREDIBILITY_NEGATIVE['low_subscribers']

        suspicious_patterns = ['fake', 'clon', 'bot', 'guru', 'millionaire']
        if any(p in channel_name for p in suspicious_patterns):
            score += self.CREDIBILITY_NEGATIVE['suspicious_name']
            factors['suspicious_name'] = self.CREDIBILITY_NEGATIVE['suspicious_name']

        if video_history:
            upload_frequency = self._calculate_upload_frequency(video_history)
            if upload_frequency > 2:
                score += self.CREDIBILITY_POSITIVE['consistent_upload']
                factors['consistent_upload'] = self.CREDIBILITY_POSITIVE['consistent_upload']
            elif upload_frequency < 0.5:
                score += self.CREDIBILITY_NEGATIVE['inconsistent_upload']
                factors['inconsistent_upload'] = self.CREDIBILITY_NEGATIVE['inconsistent_upload']

            avg_engagement = self._calculate_avg_engagement(video_history)
            if avg_engagement > 0.05:
                score += self.CREDIBILITY_POSITIVE['high_engagement']
                factors['high_engagement'] = self.CREDIBILITY_POSITIVE['high_engagement']
            elif avg_engagement < 0.01:
                score += self.CREDIBILITY_NEGATIVE['low_engagement']
                factors['low_engagement'] = self.CREDIBILITY_NEGATIVE['low_engagement']

        score = max(0, min(score, 1.0))

        if score >= self.LOW_RISK_THRESHOLD:
            risk_level = "low"
            recommendation = "Fuente confiable - proceder normalmente"
        elif score >= self.HIGH_RISK_THRESHOLD:
            risk_level = "medium"
            recommendation = "Fuente de riesgo medio - verificar información"
        else:
            risk_level = "high"
            recommendation = "Fuente no confiable - verificar cuidadosamente"

        return CredibilityScore(
            channel_id=channel_id,
            credibility_score=round(score, 2),
            risk_level=risk_level,
            factors=factors,
            recommendation=recommendation
        )

    def _calculate_upload_frequency(self, video_history: list) -> float:
        """Calcula frecuencia de subida promedio."""
        if not video_history:
            return 0

        dates = []
        for v in video_history:
            pub = v.get('published_at')
            if pub:
                try:
                    dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                    dates.append(dt)
                except:
                    pass

        if len(dates) < 2:
            return 0

        dates.sort()
        span_days = (dates[-1] - dates[0]).days
        if span_days == 0:
            return 0

        return len(dates) / span_days * 30

    def _calculate_avg_engagement(self, video_history: list) -> float:
        """Calcula engagement promedio de videos."""
        if not video_history:
            return 0

        total = 0
        count = 0

        for v in video_history:
            views = v.get('view_count', 0) or 0
            likes = v.get('like_count', 0) or 0
            comments = v.get('comment_count', 0) or 0

            if views > 0:
                total += (likes + comments * 2) / views
                count += 1

        return total / count if count > 0 else 0

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del analizador."""
        return {
            "total_analyzed": self._analysis_count,
            "model": "CredibilityScorer v1.0"
        }


def create_credibility_scorer() -> CredibilityScorer:
    """Crea una instancia del analizador de credibilidad."""
    return CredibilityScorer()


_global_scorer: Optional[CredibilityScorer] = None


def get_credibility_scorer() -> CredibilityScorer:
    """Obtiene la instancia global del analizador."""
    global _global_scorer
    if _global_scorer is None:
        _global_scorer = create_credibility_scorer()
    return _global_scorer