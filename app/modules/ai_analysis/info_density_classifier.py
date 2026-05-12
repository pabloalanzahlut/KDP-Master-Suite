"""
AI Analysis - Módulo 21: Clasificador de Densidad Informativa
=============================================================
Puntúa 1-10 la utilidad del texto extraído para tu nicho KDP
basado en densidad de conceptos clave vs. ruido.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DensityResult:
    score: float
    word_count: int
    concept_count: int
    noise_ratio: float
    key_concepts: List[str]
    recommendation: str
    reasoning: str


class InfoDensityClassifier:
    """
    Clasificador de Densidad Informativa
    Puntúa 1-10 la utilidad del texto para nicho KDP.
    """

    KDP_KEYWORDS = [
        'estrategia', 'marketing', 'ventas', 'ingresos', 'negocio',
        'escalabilidad', 'automatización', 'brand', 'marca', 'cliente',
        'fidelización', 'leads', 'conversión', 'funnel', 'embudo',
        'roi', 'inversión', 'métricas', 'kpi', 'analytics',
        'seo', 'sem', 'ads', 'publicidad', 'presupuesto',
        'pricing', 'precio', 'valor', 'costos', 'margen',
        'legal', 'impuestos', 'contratos', 'compliance',
        'autores', 'editorial', 'publicación', 'amazon', 'kdp',
        'catálogo', 'royalty', 'derechos', 'isbn',
    ]

    TECHNICAL_PATTERNS = [
        r'\d{4}-\d{2}-\d{2}',
        r'\$\d+',
        r'https?://\S+',
        r'\b[A-Z]{2,}\b',
    ]

    FILLER_PATTERNS = [
        r'\b(yeah|okay|um|uh|hmm|like|well|so)\b',
        r'\[\s*\]',
        r'\(\s*\)',
    ]

    def __init__(self, ai_client=None):
        self._ai_client = ai_client
        self._stats = {
            'total_classified': 0,
            'high_density': 0,
            'low_density': 0,
            'total_concepts': 0
        }

    def classify(self, text: str) -> DensityResult:
        """
        Clasifica densidad informativa del texto.

        Args:
            text: Texto a clasificar

        Returns:
            DensityResult con puntuación y análisis
        """
        self._stats['total_classified'] += 1

        words = self._extract_words(text)
        word_count = len(words)
        concept_count = self._count_key_concepts(text)
        noise_ratio = self._calculate_noise_ratio(text)

        ai_score = None
        if self._ai_client and self._ai_client.is_available():
            result = self._ai_client.analyze(text, "density")
            if result.success:
                ai_score = result.score

        if ai_score is not None:
            base_score = ai_score
        else:
            base_score = self._calculate_local_score(word_count, concept_count, noise_ratio)

        key_concepts = self._extract_key_concepts(text)

        recommendation = self._generate_recommendation(base_score)
        reasoning = self._generate_reasoning(word_count, concept_count, noise_ratio)

        if base_score >= 7:
            self._stats['high_density'] += 1
        else:
            self._stats['low_density'] += 1

        self._stats['total_concepts'] += concept_count

        return DensityResult(
            score=base_score,
            word_count=word_count,
            concept_count=concept_count,
            noise_ratio=noise_ratio,
            key_concepts=key_concepts[:10],
            recommendation=recommendation,
            reasoning=reasoning
        )

    def _extract_words(self, text: str) -> List[str]:
        """Extrae palabras del texto."""
        return re.findall(r'\b\w+\b', text.lower())

    def _count_key_concepts(self, text: str) -> int:
        """Cuenta conceptos clave KDP."""
        text_lower = text.lower()
        count = 0
        for keyword in self.KDP_KEYWORDS:
            count += text_lower.count(keyword)
        return count

    def _calculate_noise_ratio(self, text: str) -> float:
        """Calcula ratio de ruido (filler, URLs, etc)."""
        filler_count = 0
        for pattern in self.FILLER_PATTERNS:
            filler_count += len(re.findall(pattern, text.lower()))

        urls = len(re.findall(r'https?://\S+', text))
        timestamps = len(re.findall(r'\d{1,2}:\d{2}', text))

        total_elements = len(text.split())
        if total_elements == 0:
            return 0.0

        noise = filler_count + urls + timestamps
        return min(noise / total_elements, 1.0)

    def _calculate_local_score(
        self,
        word_count: int,
        concept_count: int,
        noise_ratio: float
    ) -> float:
        """Calcula score sin IA."""
        if word_count < 10:
            return 1.0

        concept_density = concept_count / max(word_count, 1)
        clean_ratio = 1 - noise_ratio

        score = (concept_density * 50) + (clean_ratio * 30) + (min(word_count / 100, 1) * 20)

        return min(max(score / 10, 1.0), 10.0)

    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extrae conceptos clave del texto."""
        text_lower = text.lower()
        concepts = []

        for keyword in self.KDP_KEYWORDS:
            if keyword in text_lower:
                position = text_lower.find(keyword)
                concepts.append((keyword, position))

        concepts.sort(key=lambda x: x[1])
        return [c[0] for c in concepts]

    def _generate_recommendation(self, score: float) -> str:
        """Genera recomendación basada en score."""
        if score >= 8:
            return "ALTA PRIORIDAD: Contenido muy valioso para KB KDP"
        elif score >= 6:
            return "MEDIA PRIORIDAD: Contenido útil, integrar con revisión"
        elif score >= 4:
            return "BAJA PRIORIDAD: Contenido parcial, requiere enriquecimiento"
        else:
            return "DESCARTAR: Contenido con bajo valor informacional"

    def _generate_reasoning(
        self,
        word_count: int,
        concept_count: int,
        noise_ratio: float
    ) -> str:
        """Genera explicación del score."""
        parts = []

        if concept_count > 5:
            parts.append(f"Alta densidad de conceptos KDP ({concept_count})")
        elif concept_count > 0:
            parts.append(f"Baja densidad de conceptos KDP ({concept_count})")
        else:
            parts.append("Sin conceptos KDP detectados")

        if noise_ratio < 0.1:
            parts.append("Bajo ratio de ruido")
        elif noise_ratio > 0.3:
            parts.append("Alto ratio de ruido/filler")

        if word_count > 200:
            parts.append(f"Contenido extenso ({word_count} palabras)")
        elif word_count > 50:
            parts.append(f"Contenido moderado ({word_count} palabras)")
        else:
            parts.append(f"Contenido breve ({word_count} palabras)")

        return "; ".join(parts)

    def batch_classify(self, texts: List[str]) -> List[DensityResult]:
        """Clasifica múltiples textos."""
        return [self.classify(text) for text in texts]

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        stats = self._stats.copy()
        if stats['total_classified'] > 0:
            stats['high_density_ratio'] = stats['high_density'] / stats['total_classified']
        else:
            stats['high_density_ratio'] = 0.0
        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_classified': 0,
            'high_density': 0,
            'low_density': 0,
            'total_concepts': 0
        }


def create_classifier(ai_client=None) -> InfoDensityClassifier:
    """
    Factory function para crear clasificador.
    """
    return InfoDensityClassifier(ai_client=ai_client)


def quick_classify(text: str) -> Tuple[float, str]:
    """
    Función de conveniencia para clasificación rápida.
    Retorna (score, recommendation)
    """
    classifier = InfoDensityClassifier()
    result = classifier.classify(text)
    return result.score, result.recommendation