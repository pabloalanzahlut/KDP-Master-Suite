"""
P6-53: Predicción de Próximos Videos del Canal
Sugiere qué podría publicar el canal basándose en patrones.
"""
import logging
from typing import List, Dict, Optional
from collections import Counter
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class VideoPredictor:
    """Predictor de próximos videos de un canal."""

    def __init__(self):
        self._prediction_count = 0

    def predict_next_videos(
        self,
        channel_name: str,
        video_titles: List[str],
        video_dates: List[str],
        channel_description: str = ""
    ) -> Dict:
        """
        Predice qué podría publicar el canal.
        Returns: Dict con predicted_topics, confidence, pattern
        """
        self._prediction_count += 1

        if not video_titles:
            return {
                'predicted_topics': [],
                'confidence': 0.0,
                'pattern': 'insufficient_data'
            }

        words = []
        for title in video_titles:
            words.extend(title.lower().split())

        common_words = [w for w, c in Counter(words).most_common(20) if len(w) > 3][:10]

        upload_freq = self._calculate_frequency(video_dates)

        topics = []
        topic_keywords = {
            'tutorial': ['tutorial', 'cómo', 'guía', 'enseñar'],
            'review': ['review', 'reseña', 'opinión', 'análisis'],
            'news': ['noticia', 'actualización', 'nuevo', 'lanzamiento'],
            'interview': ['entrevista', 'charla', 'conversación']
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in ' '.join(video_titles).lower() for kw in keywords):
                topics.append(topic)

        confidence = min(0.3 + (len(video_titles) / 100), 0.9)

        return {
            'predicted_topics': topics[:5],
            'confidence': round(confidence, 2),
            'common_keywords': common_words,
            'pattern': f'frecuencia_{upload_freq}_videos',
            'suggestion': f"Canal probablemente continuará con {topics[0] if topics else 'contenido similar'}"
        }

    def _calculate_frequency(self, dates: List[str]) -> str:
        """Calcula frecuencia de publicación."""
        if len(dates) < 2:
            return 'unknown'

        try:
            parsed_dates = []
            for d in dates:
                try:
                    parsed_dates.append(datetime.fromisoformat(d.replace('Z', '+00:00')))
                except:
                    pass

            if len(parsed_dates) >= 2:
                parsed_dates.sort()
                span_days = (parsed_dates[-1] - parsed_dates[0]).days
                if span_days > 0:
                    avg_days = span_days / (len(parsed_dates) - 1)
                    if avg_days < 3:
                        return 'high'
                    elif avg_days < 14:
                        return 'medium'
                    else:
                        return 'low'
        except:
            pass

        return 'unknown'


def get_video_predictor():
    return VideoPredictor()