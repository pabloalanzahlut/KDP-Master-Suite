"""
Módulos IA P1-4: Extracción de Keywords del Título
Extrae palabras clave principales del título.
"""
import re
import logging
from typing import List, Dict, Optional, Set
from collections import Counter

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """Extractor de keywords de títulos."""

    STOP_WORDS = {
        'español': ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'con', 'por', 'para', 'que', 'es', 'son', 'los', 'las', 'este', 'esta', 'estos', 'estas', 'mi', 'tu', 'su', 'y', 'o', 'pero', 'si', 'no', 'como', 'más', 'muy', 'todo', 'otros', 'sobre', 'hacia', 'sin', 'hast'],
        'ingles': ['the', 'a', 'an', 'of', 'in', 'to', 'for', 'on', 'with', 'at', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'and', 'or', 'but', 'if', 'then', 'so', 'as', 'it', 'its']
    }

    def __init__(self, language: str = 'español'):
        self.language = language
        self._extraction_count = 0

    def extract_keywords(
        self,
        title: str,
        max_keywords: int = 10,
        min_length: int = 3
    ) -> List[str]:
        """
        P1-4: Extrae keywords del título.
        Args:
            title: Título del video
            max_keywords: Máximo de keywords a extraer
            min_length: Longitud mínima de palabra
        Returns:
            Lista de keywords
        """
        self._extraction_count += 1

        title_clean = re.sub(r'[^\w\s]', '', title.lower())

        words = title_clean.split()

        stop_words = self.STOP_WORDS.get(self.language, set())
        filtered = [w for w in words if len(w) >= min_length and w not in stop_words]

        keyword_counts = Counter(filtered)

        keywords = [kw for kw, _ in keyword_counts.most_common(max_keywords)]

        return keywords

    def extract_with_scores(
        self,
        title: str,
        max_keywords: int = 10
    ) -> List[Dict[str, any]]:
        """Extrae keywords con scores de relevancia."""
        keywords = self.extract_keywords(title, max_keywords)

        title_words = len(title.split())
        results = []

        for kw in keywords:
            position = title.lower().find(kw)
            position_score = 1 - (position / max(len(title), 1))

            length_score = min(len(kw) / 10, 1.0)

            score = (position_score * 0.6) + (length_score * 0.4)

            results.append({
                'keyword': kw,
                'position': position,
                'score': round(score, 2)
            })

        return sorted(results, key=lambda x: x['score'], reverse=True)

    def extract_ngrams(
        self,
        title: str,
        n: int = 2,
        max_ngrams: int = 5
    ) -> List[str]:
        """Extrae n-grams del título."""
        title_clean = re.sub(r'[^\w\s]', '', title.lower())
        words = title_clean.split()

        if len(words) < n:
            return []

        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)

        stop_words = self.STOP_WORDS.get(self.language, set())
        filtered = [ng for ng in ngrams if not any(sw in ng.split() for sw in stop_words)]

        counter = Counter(filtered)
        return [ng for ng, _ in counter.most_common(max_ngrams)]

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del extractor."""
        return {
            "total_extracted": self._extraction_count,
            "language": self.language,
            "model": "KeywordExtractor v1.0"
        }


def create_keyword_extractor(language: str = 'español') -> KeywordExtractor:
    """Crea una instancia del extractor."""
    return KeywordExtractor(language)


_global_extractor: Optional[KeywordExtractor] = None


def get_keyword_extractor() -> KeywordExtractor:
    """Obtiene la instancia global."""
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = create_keyword_extractor()
    return _global_extractor