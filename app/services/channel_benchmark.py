"""
P6-54: Benchmarking entre Canales
Comparativa de calidad entre canales similares.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ChannelBenchmark:
    """Benchmark de canales."""

    def __init__(self):
        self._comparison_count = 0

    def compare_channels(
        self,
        channels: List[Dict]
    ) -> List[Dict]:
        """
        Compara múltiples canales.
        Returns: Lista de análisis comparativo
        """
        self._comparison_count += 1

        if len(channels) < 2:
            return [{'error': 'Se necesitan al menos 2 canales'}]

        results = []

        for ch in channels:
            video_count = ch.get('video_count', 0)
            avg_views = ch.get('avg_views', 0) or 0
            avg_likes = ch.get('avg_likes', 0) or 0

            relevance = ch.get('avg_relevance', 50) or 50
            quality_score = ch.get('quality_score', 50) or 50

            total_score = (
                (video_count / 100 * 0.1) +
                (avg_views / 10000 * 0.2) +
                (relevance * 0.35) +
                (quality_score * 0.35)
            )

            results.append({
                'channel_id': ch.get('id'),
                'channel_name': ch.get('name'),
                'video_count': video_count,
                'avg_views': avg_views,
                'total_score': round(total_score, 2),
                'rank': 0
            })

        results.sort(key=lambda x: x['total_score'], reverse=True)

        for i, r in enumerate(results):
            r['rank'] = i + 1

        return results

    def get_top_channel(self, channels: List[Dict]) -> Dict:
        """Retorna el mejor canal."""
        comparison = self.compare_channels(channels)
        return comparison[0] if comparison else {}


def get_channel_benchmark():
    return ChannelBenchmark()