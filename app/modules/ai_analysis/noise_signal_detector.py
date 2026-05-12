"""
AI Analysis - Módulo 22: Detector de Ruido vs Señal
====================================================
Identifica si el texto es contenido real educativo o solo
spam/promocional/clickbait usando análisis semántico local.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NoiseSignalResult:
    is_signal: bool
    confidence: float
    noise_types: List[str]
    signal_indicators: List[str]
    quality_score: float
    recommendation: str


class NoiseSignalDetector:
    """
    Detector de Ruido vs Señal
    Identifica contenido educativo real vs spam/promocional.
    """

    SPAM_PATTERNS = [
        r'subscribe\s+to\s+my\s+channel',
        r'like\s+and\s+share',
        r'don\'t\s+forget\s+to\s+subscribe',
        r'follow\s+me\s+on\s+instagram',
        r'link\s+in\s+description',
        r'subscribe\s+now',
        r'click\s+the\s+link',
        r'buy\s+now',
        r'limited\s+time\s+offer',
        r'100%\s+guarantee',
        r'special\s+price',
        r'act\s+now',
    ]

    CLICKBAIT_PATTERNS = [
        r'you\s+won\'t\s+believe',
        r'shocking\s+fact',
        r'amazing\s+trick',
        r'secret\s+revealed',
        r'best\s+kept\s+secret',
        r'game\s+changer',
        r'mind\s+blowing',
        r'literal',
        r'literally',
    ]

    PROMOTIONAL_PATTERNS = [
        r'\$\d+',
        r'special\s+discount',
        r'money\s+back',
        r'risk\s+free',
        r'bonus',
        r'free\s+gift',
        r'upgrade',
        r'premium',
    ]

    SIGNAL_INDICATORS = [
        r'step\s+by\s+step',
        r'tutorial',
        r'guide',
        r'example',
        r'how\s+to',
        r'instruction',
        r'method',
        r'technique',
        r'framework',
        r'strategy',
        r'analyse',
        r'estudio',
        r'caso\s+de\s+éxito',
        r'datos',
        r'evidencia',
    ]

    def __init__(self, ai_client=None):
        self._ai_client = ai_client
        self._stats = {
            'total_analyzed': 0,
            'signals_found': 0,
            'noise_found': 0
        }

    def detect(self, text: str) -> NoiseSignalResult:
        """
        Detecta ruido vs señal en el texto.

        Args:
            text: Texto a analizar

        Returns:
            NoiseSignalResult con análisis detallado
        """
        self._stats['total_analyzed'] += 1

        spam_score = self._score_spam(text)
        clickbait_score = self._score_clickbait(text)
        promo_score = self._score_promotional(text)

        signal_score = self._score_signal_indicators(text)

        ai_signal = None
        if self._ai_client and self._ai_client.is_available():
            result = self._ai_client.analyze(text, "noise")
            if result.success:
                ai_signal = result.metadata.get('signal', None)

        if ai_signal is not None:
            final_signal = ai_signal
        else:
            total_noise = spam_score + clickbait_score + promo_score
            final_signal = signal_score > total_noise

        confidence = self._calculate_confidence(
            spam_score, clickbait_score, promo_score, signal_score
        )

        quality_score = signal_score / max(spam_score + clickbait_score + promo_score + signal_score, 1)

        noise_types = self._identify_noise_types(text, spam_score, clickbait_score, promo_score)
        signal_indicators = self._find_signal_indicators(text)

        recommendation = self._generate_recommendation(final_signal, confidence, quality_score)

        if final_signal:
            self._stats['signals_found'] += 1
        else:
            self._stats['noise_found'] += 1

        return NoiseSignalResult(
            is_signal=final_signal,
            confidence=confidence,
            noise_types=noise_types,
            signal_indicators=signal_indicators[:5],
            quality_score=quality_score,
            recommendation=recommendation
        )

    def _score_spam(self, text: str) -> float:
        """Calcula score de spam."""
        text_lower = text.lower()
        spam_count = sum(1 for pattern in self.SPAM_PATTERNS if re.search(pattern, text_lower))
        return min(spam_count * 2, 10)

    def _score_clickbait(self, text: str) -> float:
        """Calcula score de clickbait."""
        text_lower = text.lower()
        clickbait_count = sum(1 for pattern in self.CLICKBAIT_PATTERNS if re.search(pattern, text_lower))
        return min(clickbait_count * 1.5, 10)

    def _score_promotional(self, text: str) -> float:
        """Calcula score promocional."""
        text_lower = text.lower()
        promo_count = sum(1 for pattern in self.PROMOTIONAL_PATTERNS if re.search(pattern, text_lower))
        return min(promo_count * 1.5, 10)

    def _score_signal_indicators(self, text: str) -> float:
        """Calcula score de indicadores de señal (contenido educativo)."""
        text_lower = text.lower()
        signal_count = sum(1 for pattern in self.SIGNAL_INDICATORS if re.search(pattern, text_lower))
        return min(signal_count * 2, 10)

    def _calculate_confidence(
        self,
        spam: float,
        clickbait: float,
        promo: float,
        signal: float
    ) -> float:
        """Calcula nivel de confianza del análisis."""
        total_noise = spam + clickbait + promo
        total_signal = signal

        if total_noise == 0 and total_signal == 0:
            return 0.5

        if total_signal > total_noise:
            return min(total_signal / (total_signal + total_noise + 1), 1.0)
        else:
            return min(total_noise / (total_signal + total_noise + 1), 1.0)

    def _identify_noise_types(
        self,
        text: str,
        spam: float,
        clickbait: float,
        promo: float
    ) -> List[str]:
        """Identifica tipos de ruido encontrados."""
        noise_types = []
        text_lower = text.lower()

        if spam > 2:
            noise_types.append("spam_call_to_action")

        if clickbait > 1.5:
            noise_types.append("clickbait_headlines")

        if promo > 1.5:
            noise_types.append("promotional_content")

        filler_count = len(re.findall(r'\b(uh|um|like|you know)\b', text_lower))
        if filler_count > 5:
            noise_types.append("excessive_filler")

        url_count = len(re.findall(r'https?://\S+', text))
        if url_count > 3:
            noise_types.append("excessive_links")

        return noise_types

    def _find_signal_indicators(self, text: str) -> List[str]:
        """Encuentra indicadores de señal educativa."""
        text_lower = text.lower()
        indicators = []

        for pattern in self.SIGNAL_INDICATORS:
            matches = re.findall(pattern, text_lower)
            if matches:
                indicators.extend(matches[:2])

        return list(set(indicators))[:10]

    def _generate_recommendation(
        self,
        is_signal: bool,
        confidence: float,
        quality_score: float
    ) -> str:
        """Genera recomendación basada en análisis."""
        if is_signal and confidence > 0.7:
            return "PROCESAR: Contenido educativo de alta calidad"
        elif is_signal and confidence > 0.5:
            return "PROCESAR CON FILTRO: Contenido mixto, requiere validación manual"
        elif not is_signal and confidence > 0.7:
            return "DESCARTAR: Principalmente ruido/promocional"
        else:
            return "REVISAR MANUAL: Análisis ambiguo, necesita validación humana"

    def batch_detect(self, texts: List[str]) -> List[NoiseSignalResult]:
        """Detecta en múltiples textos."""
        return [self.detect(text) for text in texts]

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        stats = self._stats.copy()
        if stats['total_analyzed'] > 0:
            stats['signal_ratio'] = stats['signals_found'] / stats['total_analyzed']
        else:
            stats['signal_ratio'] = 0.0
        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_analyzed': 0,
            'signals_found': 0,
            'noise_found': 0
        }


def create_detector(ai_client=None) -> NoiseSignalDetector:
    """
    Factory function para crear detector.
    """
    return NoiseSignalDetector(ai_client=ai_client)


def quick_detect(text: str) -> Tuple[bool, float]:
    """
    Función de conveniencia para detección rápida.
    Retorna (is_signal, confidence)
    """
    detector = NoiseSignalDetector()
    result = detector.detect(text)
    return result.is_signal, result.confidence