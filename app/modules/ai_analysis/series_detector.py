"""
Módulos IA P2-18: Detección de Series Educativas
Identifica si es parte de un curso estructurado.
"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SeriesCandidate:
    """Candidato de serie detectado."""
    series_name: str
    video_count: int
    consistency_score: float
    videos: List[Dict]
    is_complete: bool


class SeriesDetector:
    """Detector de series educativas."""

    SERIES_PATTERNS = [
        r'(parte|part|episode|ep)\s*[:\.]?\s*(\d+)',
        r'(cap[ií]tulo|chapter)\s*[:\.]?\s*(\d+)',
        r'(clase|lesson|lección)\s*[:\.]?\s*(\d+)',
        r'(volumen|volume)\s*[:\.]?\s*(\d+)',
        r'(nivel|level)\s*[:\.]?\s*(\d+)',
        r'serie\s*(\d+)',
        r'(\d+)/(\d+)',
    ]

    def __init__(self):
        self._detection_count = 0
        self._series_cache: Dict[str, SeriesCandidate] = {}

    def detect_series(
        self,
        videos: List[Dict],
        min_videos: int = 3
    ) -> List[SeriesCandidate]:
        """
        P2-18: Detecta series educativas en una lista de videos.
        Args:
            videos: Lista de videos a analizar
            min_videos: Mínimo de videos para formar serie
        Returns:
            Lista de SeriesCandidate
        """
        self._detection_count += 1

        series_map = defaultdict(list)

        for video in videos:
            title = video.get('title', '')
            series_info = self._extract_series_info(title)

            if series_info:
                series_key = series_info['series_name'].lower()
                series_info['video'] = video
                series_map[series_key].append(series_info)

        candidates = []

        for series_name, parts in series_map.items():
            if len(parts) >= min_videos:
                parts.sort(key=lambda p: p['part_number'])

                consistency = self._calculate_consistency(parts)

                videos_in_series = [p['video'] for p in parts]

                is_complete = self._check_completeness(parts)

                candidate = SeriesCandidate(
                    series_name=series_name,
                    video_count=len(parts),
                    consistency_score=round(consistency, 2),
                    videos=videos_in_series,
                    is_complete=is_complete
                )
                candidates.append(candidate)

        candidates.sort(key=lambda c: c.video_count, reverse=True)
        return candidates

    def _extract_series_info(self, title: str) -> Optional[Dict]:
        """Extrae información de serie de un título."""
        import re

        for pattern in self.SERIES_PATTERNS:
            match = re.search(pattern, title.lower())
            if match:
                groups = match.groups()

                if len(groups) >= 2 and groups[1]:
                    part_number = int(groups[1])
                    series_name = title[:match.start()].strip()

                    if not series_name:
                        series_name = f"Serie parte {part_number}"
                    else:
                        series_name = series_name[:50]

                    return {
                        'series_name': series_name,
                        'part_number': part_number,
                        'raw_match': match.group()
                    }

        return None

    def _calculate_consistency(self, parts: List[Dict]) -> float:
        """Calcula score de consistencia de la serie."""
        if len(parts) < 2:
            return 1.0

        numbers = [p['part_number'] for p in parts]

        expected = list(range(min(numbers), max(numbers) + 1))
        covered = len(set(numbers) & set(expected))
        completeness = covered / len(expected) if expected else 0

        gaps = sum(1 for n in expected if n not in numbers)
        gap_penalty = gaps * 0.1

        consistency = completeness - gap_penalty
        return max(0, min(consistency, 1.0))

    def _check_completeness(self, parts: List[Dict]) -> bool:
        """Verifica si la serie está completa."""
        if len(parts) < 3:
            return False

        numbers = [p['part_number'] for p in parts]
        return max(numbers) - min(numbers) + 1 == len(numbers)

    def get_series_suggestion(
        self,
        series: SeriesCandidate
    ) -> str:
        """Genera sugerencia basada en la serie detectada."""
        if series.is_complete:
            return f"Serie completa ({series.video_count} videos) - Procesar en orden"

        next_part = series.video_count + 1
        return f"Serie en progreso - {series.video_count} partes, buscar parte {next_part}"

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del detector."""
        return {
            "total_detected": self._detection_count,
            "cached_series": len(self._series_cache),
            "model": "SeriesDetector v1.0"
        }


def create_series_detector() -> SeriesDetector:
    """Crea una instancia del detector de series."""
    return SeriesDetector()


_global_detector: Optional[SeriesDetector] = None


def get_series_detector() -> SeriesDetector:
    """Obtiene la instancia global del detector."""
    global _global_detector
    if _global_detector is None:
        _global_detector = create_series_detector()
    return _global_detector