"""
KDP MASTER - Predictive Engine Module
======================================
Módulos 49-60: Optimización Predictiva y Aprendizaje
"""

import time
import os
from typing import Dict, List, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SearchTimePredictor:
    """
    MÓDULO 49: Predicción de Tiempo de Búsqueda
    IA estima duración antes de ejecutar.
    """
    
    def __init__(self):
        self._historical_times = []
        self._avg_time_by_complexity = {
            'simple': 50,
            'medium': 150,
            'complex': 400,
            'very_complex': 800
        }
    
    def predict_time(self, query: str, filters: Dict = None) -> Dict:
        """Predice tiempo de búsqueda."""
        complexity = self._estimate_complexity(query, filters)
        
        predicted_ms = self._avg_time_by_complexity.get(complexity, 200)
        
        return {
            'predicted_ms': predicted_ms,
            'complexity': complexity,
            'suggestion': self._get_suggestion(complexity),
            'continue': predicted_ms < 5000
        }
    
    def _estimate_complexity(self, query: str, filters: Dict = None) -> str:
        """Estima complejidad de la búsqueda."""
        score = 0
        
        if len(query.split()) > 5:
            score += 2
        if len(query) > 30:
            score += 1
        if ' AND ' in query.upper() or ' OR ' in query.upper():
            score += 3
        
        if filters:
            score += len(filters)
        
        if score <= 1:
            return 'simple'
        elif score <= 3:
            return 'medium'
        elif score <= 5:
            return 'complex'
        else:
            return 'very_complex'
    
    def _get_suggestion(self, complexity: str) -> str:
        """Sugiere acción según complejidad."""
        suggestions = {
            'simple': 'Búsqueda rápida',
            'medium': 'Tiempo normal',
            'complex': 'Considerea simplificar la query',
            'very_complex': 'Tiempo estimado >5s. ¿Desea continuar?'
        }
        return suggestions.get(complexity, '')
    
    def record_actual_time(self, query: str, elapsed_ms: float):
        """Registra tiempo real para aprendizaje."""
        self._historical_times.append(elapsed_ms)
        if len(self._historical_times) > 100:
            self._historical_times = self._historical_times[-100:]


class QueryOptimizer:
    """
    MÓDULO 50: Optimización de Query Automática
    IA reescribe query para mejor rendimiento.
    """
    
    def optimize(self, query: str) -> str:
        """Optimiza query para mejor rendimiento."""
        optimized = query.strip()
        
        if len(query.split()) > 10:
            words = query.split()
            optimized = ' '.join(words[:10])
        
        optimized = optimized.replace('  ', ' ')
        
        return optimized
    
    def suggest_improvements(self, query: str, results_count: int) -> List[str]:
        """Sugiere mejoras para la query."""
        suggestions = []
        
        if results_count == 0:
            if len(query.split()) < 3:
                suggestions.append("Añade más palabras clave específicas")
            
            suggestions.append("Prueba con sinónimos")
            suggestions.append("Reduce los filtros activos")
        
        if results_count > 100:
            suggestions.append("La query es muy amplia, considera ser más específico")
        
        return suggestions


class SmartCache:
    """
    MÓDULO 51: Cache Inteligente de Embeddings
    IA decide qué embeddings cachear.
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self._access_count = defaultdict(int)
        self._max_size = max_size
    
    def should_cache(self, query: str) -> bool:
        """Decide si la query merece cache."""
        return query.lower() not in ['test', 'prueba', 'xxx']
    
    def get_cached_embedding(self, query: str) -> Optional[List[float]]:
        """Obtiene embedding cacheado."""
        key = query.lower().strip()
        
        if key in self._cache:
            self._access_count[key] += 1
            return self._cache[key]
        
        return None
    
    def cache_embedding(self, query: str, embedding: List[float]):
        """Cachea embedding."""
        if not self.should_cache(query):
            return
        
        key = query.lower().strip()
        
        if len(self._cache) >= self._max_size:
            self._evict_least_used()
        
        self._cache[key] = embedding
        self._access_count[key] = 1
    
    def _evict_least_used(self):
        """Elimina el menos usado."""
        if not self._access_count:
            return
        
        least_used = min(self._access_count.items(), key=lambda x: x[1])
        del self._cache[least_used[0]]
        del self._access_count[least_used[0]]


class DomainAdapter:
    """
    MÓDULO 52: Adaptación de Modelo por Dominio
    IA ajusta modelo Ollama al contexto KDP.
    """
    
    DOMAIN_TERMS = {
        'kdp': ['Kindle Direct Publishing', 'publicación', 'autoedición'],
        'ads': ['Amazon Ads', 'publicidad', 'campaña'],
        'bsr': ['Best Seller Rank', 'ranking', 'ventas'],
        'seo': ['posicionamiento', 'keywords', 'búsqueda'],
        'royalty': ['regalías', 'ingresos', 'pagos'],
        'pricing': ['precio', 'tarifa', 'estrategia']
    }
    
    def adapt_prompt(self, base_prompt: str, context: str = 'kdp') -> str:
        """Adapta prompt al dominio KDP."""
        domain_terms = self.DOMAIN_TERMS.get(context, [])
        
        if domain_terms:
            terms_str = ', '.join(domain_terms[:3])
            adapted = f"{base_prompt}\n\nContexto del dominio KDP: {terms_str}"
            return adapted
        
        return base_prompt
    
    def detect_domain(self, query: str) -> str:
        """Detecta dominio de la query."""
        query_lower = query.lower()
        
        for domain, terms in self.DOMAIN_TERMS.items():
            if any(term.lower() in query_lower for term in terms):
                return domain
        
        return 'general'


class ProblematicQueryDetector:
    """
    MÓDULO 53: Detección de Consultas Problemáticas
    IA identifica queries que suelen fallar.
    """
    
    def __init__(self):
        self._failed_queries = Counter()
        self._zero_result_queries = Counter()
    
    def record_failure(self, query: str, has_results: bool):
        """Registra resultado de búsqueda."""
        key = query.lower().strip()
        
        if not has_results:
            self._zero_result_queries[key] += 1
            self._failed_queries[key] += 1
    
    def is_problematic(self, query: str) -> Dict:
        """Detecta si la query es problemática."""
        key = query.lower().strip()
        
        zero_count = self._zero_result_queries.get(key, 0)
        
        if zero_count >= 3:
            return {
                'is_problematic': True,
                'reason': '多次 sin resultados',
                'suggestion': 'Reformula la query o intenta sin filtros'
            }
        
        if len(key) < 3:
            return {
                'is_problematic': True,
                'reason': 'Query muy corta',
                'suggestion': 'Añade más términos de búsqueda'
            }
        
        return {'is_problematic': False}


class ViewPreferenceLearner:
    """
    MÓDULO 54: Aprendizaje de Preferencias de Visualización
    IA aprende vista favorita del usuario.
    """
    
    VIEW_PREFERENCES = {
        'list': {'icon': '📋', 'name': 'Lista'},
        'cards': {'icon': '🃏', 'name': 'Tarjetas'},
        'tree': {'icon': '🌳', 'name': 'Árbol'}
    }
    
    def __init__(self):
        self._view_history = []
        self._default_view = 'list'
    
    def record_view_selection(self, view: str, duration_seconds: int):
        """Registra selección de vista."""
        if duration_seconds > 5:
            self._view_history.append(view)
            if len(self._view_history) > 50:
                self._view_history = self._view_history[-50:]
    
    def get_preferred_view(self) -> str:
        """Obtiene vista preferida."""
        if not self._view_history:
            return self._default_view
        
        counter = Counter(self._view_history)
        return counter.most_common(1)[0][0]
    
    def get_view_options(self) -> List[Dict]:
        """Obtiene opciones de vista."""
        preferred = self.get_preferred_view()
        
        return [
            {'id': 'list', 'icon': '📋', 'name': 'Lista', 'preferred': 'list' == preferred},
            {'id': 'cards', 'icon': '🃏', 'name': 'Tarjetas', 'preferred': 'cards' == preferred},
            {'id': 'tree', 'icon': '🌳', 'name': 'Árbol', 'preferred': 'tree' == preferred}
        ]


class RelevancePredictor:
    """
    MÓDULO 55: Predicción de Relevancia Futura
    IA predice qué resultados serán útiles.
    """
    
    def predict_relevance(self, query: str, results: List[Dict]) -> List[Dict]:
        """Predice relevancia de resultados."""
        scored_results = []
        
        for r in results:
            score = 0.5
            
            if r.get('click_score', 0) > 0:
                score += 0.2
            
            date = r.get('date', '')
            if date and ('2024' in date or '2025' in date):
                score += 0.15
            
            if r.get('personalization_score', 0) > 0.7:
                score += 0.15
            
            probability = min(score * 100, 99)
            r['relevance_probability'] = probability
            scored_results.append(r)
        
        scored_results.sort(key=lambda x: x.get('relevance_probability', 0), reverse=True)
        return scored_results


class IndexOptimizer:
    """
    MÓDULO 56: Optimización de Índices con IA
    IA decide cuándo reconstruir índices.
    """
    
    def should_rebuild(self, fragmentation: float, record_count: int) -> Dict:
        """Decide si reconstruir índices."""
        should_rebuild = False
        reason = ""
        
        if fragmentation > 0.30:
            should_rebuild = True
            reason = f"Fragmentación {fragmentation*100:.0f}% > 30%"
        
        if record_count > 10000 and fragmentation > 0.15:
            should_rebuild = True
            reason = f"Índices fragmentados en dataset grande ({record_count} registros)"
        
        return {
            'should_rebuild': should_rebuild,
            'reason': reason,
            'expected_improvement': '20-40% velocidad' if should_rebuild else None
        }


class AnomalyDetector:
    """
    MÓDULO 57: Detección de Anomalías en Búsquedas
    IA detecta patrones inusuales.
    """
    
    def __init__(self):
        self._search_count_history = []
        self._max_normal_searches = 20
    
    def detect_anomaly(self, searches_last_5min: int) -> Dict:
        """Detecta anomalías en patrón de búsquedas."""
        self._search_count_history.append(searches_last_5min)
        
        if len(self._search_count_history) > 10:
            self._search_count_history = self._search_count_history[-10:]
        
        avg = sum(self._search_count_history[:-1]) / max(len(self._search_count_history) - 1, 1)
        
        if searches_last_5min > avg * 3 and avg > 5:
            return {
                'is_anomaly': True,
                'type': 'high_activity',
                'message': f'Actividad inusualmente alta: {searches_last_5min} búsquedas en 5 min (promedio: {avg:.1f})',
                'action': 'Monitorear uso'
            }
        
        return {'is_anomaly': False}


class KeywordRecommender:
    """
    MÓDULO 58: Recomendación de Palabras Clave
    IA sugiere keywords para añadir a KB.
    """
    
    def recommend_keywords(self, zero_result_queries: List[str]) -> List[Dict]:
        """Recomienda keywords basadas en búsquedas sin resultados."""
        recommendations = []
        
        keywords = Counter()
        for query in zero_result_queries:
            words = query.lower().split()
            keywords.update([w for w in words if len(w) > 3])
        
        for word, count in keywords.most_common(10):
            recommendations.append({
                'keyword': word,
                'times_searched': count,
                'suggestion': f'Considera añadir contenido sobre "{word}" a la KB'
            })
        
        return recommendations


class InterestEvolutionAnalyzer:
    """
    MÓDULO 59: Análisis de Evolución de Intereses
    IA rastrea cómo cambian búsquedas del usuario.
    """
    
    def __init__(self):
        self._search_history = []
    
    def record_search(self, query: str, category: str = None):
        """Registra búsqueda."""
        self._search_history.append({
            'query': query,
            'category': category,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self._search_history) > 200:
            self._search_history = self._search_history[-200:]
    
    def analyze_evolution(self) -> Dict:
        """Analiza evolución de intereses."""
        if len(self._search_history) < 10:
            return {'message': 'Historial insuficiente para análisis'}
        
        recent = self._search_history[-20:]
        older = self._search_history[-50:-20] if len(self._search_history) >= 50 else []
        
        recent_cats = Counter([s.get('category') for s in recent if s.get('category')])
        older_cats = Counter([s.get('category') for s in older if s.get('category')])
        
        if not recent_cats or not older_cats:
            return {'message': 'Sin datos de categoría suficientes'}
        
        recent_top = recent_cats.most_common(1)[0][0] if recent_cats else None
        older_top = older_cats.most_common(1)[0][0] if older_cats else None
        
        if recent_top != older_top:
            return {
                'trend': 'shifted',
                'previous_interest': older_top,
                'current_interest': recent_top,
                'message': f'Tu interés cambió de "{older_top}" a "{recent_top}"'
            }
        
        return {
            'trend': 'stable',
            'main_interest': recent_top,
            'message': f'Interés consistente en "{recent_top}"'
        }


class SearchInsightsGenerator:
    """
    MÓDULO 60: Generación de Insights de Búsqueda
    IA crea reporte estratégico de patrones.
    """
    
    def generate_insights(self, search_history: List[Dict], 
                         results_by_query: Dict[str, int]) -> Dict:
        """Genera insights de patrones de búsqueda."""
        insights = []
        
        if not search_history:
            return {'insights': [], 'message': 'Sin historial'}
        
        query_types = Counter()
        for s in search_history:
            q = s.get('query', '').lower()
            if 'ads' in q or 'marketing' in q:
                query_types['marketing'] += 1
            elif 'legal' in q or 'compliance' in q:
                query_types['legal'] += 1
            elif 'seo' in q or 'amazon' in q:
                query_types['amazon'] += 1
        
        total = sum(query_types.values())
        if total > 0:
            for cat, count in query_types.most_common(3):
                percentage = count / total * 100
                insights.append({
                    'type': 'distribution',
                    'message': f'{percentage:.0f}% de búsquedas son sobre "{cat}"'
                })
        
        zero_results = sum(1 for r in results_by_query.values() if r == 0)
        if zero_results > 0:
            insights.append({
                'type': 'gap',
                'message': f'{zero_results} búsquedas no encontraron resultados - considera expandir KB'
            })
        
        return {
            'insights': insights,
            'summary': ' / '.join([i['message'] for i in insights[:3]])
        }