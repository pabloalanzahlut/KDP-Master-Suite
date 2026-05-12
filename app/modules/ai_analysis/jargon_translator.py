"""
AI Analysis - Módulo 24: Traductor de Jerga Técnica a Términos KDP
==================================================================
Normaliza lenguaje del creador a terminología estandarizada de tu KB
(ej. "funnel" → "embudo de ventas KDP").

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    original: str
    translated: str
    terms_mapped: int
    term_mappings: List[Dict[str, str]]
    coverage_percentage: float


class JargonTranslator:
    """
    Traductor de Jerga Técnica a Términos KDP
    Normaliza lenguaje a terminología estandarizada.
    """

    TERM_MAPPINGS = {
        'funnel': 'embudo de ventas',
        'lead magnet': 'recurso gratuito de captura',
        'squeeze page': 'página de captura',
        'opt-in': 'registro/suscripción',
        'landing page': 'página de destino',
        'call to action': 'llamada a la acción',
        'cta': 'botón de acción',
        'bounce rate': 'tasa de rebote',
        'conversion rate': 'tasa de conversión',
        'roi': 'retorno de inversión',
        'ltv': 'valor de vida del cliente',
        'cac': 'costo de adquisición',
        'churn': 'tasa de abandono',
        'upsell': 'venta cruzada ascendente',
        'cross-sell': 'venta cruzada',
        'downsell': 'venta cruzada descendente',
        'exit intent': 'intención de salida',
        'popup': 'ventana emergente',
        'lead': 'prospecto/cliente potencial',
        'cold audience': 'audiencia fría',
        'warm audience': 'audiencia cálida',
        'hot audience': 'audiencia caliente',
        'sales funnel': 'embudo de ventas',
        'email funnel': 'secuencia de email',
        'webinar': 'seminario web',
        'launch': 'lanzamiento',
        'pre-launch': 'pre-lanzamiento',
        'launch date': 'fecha de lanzamiento',
        'affiliate': 'afiliado',
        'commission': 'comisión',
        'affiliate link': 'enlace de afiliado',
        'seo': 'optimización para buscadores',
        'sem': 'marketing en buscadores',
        'ppc': 'pago por clic',
        'cpc': 'costo por clic',
        'cpm': 'costo por mil impressions',
        'ctr': 'tasa de clic',
        'impression': 'impresión/vista',
        'remarketing': 'retargeting',
        'retargeting': 'remarketing',
        'pixel': 'píxel de seguimiento',
        'tracking': 'seguimiento',
        'analytics': 'analítica',
        'dashboard': 'panel de control',
        'kpi': 'indicador clave de rendimiento',
        'metric': 'métrica',
        'benchmark': 'referencia',
        'niche': 'nichos/micro-nicho',
        'authority': 'autoridad',
        'brand': 'marca',
        'branding': 'creación de marca',
        'copywriting': 'redacción de anuncios',
        'swipe file': 'archivo de inspiraciones',
        '素材': 'materiales/recursos',
        'funnel builder': 'constructor de embudos',
        'email marketing': 'marketing por email',
        'email sequence': 'secuencia de emails',
        'autoresponder': 'respondedor automático',
        'broadcast': 'transmisión de email',
        'squeeze page': 'página de captura de emails',
        'bridge page': 'página puente',
        'bridge video': 'video puente',
        'tripwire': 'oferta de bajo coste',
        'core offer': 'oferta principal',
        'backend': 'backend/servicios adicionales',
        'backend offer': 'oferta de backend',
        'maximize': 'maximizar',
        'scale': 'escalar',
        'automate': 'automatizar',
        'outsource': 'externalizar',
        'delegation': 'delegación',
    }

    SPANISH_EQUIVALENTS = {
        'funnel': 'embudo',
        'sales funnel': 'embudo de ventas',
        'email funnel': 'embudo de email',
        'leads': 'prospectos',
        'conversion': 'conversión',
        'inversión': 'inversión',
    }

    def __init__(self, ai_client=None):
        self._ai_client = ai_client
        self._stats = {
            'total_translated': 0,
            'terms_mapped': 0,
            'coverage_avg': 0.0
        }

    def translate(self, text: str, preserve_original: bool = False) -> TranslationResult:
        """
        Traduce jerga técnica a términos KDP.

        Args:
            text: Texto a traducir
            preserve_original: Si mantener términos originales en comentarios

        Returns:
            TranslationResult con traducción y mappings
        """
        self._stats['total_translated'] += 1

        ai_translation = None
        if self._ai_client and self._ai_client.is_available():
            result = self._ai_client.analyze(text, "jargon")
            if result.success:
                ai_translation = result.metadata.get('translated', None)

        translated = text
        mappings = []

        if ai_translation:
            translated = ai_translation
        else:
            translated, mappings = self._local_translate(text, preserve_original)

        coverage = self._calculate_coverage(text, len(mappings))

        self._stats['terms_mapped'] += len(mappings)
        self._stats['coverage_avg'] = (
            (self._stats['coverage_avg'] * (self._stats['total_translated'] - 1) + coverage) /
            self._stats['total_translated']
        )

        return TranslationResult(
            original=text,
            translated=translated,
            terms_mapped=len(mappings),
            term_mappings=mappings,
            coverage_percentage=coverage
        )

    def _local_translate(self, text: str, preserve: bool) -> Tuple[str, List[Dict]]:
        """Traducción local sin IA."""
        translated = text
        mappings = []
        used_terms = set()

        for jargon, kdp_term in self.TERM_MAPPINGS.items():
            if jargon in used_terms:
                continue

            pattern = re.compile(r'\b' + re.escape(jargon) + r'\b', re.IGNORECASE)

            def replacement(match):
                original_term = match.group(0)
                if preserve:
                    return f"{kdp_term} ({original_term})"
                return kdp_term

            new_translated = pattern.sub(replacement, translated)

            if new_translated != translated:
                mappings.append({
                    'original': jargon,
                    'kdp_term': kdp_term,
                    'occurrences': len(re.findall(pattern, translated))
                })
                used_terms.add(jargon)
                translated = new_translated

        return translated, mappings

    def _calculate_coverage(self, text: str, terms_mapped: int) -> float:
        """Calcula porcentaje de cobertura."""
        text_lower = text.lower()
        jargon_count = sum(1 for term in self.TERM_MAPPINGS if term in text_lower)

        if jargon_count == 0:
            return 100.0 if terms_mapped == 0 else 50.0

        coverage = (terms_mapped / jargon_count) * 100
        return min(coverage, 100.0)

    def add_custom_mapping(self, jargon: str, kdp_term: str):
        """Añade mapeo personalizado."""
        self.TERM_MAPPINGS[jargon.lower()] = kdp_term

    def get_mappings(self) -> Dict[str, str]:
        """Retorna todos los mapeos disponibles."""
        return self.TERM_MAPPINGS.copy()

    def batch_translate(
        self,
        texts: List[str],
        preserve_original: bool = False
    ) -> List[TranslationResult]:
        """Traduce múltiples textos."""
        return [self.translate(text, preserve_original) for text in texts]

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        stats = self._stats.copy()
        if stats['total_translated'] > 0:
            stats['avg_terms_per_text'] = stats['terms_mapped'] / stats['total_translated']
        else:
            stats['avg_terms_per_text'] = 0.0
        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_translated': 0,
            'terms_mapped': 0,
            'coverage_avg': 0.0
        }


def create_translator(ai_client=None) -> JargonTranslator:
    """
    Factory function para crear traductor.
    """
    return JargonTranslator(ai_client=ai_client)


def quick_translate(text: str) -> str:
    """
    Función de conveniencia para traducción rápida.
    """
    translator = JargonTranslator()
    result = translator.translate(text)
    return result.translated