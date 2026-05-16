"""
Módulos IA P6-56: Detección de Saturación de Tema
Detecta cuando ya hay demasiado contenido sobre un tema en la KB.
"""
import logging
from typing import List, Dict, Optional
from collections import Counter
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SaturationAnalysis:
    """Resultado del análisis de saturación."""
    topic: str
    video_count: int
    saturation_level: str
    saturation_score: float
    is_saturated: bool
    recommendation: str


class SaturationDetector:
    """Detector de saturación de temas en la KB."""

    SATURATION_THRESHOLDS = {
        'low': 5,
        'medium': 15,
        'high': 30,
        'over saturated': 50
    }

    def __init__(self):
        self._analysis_count = 0

    def analyze_topic_saturation(
        self,
        topic: str,
        existing_videos: List[Dict],
        threshold: int = 15
    ) -> SaturationAnalysis:
        """
        P6-56: Analiza si un tema está saturado.
        Args:
            topic: Tema a analizar
            existing_videos: Videos existentes en la KB
            threshold: Umbral de saturación
        Returns:
            SaturationAnalysis con resultado
        """
        self._analysis_count += 1

        topic_lower = topic.lower()
        matching_videos = []

        for video in existing_videos:
            title = video.get('title', '').lower()
            tags = video.get('tags', [])
            description = video.get('description', '').lower()

            if topic_lower in title or topic_lower in description:
                matching_videos.append(video)
            elif any(topic_lower in str(t).lower() for t in tags):
                matching_videos.append(video)

        video_count = len(matching_videos)

        if video_count >= self.SATURATION_THRESHOLDS['over saturated']:
            saturation_level = "over_saturated"
            saturation_score = 1.0
            is_saturated = True
            recommendation = f"Tema saturado ({video_count} videos). Considera buscar temas complementarios o más específicos."
        elif video_count >= self.SATURATION_THRESHOLDS['high']:
            saturation_level = "high"
            saturation_score = 0.8
            is_saturated = True
            recommendation = f"Alto contenido sobre '{topic}'. Explorar subtemas más específicos."
        elif video_count >= self.SATURATION_THRESHOLDS['medium']:
            saturation_level = "medium"
            saturation_score = 0.5
            is_saturated = False
            recommendation = f"Contenido moderado sobre '{topic}'. Espacio para más profundidad."
        elif video_count >= self.SATURATION_THRESHOLDS['low']:
            saturation_level = "low"
            saturation_score = 0.25
            is_saturated = False
            recommendation = f"Poco contenido sobre '{topic}'. Oportunidad para expansión."
        else:
            saturation_level = "minimal"
            saturation_score = 0.1
            is_saturated = False
            recommendation = f"Tema prácticamente nuevo. Excelente oportunidad para agregar contenido."

        return SaturationAnalysis(
            topic=topic,
            video_count=video_count,
            saturation_level=saturation_level,
            saturation_score=saturation_score,
            is_saturated=is_saturated,
            recommendation=recommendation
        )

    def find_unsaturated_topics(
        self,
        target_topics: List[str],
        existing_videos: List[Dict]
    ) -> List[SaturationAnalysis]:
        """Encuentra topics con menos saturación para priorizar."""
        analyses = []

        for topic in target_topics:
            analysis = self.analyze_topic_saturation(topic, existing_videos)
            analyses.append(analysis)

        unsaturated = [a for a in analyses if not a.is_saturated]
        unsaturated.sort(key=lambda x: x.saturation_score)

        return unsaturated

    def suggest_alternatives(
        self,
        saturated_topic: str,
        existing_videos: List[Dict]
    ) -> List[str]:
        """Sugiere temas alternativos menos saturados."""
        topic_lower = saturated_topic.lower()

        base_topics = ['kdp', 'marketing', 'seo', 'amazon', 'ebook', 'video', 'tutorial']

        alternatives = []
        for base in base_topics:
            if base not in topic_lower:
                analysis = self.analyze_topic_saturation(base, existing_videos)
                if not analysis.is_saturated:
                    alternatives.append(base)

        return alternatives[:5]

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del detector."""
        return {
            "total_analyzed": self._analysis_count,
            "model": "SaturationDetector v1.0"
        }


def create_saturation_detector() -> SaturationDetector:
    """Crea una instancia del detector de saturación."""
    return SaturationDetector()


_global_detector: Optional[SaturationDetector] = None


def get_saturation_detector() -> SaturationDetector:
    """Obtiene la instancia global del detector de saturación."""
    global _global_detector
    if _global_detector is None:
        _global_detector = create_saturation_detector()
    return _global_detector