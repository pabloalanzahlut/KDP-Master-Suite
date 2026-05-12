"""
AI Analysis - Processing Time Predictor
=======================================
Módulo 35: Predice tiempo de procesamiento de chunks.
Usa Ollama para estimación inteligente.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TimePrediction:
    estimated_minutes: float
    confidence: float
    factors: List[str]
    breakdown: Dict[str, float]
    warnings: List[str]


class TimePredictor:
    """
    Predice tiempo de procesamiento de contenido.
    Estima minutos basándose en complejidad y factores.
    """

    BASE_TIMES = {
        'extraction': 0.5,
        'ai_analysis': 2.0,
        'validation': 0.3,
        'storage': 0.1
    }

    COMPLEXITY_MULTIPLIERS = {
        'low': 0.8,
        'medium': 1.0,
        'high': 1.5,
        'very_high': 2.0
    }

    CONTENT_TYPE_TIMES = {
        'video': 3.0,
        'article': 1.5,
        'tutorial': 2.0,
        'case_study': 2.5,
        'theory': 1.0,
        'reference': 0.8
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self._historical_data = []

    def predict(self, text: str, content_type: Optional[str] = None, metadata: Optional[Dict] = None) -> TimePrediction:
        """
        Predice tiempo de procesamiento.

        Args:
            text: Texto a procesar
            content_type: Tipo de contenido (video, article, etc.)
            metadata: Metadata adicional (opcional)

        Returns:
            TimePrediction con estimación de tiempo
        """
        if self.ai_client and self.ai_client.is_available():
            return self._predict_with_ai(text, content_type, metadata)
        return self._predict_fallback(text, content_type, metadata)

    def _predict_with_ai(self, text: str, content_type: Optional[str], metadata: Optional[Dict]) -> TimePrediction:
        """Predice usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "time")
            if result.success:
                parsed = result.metadata
                return TimePrediction(
                    estimated_minutes=parsed.get('estimated_minutes', 5.0),
                    confidence=0.85,
                    factors=parsed.get('factors', []),
                    breakdown=parsed.get('breakdown', {}),
                    warnings=parsed.get('warnings', [])
                )
        except Exception as e:
            logger.warning(f"AI time prediction failed: {e}")
        return self._predict_fallback(text, content_type, metadata)

    def _predict_fallback(self, text: str, content_type: Optional[str], metadata: Optional[Dict]) -> TimePrediction:
        """Predice usando heurísticas."""
        word_count = len(text.split())
        char_count = len(text)

        complexity = self._assess_complexity(text)

        base_time = self.BASE_TIMES['extraction']
        if metadata and metadata.get('requires_ai'):
            base_time += self.BASE_TIMES['ai_analysis']
        base_time += self.BASE_TIMES['validation'] + self.BASE_TIMES['storage']

        type_multiplier = 1.0
        if content_type:
            type_time = self.CONTENT_TYPE_TIMES.get(content_type.lower(), 1.5)
            base_time += type_time
        else:
            if word_count > 2000:
                type_multiplier *= 1.3
            elif word_count < 500:
                type_multiplier *= 0.8

        complexity_mult = self.COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)

        total_minutes = base_time * type_multiplier * complexity_mult

        breakdown = {
            'base_processing': round(base_time * 0.4, 2),
            'ai_analysis': round(base_time * 0.4 if metadata and metadata.get('requires_ai') else base_time * 0.2, 2),
            'validation': round(base_time * 0.15, 2),
            'storage': round(base_time * 0.05, 2)
        }

        factors = [
            f"{word_count} palabras detectadas",
            f"Complejidad: {complexity}",
            f"Tipo: {content_type or 'auto-detectado'}"
        ]

        warnings = []
        if word_count > 5000:
            warnings.append("Contenido extenso puede requerir más tiempo")
        if complexity == 'very_high':
            warnings.append("Alta complejidad detectada, considerar chunking")
        if metadata and metadata.get('has_media'):
            warnings.append("Contiene media que requiere procesamiento adicional")

        self._historical_data.append({
            'word_count': word_count,
            'estimated': total_minutes,
            'actual': None
        })

        return TimePrediction(
            estimated_minutes=round(total_minutes, 1),
            confidence=0.7 if content_type else 0.6,
            factors=factors,
            breakdown=breakdown,
            warnings=warnings
        )

    def _assess_complexity(self, text: str) -> str:
        """Evalúa complejidad del texto."""
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_len = len(text) / max(len(sentences), 1)

        technical_terms = len(re.findall(r'\b[A-Z]{2,}\b|\b\w+\.\w+\b|\b\w{15,}\b', text))

        code_blocks = len(re.findall(r'```|    |\t{2}', text))

        complexity_score = 0
        if avg_sentence_len > 40:
            complexity_score += 1
        if technical_terms > 10:
            complexity_score += 1
        if code_blocks > 2:
            complexity_score += 1
        if len(text) > 10000:
            complexity_score += 1

        if complexity_score <= 1:
            return 'low'
        elif complexity_score == 2:
            return 'medium'
        elif complexity_score == 3:
            return 'high'
        return 'very_high'

    def update_with_actual(self, estimated_minutes: float, actual_minutes: float):
        """Actualiza modelo con dato real."""
        for entry in self._historical_data:
            if abs(entry['estimated'] - estimated_minutes) < 0.5:
                entry['actual'] = actual_minutes
                break

    def batch_predict(self, texts: List[str]) -> List[TimePrediction]:
        """Predice tiempos para múltiples textos."""
        return [self.predict(t) for t in texts]

    def get_total_time(self, predictions: List[TimePrediction]) -> float:
        """Suma tiempos estimados."""
        return sum(p.estimated_minutes for p in predictions)

    def get_average_time(self, predictions: List[TimePrediction]) -> float:
        """Calcula tiempo promedio."""
        if not predictions:
            return 0.0
        return sum(p.estimated_minutes for p in predictions) / len(predictions)