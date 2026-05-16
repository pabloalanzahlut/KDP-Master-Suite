"""
Módulos IA P5-50: Alerta de Profundidad Insuficiente
Detecta si un video es muy superficial para el nivel del usuario.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DepthAnalysis:
    """Resultado del análisis de profundidad."""
    depth_level: str
    score: float
    is_sufficient: bool
    gaps: List[str]
    recommendation: str


class DepthAnalyzer:
    """Analizador de profundidad de contenido."""

    LEVEL_KEYWORDS = {
        'beginner': ['básico', 'introducción', 'para principiantes', 'desde cero', 'beginner', 'basics', 'intro'],
        'intermediate': ['intermedio', 'nivel medio', 'intermediate', 'intermediate level', 'profesional'],
        'advanced': ['avanzado', 'experto', 'advanced', 'expert', 'master', 'profesional avanzado']
    }

    DEPTH_INDICATORS = {
        'high': [
            'análisis completo', 'explicación detallada', 'en profundidad',
            'step by step', 'complete guide', 'full tutorial',
            'ejemplo práctico', 'caso de estudio', 'demo completo'
        ],
        'low': [
            'resumen', 'overview', 'breve', 'intro',
            'qué es', 'what is', 'quick', 'tips'
        ]
    }

    def __init__(self):
        self._analysis_count = 0

    def analyze_depth(
        self,
        title: str,
        description: str = "",
        transcript: str = "",
        user_level: str = "intermediate"
    ) -> DepthAnalysis:
        """
        P5-50: Analiza la profundidad del contenido.
        Args:
            title: Título del video
            description: Descripción del video
            transcript: Transcripción (opcional)
            user_level: Nivel del usuario (beginner, intermediate, advanced)
        Returns:
            DepthAnalysis con resultado
        """
        self._analysis_count += 1

        content = f"{title.lower()} {description.lower()} {transcript.lower()[:500]}"
        words = content.split()

        score = 0.5
        gaps = []

        title_level = self._detect_level(title)
        desc_level = self._detect_level(description)

        detected_levels = [l for l in [title_level, desc_level] if l]
        if detected_levels:
            primary_level = detected_levels[0]
            if user_level == "beginner" and primary_level in ["intermediate", "advanced"]:
                score -= 0.3
                gaps.append("Contenido más avanzado que el nivel esperado")
            elif user_level == "advanced" and primary_level == "beginner":
                score -= 0.4
                gaps.append("Contenido muy básico para nivel avanzado")

        for indicator in self.DEPTH_INDICATORS['high']:
            if indicator in content:
                score += 0.15

        for indicator in self.DEPTH_INDICATORS['low']:
            if indicator in content:
                score -= 0.1

        if len(transcript) > 5000:
            score += 0.1
        elif len(transcript) < 1000:
            score -= 0.15
            gaps.append("Transcripción muy corta - contenido probablemente superficial")

        if len(words) < 50 and len(transcript) < 500:
            score -= 0.2
            gaps.append("Contenido muy breve para desarrollo completo del tema")

        depth_level = "intermediate"
        if score >= 0.7:
            depth_level = "advanced"
        elif score <= 0.3:
            depth_level = "beginner"

        is_sufficient = True
        if user_level == "advanced" and depth_level in ["beginner", "intermediate"]:
            is_sufficient = False
        elif user_level == "intermediate" and depth_level == "beginner":
            is_sufficient = False

        score = max(0.0, min(1.0, score))

        if not is_sufficient:
            recommendation = f"Contenido insuficiente para nivel {user_level}. Buscar videos más profundos."
        elif score >= 0.6:
            recommendation = "Contenido con profundidad adecuada"
        else:
            recommendation = "Contenido básico - adecuado para principiantes"

        return DepthAnalysis(
            depth_level=depth_level,
            score=round(score, 2),
            is_sufficient=is_sufficient,
            gaps=gaps,
            recommendation=recommendation
        )

    def _detect_level(self, text: str) -> Optional[str]:
        """Detecta el nivel del contenido."""
        text_lower = text.lower()

        for level, keywords in self.LEVEL_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return level

        return None

    def compare_with_user_level(
        self,
        video_depth: DepthAnalysis,
        user_level: str
    ) -> Dict:
        """Compara la profundidad del video con el nivel del usuario."""
        level_hierarchy = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
        video_level_num = level_hierarchy.get(video_depth.depth_level, 2)
        user_level_num = level_hierarchy.get(user_level, 2)

        gap = video_level_num - user_level_num

        if gap <= 0:
            status = "adequate"
            message = "Contenido adecuado para tu nivel"
        elif gap == 1:
            status = "slightly_advanced"
            message = "Contenido ligeramente más avanzado"
        else:
            status = "too_advanced"
            message = "Contenido muy avanzado para tu nivel"

        return {
            "status": status,
            "message": message,
            "video_level": video_depth.depth_level,
            "user_level": user_level,
            "gap": gap
        }

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del analizador."""
        return {
            "total_analyzed": self._analysis_count,
            "model": "DepthAnalyzer v1.0"
        }


def create_depth_analyzer() -> DepthAnalyzer:
    """Crea una instancia del analizador de profundidad."""
    return DepthAnalyzer()


_global_analyzer: Optional[DepthAnalyzer] = None


def get_depth_analyzer() -> DepthAnalyzer:
    """Obtiene la instancia global del analizador de profundidad."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = create_depth_analyzer()
    return _global_analyzer