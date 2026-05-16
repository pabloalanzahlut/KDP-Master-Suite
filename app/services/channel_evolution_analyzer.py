"""
Módulos IA P6-52: Análisis de Evolución de Contenido
Analiza cómo ha cambiado el enfoque del canal a lo largo del tiempo.
"""
import logging
from typing import List, Dict, Optional
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EvolutionAnalysis:
    """Resultado del análisis de evolución."""
    has_evolution: bool
    previous_focus: str
    current_focus: str
    evolution_percentage: float
    phases: List[Dict]
    trend: str


class ChannelEvolutionAnalyzer:
    """Analizador de evolución de canales."""

    TOPIC_KEYWORDS = {
        'kdp': ['kdp', 'amazon', 'ebook', 'publicar', 'autoedición', 'self-publishing'],
        'marketing': ['marketing', 'publicidad', 'ventas', 'promoción', 'digital'],
        'tutorial': ['tutorial', 'guía', 'cómo', 'aprender', 'curso', 'enseñar'],
        'tech': ['python', 'programación', 'código', 'desarrollo', 'software', 'ia'],
        'finanzas': ['dinero', 'inversión', 'renta', 'crypto', 'criptomoneda'],
        'legal': ['legal', 'ley', 'derecho', 'jurídico', 'contrato', 'compliance'],
        'productividad': ['productividad', 'organización', 'tiempo', 'habitos'],
        'video': ['video', 'youtube', 'edición', 'montaje', ' filming']
    }

    def __init__(self):
        self._analysis_count = 0

    def analyze_evolution(
        self,
        videos: List[Dict],
        time_window_days: int = 180
    ) -> EvolutionAnalysis:
        """
        P6-52: Analiza la evolución del contenido de un canal.
        Args:
            videos: Lista de videos del canal
            time_window_days: Ventana de tiempo a analizar
        Returns:
            EvolutionAnalysis con resultado
        """
        self._analysis_count += 1

        if len(videos) < 5:
            return EvolutionAnalysis(
                has_evolution=False,
                previous_focus="desconocido",
                current_focus="desconocido",
                evolution_percentage=0.0,
                phases=[],
                trend="insuficiente_datos"
            )

        sorted_videos = sorted(videos, key=lambda v: v.get('published_at', v.get('discovered_at', '')))

        first_half = sorted_videos[:len(sorted_videos)//2]
        second_half = sorted_videos[len(sorted_videos)//2:]

        first_topics = self._extract_topics([v.get('title', '') for v in first_half])
        second_topics = self._extract_topics([v.get('title', '') for v in second_half])

        previous_focus = max(first_topics, key=first_topics.get) if first_topics else "desconocido"
        current_focus = max(second_topics, key=second_topics.get) if second_topics else "desconocido"

        if previous_focus == "desconocido" or current_focus == "desconocido":
            return EvolutionAnalysis(
                has_evolution=False,
                previous_focus=previous_focus,
                current_focus=current_focus,
                evolution_percentage=0.0,
                phases=[],
                trend="tema_consistente"
            )

        previous_count = first_topics.get(previous_focus, 0)
        current_count = second_topics.get(current_focus, 0)

        first_total = sum(first_topics.values()) if first_topics else 1
        second_total = sum(second_topics.values()) if second_topics else 1

        previous_pct = previous_count / first_total
        current_pct = current_count / second_total

        evolution_percentage = abs(current_pct - previous_pct) * 100

        has_evolution = evolution_percentage > 20 and previous_focus != current_focus

        trend = "crecimiento" if current_pct > previous_pct else "declive" if current_pct < previous_pct else "estable"

        phases = [
            {"period": "primera_mitad", "topics": first_topics},
            {"period": "segunda_mitad", "topics": second_topics}
        ]

        return EvolutionAnalysis(
            has_evolution=has_evolution,
            previous_focus=previous_focus,
            current_focus=current_focus,
            evolution_percentage=round(evolution_percentage, 1),
            phases=phases,
            trend=trend
        )

    def _extract_topics(self, titles: List[str]) -> Dict[str, int]:
        """Extrae topics de una lista de títulos."""
        topic_counts = Counter()

        for title in titles:
            title_lower = title.lower()
            for topic, keywords in self.TOPIC_KEYWORDS.items():
                if any(kw in title_lower for kw in keywords):
                    topic_counts[topic] += 1

        return dict(topic_counts)

    def get_quality_trend(self, videos: List[Dict]) -> Dict:
        """Analiza la tendencia de calidad del canal."""
        if not videos:
            return {"trend": "desconocido", "score_change": 0}

        sorted_videos = sorted(videos, key=lambda v: v.get('published_at', v.get('discovered_at', '')))

        first_quality = self._calculate_avg_quality(sorted_videos[:len(sorted_videos)//3])
        last_quality = self._calculate_avg_quality(sorted_videos[-len(sorted_videos)//3:])

        score_change = last_quality - first_quality

        if score_change > 0.2:
            trend = "mejando"
        elif score_change < -0.2:
            trend = "declinando"
        else:
            trend = "estable"

        return {
            "trend": trend,
            "score_change": round(score_change, 2),
            "first_quality": round(first_quality, 2),
            "last_quality": round(last_quality, 2)
        }

    def _calculate_avg_quality(self, videos: List[Dict]) -> float:
        """Calcula calidad promedio de un conjunto de videos."""
        if not videos:
            return 0.5

        total = 0
        for v in videos:
            total += v.get('quality_score', v.get('relevance_score', 50))

        return total / len(videos) / 100

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del analizador."""
        return {
            "total_analyzed": self._analysis_count,
            "model": "ChannelEvolutionAnalyzer v1.0"
        }


def create_evolution_analyzer() -> ChannelEvolutionAnalyzer:
    """Crea una instancia del analizador de evolución."""
    return ChannelEvolutionAnalyzer()


_global_analyzer: Optional[ChannelEvolutionAnalyzer] = None


def get_evolution_analyzer() -> ChannelEvolutionAnalyzer:
    """Obtiene la instancia global del analizador de evolución."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = create_evolution_analyzer()
    return _global_analyzer