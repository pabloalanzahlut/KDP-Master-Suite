"""
Módulos IA P6-57: Sugerencia de Nuevos Canales
Sugiere nuevos canales basados en el canal actual.
"""
import logging
from typing import List, Dict, Optional, Set
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ChannelSuggestion:
    """Sugerencia de canal."""
    channel_id: str
    channel_name: str
    match_score: float
    reason: str
    similarity_topics: List[str]


class ChannelRecommender:
    """Recomendador de nuevos canales."""

    TOPIC_MAPPING = {
        'kdp': ['autoedición', 'ebook', 'publicación', 'amazon kdp', 'escritura'],
        'marketing': ['marketing digital', 'ventas', 'publicidad', 'negocios'],
        'tutorial': ['tutorial', 'cómo hacer', 'guía', 'curso', 'aprender'],
        'tech': ['programación', 'python', 'desarrollo', 'tech', 'software'],
        'productividad': ['productividad', 'organización', 'habitos', 'tiempo'],
        'finanzas': ['inversión', 'dinero', 'crypto', 'finanzas personales']
    }

    def __init__(self):
        self._recommendation_count = 0

    def analyze_channel_topics(
        self,
        channel_name: str,
        video_titles: List[str]
    ) -> Dict[str, int]:
        """Extrae topics principales de un canal."""
        topic_counts = Counter()

        titles_text = ' '.join(video_titles).lower()

        for topic, keywords in self.TOPIC_MAPPING.items():
            for kw in keywords:
                if kw in titles_text:
                    topic_counts[topic] += 1

        return dict(topic_counts)

    def suggest_similar_channels(
        self,
        current_channel_topics: Dict[str, int],
        available_channels: List[Dict],
        limit: int = 5
    ) -> List[ChannelSuggestion]:
        """
        P6-57: Sugiere canales similares.
        Args:
            current_channel_topics: Topics del canal actual
            available_channels: Canales disponibles para recomendar
            limit: Número máximo de recomendaciones
        Returns:
            Lista de ChannelSuggestion
        """
        self._recommendation_count += 1

        suggestions = []

        for channel in available_channels:
            channel_topics = channel.get('topics', {})

            common_topics = set(current_channel_topics.keys()) & set(channel_topics.keys())
            if not common_topics:
                continue

            match_score = sum(
                min(current_channel_topics.get(t, 0), channel_topics.get(t, 0))
                for t in common_topics
            )

            total_current = sum(current_channel_topics.values())
            if total_current > 0:
                match_score = match_score / total_current

            suggestions.append(ChannelSuggestion(
                channel_id=channel.get('id', ''),
                channel_name=channel.get('name', 'Unknown'),
                match_score=round(match_score, 3),
                reason=f"Comparte {len(common_topics)} temas en común",
                similarity_topics=list(common_topics)
            ))

        suggestions.sort(key=lambda s: s.match_score, reverse=True)
        return suggestions[:limit]

    def find_complementary_channels(
        self,
        current_topics: Dict[str, int],
        available_channels: List[Dict]
    ) -> List[ChannelSuggestion]:
        """Encuentra canales que complementan los temas faltantes."""
        suggestions = []

        missing_topics = set(self.TOPIC_MAPPING.keys()) - set(current_topics.keys())

        for channel in available_channels:
            channel_topics = channel.get('topics', {})
            channel_missing = set(channel_topics.keys()) & missing_topics

            if channel_missing:
                suggestions.append(ChannelSuggestion(
                    channel_id=channel.get('id', ''),
                    channel_name=channel.get('name', 'Unknown'),
                    match_score=len(channel_missing) * 0.2,
                    reason=f"Expande a temas nuevos: {', '.join(channel_missing)}",
                    similarity_topics=list(channel_missing)
                ))

        suggestions.sort(key=lambda s: s.match_score, reverse=True)
        return suggestions[:5]

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del recomendador."""
        return {
            "total_recommendations": self._recommendation_count,
            "model": "ChannelRecommender v1.0"
        }


def create_channel_recommender() -> ChannelRecommender:
    """Crea una instancia del recomendador de canales."""
    return ChannelRecommender()


_global_recommender: Optional[ChannelRecommender] = None


def get_channel_recommender() -> ChannelRecommender:
    """Obtiene la instancia global del recomendador."""
    global _global_recommender
    if _global_recommender is None:
        _global_recommender = create_channel_recommender()
    return _global_recommender