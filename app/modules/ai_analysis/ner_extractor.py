"""
AI Analysis - Módulo 25: Extractor de Entidades Nombradas (NER) Local
====================================================================
Identifica nombres de herramientas, plataformas, métricas y personas
mencionadas para indexación estructurada.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EntityType(Enum):
    TOOL = "tool"
    PLATFORM = "platform"
    METRIC = "metric"
    PERSON = "person"
    BRAND = "brand"
    PRODUCT = "product"
    CONCEPT = "concept"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    text: str
    entity_type: EntityType
    confidence: float
    context: str
    position: int


@dataclass
class NERResult:
    entities: List[Entity]
    entity_count: int
    entities_by_type: Dict[str, int]
    unique_entities: Set[str]


class LocalNERExtractor:
    """
    Extractor de Entidades Nombradas (NER) Local
    Identifica herramientas, plataformas, métricas y personas.
    """

    KNOWN_TOOLS = [
        'canva', 'shopify', 'wordpress', 'elementor', 'thrive architect',
        'convertkit', 'mailchimp', 'activecampaign', 'klaviyo', 'sendinblue',
        'mailerlite', 'getresponse', 'aweber', 'sendgrid', 'postmark',
        'stripe', 'paypal', 'square', 'gumroad', 'wooCommerce',
        'easydigitaldownloads', 'memberpress', 'teachable', 'thinkific',
        'kajabi', 'podia', 'gumroad', 'lemmatize', 'lemmatizer',
        'spacy', 'nltk', 'transformers', 'hugging face', 'openai',
        'anthropic', 'google colab', 'jupyter', 'pandas', 'numpy',
        'selenium', 'playwright', 'puppeteer', 'beautifulsoup', 'scrapy',
        'zapier', 'make', 'integromat', 'ifttt', 'webhook',
        'typeform', 'jotform', 'google forms', 'tally', 'cal.com',
        'calendly', 'carrd', 'systeme', 'clickfunnels', 'cartflow',
    ]

    KNOWN_PLATFORMS = [
        'youtube', 'instagram', 'tiktok', 'twitter', 'x', 'facebook',
        'linkedin', 'pinterest', 'snapchat', 'reddit', 'quora',
        'medium', 'substack', 'gumroad', 'kajabi', 'teachable',
        'thinkific', 'udemy', 'coursera', 'skillshare',
        'amazon', 'etsy', 'ebay', 'shopify', 'woocommerce',
        'google', 'bing', 'yahoo', 'duckduckgo',
        'chatgpt', 'claude', 'gemini', 'copilot', 'llama',
        'ollama', 'huggingface', 'replicate',
    ]

    KNOWN_METRICS = [
        'roi', 'roas', 'ctr', 'cpc', 'cpm', 'cac', 'clv', 'ltv', 'churn',
        'conversion rate', 'bounce rate', 'retention rate',
        'engagement rate', 'open rate', 'click rate',
        'revenue', 'profit', 'margin', 'ebitda',
        'mrr', 'arr', 'ltv', 'cac', 'payback period',
        'nps', 'csat', 'ces', 'kpi', 'okr',
        'traffic', 'pageviews', 'sessions', 'users', 'visitors',
        'subscribers', 'followers', 'views', 'impressions',
    ]

    KNOWN_PERSONS = [
        'jeff bezos', 'elon musk', 'steve jobs', 'bill gates', 'mark zuckerberg',
        'warren buffett', 'oprah', 'tony robbins', 'grant cardone',
        'russell brunson', 'funnel hacker', 'click funnel',
    ]

    def __init__(self, ai_client=None):
        self._ai_client = ai_client
        self._stats = {
            'total_extracted': 0,
            'entities_found': 0,
            'by_type': {et.value: 0 for et in EntityType}
        }

    def extract(self, text: str) -> NERResult:
        """
        Extrae entidades nombradas del texto.

        Args:
            text: Texo a analizar

        Returns:
            NERResult con entidades identificadas
        """
        self._stats['total_extracted'] += 1

        ai_entities = None
        if self._ai_client and self._ai_client.is_available():
            result = self._ai_client.analyze(text, "ner")
            if result.success:
                ai_entities = result.metadata.get('entities', [])

        if ai_entities:
            entities = self._parse_ai_entities(ai_entities)
        else:
            entities = self._local_extract(text)

        entities_by_type = self._count_by_type(entities)
        unique = set(e.text for e in entities)

        for etype, count in entities_by_type.items():
            if etype in self._stats['by_type']:
                self._stats['by_type'][etype] += count

        self._stats['entities_found'] += len(entities)

        return NERResult(
            entities=entities,
            entity_count=len(entities),
            entities_by_type=entities_by_type,
            unique_entities=unique
        )

    def _local_extract(self, text: str) -> List[Entity]:
        """Extracción local sin IA."""
        entities = []
        text_lower = text.lower()

        for tool in self.KNOWN_TOOLS:
            for match in re.finditer(r'\b' + re.escape(tool) + r'\b', text_lower):
                context = self._get_context(text, match.start())
                entities.append(Entity(
                    text=match.group(0).title(),
                    entity_type=EntityType.TOOL,
                    confidence=0.9,
                    context=context,
                    position=match.start()
                ))

        for platform in self.KNOWN_PLATFORMS:
            for match in re.finditer(r'\b' + re.escape(platform) + r'\b', text_lower):
                context = self._get_context(text, match.start())
                entities.append(Entity(
                    text=match.group(0).title(),
                    entity_type=EntityType.PLATFORM,
                    confidence=0.9,
                    context=context,
                    position=match.start()
                ))

        for metric in self.KNOWN_METRICS:
            for match in re.finditer(r'\b' + re.escape(metric) + r'\b', text_lower):
                context = self._get_context(text, match.start())
                entities.append(Entity(
                    text=match.group(0).upper(),
                    entity_type=EntityType.METRIC,
                    confidence=0.85,
                    context=context,
                    position=match.start()
                ))

        numbers_with_units = re.findall(r'[\d.]+\s*(%|roi|roas|ctr|cpc|cpm|kpi|hrs|dias|semanas)', text_lower)
        for match in re.finditer(r'[\d.]+\s*(%|roi|roas|ctr|cpc|cpm|kpi|hrs|dias|semanas)', text_lower):
            context = self._get_context(text, match.start())
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.METRIC,
                confidence=0.7,
                context=context,
                position=match.start()
            ))

        entities.sort(key=lambda e: e.position)

        return entities

    def _parse_ai_entities(self, ai_entities: List[Dict]) -> List[Entity]:
        """Parsea entidades de respuesta IA."""
        entities = []

        for ent_data in ai_entities:
            entity_type = EntityType.UNKNOWN
            try:
                type_str = ent_data.get('type', 'unknown').lower()
                if type_str in ['tool', 'software', 'app']:
                    entity_type = EntityType.TOOL
                elif type_str in ['platform', 'social']:
                    entity_type = EntityType.PLATFORM
                elif type_str in ['metric', 'kpi', 'measurement']:
                    entity_type = EntityType.METRIC
                elif type_str in ['person', 'author', 'speaker']:
                    entity_type = EntityType.PERSON
                elif type_str in ['brand', 'company']:
                    entity_type = EntityType.BRAND
            except Exception:
                pass

            entities.append(Entity(
                text=ent_data.get('value', ''),
                entity_type=entity_type,
                confidence=0.8,
                context='',
                position=0
            ))

        return entities

    def _get_context(self, text: str, position: int, window: int = 50) -> str:
        """Obtiene contexto alrededor de una posición."""
        start = max(0, position - window)
        end = min(len(text), position + window)
        return text[start:end].strip()

    def _count_by_type(self, entities: List[Entity]) -> Dict[str, int]:
        """Cuenta entidades por tipo."""
        counts = {}
        for entity in entities:
            etype = entity.entity_type.value
            counts[etype] = counts.get(etype, 0) + 1
        return counts

    def batch_extract(self, texts: List[str]) -> List[NERResult]:
        """Extrae de múltiples textos."""
        return [self.extract(text) for text in texts]

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        stats = self._stats.copy()
        if stats['total_extracted'] > 0:
            stats['avg_entities_per_text'] = stats['entities_found'] / stats['total_extracted']
        else:
            stats['avg_entities_per_text'] = 0.0
        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_extracted': 0,
            'entities_found': 0,
            'by_type': {et.value: 0 for et in EntityType}
        }


def create_ner_extractor(ai_client=None) -> LocalNERExtractor:
    """
    Factory function para crear extractor NER.
    """
    return LocalNERExtractor(ai_client=ai_client)


def quick_extract(text: str) -> List[str]:
    """
    Función de conveniencia para extracción rápida.
    Retorna lista de entidades únicas.
    """
    extractor = LocalNERExtractor()
    result = extractor.extract(text)
    return list(result.unique_entities)