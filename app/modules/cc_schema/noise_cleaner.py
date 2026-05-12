"""
CC Schema Monitor - Módulo 16: Protocolo de Limpieza de Ruido
==============================================================
Elimina timestamps, marcas de hablante, artefactos de auto-captions
y texto promocional repetitivo pre-análisis.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NoiseType(Enum):
    TIMESTAMP = "timestamp"
    SPEAKER_TAG = "speaker_tag"
    AUTO_CAPTION_ARTIFACT = "auto_caption_artifact"
    PROMOTIONAL = "promotional"
    FILLER = "filler"
    REPETITIVE = "repetitive"
    UNKNOWN = "unknown"


@dataclass
class CleaningResult:
    original_length: int
    cleaned_length: int
    removed_count: int
    noise_types_removed: Dict[str, int]
    issues_fixed: List[str]


class NoiseCleaner:
    """
    Protocolo de Limpieza de Ruido
    Elimina timestamps, marcas de hablante, artefactos de auto-captions
    y texto promocional repetitivo.
    """

    TIMESTAMP_PATTERNS = [
        r'\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{3})?\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{3})?',
        r'\[\d{2}:\d{2}(?::\d{2})?\]',
        r'\(\d{1,2}:\d{2}(?::\d{2})?\)',
        r'\d{1,2}:\d{2}:\d{2}',
    ]

    SPEAKER_PATTERNS = [
        r'\[Speaker\s*\d*\]',
        r'\[S\d+\]',
        r'<v\s+[^>]+>',
        r'</v>',
        r'♪[^♪]+♪',
        r'\[Music\]',
        r'\[Applause\]',
        r'\[Laughter\]',
        r'\(Applause\)',
        r'\(Laughter\)',
    ]

    AUTO_CAPTION_PATTERNS = [
        r'\[Music playing\]',
        r'\[Intro music\]',
        r'\[Outro music\]',
        r'\([\w\s]+music\)',
        r'\[.*?\]',
        r'\([^)]*\)',
    ]

    PROMOTIONAL_PATTERNS = [
        r'subscribe\s+to',
        r'like\s+and\s+share',
        r'don\'t\s+forget\s+to',
        r'follow\s+me\s+on',
        r'link\s+in\s+description',
        r'check\s+out\s+my',
        r'visit\s+my\s+',
        r'follow\s+on\s+',
        r'follow\s+on\s+instagram',
        r'follow\s+on\s+twitter',
        r'youtube\.com/',
        r'twitter\.com/',
        r'instagram\.com/',
    ]

    FILLER_PATTERNS = [
        r'\b(uh|um|uhm|ah|er)\b',
        r'\b(mmm|okay|so|like|well)\b(?:\s+\1\b){2,}',
        r'\.{3,}',
        r',,{2,}',
    ]

    def __init__(self, aggressive: bool = False):
        self.aggressive = aggressive
        self._stats = {
            'total_cleaned': 0,
            'timestamps_removed': 0,
            'speakers_removed': 0,
            'promo_removed': 0,
            'filler_removed': 0,
        }

    def clean(self, content: str) -> str:
        """
        Limpia el contenido de ruido.

        Args:
            content: Texto a limpiar

        Returns:
            Texto limpio
        """
        self._stats['total_cleaned'] += 1
        cleaned = content

        for pattern in self.TIMESTAMP_PATTERNS:
            matches = len(re.findall(pattern, cleaned))
            cleaned = re.sub(pattern, ' ', cleaned)
            self._stats['timestamps_removed'] += matches

        for pattern in self.SPEAKER_PATTERNS:
            matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
            self._stats['speakers_removed'] += matches

        if self.aggressive:
            for pattern in self.AUTO_CAPTION_PATTERNS:
                matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
                cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
                self._stats['speakers_removed'] += matches

        for pattern in self.PROMOTIONAL_PATTERNS:
            matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
            self._stats['promo_removed'] += matches

        for pattern in self.FILLER_PATTERNS:
            matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
            self._stats['filler_removed'] += matches

        cleaned = self._clean_whitespace(cleaned)

        return cleaned

    def clean_detailed(self, content: str) -> CleaningResult:
        """
        Limpia con reporte detallado.

        Args:
            content: Texto a limpiar

        Returns:
            CleaningResult con estadísticas
        """
        original_length = len(content)
        noise_types = {}

        cleaned = content

        removed = 0
        for pattern in self.TIMESTAMP_PATTERNS:
            matches = len(re.findall(pattern, cleaned))
            cleaned = re.sub(pattern, ' ', cleaned)
            removed += matches
        noise_types['timestamp'] = removed

        removed = 0
        for pattern in self.SPEAKER_PATTERNS:
            matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
            removed += matches
        noise_types['speaker_tag'] = removed

        removed = 0
        for pattern in self.PROMOTIONAL_PATTERNS:
            matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
            removed += matches
        noise_types['promotional'] = removed

        removed = 0
        for pattern in self.FILLER_PATTERNS:
            matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
            removed += matches
        noise_types['filler'] = removed

        cleaned = self._clean_whitespace(cleaned)
        cleaned_length = len(cleaned)

        total_removed = sum(noise_types.values())
        issues_fixed = []
        for noise_type, count in noise_types.items():
            if count > 0:
                issues_fixed.append(f"{noise_type}: {count}")

        return CleaningResult(
            original_length=original_length,
            cleaned_length=cleaned_length,
            removed_count=total_removed,
            noise_types_removed=noise_types,
            issues_fixed=issues_fixed
        )

    def _clean_whitespace(self, text: str) -> str:
        """Limpia espacios en blanco."""
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_cleaned': 0,
            'timestamps_removed': 0,
            'speakers_removed': 0,
            'promo_removed': 0,
            'filler_removed': 0,
        }


def create_cleaner(aggressive: bool = False) -> NoiseCleaner:
    """
    Factory function para crear el cleaner.
    """
    return NoiseCleaner(aggressive=aggressive)


def quick_clean(content: str) -> str:
    """
    Función de conveniencia para limpieza rápida.
    """
    cleaner = NoiseCleaner()
    return cleaner.clean(content)