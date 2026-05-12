"""
AI Analysis - Executive Summary Generator
==========================================
Módulo 32: Genera resúmenes ejecutivos de 3 líneas.
Usa Ollama para síntesis inteligente.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    summary: str
    key_points: List[str]
    action_items: List[str]
    category: str
    confidence: float


class ExecSummaryGenerator:
    """
    Generador de resúmenes ejecutivos.
    Crea abstract de 3 líneas + puntos clave + acciones.
    """

    MAX_SUMMARY_LENGTH = 300
    MAX_KEY_POINTS = 5

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(self, text: str, max_lines: int = 3) -> SummaryResult:
        """
        Genera resumen ejecutivo.

        Args:
            text: Texto a resumir
            max_lines: Número máximo de líneas del resumen

        Returns:
            SummaryResult con resumen y puntos clave
        """
        if self.ai_client and self.ai_client.is_available():
            return self._generate_with_ai(text, max_lines)
        return self._generate_fallback(text, max_lines)

    def _generate_with_ai(self, text: str, max_lines: int) -> SummaryResult:
        """Genera usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "summary")
            if result.success:
                parsed = result.metadata
                return SummaryResult(
                    summary=parsed.get('summary', ''),
                    key_points=parsed.get('key_points', []),
                    action_items=parsed.get('action_items', []),
                    category=parsed.get('category', 'general'),
                    confidence=0.9
                )
        except Exception as e:
            logger.warning(f"AI summary generation failed: {e}")
        return self._generate_fallback(text, max_lines)

    def _generate_fallback(self, text: str, max_lines: int) -> SummaryResult:
        """Genera usando heurísticas."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        sentences = []
        for p in paragraphs:
            sents = re.split(r'[.!?]+', p)
            sentences.extend([s.strip() for s in sents if s.strip()])

        sentences = [s for s in sentences if len(s) > 30]

        top_sentences = sentences[:max_lines]

        summary_parts = []
        for sent in top_sentences:
            if sum(len(p) for p in summary_parts) + len(sent) < self.MAX_SUMMARY_LENGTH:
                summary_parts.append(sent)

        summary = '. '.join(summary_parts)
        if summary and not summary.endswith('.'):
            summary += '.'

        key_points = self._extract_key_points(text)
        action_items = self._extract_action_items(text)
        category = self._detect_category(text)

        return SummaryResult(
            summary=summary,
            key_points=key_points,
            action_items=action_items,
            category=category,
            confidence=0.6
        )

    def _extract_key_points(self, text: str) -> List[str]:
        """Extrae puntos clave del texto."""
        patterns = [
            r'(?:punto|aspecto|elemento|concepto|principio)\s+(?:clave|principal|importante)\s*:?\s*(.{20,100}?)(?:\.|$)',
            r'(?:importante|clave|fundamental|esencial)\s+(?:es|de|del)\s+(.{20,80}?)(?:\.|$)',
            r'(?:destacar|resaltar|recordar|considerar)\s+(?:que|el|la)\s+(.{20,80}?)(?:\.|$)'
        ]

        points = []
        for p in patterns:
            matches = re.findall(p, text, re.IGNORECASE)
            for m in matches:
                if len(m) > 20:
                    points.append(m.strip()[:100])

        if not points:
            sentences = re.split(r'[.!?]+', text)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 40 and len(sent) < 150:
                    points.append(sent)
                if len(points) >= 3:
                    break

        return points[:self.MAX_KEY_POINTS]

    def _extract_action_items(self, text: str) -> List[str]:
        """Extrae items de acción."""
        patterns = [
            r'(?:deber[íi]as?|hay que|es necesario|recomendable)\s+(.{20,100}?)(?:\.|$)',
            r'(?:pasos?|acciones?|tareas?)\s+(?:a\s+)?(?:seguir|implementar|realizar)\s*:?\s*(.{20,100}?)(?:\.|$)',
            r'(?:importante|no olvidar|recordar)\s+(?:que\s+)?(?:hay|se debe|usted)\s+(.{20,80}?)(?:\.|$)'
        ]

        actions = []
        for p in patterns:
            matches = re.findall(p, text, re.IGNORECASE)
            actions.extend([m.strip()[:100] for m in matches if len(m) > 20])

        return list(dict.fromkeys(actions))[:5]

    def _detect_category(self, text: str) -> str:
        """Detecta categoría del contenido."""
        categories = {
            'estrategia': [r'estrategia', r'plan\s+de', r'modelo\s+de\s+negocio', r'visión\s+de'],
            'marketing': [r'marketing', r'campaña', r'publicidad', r'branding', r'seo'],
            'operaciones': [r'proceso', r'automatizaci[óo]n', r'flujo\s+de\s+trabajo', r'optimizaci[óo]n'],
            'finanzas': [r'ingreso', r'gasto', r'inversi[óo]n', r'rendimiento', r'presupuesto'],
            'ventas': [r'ventas', r'cliente', r'lead', r'conversi[óo]n', r'negocio'],
            'liderazgo': [r'liderazgo', r'equipo', r'gesti[óo]n', r'direcci[óo]n', r'motivaci[óo]n']
        }

        text_lower = text.lower()
        for category, patterns in categories.items():
            if any(re.search(p, text_lower) for p in patterns):
                return category

        return 'general'

    def batch_generate(self, texts: List[str]) -> List[SummaryResult]:
        """Genera resúmenes para múltiples textos."""
        return [self.generate(t) for t in texts]

    def merge_summaries(self, summaries: List[SummaryResult]) -> SummaryResult:
        """Une múltiples resúmenes."""
        all_points = []
        all_actions = []
        categories = []

        for s in summaries:
            all_points.extend(s.key_points)
            all_actions.extend(s.action_items)
            if s.category != 'general':
                categories.append(s.category)

        return SummaryResult(
            summary=f"Múltiples documentos analizados ({len(summaries)} fuentes)",
            key_points=list(dict.fromkeys(all_points))[:5],
            action_items=list(dict.fromkeys(all_actions))[:5],
            category=max(set(categories), key=lambda x: categories.count(x)) if categories else 'general',
            confidence=0.5
        )