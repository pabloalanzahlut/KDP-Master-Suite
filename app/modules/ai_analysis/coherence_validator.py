"""
AI Analysis - Coherence Validator
=================================
Módulo 30: Valida coherencia temática del contenido.
Usa Ollama para análisis semántico.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class CoherenceResult:
    is_coherent: bool
    focus_topic: str
    coherence_score: float
    topic_shifts: List[str]
    unrelated_segments: List[Tuple[int, int]]
    recommendations: List[str]


class CoherenceValidator:
    """
    Validador de coherencia temática.
    Detecta cambios de tema y segmentos no relacionados.
    """

    STOPWORDS = {
        'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'al', 'a',
        'en', 'con', 'por', 'para', 'sin', 'sobre', 'entre', 'que', 'y',
        'e', 'o', 'u', 'pero', 'si', 'no', 'se', 'su', 'sus', 'es', 'son',
        'está', 'están', 'fue', 'fueron', 'ser', 'estar', 'hay', 'ha'
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def validate(self, text: str, chunks: Optional[List[str]] = None) -> CoherenceResult:
        """
        Valida coherencia del contenido.

        Args:
            text: Texto completo a validar
            chunks: Segmentos opcionales (para análisis granular)

        Returns:
            CoherenceResult con análisis de coherencia
        """
        if chunks is None:
            chunks = self._split_into_chunks(text)

        if self.ai_client and self.ai_client.is_available():
            return self._validate_with_ai(text, chunks)
        return self._validate_fallback(text, chunks)

    def _validate_with_ai(self, text: str, chunks: List[str]) -> CoherenceResult:
        """Valida usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "coherence")
            if result.success:
                parsed = result.metadata
                return CoherenceResult(
                    is_coherent=parsed.get('coherent', True),
                    focus_topic=parsed.get('focus', 'general'),
                    coherence_score=parsed.get('score', 0.7),
                    topic_shifts=parsed.get('shifts', []),
                    unrelated_segments=parsed.get('unrelated', []),
                    recommendations=parsed.get('recommendations', [])
                )
        except Exception as e:
            logger.warning(f"AI coherence validation failed: {e}")
        return self._validate_fallback(text, chunks)

    def _validate_fallback(self, text: str, chunks: List[str]) -> CoherenceResult:
        """Valida usando análisis de keywords."""
        if len(chunks) <= 1:
            return CoherenceResult(
                is_coherent=True,
                focus_topic=self._extract_main_topic(chunks[0] if chunks else text),
                coherence_score=1.0,
                topic_shifts=[],
                unrelated_segments=[],
                recommendations=[]
            )

        chunk_topics = [self._extract_main_topic(chunk) for chunk in chunks]
        topic_changes = self._detect_topic_changes(chunks)

        coherence_score = 1.0
        if topic_changes:
            coherence_score = max(0.3, 1.0 - (len(topic_changes) * 0.15))

        unrelated = []
        for i, topic in enumerate(chunk_topics):
            if topic != chunk_topics[0] and topic not in self._get_related_topics(chunk_topics[0]):
                unrelated.append((i, i + 1))

        recommendations = []
        if coherence_score < 0.7:
            recommendations.append("Considerar separar segmentos con temas diferentes")
        if len(topic_changes) > 3:
            recommendations.append("El contenido cambia mucho de tema, revisar estructura")

        return CoherenceResult(
            is_coherent=coherence_score >= 0.5,
            focus_topic=chunk_topics[0] if chunk_topics else 'general',
            coherence_score=coherence_score,
            topic_shifts=topic_changes,
            unrelated_segments=unrelated,
            recommendations=recommendations
        )

    def _split_into_chunks(self, text: str) -> List[str]:
        """Divide texto en chunks por párrafos."""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs if paragraphs else [text]

    def _extract_main_topic(self, text: str) -> str:
        """Extrae tema principal de un texto."""
        words = re.findall(r'\b[a-záéíóúñü]{4,}\b', text.lower())
        words = [w for w in words if w not in self.STOPWORDS]

        if not words:
            return 'general'

        word_freq = Counter(words)
        top_words = word_freq.most_common(5)

        return top_words[0][0] if top_words else 'general'

    def _detect_topic_changes(self, chunks: List[str]) -> List[str]:
        """Detecta cambios de tema entre chunks."""
        if len(chunks) < 2:
            return []

        topics = [self._extract_main_topic(chunk) for chunk in chunks]
        changes = []

        for i in range(1, len(topics)):
            if topics[i] != topics[i-1]:
                changes.append(f"Cambio de '{topics[i-1]}' a '{topics[i]}' en segmento {i}")

        return changes

    def _get_related_topics(self, topic: str) -> List[str]:
        """Obtiene temas relacionados semánticamente."""
        related_map = {
            'marketing': ['estrategia', 'campaña', 'publicidad', 'contenido', 'seo'],
            'ventas': ['cliente', 'lead', 'conversión', 'negociación', 'cierre'],
            'finanzas': ['ingreso', 'gasto', 'inversión', 'rentabilidad', 'presupuesto'],
            'negocios': ['empresa', 'modelo', 'plan', 'crecimiento', 'estrategia'],
            'tecnología': ['software', 'herramienta', 'plataforma', 'sistema', 'digital'],
        }
        return related_map.get(topic, [topic])

    def batch_validate(self, texts: List[str]) -> List[CoherenceResult]:
        """Valida múltiples textos."""
        return [self.validate(t) for t in texts]

    def get_average_coherence(self, results: List[CoherenceResult]) -> float:
        """Calcula coherencia promedio de múltiples resultados."""
        if not results:
            return 0.0
        return sum(r.coherence_score for r in results) / len(results)