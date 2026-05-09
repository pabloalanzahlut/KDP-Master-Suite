"""
KDP MASTER - Search Package
============================
Paquete para módulos avanzados de búsqueda.

FASE 1: Sin IA (Determinista)
- search_cache.py - Cache LRU
- search_engine.py - Motor de búsqueda
- search_facets.py - Facetas y filtros
- search_exporter.py - Exportación
- search_analytics.py - Estadísticas

FASE 2: CON IA (Cognitiva)
- vector_search.py - Búsqueda semántica con Ollama
- semantic_reranker.py - Re-ranking semántico
- query_ai.py - Procesamiento de queries con IA
- result_analyzer.py - Análisis de resultados
- ai_assistant.py - Chat RAG y asistencia
- predictive_engine.py - Optimización predictiva
"""

from .search_cache import SearchCache, SearchCacheManager, get_search_cache_manager
from .vector_search import VectorSearchEngine, OllamaEmbedder, get_vector_search_engine
from .semantic_reranker import SemanticReRanker, get_reranker
from .query_ai import QueryExpander, QueryReformulator, IntentDetector, NaturalQA, get_query_processor
from .result_analyzer import ResultAnalyzer, get_result_analyzer
from .ai_assistant import RAGAssistant, SearchReportGenerator, get_ai_assistant
from .predictive_engine import get_predictive_engine

__all__ = [
    # Fase 1
    'SearchCache',
    'SearchCacheManager', 
    'get_search_cache_manager',
    'VectorSearchEngine',
    'OllamaEmbedder',
    'get_vector_search_engine',
    'SemanticReRanker',
    'get_reranker',
    'QueryExpander',
    'QueryReformulator',
    'IntentDetector',
    'NaturalQA',
    'get_query_processor',
    'ResultAnalyzer',
    'get_result_analyzer',
    'RAGAssistant',
    'SearchReportGenerator',
    'get_ai_assistant',
    'get_predictive_engine'
]