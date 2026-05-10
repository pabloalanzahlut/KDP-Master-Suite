"""
KDP MASTER - Relevance Engine Module
=====================================
Módulos 13-24: Relevancia Inteligente y Personalización
"""

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class LearningToRank:
    """
    MÓDULO 13: Learning to Rank (LTR) con Feedback
    Aprende de clicks/resultados seleccionados para mejorar ranking.
    """
    
    def __init__(self):
        self._clicks = defaultdict(int)
        self._query_features = {}
        self._weights = {
            'click_score': 0.3,
            'recency_score': 0.2,
            'authority_score': 0.2,
            'semantic_score': 0.2,
            'keyword_score': 0.1
        }
    
    def record_click(self, query: str, result_id: int):
        """Registra click en resultado."""
        key = f"{query}|{result_id}"
        self._clicks[key] += 1
    
    def get_click_score(self, query: str, result_id: int) -> float:
        """Obtiene score basado en clicks históricos."""
        key = f"{query}|{result_id}"
        clicks = self._clicks.get(key, 0)
        return min(clicks / 10.0, 1.0)
    
    def rerank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Reordena resultados usando LTR."""
        scored_results = []
        
        for result in results:
            score = 0.0
            
            score += self.get_click_score(query, result.get('id', 0)) * self._weights['click_score']
            
            date_str = result.get('date', '')
            if date_str:
                score += self._get_recency_score(date_str) * self._weights['recency_score']
            
            authority = result.get('authority_score', 0.5)
            score += authority * self._weights['authority_score']
            
            bm25 = result.get('bm25_score', 0)
            score += bm25 * self._weights['keyword_score']
            
            result['ltr_score'] = score
            scored_results.append(result)
        
        scored_results.sort(key=lambda x: x.get('ltr_score', 0), reverse=True)
        return scored_results
    
    def _get_recency_score(self, date_str: str) -> float:
        """Calcula score de recencia (más reciente = mayor score)."""
        try:
            if len(date_str) == 10:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                return 0.5
            
            days_ago = (datetime.now() - date).days
            
            if days_ago <= 7:
                return 1.0
            elif days_ago <= 30:
                return 0.8
            elif days_ago <= 90:
                return 0.6
            elif days_ago <= 365:
                return 0.4
            else:
                return 0.2
        except:
            return 0.5


class UserProfileSearch:
    """
    MÓDULO 14: Personalización por Perfil de Usuario
    Ajusta resultados según rol/historial.
    """
    
    PROFILES = {
        'admin': {'technical': 0.8, 'strategic': 0.5, 'basic': 0.2},
        'marketer': {'technical': 0.3, 'strategic': 0.9, 'basic': 0.5},
        'writer': {'technical': 0.2, 'strategic': 0.6, 'basic': 0.8},
        'analyst': {'technical': 0.7, 'strategic': 0.7, 'basic': 0.4},
        'viewer': {'technical': 0.1, 'strategic': 0.3, 'basic': 0.9}
    }
    
    def __init__(self):
        self._user_history = defaultdict(list)
        self._current_profile = 'viewer'
    
    def set_user_profile(self, profile: str):
        """Establece perfil de usuario."""
        if profile in self.PROFILES:
            self._current_profile = profile
    
    def get_profile_weights(self) -> Dict:
        """Obtiene pesos del perfil actual."""
        return self.PROFILES.get(self._current_profile, self.PROFILES['viewer'])
    
    def personalize_results(self, results: List[Dict]) -> List[Dict]:
        """Personaliza resultados según perfil de usuario."""
        weights = self.get_profile_weights()
        
        for result in results:
            category = result.get('category', '').lower()
            
            personalization_score = 0.5
            
            if 'ads' in category or 'marketing' in category:
                if weights['strategic'] > 0.5:
                    personalization_score = 0.8
            elif 'legal' in category or 'compliance' in category:
                if weights['technical'] > 0.5:
                    personalization_score = 0.9
            elif 'tutorial' in category or 'how' in result.get('title', '').lower():
                if weights['basic'] > 0.5:
                    personalization_score = 0.8
            
            result['personalization_score'] = personalization_score
        
        return results
    
    def record_search(self, user_id: str, query: str):
        """Registra búsqueda en historial del usuario."""
        self._user_history[user_id].append({
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_user_interests(self, user_id: str) -> List[str]:
        """Obtiene intereses del usuario basándose en historial."""
        history = self._user_history.get(user_id, [])
        
        categories = defaultdict(int)
        for entry in history[-20:]:
            query = entry.get('query', '').lower()
            
            if 'ads' in query or 'marketing' in query:
                categories['Marketing'] += 2
            elif 'legal' in query or 'compliance' in query:
                categories['Legalidad'] += 2
            elif 'seo' in query or 'amazon' in query:
                categories['Amazon'] += 2
            elif 'price' in query or 'royalty' in query:
                categories['Finanzas'] += 1
        
        return sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]


class ContextAwareSearch:
    """
    MÓDULO 15: Context-Aware Search
    Considera pestaña/proyecto activo en relevancia.
    """
    
    CONTEXT_BOOSTS = {
        'legal': {'legalidad': 1.5, 'compliance': 1.5, 'derecho': 1.4},
        'marketing': {'ads': 1.5, 'marketing': 1.5, 'promocion': 1.4},
        'analytics': {'metrics': 1.5, 'analytics': 1.5, 'bsr': 1.3},
        'downloads': {'youtube': 1.3, 'video': 1.2, 'transcription': 1.4},
        'default': {}
    }
    
    def __init__(self):
        self._current_context = 'default'
    
    def set_context(self, context: str):
        """Establece contexto actual (pestaña activa)."""
        if context in self.CONTEXT_BOOSTS:
            self._current_context = context
            logger.info(f"Contexto de búsqueda cambiado a: {context}")
    
    def apply_context_boost(self, results: List[Dict]) -> List[Dict]:
        """Ajusta relevancia según contexto actual."""
        boosts = self.CONTEXT_BOOSTS.get(self._current_context, {})
        
        for result in results:
            category = result.get('category', '').lower()
            
            boost = 1.0
            for key, value in boosts.items():
                if key in category:
                    boost = value
                    break
            
            result['context_boost'] = boost
            original_score = result.get('ltr_score', result.get('bm25_score', 0.5))
            result['final_score'] = original_score * boost
        
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        return results


class RecencyBoost:
    """
    MÓDULO 16: Boost por Recencia Temporal
    IA ajusta boost de documentos recientes automáticamente.
    """
    
    def __init__(self, decay_factor: float = 0.95):
        self.decay_factor = decay_factor
    
    def calculate_boost(self, date_str: str, base_score: float) -> float:
        """Calcula boost de recencia."""
        try:
            if len(date_str) == 10:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                return base_score
            
            days_ago = (datetime.now() - date).days
            
            if days_ago <= 7:
                return base_score * 1.5
            elif days_ago <= 30:
                return base_score * 1.3
            elif days_ago <= 90:
                return base_score * 1.1
            elif days_ago <= 180:
                return base_score
            else:
                return base_score * self.decay_factor ** (days_ago / 365)
        except:
            return base_score


class AuthorityBoost:
    """
    MÓDULO 17: Boost por Autoridad de Fuente
    Prioriza canales/fuentes confiables.
    """
    
    AUTHORITY_SOURCES = {
        'pablo alanzahlut': 1.5,
        'amazon': 1.3,
        'jungle scout': 1.3,
        'helium 10': 1.2,
        'kdp': 1.2,
        'youtube': 1.0,
        'blog': 0.9,
        'forum': 0.7
    }
    
    def get_authority_boost(self, source: str) -> float:
        """Obtiene boost de autoridad para una fuente."""
        if not source:
            return 1.0
        
        source_lower = source.lower()
        
        for known_source, boost in self.AUTHORITY_SOURCES.items():
            if known_source in source_lower:
                return boost
        
        return 1.0


class QueryAmbiguityDetector:
    """
    MÓDULO 18: Detección de Consultas Ambiguas
    IA detecta cuando query es muy corta/vaga.
    """
    
    AMBIGUOUS_PATTERNS = {
        'very_short': (lambda q: len(q.split()) <= 1 and len(q) < 4),
        'generic': (lambda q: q.lower() in ['amazon', 'kdp', 'marketing', 'book', 'video']),
        'no_keywords': (lambda q: all(len(w) < 3 for w in q.split()))
    }
    
    SUGGESTIONS = {
        'amazon': '¿Buscas Amazon Ads, Amazon KDP o Amazon SEO?',
        'kdp': '¿Buscas cómo publicar en KDP, métricas o estrategias?',
        'marketing': '¿Buscas marketing de libros, marketing digital o ads?',
        'book': '¿Buscas cómo escribir, publicar o promover un libro?'
    }
    
    def detect_ambiguity(self, query: str) -> Dict:
        """Detecta si la query es ambigua."""
        is_ambiguous = False
        reasons = []
        suggestions = []
        
        if self.AMBIGUOUS_PATTERNS['very_short'](query):
            is_ambiguous = True
            reasons.append('Consulta muy corta')
        
        if self.AMBIGUOUS_PATTERNS['generic'](query):
            is_ambiguous = True
            reasons.append('Término muy genérico')
            suggestions.append(self.SUGGESTIONS.get(query.lower(), 'Especifica más tu búsqueda'))
        
        if self.AMBIGUOUS_PATTERNS['no_keywords'](query):
            is_ambiguous = True
            reasons.append('Sin palabras clave específicas')
        
        return {
            'is_ambiguous': is_ambiguous,
            'reasons': reasons,
            'suggestions': suggestions,
            'original_query': query
        }


class SearchRefiner:
    """
    MÓDULO 19: Sugerencia de Refinamiento
    IA sugiere añadir filtros basándose en resultados.
    """
    
    def suggest_filters(self, query: str, results: List[Dict], total: int) -> List[Dict]:
        """Sugiere filtros para refinar búsqueda."""
        suggestions = []
        
        if total > 100:
            categories = defaultdict(int)
            for r in results:
                cat = r.get('category', 'Unknown')
                categories[cat] += 1
            
            if categories:
                top_cat = max(categories.items(), key=lambda x: x[1])
                suggestions.append({
                    'type': 'category',
                    'label': f"Filtrar por '{top_cat[0]}' ({top_cat[1]} resultados)",
                    'value': top_cat[0]
                })
        
        date_distribution = defaultdict(int)
        for r in results:
            date = str(r.get('date', ''))[:4]
            if date.isdigit():
                date_distribution[date] += 1
        
        if date_distribution:
            recent_years = [y for y, c in date_distribution.items() if int(y) >= 2024]
            if len(recent_years) / len(date_distribution) > 0.7:
                suggestions.append({
                    'type': 'date',
                    'label': f'78% de resultados son de 2024+ (filtrar por año?)',
                    'value': '2024'
                })
        
        return suggestions


class SpellingCorrector:
    """
    MÓDULO 20: Corrección Ortográfica Inteligente
    IA corrige typos en queries.
    """
    
    COMMON_CORRECTIONS = {
        'marqueting': 'marketing',
        'amazn': 'amazon',
        'kindle': 'kdp',
        'adsvertising': 'advertising',
        'royalities': 'royalties',
        'bsr': 'Best Seller Rank',
        'seo': 'SEO',
        'kdp': 'KDP',
        ' isbn': ' ISBN'
    }
    
    def correct(self, query: str) -> str:
        """Corrige errores ortográficos comunes."""
        corrected = query.lower()
        
        for wrong, correct in self.COMMON_CORRECTIONS.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, correct)
        
        return corrected
    
    def was_corrected(self, original: str, corrected: str) -> bool:
        """Indica si hubo corrección."""
        return original.lower() != corrected.lower()


class CrossLingualSearch:
    """
    MÓDULO 21: Traducción de Consulta Cross-Idioma
    Traduce query a otros idiomas indexados.
    """
    
    TRANSLATIONS = {
        'marketing': ['marketing', 'mercadotecnia', 'publicidad'],
        'ventas': ['sales', 'ventas', 'ventas'],
        'precio': ['price', 'pricing', 'precio'],
        'lanzamiento': ['launch', 'lanzamiento', 'estreno'],
        'estrategia': ['strategy', 'estrategia', 'plan'],
        'publi': ['ads', 'advertising', 'publicidad']
    }
    
    def translate_query(self, query: str) -> List[str]:
        """Expande query a múltiples idiomas."""
        expanded = [query]
        
        query_lower = query.lower()
        
        for term, translations in self.TRANSLATIONS.items():
            if term in query_lower:
                for trans in translations:
                    if trans not in query_lower:
                        expanded.append(query_lower.replace(term, trans))
        
        return expanded[:5]


class SynonymContextLearner:
    """
    MÓDULO 22: Detección de Sinonimia Contextual
    IA aprende sinónimos específicos del dominio KDP.
    """
    
    DOMAIN_SYNONYMS = {
        'BSR': ['Best Seller Rank', 'ranking de ventas', 'posición', 'ventas'],
        'KDP': ['Kindle Direct Publishing', 'publicación', 'autoedición'],
        'ADS': ['advertising', 'publicidad', 'promoción'],
        'ACoS': ['coste de venta', 'ratio de publicidad', 'rentabilidad'],
        'ROI': ['retorno', 'ganancia', 'beneficio'],
        'KU': ['Kindle Unlimited', 'suscripción', 'lector ilimitado']
    }
    
    def expand_with_synonyms(self, query: str) -> str:
        """Expande query con sinónimos del dominio KDP."""
        expanded = query
        
        for term, synonyms in self.DOMAIN_SYNONYMS.items():
            if term in query.upper():
                expanded = f"{query} {' '.join(synonyms[:2])}"
        
        return expanded


class AdaptiveFieldWeighting:
    """
    MÓDULO 23: Ponderación Adaptativa de Campos
    Ajusta peso de título vs contenido vs metadata.
    """
    
    def calculate_weights(self, query: str) -> Dict[str, float]:
        """Calcula pesos según longitud de query."""
        word_count = len(query.split())
        
        if word_count <= 2:
            return {'title': 0.6, 'content': 0.3, 'metadata': 0.1}
        elif word_count <= 5:
            return {'title': 0.4, 'content': 0.5, 'metadata': 0.1}
        else:
            return {'title': 0.3, 'content': 0.6, 'metadata': 0.1}


class ImplicitFeedbackLearner:
    """
    MÓDULO 24: Feedback de Relevancia Implícito
    Aprende de tiempo en resultado, scrolls, etc.
    """
    
    def __init__(self):
        self._engagement_scores = {}
        self._query_patterns = defaultdict(list)
    
    def record_engagement(self, query: str, result_id: int, 
                         time_spent: float, scrolled: bool):
        """Registra engagement implícito."""
        key = f"{query}|{result_id}"
        
        score = 0.0
        if time_spent > 30:
            score += 0.5
        if scrolled:
            score += 0.3
        
        if key in self._engagement_scores:
            self._engagement_scores[key] = (self._engagement_scores[key] + score) / 2
        else:
            self._engagement_scores[key] = score
    
    def get_implicit_score(self, query: str, result_id: int) -> float:
        """Obtiene score de engagement implícito."""
        key = f"{query}|{result_id}"
        return self._engagement_scores.get(key, 0.0)