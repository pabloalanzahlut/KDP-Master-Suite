"""
AI Analysis - Stale Information Detector
=========================================
Módulo 37: Detecta información obsoleta en contenido.
Usa Ollama para análisis de fechas y políticas.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class StaleItem:
    text: str
    date_mentioned: Optional[str]
    issue_type: str
    severity: float
    recommendation: str


@dataclass
class StaleDetectionResult:
    is_stale: bool
    stale_items: List[StaleItem]
    overall_score: float
    last_verified: Optional[str]
    warnings: List[str]
    recommendations: List[str]


class StaleDetector:
    """
    Detector de información obsoleta.
    Analiza fechas, políticas y referencias temporales.
    """

    DATE_PATTERNS = [
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{4}\b',
    ]

    POLICY_PATTERNS = [
        r'pol[íi]tica\s+de\s+(?:privacidad|devoluciones|env[íi]os|terminos)',
        r't[ée]rminos\s+y\s+condiciones',
        r'acuerdo\s+de\s+(?:servicio|nivel)',
        r'contrato\s+de',
        r'licencia\s+de\s+uso'
    ]

    VERIFICATION_KEYWORDS = [
        r'actualizado\s+el', r'verificado\s+el', r'revisado\s+el',
        r'[úu]ltima\s+actualizaci[óo]n', r'v[áa]lido\s+hasta',
        r'vigente\s+desde', r'fecha\s+de\s+publicaci[óo]n'
    ]

    STALE_THRESHOLD_DAYS = 180

    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.reference_date = datetime.now()

    def detect(self, text: str, content_type: Optional[str] = None) -> StaleDetectionResult:
        """
        Detecta información obsoleta.

        Args:
            text: Texto a analizar
            content_type: Tipo de contenido (opcional)

        Returns:
            StaleDetectionResult con items obsoletos
        """
        if self.ai_client and self.ai_client.is_available():
            return self._detect_with_ai(text)
        return self._detect_fallback(text, content_type)

    def _detect_with_ai(self, text: str) -> StaleDetectionResult:
        """Detecta usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "stale")
            if result.success:
                parsed = result.metadata
                stale_items = [
                    StaleItem(
                        text=item.get('text', ''),
                        date_mentioned=item.get('date'),
                        issue_type=item.get('type', 'unknown'),
                        severity=item.get('severity', 0.5),
                        recommendation=item.get('recommendation', 'Revisar')
                    )
                    for item in parsed.get('outdated_items', [])
                ]

                return StaleDetectionResult(
                    is_stale=parsed.get('stale', False),
                    stale_items=stale_items,
                    overall_score=parsed.get('score', 0.5),
                    last_verified=parsed.get('verified_date'),
                    warnings=parsed.get('warnings', []),
                    recommendations=parsed.get('recommendations', [])
                )
        except Exception as e:
            logger.warning(f"AI stale detection failed: {e}")
        return self._detect_fallback(text, None)

    def _detect_fallback(self, text: str, content_type: Optional[str]) -> StaleDetectionResult:
        """Detecta usando análisis de fechas."""
        stale_items = []
        warnings = []

        dates = self._extract_dates(text)
        policy_mentions = self._find_policy_mentions(text)

        for date_str, position in dates:
            days_old = self._estimate_days_old(date_str)

            if days_old and days_old > self.STALE_THRESHOLD_DAYS:
                stale_items.append(StaleItem(
                    text=text[max(0, position-30):position+len(date_str)+30],
                    date_mentioned=date_str,
                    issue_type='old_date',
                    severity=min(1.0, days_old / 365),
                    recommendation=f"Datos de hace {days_old} días, verificar vigencia"
                ))

        if policy_mentions:
            has_verification = any(
                re.search(p, text, re.IGNORECASE)
                for p in self.VERIFICATION_KEYWORDS
            )

            if not has_verification:
                warnings.append("Políticas mencionadas sin fecha de verificación")
                if content_type in ['tutorial', 'reference']:
                    stale_items.append(StaleItem(
                        text='; '.join(policy_mentions[:2]),
                        date_mentioned=None,
                        issue_type='unverified_policy',
                        severity=0.6,
                        recommendation="Agregar fecha de última actualización de políticas"
                    ))

        overall_score = 0.0
        if stale_items:
            overall_score = min(1.0, sum(s.severity for s in stale_items) / len(stale_items))

        recommendations = []
        if stale_items:
            recommendations.append("Revisar fechas en contenido para verificar vigencia")
            recommendations.append("Actualizar referencias a políticas y términos")
        if overall_score > 0.7:
            recommendations.append("Considerar reescribir secciones con información desactualizada")

        last_verified = self._extract_verification_date(text)

        return StaleDetectionResult(
            is_stale=len(stale_items) > 0 or overall_score > 0.5,
            stale_items=stale_items,
            overall_score=overall_score,
            last_verified=last_verified,
            warnings=warnings,
            recommendations=recommendations
        )

    def _extract_dates(self, text: str) -> List[Tuple[str, int]]:
        """Extrae fechas del texto."""
        dates = []
        for pattern in self.DATE_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                dates.append((match.group(), match.start()))
        return dates

    def _find_policy_mentions(self, text: str) -> List[str]:
        """Encuentra menciones de políticas."""
        mentions = []
        for pattern in self.POLICY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentions.extend(matches)
        return list(dict.fromkeys(mentions))

    def _extract_verification_date(self, text: str) -> Optional[str]:
        """Extrae fecha de verificación."""
        for pattern in self.VERIFICATION_KEYWORDS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                after = text[match.end():match.end()+50]
                date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}', after)
                if date_match:
                    return date_match.group()
        return None

    def _estimate_days_old(self, date_str: str) -> Optional[int]:
        """Estima días desde fecha."""
        try:
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                date = datetime.strptime(date_str, '%Y-%m-%d')
            elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                date = datetime.strptime(date_str, '%m/%d/%Y')
            else:
                return None

            return (self.reference_date - date).days
        except:
            return None

    def batch_detect(self, texts: List[str]) -> List[StaleDetectionResult]:
        """Detecta en múltiples textos."""
        return [self.detect(t) for t in texts]

    def get_stale_summary(self, results: List[StaleDetectionResult]) -> Dict[str, Any]:
        """Resumen de detección de obsolescencia."""
        total = len(results)
        stale_count = sum(1 for r in results if r.is_stale)
        avg_score = sum(r.overall_score for r in results) / max(total, 1)

        return {
            'total_analyzed': total,
            'stale_count': stale_count,
            'fresh_count': total - stale_count,
            'average_stale_score': round(avg_score, 2),
            'requires_update': stale_count > total * 0.3
        }