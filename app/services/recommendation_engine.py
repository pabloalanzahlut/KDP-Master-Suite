"""
KDP MASTER - Video Recommendation Engine
==========================================
Motor de recomendaciones de videos basado en similaridad temática.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Motor de recomendación de videos relacionados.

    Usa similitud de palabras clave y scoring de relevancia para
    sugerir videos relacionados o "ver después".
    """

    # Stopwords en español
    STOPWORDS = {
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'de', 'del', 'en', 'a', 'al', 'por', 'para', 'con', 'sin',
        'que', 'y', 'o', 'pero', 'si', 'no', 'se', 'su', 'sus',
        'lo', 'más', 'menos', 'muy', 'ya', 'también', 'este', 'esta',
        'como', 'https', 'http', 'www', 'com', 'youtube', 'video'
    }

    # Palabras que indican una serie (parte 1, 2, etc.)
    SERIES_PATTERNS = [
        r'parte\s*(\d+)',
        r'cap[ií]tulo\s*(\d+)',
        r'episode\s*(\d+)',
        r'session\s*(\d+)',
        r'ep\.\s*(\d+)',
        r'#(\d+)',
        r'vol\.?\s*(\d+)',
    ]

    def __init__(self, min_similarity_score: float = 0.3):
        """
        Args:
            min_similarity_score: Score mínimo de similaridad (0-1)
        """
        self.min_similarity_score = min_similarity_score

    def extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave significativas de un texto."""
        if not text:
            return []

        # Limpiar y tokenizar
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Quitar puntuación
        words = text.split()

        # Filtrar stopwords y palabras cortas
        keywords = [
            w for w in words
            if w not in self.STOPWORDS and len(w) > 2 and not w.isdigit()
        ]

        return keywords

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridad entre dos textos basada en palabras clave.

        Returns:
            float: Score de 0 (nada similar) a 1 (idéntico)
        """
        if not text1 or not text2:
            return 0.0

        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))

        if not keywords1 or not keywords2:
            return 0.0

        # Coeficiente de Jaccard
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        jaccard = len(intersection) / len(union) if union else 0

        # Penalizar si hay mucha diferencia en longitud
        len_ratio = min(len(keywords1), len(keywords2)) / max(len(keywords1), len(keywords2))

        return jaccard * len_ratio

    def detect_series(self, title: str) -> Optional[Dict]:
        """
        Detecta si un video es parte de una serie numerada.

        Returns:
            Dict con {base_title, part_number, season} o None
        """
        title_lower = title.lower()

        for pattern in self.SERIES_PATTERNS:
            match = re.search(pattern, title_lower)
            if match:
                part_num = int(match.group(1))

                # Extraer título base (sin el número de parte)
                base_title = re.sub(pattern, '', title_lower, flags=re.IGNORECASE)
                base_title = re.sub(r'\s+', ' ', base_title).strip()

                return {
                    "base_title": base_title,
                    "part_number": part_num,
                    "full_match": match.group(0)
                }

        return None

    def group_series(self, videos: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa videos que son parte de la misma serie.

        Returns:
            Dict con {series_name: [videos_ordenados]}
        """
        series_groups = defaultdict(list)
        standalone = []

        for video in videos:
            title = video.get('title', '')
            series_info = self.detect_series(title)

            if series_info:
                series_key = series_info['base_title']
                video_with_series = dict(video)
                video_with_series['_series_info'] = series_info
                series_groups[series_key].append(video_with_series)
            else:
                standalone.append(video)

        # Ordenar cada serie por número de parte
        for series_key in series_groups:
            series_groups[series_key].sort(
                key=lambda v: v.get('_series_info', {}).get('part_number', 0)
            )

        # Agregar series como grupo especial
        result = {f"serie:{k}": v for k, v in series_groups.items()}
        result["_standalone"] = standalone

        return result

    def find_related_videos(self, target_title: str, target_description: str,
                          video_pool: List[Dict], limit: int = 5,
                          exclude_ids: List[str] = None) -> List[Dict]:
        """
        Encuentra videos relacionados con un video objetivo.

        Args:
            target_title: Título del video de referencia
            target_description: Descripción del video de referencia
            video_pool: Lista de videos a evaluar
            limit: Número máximo de recomendaciones
            exclude_ids: IDs a excluir (usualmente el video objetivo)

        Returns:
            Lista de videos relacionados ordenados por similitud
        """
        if exclude_ids is None:
            exclude_ids = []

        target_text = f"{target_title} {target_description}"
        target_keywords = set(self.extract_keywords(target_text))

        scored_videos = []

        for video in video_pool:
            video_id = video.get('video_id') or video.get('id')
            if video_id in exclude_ids:
                continue

            video_title = video.get('title', '')
            video_desc = video.get('description', '')

            # Calcular similitud
            video_text = f"{video_title} {video_desc}"
            similarity = self.calculate_similarity(target_text, video_text)

            if similarity >= self.min_similarity_score:
                # Calcular additional score
                video_keywords = set(self.extract_keywords(video_text))
                keyword_overlap = len(target_keywords & video_keywords)

                scored_videos.append({
                    'video': video,
                    'similarity_score': round(similarity, 3),
                    'keyword_overlap': keyword_overlap,
                    'combined_score': round(similarity + (keyword_overlap * 0.1), 3)
                })

        # Ordenar por combined_score
        scored_videos.sort(key=lambda x: x['combined_score'], reverse=True)

        # Verificar series
        target_series = self.detect_series(target_title)
        if target_series:
            # Buscar videos de la misma serie
            for video in video_pool:
                video_id = video.get('video_id') or video.get('id')
                if video_id in exclude_ids:
                    continue
                video_series = self.detect_series(video.get('title', ''))
                if video_series and video_series['base_title'] == target_series['base_title']:
                    if video not in [sv['video'] for sv in scored_videos]:
                        part_num = video_series['part_number']
                        # Agregar si es el siguiente en la serie
                        if abs(part_num - target_series['part_number']) == 1:
                            scored_videos.insert(0, {
                                'video': video,
                                'similarity_score': 1.0,
                                'keyword_overlap': len(target_keywords),
                                'combined_score': 1.5,  # Prioridad alta para series
                                'is_series_next': True
                            })

        return scored_videos[:limit]

    def get_watch_next_recommendations(self, current_video: Dict,
                                      video_library: List[Dict]) -> Dict[str, List]:
        """
        Genera recomendaciones para "ver después" basadas en el video actual.

        Returns:
            Dict con:
            - 'same_series': Siguiente video en la serie
            - 'same_topic': Videos sobre el mismo tema
            - 'same_channel': Más videos del mismo canal
        """
        recommendations = {
            'same_series': [],
            'same_topic': [],
            'same_channel': [],
            'curated': []
        }

        current_id = current_video.get('video_id') or current_video.get('id')
        current_channel = current_video.get('channel_name') or current_video.get('channel')
        current_title = current_video.get('title', '')

        for video in video_library:
            video_id = video.get('video_id') or video.get('id')
            if video_id == current_id:
                continue

            # Mismo canal
            video_channel = video.get('channel_name') or video.get('channel')
            if video_channel == current_channel:
                recommendations['same_channel'].append(video)

            # Mismo tópico (alta similitud)
            similarity = self.calculate_similarity(
                current_title,
                video.get('title', '')
            )
            if similarity > 0.3:
                recommendations['same_topic'].append({
                    'video': video,
                    'similarity': similarity
                })

        # Ordenar same_topic por similitud
        recommendations['same_topic'].sort(key=lambda x: x['similarity'], reverse=True)
        recommendations['same_topic'] = [
            item['video'] for item in recommendations['same_topic']
        ][:10]

        # Limitar same_channel
        recommendations['same_channel'] = recommendations['same_channel'][:5]

        # Detectar siguiente en serie
        current_series = self.detect_series(current_title)
        if current_series:
            next_part = current_series['part_number'] + 1
            for video in video_library:
                video_series = self.detect_series(video.get('title', ''))
                if (video_series and
                    video_series['base_title'] == current_series['base_title'] and
                    video_series['part_number'] == next_part):
                    recommendations['same_series'] = [video]
                    break

        return recommendations


def create_recommendation_engine(min_similarity: float = 0.3) -> RecommendationEngine:
    """Factory function."""
    return RecommendationEngine(min_similarity_score=min_similarity)