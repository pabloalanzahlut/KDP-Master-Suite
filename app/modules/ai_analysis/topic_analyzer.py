"""
P1-3: Clasificación Temática Automática
Asigna etiqueta: Tutorial, Noticias, Opinión.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class TopicClassifier:
    TOPIC_PATTERNS = {
        'tutorial': ['tutorial', 'how to', 'cómo hacer', 'guía', 'curso'],
        'noticia': ['news', 'noticia', 'actualización', 'anuncio'],
        'opinion': ['opinión', 'review', 'reseña', 'analisis'],
        'entrevista': ['interview', 'entrevista', 'charla']
    }

    def classify(self, title: str, description: str = "") -> Dict:
        content = f"{title.lower()} {description.lower()}"
        for topic, keywords in self.TOPIC_PATTERNS.items():
            if any(kw in content for kw in keywords):
                return {'topic': topic, 'confidence': 0.8}
        return {'topic': 'general', 'confidence': 0.3}


def get_topic_classifier():
    return TopicClassifier()