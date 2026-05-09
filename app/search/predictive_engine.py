"""
KDP MASTER - Predictive Engine Module
=====================================
Módulos 49-60: Optimización Predictiva y Aprendizaje
Predicciones, cache inteligente, detección de anomalías, insights.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SearchPrediction:
    query: str
    predicted_results: int
    confidence: float
    estimated_time_ms: int
    suggested_alternatives: List[str]


class SearchPredictor:
    """
    MÓDULO 49: Predicción de Tiempo de Búsqueda
    Estima duración antes de ejecutar.
    """
    
    def __init__(self):
        self._history: List[Dict] = []
        self._query_patterns = defaultdict(list)
    
    def predict(self, query: str, filters: Dict = None) -> SearchPrediction:
        """
        Predice tiempo de búsqueda y resultados.
        
        Returns:
            SearchPrediction con estimaciones
        """
        query_lower = query.lower()
        
        matching_queries = []
        for past in self._history[-50:]:
            past_query = past.get('query', '').lower()
            
            common_terms = set(query_lower.split()) & set(past_query.split())
            if common_terms:
                matching_queries.append(past)
        
        if matching_queries:
            avg_results = sum(q.get('results', 0) for q in matching_queries) / len(matching_queries)
            avg_time = sum(q.get('time_ms', 100) for q in matching_queries) / len(matching_queries)
            
            confidence = min(len(matching_queries) / 10.0, 0.9)
        else:
            avg_results = 50
            avg_time = 200
            confidence = 0.3
        
        if len(query) > 50:
            avg_time *= 1.5
        if filters:
            avg_time *= 1.2
        
        return SearchPrediction(
            query=query,
            predicted_results=int(avg_results),
            confidence=round(confidence, 2),
            estimated_time_ms=int(avg_time),
            suggested_alternatives=[]
        )
    
    def record_search(self, query: str, results: int, time_ms: int):
        """Registra búsqueda para aprendizaje."""
        self._history.append({
            'query': query,
            'results': results,
            'time_ms': time_ms,
            'timestamp': datetime.now().isoformat()
        })
        
        query_lower = query.lower()
        if len(query.split()) <= 3:
            self._query_patterns[query_lower.split()[0]].append({
                'results': results,
                'time_ms': time_ms
            })


class QueryOptimizer:
    """
    MÓDULO 50: Optimización de Query Automática
    Reescribe query para mejor rendimiento.
    """
    
    def optimize(self, query: str) -> str:
        """
        Optimiza query para búsqueda más eficiente.
        
        Returns:
            Query optimizada
        """
        query = query.strip()
        
        if len(query) > 200:
            query = query[:200]
        
        query = ' '.join(query.split())
        
        stopwords = ['el', 'la', 'los', 'las', 'de', 'que', 'es', 'en', 'con', 'para']
        words = query.split()
        optimized = ' '.join(w for w in words if w.lower() not in stopwords or w.isupper())
        
        return optimized if optimized else query
    
    def suggest_improvements(self, query: str) -> List[str]:
        """Sugiere mejoras para la query."""
        suggestions = []
        
        if ' ' not in query and len(query) > 3:
            suggestions.append(f"Considera usar múltiples términos: '{query} Amazon Ads'")
        
        if any(c in query for c in ['?', '¿', '!']):
            suggestions.append("Las preguntas pueden dar mejores resultados con palabras clave")
        
        if len(query) < 4:
            suggestions.append("Query muy corta, considera añadir más contexto")
        
        return suggestions


class IntelligentCache:
    """
    MÓDULO 51: Cache Inteligente de Embeddings
    Decide qué embeddings pre-calcular.
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict] = {}
        self._max_size = max_size
        self._access_count = Counter()
        self._last_access = {}
    
    def should_cache(self, query: str) -> bool:
        """Decide si una query merece ser cacheada."""
        query_lower = query.lower()
        
        if query_lower in self._access_count:
            return self._access_count[query_lower] >= 2
        
        return len(query.split()) >= 2
    
    def get(self, key: str) -> Optional[Dict]:
        """Obtiene del cache."""
        if key in self._cache:
            self._access_count[key] += 1
            self._last_access[key] = time.time()
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Dict):
        """Almacena en cache."""
        if len(self._cache) >= self._max_size:
            self._evict_lru()
        
        self._cache[key] = value
        self._access_count[key] = 1
        self._last_access[key] = time.time()
    
    def _evict_lru(self):
        """Elimina entrada menos usada."""
        if not self._last_access:
            return
        
        lru_key = min(self._last_access, key=self._last_access.get)
        del self._cache[lru_key]
        del self._access_count[lru_key]
        del self._last_access[lru_key]
    
    def get_stats(self) -> Dict:
        """Estadísticas del cache."""
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'top_queries': self._access_count.most_common(10)
        }


class DomainAdapter:
    """
    MÓDULO 52: Adaptación de Modelo por Dominio
    Ajusta comportamiento al contexto KDP.
    """
    
    def __init__(self):
        self.kdp_terms = {
            'bsr': 'Best Seller Rank',
            'kdp': 'Kindle Direct Publishing',
            'ads': 'Amazon Advertising',
            'ku': 'Kindle Unlimited',
            'royalties': 'regalías',
            'acos': 'Advertising Cost of Sales',
            'impressions': 'impresiones',
            'clicks': 'clics',
            'conversions': 'conversiones'
        }
    
    def adapt_query(self, query: str) -> str:
        """Adapta query al dominio KDP."""
        query_lower = query.lower()
        
        for abbr, full in self.kdp_terms.items():
            if abbr in query_lower and full not in query_lower:
                query = query + f" {full}"
        
        return query
    
    def get_domain_context(self) -> Dict:
        """Retorna contexto del dominio."""
        return {
            'terms': self.kdp_terms,
            'categories': [
                'Amazon Ads', 'Amazon KDP', 'Amazon SEO', 'Legalidad',
                'Marketing', 'Pricing', 'Kindle Unlimited', 'Herramientas'
            ]
        }


class QueryProblemDetector:
    """
    MÓDULO 53: Detección de Consultas Problemáticas
    Identifica queries que suelen fallar.
    """
    
    def __init__(self):
        self._problem_queries: Dict[str, int] = {}
        self._zero_results_queries: set = set()
    
    def check_query(self, query: str) -> Dict:
        """
        Verifica si la query es problemática.
        
        Returns:
            Diccionario con diagnóstico
        """
        query_lower = query.lower().strip()
        
        if query_lower in self._zero_results_queries:
            return {
                'is_problematic': True,
                'issue': 'zero_results_history',
                'suggestion': 'Esta query no dio resultados anteriormente. ¿Quieres reformularla?',
                'reformulation': self._suggest_reformulation(query)
            }
        
        if len(query) < 2:
            return {
                'is_problematic': True,
                'issue': 'too_short',
                'suggestion': 'Query muy corta. Añade más contexto.'
            }
        
        if query.isdigit():
            return {
                'is_problematic': True,
                'issue': 'numeric_only',
                'suggestion': 'Solo números. Añade contexto como "BSR 100000"'
            }
        
        return {'is_problematic': False}
    
    def record_zero_results(self, query: str):
        """Registra query sin resultados."""
        self._zero_results_queries.add(query.lower().strip())
    
    def _suggest_reformulation(self, query: str) -> str:
        """Sugiere reformulación."""
        words = query.split()
        
        if len(words) == 1:
            return f"{query} Amazon KDP"
        
        return f"{query} tutorial guía"


class SearchPreferenceLearner:
    """
    MÓDULO 54: Aprendizaje de Preferencias de Visualización
    Aprende preferencias del usuario.
    """
    
    def __init__(self):
        self._view_preferences: Dict[str, str] = {}
        self._order_preferences: Dict[str, str] = {}
    
    def record_view_choice(self, view_type: str):
        """Registra elección de vista."""
        self._view_preferences[view_type] = self._view_preferences.get(view_type, 0) + 1
    
    def get_preferred_view(self) -> str:
        """Retorna vista preferida."""
        if not self._view_preferences:
            return 'list'
        return max(self._view_preferences, key=self._view_preferences.get)
    
    def record_order_choice(self, order: str):
        """Registra preferencia de ordenamiento."""
        self._order_preferences[order] = self._order_preferences.get(order, 0) + 1
    
    def get_preferred_order(self) -> str:
        """Retorna orden preferido."""
        if not self._order_preferences:
            return 'Nuevos primero'
        return max(self._order_preferences, key=self._order_preferences.get)


class RelevancePredictor:
    """
    MÓDULO 55: Predicción de Relevancia Futura
    Predice qué resultados serán útiles.
    """
    
    def __init__(self):
        self._feedback_history: List[Dict] = []
    
    def predict_relevance(self, results: List[Dict]) -> List[Dict]:
        """
        Predice relevancia de resultados.
        
        Returns:
            Resultados con scores de predicción
        """
        if not results:
            return []
        
        for r in results:
            score = 0.5
            
            if r.get('semantic_score', 0) > 0.7:
                score += 0.2
            
            content_len = len(r.get('content', ''))
            if 500 < content_len < 3000:
                score += 0.1
            
            if r.get('category'):
                score += 0.1
            
            r['predicted_relevance'] = min(score, 1.0)
        
        return sorted(results, key=lambda x: x.get('predicted_relevance', 0), reverse=True)
    
    def record_feedback(self, result_id: int, useful: bool):
        """Registra feedback del usuario."""
        self._feedback_history.append({
            'result_id': result_id,
            'useful': useful,
            'timestamp': datetime.now().isoformat()
        })


class AnomalyDetector:
    """
    MÓDULO 57: Detección de Anomalías en Búsquedas
    Detecta patrones inusuales.
    """
    
    def __init__(self):
        self._searches_per_minute = []
        self._last_check = time.time()
        self._search_count = 0
    
    def record_search(self):
        """Registra búsqueda."""
        self._search_count += 1
        now = time.time()
        
        if now - self._last_check > 60:
            self._searches_per_minute.append(self._search_count)
            self._search_count = 0
            self._last_check = now
            
            if len(self._searches_per_minute) > 10:
                self._searches_per_minute.pop(0)
    
    def check_anomaly(self) -> Optional[Dict]:
        """Detecta anomalías."""
        if len(self._searches_per_minute) < 5:
            return None
        
        avg = sum(self._searches_per_minute) / len(self._searches_per_minute)
        
        if self._search_count > avg * 3:
            return {
                'type': 'high_search_volume',
                'message': f'Estas haciendo {self._search_count} búsquedas/min vs tu promedio de {avg:.1f}',
                'severity': 'warning'
            }
        
        return None


class SearchInsightGenerator:
    """
    MÓDULO 60: Generación de Insights de Búsqueda
    Crea reporte estratégico de patrones.
    """
    
    def __init__(self):
        self._search_history: List[Dict] = []
    
    def add_search(self, query: str, results: int, filters: Dict):
        """Registra búsqueda."""
        self._search_history.append({
            'query': query,
            'results': results,
            'filters': filters,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_insights(self, days: int = 7) -> Dict:
        """
        Genera insights de patrones de búsqueda.
        
        Returns:
            Diccionario con insights
        """
        if len(self._search_history) < 5:
            return {'status': 'insufficient_data'}
        
        query_counter = Counter()
        category_counter = Counter()
        zero_result_count = 0
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for s in self._search_history:
            try:
                ts = datetime.fromisoformat(s['timestamp'])
                if ts < cutoff:
                    continue
            except:
                continue
            
            query_counter[s['query']] += 1
            
            if s.get('filters', {}).get('category'):
                category_counter[s['filters']['category']] += 1
            
            if s['results'] == 0:
                zero_result_count += 1
        
        return {
            'period_days': days,
            'total_searches': len(self._search_history),
            'top_queries': query_counter.most_common(5),
            'top_categories': category_counter.most_common(5),
            'zero_results_rate': round(zero_result_count / len(self._search_history) * 100, 1),
            'insights': self._generate_insight_text(query_counter, category_counter, zero_result_count)
        }
    
    def _generate_insight_text(self, queries: Counter, categories: Counter, zero_count: int) -> List[str]:
        """Genera texto de insights."""
        insights = []
        
        if queries:
            top_query = queries.most_common(1)[0]
            insights.append(f"Tu búsqueda más frecuente es '{top_query[0]}' ({top_query[1]} veces)")
        
        if categories:
            top_cat = categories.most_common(1)[0]
            insights.append(f"Categoría más consultada: {top_cat[0]} ({top_cat[1]} búsquedas)")
        
        if zero_count > len(self._search_history) * 0.3:
            insights.append("Alto porcentaje de búsquedas sin resultados. Considera revisar tu base de conocimiento.")
        
        return insights


def get_predictive_engine() -> Dict:
    """Factory para obtener el motor predictivo."""
    return {
        'predictor': SearchPredictor(),
        'query_optimizer': QueryOptimizer(),
        'intelligent_cache': IntelligentCache(),
        'domain_adapter': DomainAdapter(),
        'problem_detector': QueryProblemDetector(),
        'preference_learner': SearchPreferenceLearner(),
        'relevance_predictor': RelevancePredictor(),
        'anomaly_detector': AnomalyDetector(),
        'insight_generator': SearchInsightGenerator()
    }