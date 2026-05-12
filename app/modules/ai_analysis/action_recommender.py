"""
AI Analysis - Post-Extraction Action Recommender
=================================================
Módulo 39: Recomienda acciones post-extracción (indexar, revisar, descartar).
Usa Ollama para decisiones inteligentes.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(Enum):
    INDEX = "index"
    REVIEW = "review"
    DISCARD = "discard"
    SPLIT = "split"
    ENRICH = "enrich"


@dataclass
class ActionRecommendation:
    action: ActionType
    priority: int
    confidence: float
    reason: str
    next_steps: List[str]
    warnings: List[str]
    estimated_impact: str


class ActionRecommender:
    """
    Recomendador de acciones post-extracción.
    Decide qué hacer con contenido extraído.
    """

    INDEX_THRESHOLD = 0.75
    REVIEW_THRESHOLD = 0.45
    DISCARD_THRESHOLD = 0.25

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def recommend(self, extraction_result: Dict, metadata: Optional[Dict] = None) -> ActionRecommendation:
        """
        Recomienda acción para contenido extraído.

        Args:
            extraction_result: Resultado de extracción
            metadata: Metadata adicional (opcional)

        Returns:
            ActionRecommendation con acción sugerida
        """
        if self.ai_client and self.ai_client.is_available():
            return self._recommend_with_ai(extraction_result, metadata)
        return self._recommend_fallback(extraction_result, metadata)

    def _recommend_with_ai(self, extraction_result: Dict, metadata: Optional[Dict]) -> ActionRecommendation:
        """Recomienda usando Ollama."""
        text = extraction_result.get('content', '')
        try:
            result = self.ai_client.analyze(text, "action")
            if result.success:
                parsed = result.metadata
                action_str = parsed.get('action', 'review')
                action = ActionType(action_str)

                priority = 1
                if action == ActionType.INDEX:
                    priority = 3
                elif action == ActionType.DISCARD:
                    priority = 1

                return ActionRecommendation(
                    action=action,
                    priority=priority,
                    confidence=parsed.get('confidence', 0.7),
                    reason=parsed.get('reason', 'Recomendación IA'),
                    next_steps=parsed.get('next_steps', []),
                    warnings=parsed.get('warnings', []),
                    estimated_impact=parsed.get('impact', 'medium')
                )
        except Exception as e:
            logger.warning(f"AI action recommendation failed: {e}")
        return self._recommend_fallback(extraction_result, metadata)

    def _recommend_fallback(self, extraction_result: Dict, metadata: Optional[Dict]) -> ActionRecommendation:
        """Recomienda usando heurísticas."""
        content = extraction_result.get('content', '')
        quality = extraction_result.get('quality', 0.5)
        completeness = extraction_result.get('completeness', 0.5)

        score = (quality * 0.4) + (completeness * 0.3)

        if metadata:
            if metadata.get('from_trusted_source'):
                score += 0.15
            if metadata.get('has_media'):
                score += 0.1
            if metadata.get('is_comprehensive'):
                score += 0.15

        word_count = len(content.split())
        if word_count < 50:
            score -= 0.2
        elif word_count > 5000:
            score += 0.1

        duplicate_score = extraction_result.get('duplicate_score', 0)
        if duplicate_score > 0.7:
            score -= 0.3

        score = max(0, min(1, score))

        warnings = []
        next_steps = []

        if score >= self.INDEX_THRESHOLD:
            action = ActionType.INDEX
            reason = f"Contenido de alta calidad (score: {score:.2f})"
            next_steps = [
                "Agregar a índice de KB",
                "Vincular con entradas relacionadas",
                "Generar tags automáticos"
            ]
            if word_count > 3000:
                action = ActionType.SPLIT
                reason += " - Contenido extenso, considerar split"
                next_steps.append("Dividir en segmentos lógicos")
                warnings.append("Contenido extenso detectado")

        elif score >= self.REVIEW_THRESHOLD:
            action = ActionType.REVIEW
            reason = f"Contenido requiere revisión manual (score: {score:.2f})"
            next_steps = [
                "Revisar contenido para verificar calidad",
                "Verificar fuentes y referencias",
                "Decidir sobre indexación"
            ]
            if completeness < 0.5:
                warnings.append("Contenido incompleto, requiere complemento")

        elif score >= self.DISCARD_THRESHOLD:
            action = ActionType.REVIEW
            reason = f"Contenido marginal, revisión necesaria (score: {score:.2f})"
            next_steps = [
                "Evaluar relevancia específica",
                "Considerar como referencia parcial",
                "Descartar si no es útil"
            ]
            warnings.append("Contenido de baja calidad detectado")

        else:
            action = ActionType.DISCARD
            reason = f"Contenido insuficiente (score: {score:.2f})"
            next_steps = [
                "Descartar contenido",
                "Marcar como no procesable",
                "Registrar en log de descartes"
            ]
            warnings.append("No cumple umbrales mínimos")

        if duplicate_score > 0.5:
            warnings.append(f"Posible duplicado (similitud: {duplicate_score:.0%})")

        return ActionRecommendation(
            action=action,
            priority=3 if action == ActionType.INDEX else (2 if action == ActionType.REVIEW else 1),
            confidence=0.7,
            reason=reason,
            next_steps=next_steps,
            warnings=warnings,
            estimated_impact=self._get_impact(action, score)
        )

    def _get_impact(self, action: ActionType, score: float) -> str:
        """Determina impacto estimado."""
        if action == ActionType.INDEX:
            return "high" if score > 0.8 else "medium"
        elif action == ActionType.REVIEW:
            return "medium"
        return "low"

    def batch_recommend(self, results: List[Dict]) -> List[ActionRecommendation]:
        """Recomienda acciones para múltiples resultados."""
        return [self.recommend(r) for r in results]

    def get_action_summary(self, recommendations: List[ActionRecommendation]) -> Dict[str, Any]:
        """Resumen de acciones recomendadas."""
        summary = {
            'total': len(recommendations),
            'index_count': 0,
            'review_count': 0,
            'discard_count': 0,
            'split_count': 0,
            'enrich_count': 0,
            'avg_confidence': 0.0
        }

        for r in recommendations:
            if r.action == ActionType.INDEX:
                summary['index_count'] += 1
            elif r.action == ActionType.REVIEW:
                summary['review_count'] += 1
            elif r.action == ActionType.DISCARD:
                summary['discard_count'] += 1
            elif r.action == ActionType.SPLIT:
                summary['split_count'] += 1
            elif r.action == ActionType.ENRICH:
                summary['enrich_count'] += 1

        if recommendations:
            summary['avg_confidence'] = sum(r.confidence for r in recommendations) / len(recommendations)

        return summary

    def filter_by_action(self, recommendations: List[ActionRecommendation], action: ActionType) -> List[ActionRecommendation]:
        """Filtra recomendaciones por tipo de acción."""
        return [r for r in recommendations if r.action == action]