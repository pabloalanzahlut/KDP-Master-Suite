"""
AI Analysis - Content Type Classifier
======================================
Módulo 26: Clasificador de tipo de contenido (Tutorial, Caso Estudio, Teoría, etc.)
Usa Ollama para análisis semántico.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(Enum):
    TUTORIAL = "tutorial"
    CASE_STUDY = "case_study"
    THEORY = "theory"
    LIST = "list"
    INTERVIEW = "interview"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


@dataclass
class ContentTypeResult:
    content_type: ContentType
    confidence: float
    reasoning: str
    subtypes: list
    keywords: list


class ContentTypeClassifier:
    """
    Clasificador de tipo de contenido usando IA.
    Fallback con heurísticas cuando Ollama no disponible.
    """

    FALLBACK_PATTERNS = {
        ContentType.TUTORIAL: [
            r'pasos?\s+para', r'cómo\s+(?:hacer|crear|instalar)',
            r'tutorial', r'guía\s+de', r'instrucciones?',
            r'primeros?\s+pasos', r'empezar', r'paso\s+\d+'
        ],
        ContentType.CASE_STUDY: [
            r'caso\s+de\s+estudio', r'caso\s+práctico', r'ejemplo\s+real',
            r'cliente\s+que', r'empresa\s+que', r'resultados?\s+de',
            r'mejor[óo]\s+\d+', r'aumento\s+del', r'redujo\s+'
        ],
        ContentType.THEORY: [
            r'concepto\s+de', r'principios?\s+de', r'fundamentos?\s+de',
            r'teor[íi]a\s+de', r'modelo\s+de', r'marco\s+teórico',
            r'base\s+cient[íi]fica', r' investigaci[óo]n\s+'
        ],
        ContentType.LIST: [
            r'\d+\s+(?:razones?|tips?|consejos?|estrategias?|pasos?|puntos?)',
            r'lista\s+de', r'top\s+\d+', r'los\s+\d+\s+mejores?',
            r'pros?\s+y\s+cons', r'comparaci[óo]n\s+de'
        ],
        ContentType.INTERVIEW: [
            r'entrevista\s+con', r'conversaci[óo]n\s+con',
            r'dijo\s+(?:que|sobre|acerca)', r'coment[óo]\s+(?:que|sobre)',
            r'expert[oe]\s+(?:dice|señal[óo]|explica)'
        ],
        ContentType.REFERENCE: [
            r' seg[úu]n\s+', r'fuente\s+:', r'referencia\s+',
            r'datos?\s+de\s+', r'estad[íi]sticas?\s+', r'cifras?\s+'
        ]
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def classify(self, text: str, metadata: Optional[Dict] = None) -> ContentTypeResult:
        """
        Clasifica el tipo de contenido.

        Args:
            text: Texto a clasificar
            metadata: Metadata adicional (opcional)

        Returns:
            ContentTypeResult con tipo y confianza
        """
        if self.ai_client and self.ai_client.is_available():
            return self._classify_with_ai(text)
        return self._classify_fallback(text)

    def _classify_with_ai(self, text: str) -> ContentTypeResult:
        """Clasifica usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "type")
            if result.success:
                parsed = result.metadata
                content_type = ContentType(parsed.get('type', 'unknown').lower())
                return ContentTypeResult(
                    content_type=content_type,
                    confidence=parsed.get('confidence', 0.5),
                    reasoning=parsed.get('reason', 'Clasificado por IA'),
                    subtypes=parsed.get('subtypes', []),
                    keywords=parsed.get('keywords', [])
                )
        except Exception as e:
            logger.warning(f"AI classification failed: {e}")
        return self._classify_fallback(text)

    def _classify_fallback(self, text: str) -> ContentTypeResult:
        """Clasifica usando heurísticas."""
        text_lower = text.lower()
        scores = {}

        for content_type, patterns in self.FALLBACK_PATTERNS.items():
            import re
            matches = sum(1 for p in patterns if re.search(p, text_lower, re.IGNORECASE))
            scores[content_type] = matches

        if scores:
            best_type = max(scores, key=scores.get)
            max_score = scores[best_type]
            confidence = min(0.9, 0.4 + (max_score * 0.15))

            if max_score == 0:
                return ContentTypeResult(
                    content_type=ContentType.UNKNOWN,
                    confidence=0.3,
                    reasoning="No se detectaron patrones específicos",
                    subtypes=[],
                    keywords=[]
                )

            return ContentTypeResult(
                content_type=best_type,
                confidence=confidence,
                reasoning=f"Detectado por {max_score} patrones de {best_type.value}",
                subtypes=[],
                keywords=[]
            )

        return ContentTypeResult(
            content_type=ContentType.UNKNOWN,
            confidence=0.3,
            reasoning="Sin clasificación",
            subtypes=[],
            keywords=[]
        )

    def batch_classify(self, texts: list) -> list:
        """Clasifica múltiples textos."""
        return [self.classify(t) for t in texts]