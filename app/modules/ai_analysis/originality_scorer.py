"""
P2-12: Scoring Avanzado de Originalidad
Análisis avanzado de originality del contenido.
"""
import re
from typing import Dict, List
from collections import Counter


class OriginalityScorer:
    """Scorer de originalidad de contenido."""

    def __init__(self):
        self._scored_videos: Dict[str, float] = {}
        self._scoring_count = 0

    def score_originality(
        self,
        title: str,
        description: str = "",
        transcript: str = "",
        similar_titles: List[str] = None
    ) -> Dict:
        """
        Calcula score de originalidad (0-100).
        Returns: Dict con score, factors, recommendation
        """
        self._scoring_count += 1

        score = 50
        factors = {}

        title_words = title.lower().split()
        unique_ratio = len(set(title_words)) / len(title_words) if title_words else 1
        factors['title_unique_ratio'] = round(unique_ratio, 2)

        if unique_ratio > 0.8:
            score += 15
        elif unique_ratio < 0.5:
            score -= 10

        if description:
            desc_len = len(description)
            if 200 < desc_len < 2000:
                score += 10
                factors['description_quality'] = 'good'
            elif desc_len < 50:
                score -= 10
                factors['description_quality'] = 'poor'
            else:
                factors['description_quality'] = 'average'

        if transcript:
            trans_words = transcript.lower().split()
            unique_trans = len(set(trans_words)) / len(trans_words) if trans_words else 1
            factors['transcript_unique_ratio'] = round(unique_trans, 2)
            if unique_trans > 0.4:
                score += 15

        if similar_titles:
            match_count = sum(1 for st in similar_titles if self._calculate_similarity(title, st) > 0.7)
            similarity_penalty = min(match_count * 10, 30)
            score -= similarity_penalty
            factors['similar_titles_count'] = match_count

        score = max(0, min(100, score))

        if score >= 70:
            recommendation = "Contenido original"
        elif score >= 40:
            recommendation = "Contenido parcialmente repetido"
        else:
            recommendation = "Alto nivel de repetición - considerar no procesar"

        return {
            'originality_score': score,
            'confidence': 0.75,
            'factors': factors,
            'recommendation': recommendation
        }

    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calcula similitud básica entre títulos."""
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0


def get_originality_scorer():
    return OriginalityScorer()