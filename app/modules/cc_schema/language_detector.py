"""
CC Schema Monitor - Módulo 15: Detector de Idioma Automático
===========================================================
Identifica idioma del texto extraído (fastText local) para enrutamiento
a modelos Ollama correctos sin re-procesamiento.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)

LANGUAGE_CONFIDENCE_THRESHOLD = 0.6
MIN_TEXT_LENGTH = 20


@dataclass
class LanguageInfo:
    language: str
    code: str
    confidence: float
    alternatives: List[Tuple[str, float]]
    script: str


@dataclass
class DetectionResult:
    detected: bool
    primary: Optional[LanguageInfo]
    script_hint: str
    needs_transliteration: bool


class LanguageDetector:
    """
    Detector de Idioma Automático
    Identifica idioma del texto para enrutamiento a modelos correctos.
    """

    SCRIPT_RANGES = {
        'latin': (0x0041, 0x007A, 0x00C0, 0x024F),
        'cyrillic': (0x0400, 0x04FF),
        'cjk': (0x4E00, 0x9FFF),
        'arabic': (0x0600, 0x06FF),
        'hebrew': (0x0590, 0x05FF),
        'devanagari': (0x0900, 0x097F),
        'korean': (0xAC00, 0xAC00, 0xD7AF, 0xD7AF),
        'japanese': (0x3040, 0x309F, 0x30A0, 0x30FF),
    }

    COMMON_PATTERNS = {
        'es': [r'\b(el|la|los|las|un|una|de|que|es|en|con|por|para)\b', r'[áéíóúñü]', r'\b(¿|¡)\b'],
        'en': [r'\b(the|and|of|to|a|in|is|it|that|this|for)\b', r"\b(I am|do not|cannot|will not|it is)\b"],
        'de': [r'\b(der|die|das|ein|eine|und|ist|von|mit|für)\b', r'[ß]', r'\b(ö|ä|ü)\b'],
        'fr': [r'\b(le|la|les|un|une|de|du|et|est|que|pas)\b', r'[àâçéèêëîïôûùüÿœæ]', r'\b(c est|qu il)\b'],
        'pt': [r'\b(o|a|os|as|um|uma|de|que|é|em|com|para)\b', r'[ãõç]', r'\b(ao|oes)\b'],
        'ru': [r'[а-яА-ЯёЁ]', r'\b(это|что|не|в|на|с|по)\b'],
        'zh': [r'[\u4e00-\u9fff]', r'\b(的|是|不|了|在|人|有)\b'],
        'ja': [r'[\u3040-\u309f\u30a0-\u30ff]', r'\b(です|ます|した|して)\b'],
        'ko': [r'[\uac00-\ud7af]', r'\b(입니다|했습니다|합니다)\b'],
        'ar': [r'[\u0600-\u06ff]', r'\b(ال|في|من|على|أن)\b'],
        'hi': [r'[\u0900-\u097f]', r'\b(है|की|में|का|को)\b'],
    }

    LANGUAGE_NAMES = {
        'es': ('Spanish', 'es'),
        'en': ('English', 'en'),
        'de': ('German', 'de'),
        'fr': ('French', 'fr'),
        'pt': ('Portuguese', 'pt'),
        'ru': ('Russian', 'ru'),
        'zh': ('Chinese', 'zh'),
        'ja': ('Japanese', 'ja'),
        'ko': ('Korean', 'ko'),
        'ar': ('Arabic', 'ar'),
        'hi': ('Hindi', 'hi'),
        'it': ('Italian', 'it'),
        'nl': ('Dutch', 'nl'),
        'pl': ('Polish', 'pl'),
        'tr': ('Turkish', 'tr'),
        'vi': ('Vietnamese', 'vi'),
        'th': ('Thai', 'th'),
        'id': ('Indonesian', 'id'),
        'uk': ('Ukrainian', 'uk'),
        'sv': ('Swedish', 'sv'),
    }

    def __init__(self):
        self._stats = {
            'total_detections': 0,
            'high_confidence': 0,
            'low_confidence': 0,
            'script_detections': 0
        }

    def detect(self, text: str) -> DetectionResult:
        """
        Detecta el idioma del texto.

        Args:
            text: Texto a analizar

        Returns:
            DetectionResult con información del idioma
        """
        self._stats['total_detections'] += 1

        if len(text.strip()) < MIN_TEXT_LENGTH:
            return DetectionResult(
                detected=False,
                primary=None,
                script_hint="unknown",
                needs_transliteration=False
            )

        script_hint = self._detect_script(text)
        self._stats['script_detections'] += 1

        needs_transliteration = script_hint in ['cyrillic', 'arabic', 'cjk', 'korean', 'japanese', 'devanagari']

        lang_scores = self._score_languages(text)

        if not lang_scores:
            return DetectionResult(
                detected=False,
                primary=None,
                script_hint=script_hint,
                needs_transliteration=needs_transliteration
            )

        primary_lang, primary_score = max(lang_scores.items(), key=lambda x: x[1])
        alternatives = [(lang, score) for lang, score in sorted(lang_scores.items(), key=lambda x: -x[1]) if lang != primary_lang][:3]

        if primary_score >= LANGUAGE_CONFIDENCE_THRESHOLD:
            self._stats['high_confidence'] += 1
        else:
            self._stats['low_confidence'] += 1

        lang_name, lang_code = self.LANGUAGE_NAMES.get(primary_lang, (primary_lang, primary_lang))

        primary = LanguageInfo(
            language=lang_name,
            code=lang_code,
            confidence=primary_score,
            alternatives=alternatives,
            script=script_hint
        )

        return DetectionResult(
            detected=True,
            primary=primary,
            script_hint=script_hint,
            needs_transliteration=needs_transliteration
        )

    def _detect_script(self, text: str) -> str:
        """Detecta el script principal del texto."""
        script_counts = Counter()

        for char in text:
            code_point = ord(char)

            if 0x0041 <= code_point <= 0x007A or 0x00C0 <= code_point <= 0x024F:
                if ord('ñ') == code_point or 0x00E0 <= code_point <= 0x00FF:
                    script_counts['latin_spanish'] += 1
                else:
                    script_counts['latin'] += 1

            elif 0x0400 <= code_point <= 0x04FF:
                script_counts['cyrillic'] += 1

            elif 0x4E00 <= code_point <= 0x9FFF:
                script_counts['cjk'] += 1

            elif 0x0600 <= code_point <= 0x06FF:
                script_counts['arabic'] += 1

            elif 0x0590 <= code_point <= 0x05FF:
                script_counts['hebrew'] += 1

            elif 0x0900 <= code_point <= 0x097F:
                script_counts['devanagari'] += 1

            elif 0x3040 <= code_point <= 0x30FF:
                script_counts['japanese'] += 1

            elif 0xAC00 <= code_point <= 0xD7AF:
                script_counts['korean'] += 1

        if not script_counts:
            return 'latin'

        most_common = script_counts.most_common(1)[0][0]

        if most_common in ['cjk', 'japanese', 'korean']:
            return most_common

        return 'latin' if 'latin' in most_common else most_common

    def _score_languages(self, text: str) -> Dict[str, float]:
        """Calcula scores de probabilidad para cada idioma."""
        scores = {}

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        for lang, patterns in self.COMMON_PATTERNS.items():
            matches = 0
            total_pattern_weight = 0

            for pattern in patterns:
                if re.search(pattern, text_lower):
                    matches += 1
                    total_pattern_weight += 1

            if matches > 0:
                base_score = matches / len(patterns)

                if words:
                    stopword_hits = 0
                    for word in words[:50]:
                        for pattern in patterns:
                            if re.search(r'\b' + re.escape(word) + r'\b', ' '.join(['the', 'and', 'el', 'la', 'der', 'die', 'le', 'la'])):
                                stopword_hits += 1
                                break

                    context_bonus = min(stopword_hits / max(len(words), 1), 0.3)
                    base_score = min(base_score + context_bonus, 1.0)

                scores[lang] = base_score

        total_score = sum(scores.values())
        if total_score > 0:
            for lang in scores:
                scores[lang] = scores[lang] / total_score

        return scores

    def get_supported_languages(self) -> List[str]:
        """Retorna lista de idiomas soportados."""
        return list(self.LANGUAGE_NAMES.keys())

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_detections': 0,
            'high_confidence': 0,
            'low_confidence': 0,
            'script_detections': 0
        }


class MultiLanguageSegmenter:
    """
    Segmenta texto en partes del mismo idioma.
    Útil para videos con múltiples idiomas.
    """

    def __init__(self):
        self.detector = LanguageDetector()

    def segment(self, text: str) -> List[Tuple[str, str]]:
        """
        Segmenta texto por idioma.

        Args:
            text: Texto a segmentar

        Returns:
            Lista de (idioma, segmento)
        """
        lines = text.split('\n')
        segments = []
        current_lang = None
        current_segment = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            result = self.detector.detect(line)
            lang = result.primary.code if result.primary else 'unknown'

            if lang != current_lang:
                if current_segment and current_lang:
                    segments.append((current_lang, '\n'.join(current_segment)))

                current_lang = lang
                current_segment = [line]
            else:
                current_segment.append(line)

        if current_segment and current_lang:
            segments.append((current_lang, '\n'.join(current_segment)))

        return segments


def create_detector() -> LanguageDetector:
    """
    Factory function para crear el detector.
    """
    return LanguageDetector()


def quick_detect(text: str) -> Optional[str]:
    """
    Función de conveniencia para detección rápida.
    Retorna código de idioma o None.
    """
    detector = LanguageDetector()
    result = detector.detect(text)
    return result.primary.code if result.primary else None