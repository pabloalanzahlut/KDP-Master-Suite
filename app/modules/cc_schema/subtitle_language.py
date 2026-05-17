"""
Subtitle Language Detector - Módulo 28 de URL Intelligence
==========================================================
Detecta idiomas disponibles de subtítulos.
Filtrar videos sin subtítulos en idioma deseado.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


LANGUAGE_MAP = {
    'en': 'English',
    'es': 'Spanish',
    'pt': 'Portuguese',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'nl': 'Dutch',
    'pl': 'Polish',
    'tr': 'Turkish',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
}


@dataclass
class SubtitleLanguageResult:
    languages: List[str]
    language_names: List[str]
    has_target_language: bool
    is_valid: bool
    error: Optional[str]


class SubtitleLanguageDetector:
    """
    Detector de idiomas de subtítulos.
    Detecta y filtra por idioma deseado.
    """

    def __init__(self, target_languages: Optional[List[str]] = None):
        self.target_languages = target_languages or ['en', 'es']

    def detect(self, metadata: dict) -> SubtitleLanguageResult:
        """
        Detecta idiomas de subtítulos.

        Args:
            metadata: Metadatos del video

        Returns:
            SubtitleLanguageResult con idiomas detectados
        """
        subtitle_langs = metadata.get('subtitle_languages') or metadata.get('caption_languages') or []

        if isinstance(subtitle_langs, str):
            subtitle_langs = [subtitle_langs] if subtitle_langs else []

        languages = [lang.lower()[:2] for lang in subtitle_langs]
        language_names = [LANGUAGE_MAP.get(lang, lang.upper()) for lang in languages]

        has_target = any(lang in self.target_languages for lang in languages)

        return SubtitleLanguageResult(
            languages=languages,
            language_names=language_names,
            has_target_language=has_target,
            is_valid=bool(languages),
            error=None if languages else "No se detectaron idiomas"
        )

    def supports_language(self, metadata: dict, language: str) -> bool:
        """Verifica si soporta un idioma."""
        result = self.detect(metadata)
        return language.lower() in result.languages


def create_subtitle_language_detector(
    target_languages: Optional[List[str]] = None
) -> SubtitleLanguageDetector:
    """Factory function."""
    return SubtitleLanguageDetector(target_languages=target_languages)