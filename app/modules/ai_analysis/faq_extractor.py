"""
Módulos IA P5-46: Extracción de Preguntas Frecuentes (FAQ)
Extrae preguntas frecuentes que un video responde.
"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FAQItem:
    """Una pregunta frecuente extraída."""
    question: str
    answer_preview: str
    confidence: float
    timestamp: Optional[int] = None


class FAQExtractor:
    """Extractor de preguntas frecuentes de transcripciones."""

    QUESTION_PATTERNS = [
        r'(?:¿|what|how|why|when|where|who|which)\s+[\w\s]+\?',
        r'^[\w\s]+\?',
        r'(?:pregunta|pregunt):\s*([^\n]+)',
        r'(?:q:|question:)\s*([^\n]+)'
    ]

    ANSWER_INDICATORS = [
        'la respuesta', 'the answer is', 'respuesta:',
        'esto significa', 'this means', 'básicamente',
        'en resumen', 'in summary', 'en conclusión'
    ]

    def __init__(self):
        self._extraction_count = 0

    def extract_faqs(
        self,
        transcript: str,
        title: str = "",
        max_faqs: int = 10
    ) -> List[FAQItem]:
        """
        P5-46: Extrae preguntas frecuentes de la transcripción.
        Args:
            transcript: Transcripción del video
            title: Título del video (para contexto)
            max_faqs: Máximo de FAQs a extraer
        Returns:
            Lista de FAQItem
        """
        self._extraction_count += 1
        faqs = []

        sentences = re.split(r'[.!?\n]', transcript)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 20]

        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            is_question = any(re.search(pattern, sentence_lower, re.IGNORECASE | re.MULTILINE)
                            for pattern in self.QUESTION_PATTERNS)

            if not is_question:
                is_question = any(kw in sentence_lower for kw in ['¿qué', '¿cómo', '¿por qué', '¿cuándo', 'why', 'how', 'what', 'when'])

            if is_question:
                confidence = 0.5

                if '¿' in sentence or '?' in sentence:
                    confidence += 0.3

                words = sentence.split()
                if len(words) <= 15:
                    confidence += 0.1

                question_clean = re.sub(r'^[¿\s]+', '', sentence).strip()

                next_sentences = sentences[i + 1:i + 3] if i + 1 < len(sentences) else []
                answer_preview = ' '.join(next_sentences)[:100] if next_sentences else ""

                if any(indicator in sentence_lower for indicator in self.ANSWER_INDICATORS):
                    confidence += 0.2

                faqs.append(FAQItem(
                    question=question_clean[:150],
                    answer_preview=answer_preview,
                    confidence=min(confidence, 1.0),
                    timestamp=None
                ))

        faqs.sort(key=lambda f: f.confidence, reverse=True)

        return faqs[:max_faqs]

    def extract_from_description(self, description: str) -> List[str]:
        """Extrae FAQs de la descripción del video."""
        faqs = []

        qna_patterns = [
            r'preg[úu]nta:\s*([^\n]+)',
            r'question:\s*([^\n]+)',
            r'(?:¿|Q:)\s*([^\n]+)',
            r'FAQ[:\s]*([^\n]+)'
        ]

        for pattern in qna_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            faqs.extend([m.strip() for m in matches if m.strip()])

        return faqs[:5]

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del extractor."""
        return {
            "total_extracted": self._extraction_count,
            "model": "FAQExtractor v1.0"
        }


def create_faq_extractor() -> FAQExtractor:
    """Crea una instancia del extractor de FAQs."""
    return FAQExtractor()


_global_extractor: Optional[FAQExtractor] = None


def get_faq_extractor() -> FAQExtractor:
    """Obtiene la instancia global del extractor de FAQs."""
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = create_faq_extractor()
    return _global_extractor