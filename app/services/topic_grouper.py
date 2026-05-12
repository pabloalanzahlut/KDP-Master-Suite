"""
KDP MASTER - Topic Grouping Service
====================================
Servicio para agrupar videos por tema/topics para procesamiento en batch.
"""

import logging
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class TopicGrouper:
    """
    Agrupa videos por temas/topics comunes para procesamiento optimizado.

    Útil para:
    - Procesar videos similares juntos (mejor cache de IA)
    - Crear batches temáticos para el usuario
    - Descubrir patrones en el contenido de un canal
    """

    # Mapeo de categorías KDP a keywords
    TOPIC_KEYWORDS = {
        "amazon_kdp": [
            "kdp", "amazon", "print on demand", "self publishing",
            "libro", "ebook", "publicar", "royalty", "ventas"
        ],
        "marketing": [
            "marketing", "ads", "publicidad", "facebook ads", "google ads",
            "campaña", "estrategia", "conversion", "ctr", "roi"
        ],
        "seo": [
            "seo", "keywords", "busqueda", "ranking", "amazon a9",
            "optimizacion", "search"
        ],
        "diseño": [
            "diseño", "cover", "portada", "interior", "format",
            "plantilla", "portrait", "formatting"
        ],
        "inversiones": [
            "inversion", "invertir", "bolsa", "fondos", "cartera",
            "portfolio", "rendimiento", "dividendos"
        ],
        "finanzas": [
            "finanzas", "dinero", "presupuesto", "ahorro", "deuda",
            "credito", "banco", "economia"
        ],
        "cripto": [
            "bitcoin", "cripto", "crypto", "ethereum", "blockchain",
            "nft", "trading", "defi"
        ],
        "productividad": [
            "productividad", "habitos", "rutina", "organizacion",
            "tiempo", "focus", "eficienc"
        ],
        "emprendimiento": [
            "emprendedor", "negocio", "startup", "freelance",
            "autonomo", "empresa", "cliente"
        ],
        "tecnologia": [
            "tecnologia", "software", "ia", "ai", "python",
            "automation", "herramienta"
        ]
    }

    def __init__(self, confidence_threshold: float = 0.3):
        """
        Args:
            confidence_threshold: Threshold mínimo de confianza para categorización
        """
        self.confidence_threshold = confidence_threshold

    def classify_topic(self, title: str, description: str = "") -> Dict[str, any]:
        """
        Clasifica un video en uno o más topics.

        Returns:
            Dict con:
            - primary_topic: Topic principal
            - all_topics: Todos los topics con score
            - confidence: Confianza de la clasificación
        """
        text = f"{title} {description}".lower()
        topic_scores = {}

        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword.lower() in text:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                topic_scores[topic] = {
                    'score': score,
                    'keywords': matched_keywords,
                    'confidence': min(score / 3.0, 1.0)  # Normalizar a 0-1
                }

        if not topic_scores:
            return {
                'primary_topic': 'general',
                'all_topics': [],
                'confidence': 0
            }

        # Ordenar por score
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )

        primary = sorted_topics[0]
        confidence = primary[1]['confidence']

        return {
            'primary_topic': primary[0],
            'all_topics': [
                {'topic': t, 'score': s['score'], 'confidence': s['confidence']}
                for t, s in sorted_topics
            ],
            'confidence': confidence
        }

    def group_videos_by_topic(self, videos: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa videos por topic/tema.

        Args:
            videos: Lista de dicts con 'title' y opcionalmente 'description'

        Returns:
            Dict con {topic_name: [videos]}
        """
        groups = defaultdict(list)

        for video in videos:
            title = video.get('title', '')
            description = video.get('description', '')

            classification = self.classify_topic(title, description)
            topic = classification['primary_topic']

            # Solo agregar si confidence suficiente
            if classification['confidence'] >= self.confidence_threshold:
                video_with_topic = dict(video)
                video_with_topic['_topic_classification'] = classification
                groups[topic].append(video_with_topic)

        # Agregar videos sin topic claro a 'general'
        for topic in list(groups.keys()):
            if not groups[topic]:
                del groups[topic]

        return dict(groups)

    def optimize_batch_order(self, videos: List[Dict]) -> List[Dict]:
        """
        Ordena videos para procesamiento batch optimizado.

        Prioriza:
        1. Videos del mismo topic juntos (mejora cache de IA)
        2. Dentro de cada topic, ordenar por score de relevance si disponible

        Returns:
            Lista de videos ordenada óptimamente
        """
        groups = self.group_videos_by_topic(videos)

        # Ordenar topics por cantidad (más videos primero = más eficiencia)
        sorted_topics = sorted(
            groups.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        # Concatenar en orden
        optimized = []
        for topic, topic_videos in sorted_topics:
            # Ordenar dentro del topic por relevance si está disponible
            topic_videos.sort(
                key=lambda v: v.get('_topic_classification', {}).get('confidence', 0),
                reverse=True
            )
            optimized.extend(topic_videos)

        return optimized

    def get_topic_summary(self, videos: List[Dict]) -> Dict:
        """
        Genera resumen de topics en la colección de videos.

        Returns:
            Dict con estadísticas por topic
        """
        groups = self.group_videos_by_topic(videos)

        summary = {
            'total_videos': len(videos),
            'topics_count': len(groups),
            'topics': []
        }

        for topic, topic_videos in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True):
            topic_info = {
                'topic': topic,
                'count': len(topic_videos),
                'percentage': round(len(topic_videos) / len(videos) * 100, 1) if videos else 0,
                'avg_confidence': sum(
                    v.get('_topic_classification', {}).get('confidence', 0)
                    for v in topic_videos
                ) / len(topic_videos) if topic_videos else 0
            }
            summary['topics'].append(topic_info)

        return summary

    def suggest_topic_filter(self, videos: List[Dict], exclude_topics: List[str] = None) -> List[Dict]:
        """
        Sugiere videos que NO sean de ciertos topics.

        Útil para filtrar contenido no deseado.
        """
        if exclude_topics is None:
            exclude_topics = []

        exclude_topics_lower = [t.lower() for t in exclude_topics]
        suggested = []

        for video in videos:
            classification = self.classify_topic(
                video.get('title', ''),
                video.get('description', '')
            )

            if classification['primary_topic'].lower() not in exclude_topics_lower:
                suggested.append(video)

        return suggested


def create_topic_grouper(confidence: float = 0.3) -> TopicGrouper:
    """Factory function."""
    return TopicGrouper(confidence_threshold=confidence)