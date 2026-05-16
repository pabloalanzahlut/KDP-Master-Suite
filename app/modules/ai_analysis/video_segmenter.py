"""
Módulos IA P4-36: Sugerencia de Segmentación
Sugiere dividir un video largo en partes más pequeñas.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SegmentSuggestion:
    """Sugerencia de segmento."""
    start_time: int
    end_time: int
    title: str
    reason: str
    confidence: float


class VideoSegmenter:
    """Segmentador de videos para procesamiento óptimo."""

    OPTIMAL_SEGMENT_MINUTES = 10
    MIN_SEGMENT_MINUTES = 3
    MAX_SEGMENT_MINUTES = 30

    CHAPTER_INDICATORS = [
        'capítulo', 'chapter', 'parte', 'part',
        'sección', 'section', 'módulo', 'module',
        'tema', 'topic', 'punto', 'point'
    ]

    def __init__(self):
        self._segmentation_count = 0

    def suggest_segmentation(
        self,
        duration_seconds: int,
        transcript: str = "",
        chapters: List[Dict] = None
    ) -> List[SegmentSuggestion]:
        """
        P4-36: Sugiere cómo dividir un video en segmentos.
        Args:
            duration_seconds: Duración total del video en segundos
            transcript: Transcripción del video (opcional)
            chapters: Lista de capítulos detectados {title, start_time}
        Returns:
            Lista de SegmentSuggestion
        """
        self._segmentation_count += 1
        suggestions = []

        duration_minutes = duration_seconds / 60

        if duration_minutes <= self.OPTIMAL_SEGMENT_MINUTES:
            suggestions.append(SegmentSuggestion(
                start_time=0,
                end_time=duration_seconds,
                title="Video completo",
                reason="Duración óptima para un solo segmento",
                confidence=1.0
            ))
            return suggestions

        if chapters and len(chapters) >= 2:
            for i, chapter in enumerate(chapters):
                start = chapter.get('start_time', 0)
                end = chapters[i + 1].get('start_time', duration_seconds) if i + 1 < len(chapters) else duration_seconds
                suggestions.append(SegmentSuggestion(
                    start_time=start,
                    end_time=end,
                    title=chapter.get('title', f'Parte {i + 1}'),
                    reason="Basado en capítulos detectados",
                    confidence=0.9
                ))
            return suggestions

        num_segments = max(2, int(duration_minutes / self.OPTIMAL_SEGMENT_MINUTES))
        segment_duration = duration_seconds // num_segments

        for i in range(num_segments):
            start = i * segment_duration
            end = (i + 1) * segment_duration if i < num_segments - 1 else duration_seconds

            segment_minutes = (end - start) / 60

            if segment_minutes > self.MAX_SEGMENT_MINUTES:
                sub_segments = int(segment_minutes / self.OPTIMAL_SEGMENT_MINUTES)
                sub_duration = segment_duration // sub_segments
                for j in range(sub_segments):
                    sub_start = start + j * sub_duration
                    sub_end = start + (j + 1) * sub_duration
                    suggestions.append(SegmentSuggestion(
                        start_time=sub_start,
                        end_time=sub_end,
                        title=f"Segmento {i + 1}.{j + 1}",
                        reason=f"Duración: {sub_duration / 60:.1f} min",
                        confidence=0.7
                    ))
            else:
                suggestions.append(SegmentSuggestion(
                    start_time=start,
                    end_time=end,
                    title=f"Parte {i + 1}",
                    reason=f"Duración: {segment_minutes:.1f} min",
                    confidence=0.8 if num_segments <= 5 else 0.6
                ))

        logger.info(f"Video de {duration_minutes:.1f} min segmentado en {len(suggestions)} partes")
        return suggestions

    def estimate_processing_time(
        self,
        segments: List[SegmentSuggestion]
    ) -> Dict:
        """Estima el tiempo de procesamiento para los segmentos."""
        total_seconds = sum(s.end_time - s.start_time for s in segments)
        processing_speed = 10

        estimated_seconds = total_seconds / processing_speed

        return {
            "total_duration_seconds": total_seconds,
            "estimated_processing_seconds": round(estimated_seconds),
            "estimated_processing_minutes": round(estimated_seconds / 60, 1),
            "segment_count": len(segments),
            "avg_segment_duration_minutes": round(total_seconds / len(segments) / 60, 1) if segments else 0
        }

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del segmentador."""
        return {
            "total_segmented": self._segmentation_count,
            "model": "VideoSegmenter v1.0"
        }


def create_video_segmenter() -> VideoSegmenter:
    """Crea una instancia del segmentador de videos."""
    return VideoSegmenter()


_global_segmenter: Optional[VideoSegmenter] = None


def get_video_segmenter() -> VideoSegmenter:
    """Obtiene la instancia global del segmentador de videos."""
    global _global_segmenter
    if _global_segmenter is None:
        _global_segmenter = create_video_segmenter()
    return _global_segmenter