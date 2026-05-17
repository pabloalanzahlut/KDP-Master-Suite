"""
P1-8: Detección de Patrocinios en Título
Detecta si el video tiene patrocinios o contenido comercial.
"""
import re
from typing import Dict, List


class SponsorDetector:
    """Detector de patrocinios en videos."""

    SPONSOR_PATTERNS = [
        r'patrocinad[oa]',
        r'sponsored',
        r'gift|regalo',
        r'colaborac',
        r'partner',
        r'ad\b',
        r'anuncio',
        r'promo[cóó]digo',
        r'afiliate',
        r'presented by',
        r'powered by',
        r'thanks to',
        r'gracias a'
    ]

    def __init__(self):
        self._detection_count = 0

    def detect(self, title: str, description: str = "") -> Dict:
        """
        Detecta patrocinios en título o descripción.
        Returns: Dict con is_sponsored, confidence, pattern_found
        """
        self._detection_count += 1

        content = f"{title.lower()} {description.lower()}"

        for pattern in self.SPONSOR_PATTERNS:
            if re.search(pattern, content):
                return {
                    'is_sponsored': True,
                    'confidence': 0.8,
                    'pattern': pattern,
                    'type': 'sponsor'
                }

        return {
            'is_sponsored': False,
            'confidence': 0.6,
            'pattern': None,
            'type': 'none'
        }

    def batch_detect(self, videos: List[Dict]) -> List[Dict]:
        """Detecta patrocinios en lista de videos."""
        return [
            {'video': v, 'detection': self.detect(v.get('title', ''), v.get('description', ''))}
            for v in videos
        ]


def get_sponsor_detector():
    return SponsorDetector()