"""
AI Analysis - Knowledge Base Fusion
===================================
Módulo 36: Fusiona nuevo contenido con KB existente.
Usa Ollama para sugerir integración óptima.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FusionAction(Enum):
    FUSE = "fuse"
    COMPLEMENT = "complement"
    SEPARATE = "separate"
    REPLACE = "replace"


@dataclass
class FusionResult:
    action: FusionAction
    confidence: float
    target_kb_entries: List[str]
    merge_strategy: str
    reasoning: str
    conflicts: List[str]
    recommendations: List[str]


@dataclass
class KBEntry:
    id: str
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KBFusion:
    """
    Fusionador de contenido con Knowledge Base.
    Sugiere cómo integrar nuevo contenido.
    """

    TAG_SIMILARITY_THRESHOLD = 0.5
    CONTENT_SIMILARITY_THRESHOLD = 0.7

    def __init__(self, ai_client=None, kb_entries: Optional[List[KBEntry]] = None):
        self.ai_client = ai_client
        self.kb_entries = kb_entries or []

    def add_kb_entry(self, entry: KBEntry):
        """Agrega entrada a KB."""
        self.kb_entries.append(entry)

    def suggest_fusion(self, new_content: str, new_tags: Optional[List[str]] = None) -> FusionResult:
        """
        Sugiere cómo fusionar nuevo contenido.

        Args:
            new_content: Contenido a fusionar
            new_tags: Tags del nuevo contenido

        Returns:
            FusionResult con estrategia de fusión
        """
        if self.ai_client and self.ai_client.is_available():
            return self._suggest_with_ai(new_content, new_tags)
        return self._suggest_fallback(new_content, new_tags)

    def _suggest_with_ai(self, new_content: str, new_tags: Optional[List[str]]) -> FusionResult:
        """Sugiere usando Ollama."""
        try:
            result = self.ai_client.analyze(new_content, "fusion")
            if result.success:
                parsed = result.metadata
                action = FusionAction(parsed.get('action', 'separate'))

                return FusionResult(
                    action=action,
                    confidence=0.85,
                    target_kb_entries=parsed.get('targets', []),
                    merge_strategy=parsed.get('strategy', 'merge_paragraphs'),
                    reasoning=parsed.get('reason', 'Análisis IA'),
                    conflicts=parsed.get('conflicts', []),
                    recommendations=parsed.get('recommendations', [])
                )
        except Exception as e:
            logger.warning(f"AI fusion suggestion failed: {e}")
        return self._suggest_fallback(new_content, new_tags)

    def _suggest_fallback(self, new_content: str, new_tags: Optional[List[str]]) -> FusionResult:
        """Sugiere usando análisis de similitud."""
        new_tags = new_tags or []
        new_words = set(re.findall(r'\b[a-záéíóúñü]{4,}\b', new_content.lower()))

        similar_entries = []
        for entry in self.kb_entries:
            entry_words = set(re.findall(r'\b[a-záéíóúñü]{4,}\b', entry.content.lower()))

            if new_words & entry_words:
                overlap = len(new_words & entry_words) / len(new_words | entry_words)
                if overlap > 0.3:
                    similar_entries.append((entry, overlap))

        similar_entries.sort(key=lambda x: x[1], reverse=True)

        if not similar_entries:
            return FusionResult(
                action=FusionAction.SEPARATE,
                confidence=0.7,
                target_kb_entries=[],
                merge_strategy="Crear nueva entrada",
                reasoning="No se encontraron entradas similares",
                conflicts=[],
                recommendations=["Crear nueva entrada en KB", "Considerar crear nueva categoría"]
            )

        top_entry, similarity = similar_entries[0]

        conflicts = []
        if similarity > 0.8:
            conflicts.append(f"Alta similitud ({similarity:.0%}) con entrada existente")
            action = FusionAction.REPLACE
            strategy = "Reemplazar entrada existente"
        elif similarity > 0.5:
            action = FusionAction.FUSE
            strategy = "Fusionar contenido en entrada existente"
        else:
            action = FusionAction.COMPLEMENT
            strategy = "Agregar como complemento"

        return FusionResult(
            action=action,
            confidence=min(0.9, similarity + 0.2),
            target_kb_entries=[top_entry.id],
            merge_strategy=strategy,
            reasoning=f"Similitud {similarity:.0%} con '{top_entry.title}'",
            conflicts=conflicts,
            recommendations=self._get_recommendations(action, similarity)
        )

    def _get_recommendations(self, action: FusionAction, similarity: float) -> List[str]:
        """Obtiene recomendaciones según acción."""
        recommendations = []

        if action == FusionAction.REPLACE:
            recommendations.append("Verificar si la nueva versión es más completa")
            recommendations.append("Respaldar contenido anterior antes de reemplazar")
        elif action == FusionAction.FUSE:
            recommendations.append("Revisar contenido duplicado antes de fusionar")
            recommendations.append("Mantener tags de ambas fuentes")
        elif action == FusionAction.COMPLEMENT:
            recommendations.append("Agregar referencia cruzada entre entradas")
            recommendations.append("Actualizar índice de tags")
        else:
            recommendations.append("Crear nueva categoría si no existe")
            recommendations.append("Asignar tags únicos")

        return recommendations

    def execute_fusion(self, fusion_result: FusionResult, new_content: str) -> str:
        """Ejecuta fusión y retorna contenido mergeado."""
        if fusion_result.action == FusionAction.SEPARATE:
            return new_content

        if not fusion_result.target_kb_entries:
            return new_content

        target_entry = next((e for e in self.kb_entries if e.id == fusion_result.target_kb_entries[0]), None)
        if not target_entry:
            return new_content

        if fusion_result.action == FusionAction.REPLACE:
            return new_content

        if fusion_result.action == FusionAction.FUSE:
            return f"{target_entry.content}\n\n## Complemento\n\n{new_content}"

        if fusion_result.action == FusionAction.COMPLEMENT:
            return f"{target_entry.content}\n\n---\n\n**Nota adicional:**\n{new_content[:500]}..."

        return new_content

    def batch_suggest(self, contents: List[str]) -> List[FusionResult]:
        """Sugiere fusión para múltiples contenidos."""
        return [self.suggest_fusion(c) for c in contents]