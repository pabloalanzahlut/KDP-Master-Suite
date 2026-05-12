"""
CC Schema Monitor - Módulo 6: Filtro de Calidad de Subtítulos
==============================================================
Descarta auto-generated captions con <80% precisión, sin timestamps válidos
o con densidad <50 palabras/min.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    REJECTED = "rejected"


@dataclass
class QualityMetrics:
    word_density: float
    timestamp_coverage: float
    has_valid_timestamps: bool
    average_words_per_subtitle: float
    filler_ratio: float
    auto_generated: bool
    overall_score: float
    rejection_reasons: List[str]


@dataclass
class QualityFilterResult:
    passed: bool
    quality_level: QualityLevel
    metrics: QualityMetrics
    recommendation: str
    warnings: List[str]


class SubtitleQualityFilter:
    """
    Filtro de Calidad de Subtítulos
    Descarta auto-generated captions con baja calidad.
    """

    MIN_WORD_DENSITY = 50
    MIN_TIMESTAMP_COVERAGE = 0.7
    MIN_AVG_WORDS_PER_SUB = 3
    MAX_FILLER_RATIO = 0.4
    MIN_QUALITY_SCORE = 0.6

    FILLER_PATTERNS = [
        r'\b(mmm|mmm\.|uh|uhh|uhm|uhmm|ah|ahh)\b',
        r'\b(lets|okay|ok|so|well|like)\b',
        r'\[\s*\]',
        r'\(\s*\)',
    ]

    TIMESTAMP_PATTERN = re.compile(
        r'\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{3})?\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{3})?'
    )

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._stats = {
            'total_checked': 0,
            'passed': 0,
            'rejected': 0,
            'by_auto_gen': 0,
            'by_low_density': 0,
            'by_timestamps': 0
        }

    def analyze_quality(self, content: str, is_auto_generated: bool = False) -> QualityMetrics:
        """
        Analiza la calidad del contenido de subtítulos.

        Args:
            content: Texto de subtítulos
            is_auto_generated: Si los subtítulos son auto-generados

        Returns:
            QualityMetrics con análisis detallado
        """
        self._stats['total_checked'] += 1

        lines = [l.strip() for l in content.split('\n') if l.strip()]
        timestamps = self._extract_timestamps(content)
        text_lines = [l for l in lines if not self._is_timestamp_line(l)]

        word_count = sum(len(l.split()) for l in text_lines)
        subtitle_count = len([l for l in text_lines if l and not l.startswith('<')])

        word_density = (word_count / max(subtitle_count, 1)) if subtitle_count > 0 else 0

        timestamp_coverage = len(timestamps) / max(subtitle_count, 1) if subtitle_count > 0 else 0

        has_valid_timestamps = len(timestamps) > 0 and all(
            self._validate_timestamp(ts) for ts in timestamps[:10]
        )

        avg_words_per_sub = word_density

        filler_count = self._count_fillers(content)
        filler_ratio = filler_count / max(word_count, 1) if word_count > 0 else 0

        base_score = 0.5
        if is_auto_generated:
            base_score -= 0.2

        score_adjustments = [
            (word_density >= 50, 0.15),
            (word_density >= 30, 0.1),
            (timestamp_coverage >= 0.8, 0.1),
            (has_valid_timestamps, 0.1),
            (avg_words_per_sub >= 5, 0.1),
            (filler_ratio <= 0.1, 0.05),
        ]

        for condition, adjustment in score_adjustments:
            if condition:
                base_score += adjustment

        overall_score = min(max(base_score, 0.0), 1.0)

        rejection_reasons = []
        if is_auto_generated and overall_score < 0.7:
            rejection_reasons.append("auto_generated_low_quality")
        if word_density < self.MIN_WORD_DENSITY:
            rejection_reasons.append(f"low_word_density:{word_density:.1f}")
        if not has_valid_timestamps and timestamp_coverage < 0.3:
            rejection_reasons.append("invalid_timestamps")
        if avg_words_per_sub < self.MIN_AVG_WORDS_PER_SUB:
            rejection_reasons.append(f"low_words_per_sub:{avg_words_per_sub:.1f}")
        if filler_ratio > self.MAX_FILLER_RATIO:
            rejection_reasons.append(f"high_filler_ratio:{filler_ratio:.2f}")

        return QualityMetrics(
            word_density=word_density,
            timestamp_coverage=timestamp_coverage,
            has_valid_timestamps=has_valid_timestamps,
            average_words_per_subtitle=avg_words_per_sub,
            filler_ratio=filler_ratio,
            auto_generated=is_auto_generated,
            overall_score=overall_score,
            rejection_reasons=rejection_reasons
        )

    def filter(self, content: str, is_auto_generated: bool = False) -> QualityFilterResult:
        """
        Filtra subtítulos según criterios de calidad.

        Args:
            content: Texto de subtítulos
            is_auto_generated: Si son auto-generados

        Returns:
            QualityFilterResult con decisión de filtrado
        """
        metrics = self.analyze_quality(content, is_auto_generated)

        warnings = []
        recommendations = []
        rejection_reasons = []

        passed = True
        quality_level = QualityLevel.GOOD

        if is_auto_generated and metrics.overall_score < 0.7:
            if self.strict_mode:
                passed = False
                self._stats['by_auto_gen'] += 1
                rejection_reasons.append("Auto-generated with quality below threshold")
            else:
                warnings.append("Auto-generated subtitles - verify accuracy")

        if metrics.word_density < self.MIN_WORD_DENSITY:
            warnings.append(f"Low word density: {metrics.word_density:.1f} words/min")
            if metrics.word_density < self.MIN_WORD_DENSITY * 0.5:
                passed = False
                self._stats['by_low_density'] += 1
                rejection_reasons.append(f"Word density too low: {metrics.word_density:.1f}")

        if not metrics.has_valid_timestamps and not metrics.timestamp_coverage:
            warnings.append("No valid timestamps found")
            if self.strict_mode:
                passed = False
                self._stats['by_timestamps'] += 1
                rejection_reasons.append("Missing valid timestamps")

        if metrics.filler_ratio > self.MAX_FILLER_RATIO:
            warnings.append(f"High filler ratio: {metrics.filler_ratio:.2%}")

        if metrics.overall_score < self.MIN_QUALITY_SCORE:
            passed = False
            self._stats['rejected'] += 1
        else:
            self._stats['passed'] += 1

        if metrics.overall_score >= 0.85:
            quality_level = QualityLevel.EXCELLENT
            recommendations.append("Excellent quality - high reliability")
        elif metrics.overall_score >= 0.7:
            quality_level = QualityLevel.GOOD
            recommendations.append("Good quality - suitable for processing")
        elif metrics.overall_score >= self.MIN_QUALITY_SCORE:
            quality_level = QualityLevel.ACCEPTABLE
            recommendations.append("Acceptable quality - proceed with caution")
        else:
            quality_level = QualityLevel.POOR if metrics.overall_score >= 0.4 else QualityLevel.REJECTED
            recommendations.append("Poor quality - consider manual review")

        if not passed:
            recommendations.append("REJECTED: " + "; ".join(rejection_reasons))

        return QualityFilterResult(
            passed=passed,
            quality_level=quality_level,
            metrics=metrics,
            recommendation=" | ".join(recommendations),
            warnings=warnings
        )

    def _extract_timestamps(self, content: str) -> List[str]:
        """Extrae timestamps del contenido."""
        return self.TIMESTAMP_PATTERN.findall(content)

    def _is_timestamp_line(self, line: str) -> bool:
        """Verifica si una línea es un timestamp."""
        return bool(self.TIMESTAMP_PATTERN.match(line.strip()))

    def _validate_timestamp(self, ts: str) -> bool:
        """Valida formato de timestamp."""
        try:
            parts = re.split(r'[-:.,]', ts.replace('-->', '').strip())
            parts = [p for p in parts if p]
            if len(parts) >= 4:
                minutes = int(parts[1]) if len(parts) > 1 else 0
                return minutes >= 0
            return False
        except (ValueError, IndexError):
            return False

    def _count_fillers(self, content: str) -> int:
        """Cuenta palabras de relleno (filler)."""
        total = 0
        for pattern in self.FILLER_PATTERNS:
            total += len(re.findall(pattern, content.lower()))
        return total

    def get_stats(self) -> dict:
        """Retorna estadísticas del filtro."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_checked': 0,
            'passed': 0,
            'rejected': 0,
            'by_auto_gen': 0,
            'by_low_density': 0,
            'by_timestamps': 0
        }


def create_filter(strict: bool = False) -> SubtitleQualityFilter:
    """
    Factory function para crear el filtro.
    """
    return SubtitleQualityFilter(strict_mode=strict)


def quick_quality_check(content: str, is_auto: bool = False) -> Tuple[bool, float]:
    """
    Función de conveniencia para check rápido.
    Retorna (passed, score)
    """
    filter = SubtitleQualityFilter()
    result = filter.filter(content, is_auto)
    return result.passed, result.metrics.overall_score