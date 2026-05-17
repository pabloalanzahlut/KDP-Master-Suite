"""
P4-40: Compresión Predictiva de Transcripciones
Sugiere comprimir transcripciones largas.
"""
import re
from typing import Dict


class TranscriptCompressor:
    """Compresor predictivo de transcripciones."""

    LARGE_THRESHOLD_CHARS = 50000
    MEDIUM_THRESHOLD_CHARS = 20000

    def should_compress(
        self,
        transcript: str,
        estimated_processing_time_minutes: int = 0
    ) -> Dict:
        """
        Determina si una transcripción debe comprimirse.
        Returns: Dict con recommendation, reason, estimated_savings
        """
        char_count = len(transcript)

        if char_count > self.LARGE_THRESHOLD_CHARS:
            recommendation = 'compress'
            reason = f'Transcripción muy grande ({char_count} chars)'
            savings_percent = 60
        elif char_count > self.MEDIUM_THRESHOLD_CHARS:
            recommendation = 'consider'
            reason = f'Transcripción grande ({char_count} chars)'
            savings_percent = 40
        else:
            recommendation = 'no_compress'
            reason = f'Tamaño óptimo ({char_count} chars)'
            savings_percent = 0

        if estimated_processing_time_minutes > 30 and recommendation != 'compress':
            recommendation = 'compress'
            reason += ' - procesamiento largo'
            savings_percent += 20

        return {
            'recommendation': recommendation,
            'reason': reason,
            'char_count': char_count,
            'estimated_savings_percent': savings_percent,
            'method': 'gzip' if recommendation == 'compress' else None
        }

    def compress(self, text: str, level: int = 6) -> bytes:
        """Comprime texto usando gzip."""
        import gzip
        return gzip.compress(text.encode('utf-8'), compresslevel=level)

    def decompress(self, data: bytes) -> str:
        """Descomprime texto."""
        import gzip
        return gzip.decompress(data).decode('utf-8')


def get_transcript_compressor():
    return TranscriptCompressor()