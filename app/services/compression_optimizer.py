"""
P4-40 (avanzado): Optimizador de Compresión por Tipo de Contenido
Optimiza la compresión basándose en el tipo de contenido.
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CompressionOptimizer:
    """Optimizador de compresión por tipo de contenido."""

    COMPRESSION_LEVELS = {
        'tutorial': 3,
        'interview': 5,
        'review': 4,
        'podcast': 6,
        'default': 4
    }

    def get_optimal_settings(
        self,
        content_type: str,
        transcript_length: int
    ) -> Dict:
        """
        Obtiene configuración óptima de compresión.
        Returns: Dict con level, method, estimated_ratio
        """
        level = self.COMPRESSION_LEVELS.get(content_type, self.COMPRESSION_LEVELS['default'])

        if transcript_length > 50000:
            method = 'gzip'
            estimated_ratio = 0.7
        elif transcript_length > 20000:
            method = 'zstd'
            estimated_ratio = 0.6
        else:
            method = 'none'
            estimated_ratio = 1.0

        return {
            'content_type': content_type,
            'compression_level': level,
            'method': method,
            'estimated_ratio': estimated_ratio,
            'will_compress': method != 'none'
        }

    def estimate_savings(self, transcript_length: int, method: str) -> int:
        """Estima bytes ahorrados."""
        if method == 'none':
            return 0
        if method == 'gzip':
            return int(transcript_length * 0.3)
        return int(transcript_length * 0.4)


def get_compression_optimizer():
    return CompressionOptimizer()