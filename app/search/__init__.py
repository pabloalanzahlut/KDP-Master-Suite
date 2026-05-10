"""
KDP MASTER - Search Package
============================
Paquete para módulos avanzados de búsqueda.

FASE 1 (Sin IA): Módulos 1-60 - Indexación, Consultas, Filtros, UI, Auditoría
FASE 2 (CON IA): Módulos 1-60 - Semántica, Relevancia, Análisis, Asistencia, Predicción
"""

# FASE 1: Módulos Sin IA
from .search_cache import SearchCache, SearchCacheManager, get_search_cache_manager
from .search_engine import SearchEngine, SearchFacade, SearchQueryParser, SearchHighlighter
from .search_facets import SearchFacets, SearchFilters, SearchPreferences, SearchHistory
from .search_exporter import SearchExporter
from .search_analytics import SearchAnalytics, SearchPermissions, SearchQuota, SearchHealthCheck

# FASE 2: Módulos CON IA (Ollama)
try:
    from .ollama_client import OllamaClient, OllamaVectorStore, get_ollama_client, get_vector_store
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from .relevance_engine import (
        LearningToRank, UserProfileSearch, ContextAwareSearch, RecencyBoost,
        AuthorityBoost, QueryAmbiguityDetector, SearchRefiner, SpellingCorrector,
        CrossLingualSearch, SynonymContextLearner, AdaptiveFieldWeighting, ImplicitFeedbackLearner
    )
except ImportError:
    pass

try:
    from .result_analyzer import (
        ResultSummarizer, KeyPointExtractor, ContradictionDetector, ContentTypeClassifier,
        FreshnessScorer, DuplicateDetector, MetricsExtractor, ToolsMentionExtractor,
        SentimentAnalyzer, ExpertiseLevelDetector, ActionableExtractor, ConceptMapGenerator
    )
except ImportError:
    pass

try:
    from .ai_assistant import (
        ChatRAG, SearchReportGenerator, RelatedSearchSuggester, KnowledgeGapDetector,
        ReadingPrioritizer, CitationExtractor, VersionComparator, TrendDetector,
        FAQGenerator, BestPracticesExtractor, InformationGapAnalyzer, PostSearchRecommender
    )
except ImportError:
    pass

try:
    from .predictive_engine import (
        SearchTimePredictor, QueryOptimizer, SmartCache, DomainAdapter,
        ProblematicQueryDetector, ViewPreferenceLearner, RelevancePredictor,
        IndexOptimizer, AnomalyDetector, KeywordRecommender, InterestEvolutionAnalyzer,
        SearchInsightsGenerator
    )
except ImportError:
    pass

__all__ = [
    # FASE 1
    'SearchCache', 'SearchCacheManager', 'get_search_cache_manager',
    'SearchEngine', 'SearchFacade', 'SearchQueryParser', 'SearchHighlighter',
    'SearchFacets', 'SearchFilters', 'SearchPreferences', 'SearchHistory',
    'SearchExporter', 'SearchAnalytics', 'SearchPermissions', 'SearchQuota', 'SearchHealthCheck',
    # FASE 2
    'OLLAMA_AVAILABLE',
]