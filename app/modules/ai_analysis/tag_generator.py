"""
AI Analysis - Semantic Tag Generator
====================================
Módulo 29: Generador de tags semánticos basados en contenido.
Usa Ollama para análisis semántico.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TagGenerationResult:
    tags: List[str]
    tag_count: int
    categories: List[str]
    primary_tag: str
    reasoning: str
    confidence: float


class TagGenerator:
    """
    Generador de tags semánticos para contenido.
    Combina análisis IA con extracción de keywords.
    """

    STOPWORDS = {
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del',
        'al', 'a', 'en', 'con', 'por', 'para', 'sin', 'sobre', 'entre',
        'que', 'y', 'e', 'o', 'u', 'pero', 'si', 'no', 'se', 'su', 'sus',
        'es', 'son', 'está', 'están', 'fue', 'fueron', 'ser', 'estar',
        'hay', 'han', 'ha', 'este', 'esta', 'estos', 'estas', 'ese', 'esa',
        'como', 'más', 'menos', 'muy', 'también', 'solo', 'ya', 'aún',
        'del', 'al', 'lo', 'le', 'les', 'me', 'te', 'nos', 'os'
    }

    TAG_CATEGORIES = {
        'platform': ['youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin', 'google', 'amazon', 'shopify', 'wordpress'],
        'format': ['video', 'tutorial', 'guía', 'curso', 'webinar', 'podcast', 'artículo', 'infografía', 'plantilla', 'checklist'],
        'topic': ['marketing', 'ventas', 'negocios', 'finanzas', 'tecnología', 'productividad', 'liderazgo', 'estrategia'],
        'industry': ['ecommerce', 'saas', 'consultoría', 'agencia', 'startup', 'pyme', 'empresa', 'freelance'],
        'action': ['estrategia', 'implementación', 'optimización', 'automatización', 'escalabilidad', 'crecimiento']
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(self, text: str, metadata: Optional[Dict] = None, max_tags: int = 10) -> TagGenerationResult:
        """
        Genera tags semánticos.

        Args:
            text: Texto a analizar
            metadata: Metadata adicional (opcional)
            max_tags: Máximo número de tags

        Returns:
            TagGenerationResult con tags generados
        """
        if self.ai_client and self.ai_client.is_available():
            return self._generate_with_ai(text, max_tags)
        return self._generate_fallback(text, max_tags)

    def _generate_with_ai(self, text: str, max_tags: int) -> TagGenerationResult:
        """Genera usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "tags")
            if result.success:
                parsed = result.metadata
                tags = parsed.get('tags', [])
                return TagGenerationResult(
                    tags=tags[:max_tags],
                    tag_count=len(tags),
                    categories=parsed.get('categories', []),
                    primary_tag=tags[0] if tags else 'general',
                    reasoning=parsed.get('reason', 'Generado por IA'),
                    confidence=0.85
                )
        except Exception as e:
            logger.warning(f"AI tag generation failed: {e}")
        return self._generate_fallback(text, max_tags)

    def _generate_fallback(self, text: str, max_tags: int) -> TagGenerationResult:
        """Genera usando extracción de keywords."""
        words = re.findall(r'\b[a-záéíóúñü]{4,}\b', text.lower())

        word_freq = {}
        for word in words:
            if word not in self.STOPWORDS and len(word) >= 4:
                word_freq[word] = word_freq.get(word, 0) + 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_tags * 2]

        tags = [word for word, _ in top_words]

        categories = []
        text_lower = text.lower()
        for cat, keywords in self.TAG_CATEGORIES.items():
            if any(kw in text_lower for kw in keywords):
                categories.append(cat)

        ngrams = self._extract_ngrams(text.lower(), 2, 3)
        for ngram in ngrams:
            if len(tags) < max_tags and ngram not in tags:
                tags.append(ngram)

        tags = tags[:max_tags]

        return TagGenerationResult(
            tags=tags,
            tag_count=len(tags),
            categories=categories,
            primary_tag=tags[0] if tags else 'general',
            reasoning=f"Extraídos {len(tags)} tags de keywords más frecuentes",
            confidence=0.6
        )

    def _extract_ngrams(self, text: str, min_n: int, max_n: int) -> List[str]:
        """Extrae n-grams significativos."""
        words = re.findall(r'\b[a-záéíóúñü]{3,}\b', text)
        ngrams = []

        for n in range(min_n, max_n + 1):
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                if ngram not in self.STOPWORDS:
                    ngrams.append(ngram)

        return ngrams[:5]

    def batch_generate(self, texts: List[str], max_tags: int = 10) -> List[TagGenerationResult]:
        """Genera tags para múltiples textos."""
        return [self.generate(t, max_tags=max_tags) for t in texts]

    def merge_tags(self, tag_lists: List[List[str]]) -> List[str]:
        """Une tags de múltiples fuentes."""
        all_tags = set()
        for tags in tag_lists:
            all_tags.update(tags)
        return sorted(list(all_tags), key=str.lower)[:15]

    def validate_tags(self, tags: List[str], allowed_tags: Set[str]) -> List[str]:
        """Valida tags contra lista permitida."""
        return [t for t in tags if t in allowed_tags or len(t) >= 4]