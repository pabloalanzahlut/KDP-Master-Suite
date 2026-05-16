"""
Módulos IA P5-48: Detección de Casos de Estudio
Identifica ejemplos reales narrados en el contenido.
"""
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CaseStudyInfo:
    """Información de caso de estudio detectado."""
    case_type: str
    confidence: float
    evidence: List[str]
    description: str


class CaseStudyDetector:
    """Detector de casos de estudio en videos."""

    CASE_PATTERNS = {
        'success_story': [
            r'caso de éxito', 'success story', 'historia de éxito',
            r'cómo gan[oé] \d+', 'earned \$', 'ganó \$',
            r'mi experiencia', 'my experience', 'resultado real'
        ],
        'failure': [
            'fallo', 'failure', 'error', 'qué salió mal',
            'what went wrong', 'mistake', 'problema'
        ],
        'comparison': [
            'vs ', 'versus', 'comparación', 'comparison',
            'antes y después', 'before and after'
        ],
        'step_by_step': [
            'step by step', 'paso a paso', 'tutorial',
            'cómo hacer', 'how to', 'guía paso'
        ],
        'experiment': [
            'experiment', 'prueba', 'test', 'pruebas',
            'resultados de', 'results of', 'probando'
        ]
    }

    def __init__(self):
        self._detection_count = 0

    def detect_case_study(
        self,
        title: str,
        description: str = "",
        transcript: str = ""
    ) -> Optional[CaseStudyInfo]:
        """
        P5-48: Detecta si el contenido incluye casos de estudio.
        Args:
            title: Título del video
            description: Descripción del video
            transcript: Transcripción
        Returns:
            CaseStudyInfo si se detecta caso de estudio
        """
        self._detection_count += 1

        content = f"{title.lower()} {description.lower()}"

        for case_type, patterns in self.CASE_PATTERNS.items():
            match_count = 0
            evidence = []

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    match_count += 1
                    evidence.append(pattern)

            if match_count >= 2:
                confidence = min(0.5 + (match_count * 0.15), 1.0)

                descriptions = {
                    'success_story': 'Historia de éxito/resultado positivo',
                    'failure': 'Análisis de fallo o error',
                    'comparison': 'Comparación de opciones',
                    'step_by_step': 'Tutorial paso a paso',
                    'experiment': 'Experimento o prueba'
                }

                return CaseStudyInfo(
                    case_type=case_type,
                    confidence=round(confidence, 2),
                    evidence=evidence[:3],
                    description=descriptions.get(case_type, '')
                )

        return None

    def extract_examples(
        self,
        transcript: str,
        max_examples: int = 5
    ) -> List[str]:
        """Extrae ejemplos mencionados en la transcripción."""
        examples = []

        example_patterns = [
            r'ejemplo[:\s]+([^\n]+)',
            r'por ejemplo[:\s]+([^\n]+)',
            r'for example[:\s]+([^\n]+)',
            r'como[:\s]+([^\n]+)'
        ]

        for pattern in example_patterns:
            matches = re.findall(pattern, transcript.lower(), re.IGNORECASE)
            examples.extend([m.strip() for m in matches if len(m.strip()) > 20])

        return examples[:max_examples]

    def analyze_value_level(
        self,
        title: str,
        description: str = "",
        has_case_study: bool = False
    ) -> str:
        """Analiza el nivel de valor del contenido."""
        title_lower = title.lower()

        if has_case_study:
            if any(w in title_lower for w in ['ejemplo', 'example', 'caso', 'real']):
                return 'high'
            return 'medium'

        if any(w in title_lower for w in ['tutorial', 'guía', 'how to', 'complete']):
            return 'medium'

        return 'low'

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del detector."""
        return {
            "total_detected": self._detection_count,
            "model": "CaseStudyDetector v1.0"
        }


def create_case_study_detector() -> CaseStudyDetector:
    """Crea una instancia del detector."""
    return CaseStudyDetector()


_global_detector: Optional[CaseStudyDetector] = None


def get_case_study_detector() -> CaseStudyDetector:
    """Obtiene la instancia global."""
    global _global_detector
    if _global_detector is None:
        _global_detector = create_case_study_detector()
    return _global_detector