"""
KDP MASTER - Search Engine
===========================
Motor de búsqueda unificado que combina FTS5, BM25, cache y filtros avanzados.
Módulos 13-24: Query Parser, Timeout, Async, Highlighting, Snippets, etc.
"""

import time
import re
import threading
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchRequest:
    query: str
    filters: Dict
    page: int = 1
    page_size: int = 20
    order_by: str = "timestamp DESC"
    algorithm: str = "auto"
    timeout_ms: int = 10000


@dataclass 
class SearchResponse:
    results: List[Dict]
    total: int
    pages: int
    elapsed_ms: float
    algorithm: str
    query: str
    cache_hit: bool = False


class SearchQueryParser:
    """
    MÓDULO 13-15: Query Parser con Soporte Booleano, Wildcards y Proximidad
    """
    
    def __init__(self):
        self.operators = ['AND', 'OR', 'NOT']
    
    def parse(self, query: str) -> Dict:
        """
        Parsea query avanzada con operadores booleanos, wildcards y proximidad.
        
        Formatos soportados:
        - "marketing AND ads" → ambos términos
        - "marketing OR ads" → cualquiera
        - "marketing NOT gratis" → excluir término
        - "Amazon Ads~5" → términos a distancia 5
        - "market*" → wildcard
        """
        parsed = {
            'original': query,
            'terms': [],
            'required': [],
            'optional': [],
            'excluded': [],
            'proximity_pairs': [],
            'wildcards': []
        }
        
        if not query:
            return parsed
        
        query = query.strip()
        
        proximity_match = re.search(r'(\w+)\s*~\s*(\d+)', query)
        if proximity_match:
            parsed['proximity_pairs'].append({
                'term1': proximity_match.group(1),
                'distance': int(proximity_match.group(2))
            })
            query = query[:proximity_match.start()] + query[proximity_match.end():]
        
        wildcard_pattern = r'(\w+\*)'
        for match in re.finditer(wildcard_pattern, query):
            parsed['wildcards'].append(match.group(1).replace('*', ''))
        
        parts = re.split(r'\s+(AND|OR|NOT)\s+', query, flags=re.IGNORECASE)
        
        current_terms = parts[0] if parts else query
        
        for i, part in enumerate(parts[1:], 1):
            if i % 2 == 1:
                operator = part.upper()
                next_term = parts[i + 1] if i + 1 < len(parts) else ""
                
                if operator == 'AND':
                    parsed['required'].append(current_terms.strip())
                    current_terms = next_term
                elif operator == 'OR':
                    parsed['optional'].append(current_terms.strip())
                    current_terms = next_term
                elif operator == 'NOT':
                    parsed['excluded'].append(next_term.strip())
        
        if current_terms.strip():
            if parsed['required']:
                parsed['optional'].append(current_terms.strip())
            else:
                parsed['terms'].append(current_terms.strip())
        
        if not parsed['terms'] and not parsed['required']:
            parsed['terms'] = [query]
        
        return parsed
    
    def to_sql_like(self, parsed_query: Dict) -> tuple:
        """Convierte query parseada a condiciones SQL LIKE."""
        conditions = []
        params = []
        
        for term in parsed_query.get('terms', []):
            conditions.append("content LIKE ?")
            params.append(f'%{term}%')
        
        for term in parsed_query.get('required', []):
            conditions.append("content LIKE ?")
            params.append(f'%{term}%')
        
        for term in parsed_query.get('optional', []):
            conditions.append(f"({' OR '.join(['content LIKE ?'] * len(parsed_query.get('optional', [term])))}")
        
        for term in parsed_query.get('excluded', []):
            conditions.append("content NOT LIKE ?")
            params.append(f'%{term}%')
        
        return conditions, params


class SearchEngine:
    """
    Motor de búsqueda unificado con timeout, cache y ejecución asíncrona.
    """
    
    def __init__(self, knowledge_db, cache_manager=None):
        """
        Inicializa el motor de búsqueda.
        
        Args:
            knowledge_db: Instancia de KnowledgeDBManager
            cache_manager: Instancia de SearchCacheManager (opcional)
        """
        self.db = knowledge_db
        self.cache = cache_manager
        self.query_parser = SearchQueryParser()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="search")
        
        self._timeout_default = 10000
        self._default_page_size = 20
        
        logger.info("SearchEngine inicializado")
    
    def search(self, request: SearchRequest) -> SearchResponse:
        """
        Ejecuta búsqueda con timeout y cache.
        
        Args:
            request: SearchRequest con parámetros de búsqueda
            
        Returns:
            SearchResponse con resultados paginados
        """
        start_time = time.time()
        
        if self.cache and request.page == 1:
            cached = self.cache.get_cache('fts5').get(
                request.query, request.filters, request.page, 
                request.page_size, request.order_by
            )
            if cached:
                elapsed = (time.time() - start_time) * 1000
                return SearchResponse(
                    results=cached.get('results', []),
                    total=cached.get('total', 0),
                    pages=cached.get('pages', 1),
                    elapsed_ms=round(elapsed, 2),
                    algorithm=cached.get('algorithm', 'FTS5'),
                    query=request.query,
                    cache_hit=True
                )
        
        parsed_query = self.query_parser.parse(request.query)
        
        try:
            future = self._executor.submit(
                self._execute_search, request, parsed_query
            )
            
            result = future.result(timeout=request.timeout_ms / 1000)
            
            if self.cache and request.page == 1:
                self.cache.get_cache('fts5').set(
                    request.query, result, request.filters,
                    request.page, request.page_size, request.order_by
                )
            
            elapsed = (time.time() - start_time) * 1000
            
            return SearchResponse(
                results=result.get('results', []),
                total=result.get('total', 0),
                pages=result.get('pages', 1),
                elapsed_ms=round(elapsed, 2),
                algorithm=result.get('algorithm', 'FTS5'),
                query=request.query,
                cache_hit=False
            )
            
        except FutureTimeoutError:
            logger.warning(f"Búsqueda timeout: {request.query}")
            return SearchResponse(
                results=[],
                total=0,
                pages=0,
                elapsed_ms=request.timeout_ms,
                algorithm='TIMEOUT',
                query=request.query,
                cache_hit=False
            )
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return SearchResponse(
                results=[],
                total=0,
                pages=0,
                elapsed_ms=(time.time() - start_time) * 1000,
                algorithm='ERROR',
                query=request.query,
                cache_hit=False
            )
    
    def _execute_search(self, request: SearchRequest, parsed_query: Dict) -> Dict:
        """Ejecuta la búsqueda en la base de datos."""
        
        if request.algorithm == 'bm25':
            result = self.db.search_bm25(
                query=request.query,
                limit=request.page_size * request.page,
                filters=request.filters
            )
            result['algorithm'] = 'BM25'
        elif request.algorithm == 'synonyms':
            result = self.db.search_with_synonyms(
                query=request.query,
                limit=request.page_size * request.page
            )
            result['algorithm'] = 'FTS5+Sinonyms'
        elif request.algorithm == 'proximity':
            result = self.db.search_with_proximity(
                query=request.query,
                limit=request.page_size * request.page
            )
            result['algorithm'] = 'Proximity'
        elif request.algorithm == 'ngram':
            result = self.db.search_with_ngrams(
                query=request.query,
                limit=request.page_size * request.page
            )
            result['algorithm'] = 'N-gram'
        else:
            result = self.db.search_entries(
                query=request.query,
                filters=request.filters,
                page=request.page,
                page_size=request.page_size,
                order_by=request.order_by
            )
            result['algorithm'] = 'FTS5'
        
        entries = result.get('entries', result.get('results', []))
        
        total = result.get('total', len(entries))
        pages = (total + request.page_size - 1) // request.page_size if request.page_size > 0 else 1
        
        start_idx = (request.page - 1) * request.page_size
        paged_results = entries[start_idx:start_idx + request.page_size]
        
        return {
            'results': paged_results,
            'total': total,
            'pages': pages,
            'elapsed_ms': result.get('elapsed_ms', 0),
            'algorithm': result.get('algorithm', 'FTS5')
        }
    
    def search_parallel(self, queries: List[str], filters: Dict = None) -> Dict:
        """
        MÓDULO 22: Búsqueda en Múltiples Fuentes en Paralelo
        
        Args:
            queries: Lista de queries a buscar
            filters: Filtros comunes
            
        Returns:
            Resultados combinados de todas las fuentes
        """
        futures = []
        
        for query in queries:
            if query.strip():
                future = self._executor.submit(
                    self._execute_search,
                    SearchRequest(query=query, filters=filters or {}),
                    self.query_parser.parse(query)
                )
                futures.append((query, future))
        
        all_results = []
        seen_ids = set()
        
        for query, future in futures:
            try:
                result = future.result(timeout=5)
                for entry in result.get('results', []):
                    if entry.get('id') not in seen_ids:
                        entry['_search_query'] = query
                        all_results.append(entry)
                        seen_ids.add(entry.get('id'))
            except Exception as e:
                logger.warning(f"Error en búsqueda paralela '{query}': {e}")
        
        all_results.sort(key=lambda x: x.get('bm25_score', x.get('confidence_score', 0)), reverse=True)
        
        return {
            'results': all_results[:50],
            'total': len(all_results),
            'queries_executed': len(queries),
            'algorithm': 'Parallel-Merge'
        }
    
    def close(self):
        """Cierra el pool de threads."""
        self._executor.shutdown(wait=False)
        logger.info("SearchEngine cerrado")


class SearchHighlighter:
    """
    MÓDULO 19: Highlighting de Términos Buscados
    """
    
    def highlight(self, text: str, query: str, max_length: int = 200) -> str:
        """
        Resalta términos de búsqueda en el texto.
        
        Args:
            text: Texto original
            query: Query de búsqueda
            max_length: Longitud máxima del resultado
            
        Returns:
            Texto con términos resaltados
        """
        if not text or not query:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        for term in query_terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            text = pattern.sub(f"**{term.upper()}**", text)
        
        if len(text) > max_length:
            first_match = min((text_lower.find(t) for t in query_terms if t in text_lower), default=0)
            start = max(0, first_match - 50)
            text = "..." + text[start:start + max_length] + "..."
        
        return text


class SearchSnippetGenerator:
    """
    MÓDULO 20: Snippet Generation (±50 palabras)
    """
    
    def generate_snippet(self, content: str, query: str, context_words: int = 50) -> str:
        """
        Genera snippet con contexto alrededor del match.
        
        Args:
            content: Contenido completo
            query: Query de búsqueda
            context_words: Palabras de contexto alrededor del match
            
        Returns:
            Snippet con contexto
        """
        if not content:
            return ""
        
        content_words = content.split()
        
        query_terms = [t.lower() for t in query.split()]
        
        best_position = 0
        best_score = 0
        
        for i, word in enumerate(content_words):
            word_lower = word.lower()
            score = sum(1 for t in query_terms if t in word_lower)
            if score > best_score:
                best_score = score
                best_position = i
        
        start = max(0, best_position - context_words)
        end = min(len(content_words), best_position + context_words)
        
        snippet = " ".join(content_words[start:end])
        
        if start > 0:
            snippet = "..." + snippet
        if end < len(content_words):
            snippet = snippet + "..."
        
        return snippet


class SearchFacade:
    """
    Fachada unificada para todas las búsquedas.
    Integra: Parser, Engine, Cache, Highlighting, Snippets.
    """
    
    def __init__(self, knowledge_db, cache_manager=None):
        self.engine = SearchEngine(knowledge_db, cache_manager)
        self.highlighter = SearchHighlighter()
        self.snippet_gen = SearchSnippetGenerator()
    
    def search(self, query: str, filters: Dict = None, page: int = 1, 
               page_size: int = 20, order_by: str = "timestamp DESC",
               highlight: bool = True, snippets: bool = True,
               algorithm: str = "auto") -> Dict:
        """
        Búsqueda unificada con todas las características.
        
        Args:
            query: Término de búsqueda
            filters: Filtros (type, category, date_from, date_to)
            page: Página
            page_size: Resultados por página
            order_by: Orden
            highlight: Resaltar términos
            snippets: Generar snippets
            algorithm: 'auto', 'bm25', 'fts5', 'synonyms', 'proximity', 'ngram'
            
        Returns:
            Diccionario con resultados procesados
        """
        request = SearchRequest(
            query=query,
            filters=filters or {},
            page=page,
            page_size=page_size,
            order_by=order_by,
            algorithm=algorithm
        )
        
        response = self.engine.search(request)
        
        processed_results = []
        
        for result in response.results:
            processed = result.copy()
            
            if highlight:
                processed['content_highlighted'] = self.highlighter.highlight(
                    result.get('content', ''), query
                )
            
            if snippets:
                processed['snippet'] = self.snippet_gen.generate_snippet(
                    result.get('content', ''), query
                )
            
            processed_results.append(processed)
        
        return {
            'results': processed_results,
            'total': response.total,
            'pages': response.pages,
            'elapsed_ms': response.elapsed_ms,
            'algorithm': response.algorithm,
            'cache_hit': response.cache_hit,
            'query': query
        }
    
    def close(self):
        """Cierra recursos."""
        self.engine.close()