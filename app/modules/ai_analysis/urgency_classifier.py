"""
AI Analysis - Urgency Classifier
================================
Módulo 33: Clasifica urgencia de procesamiento (ahora vs lote nocturno).
Usa Ollama para análisis de时效性.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ProcessingUrgency(Enum):
    NOW = "now"
    BATCH = "batch"
    DEFERRED = "deferred"


@dataclass
class UrgencyResult:
    urgency: ProcessingUrgency
    reason: str
    priority_score: float
    estimated_processing_time: int
    factors: list


class UrgencyClassifier:
    """
    Clasificador de urgencia de procesamiento.
    Decide si procesar ahora o en lote nocturno.
    """

    HIGH_URGENCY_KEYWORDS = [
        r'tendencia\s+actual', r'nuevo\s+lanzamiento', r'actualizaci[óo]n\s+de\s+(?:algoritmo|pol[íi]tica)',
        r'noticia\s+de[úu]ltima\s+hora', r'urgente', r'emergencia',
        r'cambio\s+en\s+plataforma', r'nueva\s+normativa', r'ley\s+que\s+entra\s+en\s+vigor',
        r'deadline\s+de', r'fecha\s+l[íi]mite', r's[óo]lo\s+por\s+tiempo\s+limitado'
    ]

    CONTENT_TYPE_URGENCY = {
        'news': 0.9,
        'tutorial': 0.6,
        'case_study': 0.5,
        'theory': 0.4,
        'list': 0.5,
        'reference': 0.3
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def classify(self, text: str, metadata: Optional[Dict] = None) -> UrgencyResult:
        """
        Clasifica urgencia de procesamiento.

        Args:
            text: Texto a analizar
            metadata: Metadata adicional (opcional)

        Returns:
            UrgencyResult con clasificación de urgencia
        """
        if self.ai_client and self.ai_client.is_available():
            return self._classify_with_ai(text)
        return self._classify_fallback(text, metadata)

    def _classify_with_ai(self, text: str) -> UrgencyResult:
        """Clasifica usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "urgency")
            if result.success:
                parsed = result.metadata
                urgency_str = parsed.get('urgency', 'batch')
                urgency = ProcessingUrgency.NOW if urgency_str == 'now' else ProcessingUrgency.BATCH

                return UrgencyResult(
                    urgency=urgency,
                    reason=parsed.get('reason', 'Clasificación IA'),
                    priority_score=parsed.get('priority', 0.5),
                    estimated_processing_time=parsed.get('estimated_minutes', 5),
                    factors=parsed.get('factors', [])
                )
        except Exception as e:
            logger.warning(f"AI urgency classification failed: {e}")
        return self._classify_fallback(text, metadata=None)

    def _classify_fallback(self, text: str, metadata: Optional[Dict]) -> UrgencyResult:
        """Clasifica usando heurísticas."""
        text_lower = text.lower()

        urgency_score = 0.5

        for pattern in self.HIGH_URGENCY_KEYWORDS:
            if re.search(pattern, text_lower):
                urgency_score += 0.3
                break

        if metadata:
            content_type = metadata.get('type', '').lower()
            urgency_score += self.CONTENT_TYPE_URGENCY.get(content_type, 0.5) - 0.5

            if metadata.get('recency') == 'recent':
                urgency_score += 0.2

            if metadata.get('author_authority', 0) > 0.7:
                urgency_score += 0.15

        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'hace\s+\d+\s+(?:d[íi]as?|horas?|semanas?)'
        ]
        for p in date_patterns:
            if re.search(p, text_lower):
                urgency_score += 0.1
                break

        urgency_score = min(1.0, urgency_score)

        if urgency_score >= 0.75:
            urgency = ProcessingUrgency.NOW
            reason = "Alta prioridad: contenido时效性 crítico"
        elif urgency_score >= 0.5:
            urgency = ProcessingUrgency.BATCH
            reason = "Prioridad media: procesar en próximo lote"
        else:
            urgency = ProcessingUrgency.DEFERRED
            reason = "Baja prioridad: contenido de referencia"

        factors = []
        if any(re.search(p, text_lower) for p in self.HIGH_URGENCY_KEYWORDS):
            factors.append("Keywords de alta urgencia detectados")
        if metadata and metadata.get('recency') == 'recent':
            factors.append("Contenido reciente")
        if urgency_score >= 0.75:
            factors.append("Score de prioridad elevado")

        estimated_time = max(1, int(urgency_score * 15))

        return UrgencyResult(
            urgency=urgency,
            reason=reason,
            priority_score=urgency_score,
            estimated_processing_time=estimated_time,
            factors=factors
        )

    def batch_classify(self, texts: list) -> list:
        """Clasifica urgencia de múltiples textos."""
        return [self.classify(t) for t in texts]

    def filter_by_urgency(self, results: list, min_urgency: ProcessingUrgency) -> list:
        """Filtra resultados por urgencia mínima."""
        urgency_order = {
            ProcessingUrgency.NOW: 3,
            ProcessingUrgency.BATCH: 2,
            ProcessingUrgency.DEFERRED: 1
        }
        min_level = urgency_order.get(min_urgency, 1)
        return [r for r in results if urgency_order.get(r.urgency, 0) >= min_level]

    def get_processing_plan(self, results: list) -> Dict[str, list]:
        """Genera plan de procesamiento por urgencia."""
        plan = {
            'now': [],
            'batch': [],
            'deferred': []
        }

        for i, result in enumerate(results):
            plan[result.urgency.value].append(i)

        return plan