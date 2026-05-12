"""
AI Analysis - Bias Detector
============================
Módulo 28: Detecta sesgo en fuentes (tono promocional, marketing encubierto).
Usa Ollama para análisis semántico.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BiasAnalysis:
    is_biased: bool
    bias_type: str
    severity: float
    indicators: List[str]
    reasoning: str
    recommendations: List[str]


class BiasDetector:
    """
    Detector de sesgo en contenido de fuentes.
    Fallback con patrones cuando Ollama no disponible.
    """

    MARKETING_PATTERNS = {
        'promotional': [
            r'¡(?:\w+\s+){0,2}incre[íi]ble!',
            r'el\s+mejor\s+(?:\w+\s+){0,2}del\s+mercado',
            r'soluci[óo]n\s+definitiva',
            r'garant[íi]a\s+(?:\w+\s+){0,2}100%',
            r'no\s+pierdas\s+(?:\w+\s+){0,2}esta\s+oportunidad',
            r's[óo]lo\s+por\s+hoy',
            r'm[áa]s\s+vendido',
            r'#1\s+(?:en|del)',
            r'resultados?\s+garantizados?'
        ],
        'affiliate': [
            r'link\s+de\s+afiliado',
            r'c[óo]digo\s+de\s+descuento',
            r'enlace\s+(?:de\s+)?afiliado',
            r'gracias\s+a\s+(?:mi|nuestro)\s+enlace',
            r'comisi[óo]n\s+por\s+referencia'
        ],
        'subjective': [
            r'me\s+encant[óa]',
            r'es\s+fant[áa]stico',
            r'no\s+puedo\s+vivir\s+sin',
            r'absolutamente\s+recomendable',
            r'sin\s+duda\s+(?:el\s+)?mejor',
            r'变换味\s+verdader[óa]'
        ],
        'unverified': [
            r'fuente:\s*(?:desconocida|no\s+verificada|no\s+citada)',
            r'datos?\s+(?:no\s+)?confirmados?',
            r'seg[úu]n\s+(?:fuente\s+)?(?:an[óo]nima|desconocida)',
            r'rumores?\s+indican'
        ]
    }

    TRUST_INDICATORS = [
        r'estudio\s+de\s+', r'investigaci[óo]n\s+de',
        r'datos\s+de\s+\d{4}', r'fuente:\s+\w+',
        r'seg[úu]n\s+\w+\s+\w+\s+\w+',
        r'cita:\s+\"',
        r'referencia:\s+\d+'
    ]

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def analyze(self, text: str, source_url: Optional[str] = None) -> BiasAnalysis:
        """
        Analiza contenido en busca de sesgo.

        Args:
            text: Texto a analizar
            source_url: URL de la fuente (opcional)

        Returns:
            BiasAnalysis con resultados del análisis
        """
        if self.ai_client and self.ai_client.is_available():
            return self._analyze_with_ai(text)
        return self._analyze_fallback(text)

    def _analyze_with_ai(self, text: str) -> BiasAnalysis:
        """Analiza usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "bias")
            if result.success:
                parsed = result.metadata
                return BiasAnalysis(
                    is_biased=parsed.get('biased', False),
                    bias_type=parsed.get('type', 'unknown'),
                    severity=parsed.get('severity', 0.5),
                    indicators=parsed.get('indicators', []),
                    reasoning=parsed.get('reason', 'Análisis IA'),
                    recommendations=parsed.get('recommendations', [])
                )
        except Exception as e:
            logger.warning(f"AI bias analysis failed: {e}")
        return self._analyze_fallback(text)

    def _analyze_fallback(self, text: str) -> BiasAnalysis:
        """Analiza usando patrones."""
        text_lower = text.lower()
        detected_indicators = []
        bias_types = []

        for bias_type, patterns in self.MARKETING_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    detected_indicators.append(pattern)
                    if bias_type not in bias_types:
                        bias_types.append(bias_type)

        trust_matches = sum(1 for p in self.TRUST_INDICATORS if re.search(p, text_lower, re.IGNORECASE))

        is_biased = len(detected_indicators) >= 2 or len(bias_types) > 0

        if trust_matches >= 2 and len(detected_indicators) <= 1:
            is_biased = False

        severity = min(1.0, len(detected_indicators) * 0.15 + len(bias_types) * 0.2)

        recommendations = []
        if is_biased:
            recommendations.append("Verificar información con fuentes primarias")
            if 'promotional' in bias_types:
                recommendations.append("Buscar datos independientes del producto/servicio")
            if 'affiliate' in bias_types:
                recommendations.append("Identificar relaciones de afiliación")

        return BiasAnalysis(
            is_biased=is_biased,
            bias_type=', '.join(bias_types) if bias_types else 'unknown',
            severity=severity,
            indicators=detected_indicators[:10],
            reasoning=f"Detectados {len(detected_indicators)} indicadores de sesgo, {trust_matches} indicadores de confianza",
            recommendations=recommendations
        )

    def batch_analyze(self, texts: List[str]) -> List[BiasAnalysis]:
        """Analiza múltiples textos."""
        return [self.analyze(t) for t in texts]

    def filter_unbiased(self, analyses: List[BiasAnalysis]) -> List[BiasAnalysis]:
        """Filtra análisis para retornar solo los no sesgados."""
        return [a for a in analyses if not a.is_biased or a.severity < 0.5]