"""
AI Analysis - Manual Value Predictor
=====================================
Módulo 27: Predice valor para inclusión en Legalidad, Fórmulas o Matriz.
Usa Ollama para análisis semántico.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ManualCategory(Enum):
    LEGALIDAD = "legalidad"
    FÓRMULAS = "fórmulas"
    MATRIZ = "matriz"
    GENERAL = "general"


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ManualPrediction:
    category: ManualCategory
    priority: Priority
    reasoning: str
    keywords: List[str]
    manual_section: Optional[str] = None
    confidence: float = 0.5


class ManualPredictor:
    """
    Predice valor de contenido para manuales KDP.
    Fallback con keywords cuando Ollama no disponible.
    """

    CATEGORY_KEYWORDS = {
        ManualCategory.LEGALIDAD: [
            r'legal', r'jur[íi]dico', r'regulaci[óo]n', r'compliance',
            r'pol[íi]tica\s+de', r't[éé]rminos?\s+de\s+servicio',
            r'privacidad', r'gdpr', r'ccpa', r'copyright',
            r'licencia\s+de', r'derechos?\s+de\s+autor', r'patente'
        ],
        ManualCategory.FÓRMULAS: [
            r'f[óo]rmula', r'c[áa]lculo', r'ecuaci[óo]n', r'matem[áa]tica',
            r'conversi[óo]n\s+de', r'tasa\s+de', r'ratio\s+de',
            r'roi\s+=', r'beneficio\s+neto', r'm[áa]rgen\s+de',
            r'capital\s+de\s+trabajo', r'punto\s+de\s+equilibrio'
        ],
        ManualCategory.MATRIZ: [
            r'matriz\s+de', r'framework\s+de', r'modelo\s+estratégico',
            r'an[áa]lisis\s+swot', r'priorizaci[óo]n\s+de',
            r'clasificaci[óo]n\s+de', r'tabla\s+de', r'dashboard\s+de',
            r'm[éé]tricas?\s+de', r'kpi\s+de', r'indicadores?\s+de'
        ]
    }

    HIGH_VALUE_PATTERNS = [
        r'n[úu]cleo\s+esencial', r'fundamentos?\s+de', r'principios?\s+b[áa]sicos?',
        r'base\s+de\s+datos', r'tabla\s+de\s+referencia', r'gu[íi]a\s+de',
        r'directorio\s+de', r'repositorio\s+de', r'enciclopedia\s+de',
        r'diccionario\s+de', r'cat[áa]logo\s+de', r'manual\s+de'
    ]

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def predict(self, text: str, metadata: Optional[Dict] = None) -> ManualPrediction:
        """
        Predice valor para manuales KDP.

        Args:
            text: Texto a analizar
            metadata: Metadata adicional (opcional)

        Returns:
            ManualPrediction con categoría y prioridad
        """
        if self.ai_client and self.ai_client.is_available():
            return self._predict_with_ai(text)
        return self._predict_fallback(text)

    def _predict_with_ai(self, text: str) -> ManualPrediction:
        """Predice usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "manual")
            if result.success:
                parsed = result.metadata
                category_str = parsed.get('manual', 'general')
                category = ManualCategory(category_str.lower())
                priority = Priority(parsed.get('priority', 'low'))

                return ManualPrediction(
                    category=category,
                    priority=priority,
                    reasoning=parsed.get('reason', 'Predicción IA'),
                    keywords=parsed.get('keywords', []),
                    manual_section=parsed.get('section'),
                    confidence=0.8
                )
        except Exception as e:
            logger.warning(f"AI prediction failed: {e}")
        return self._predict_fallback(text)

    def _predict_fallback(self, text: str) -> ManualPrediction:
        """Predice usando heurísticas."""
        text_lower = text.lower()

        category_scores = {}
        for category, patterns in self.CATEGORY_KEYWORDS.items():
            matches = sum(1 for p in patterns if re.search(p, text_lower, re.IGNORECASE))
            category_scores[category] = matches

        best_category = max(category_scores, key=category_scores.get)
        max_matches = category_scores[best_category]

        if max_matches == 0:
            best_category = ManualCategory.GENERAL

        priority = Priority.LOW
        if any(re.search(p, text_lower, re.IGNORECASE) for p in self.HIGH_VALUE_PATTERNS):
            priority = Priority.HIGH
        elif max_matches >= 2:
            priority = Priority.MEDIUM

        keywords = []
        for cat, patterns in self.CATEGORY_KEYWORDS.items():
            for p in patterns:
                if re.search(p, text_lower, re.IGNORECASE):
                    keyword = re.sub(r'[^\w\s]', '', p)
                    if keyword not in keywords:
                        keywords.append(keyword)
        keywords = keywords[:5]

        confidence = min(0.9, 0.3 + (max_matches * 0.2))

        return ManualPrediction(
            category=best_category,
            priority=priority,
            reasoning=f"Detectadas {max_matches} keywords de {best_category.value}",
            keywords=keywords,
            manual_section=None,
            confidence=confidence
        )

    def batch_predict(self, texts: list) -> list:
        """Predice para múltiples textos."""
        return [self.predict(t) for t in texts]

    def filter_by_priority(self, predictions: List[ManualPrediction], min_priority: Priority) -> List[ManualPrediction]:
        """Filtra predicciones por prioridad mínima."""
        priority_order = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
        min_level = priority_order.get(min_priority, 1)
        return [p for p in predictions if priority_order.get(p.priority, 0) >= min_level]