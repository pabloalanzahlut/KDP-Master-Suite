"""
KDP MASTER - Search Cache Module (LRU)
========================================
Módulo 4: Cache de Consultas Frecuentes (LRU)
Almacena resultados de búsquedas repetidas en RAM para respuesta instantánea.
"""

import time
import hashlib
import threading
from typing import Dict, Optional, List, Any
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class SearchCache:
    """
    Cache LRU (Least Recently Used) para búsquedas en la base de conocimiento.
    
    Características:
    - Thread-safe para acceso concurrente
    - TTL configurable por resultado
    - Key basada en query + filtros + página
    - Estadísticas de命中率 (hit rate)
    """
    
    def __init__(self, max_size: int = 200, default_ttl: int = 300):
        """
        Inicializa el cache de búsqueda.
        
        Args:
            max_size: Máximo de entradas en cache (default: 200)
            default_ttl: Tiempo de vida por defecto en segundos (default: 5 min)
        """
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._default_ttl = default_ttl
        
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_queries': 0
        }
        
        self._hits_by_query: Dict[str, int] = {}
        logger.info(f"SearchCache inicializado: max_size={max_size}, ttl={default_ttl}s")
    
    def _generate_key(self, query: str, filters: Dict = None, page: int = 1, 
                      page_size: int = 20, order_by: str = "timestamp DESC") -> str:
        """
        Genera una clave única para la búsqueda basándose en todos los parámetros.
        
        Args:
            query: Término de búsqueda
            filters: Diccionario de filtros
            page: Número de página
            page_size: Tamaño de página
            order_by: Orden de resultados
            
        Returns:
            Hash MD5 como clave de cache
        """
        key_data = {
            'query': query.lower().strip(),
            'filters': filters or {},
            'page': page,
            'page_size': page_size,
            'order_by': order_by
        }
        
        key_string = str(sorted(key_data.items()))
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, query: str, filters: Dict = None, page: int = 1,
            page_size: int = 20, order_by: str = "timestamp DESC") -> Optional[Dict]:
        """
        Obtiene un resultado del cache si existe y no ha expirado.
        
        Args:
            query: Término de búsqueda
            filters: Filtros aplicados
            page: Página solicitada
            page_size: Tamaño de página
            order_by: Orden de resultados
            
        Returns:
            Resultado cacheado o None si no existe/expired
        """
        with self._lock:
            key = self._generate_key(query, filters, page, page_size, order_by)
            self._stats['total_queries'] += 1
            
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            if entry['expires_at'] < time.time():
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            self._cache.move_to_end(key)
            self._stats['hits'] += 1
            
            query_key = f"{query.lower().strip()}|{len(filters or {})}"
            self._hits_by_query[query_key] = self._hits_by_query.get(query_key, 0) + 1
            
            logger.debug(f"Cache HIT: query='{query}', key={key[:8]}")
            return entry['result'].copy()
    
    def set(self, query: str, result: Dict, filters: Dict = None, 
            page: int = 1, page_size: int = 20, order_by: str = "timestamp DESC",
            ttl: int = None) -> None:
        """
        Almacena un resultado en el cache.
        
        Args:
            query: Término de búsqueda
            result: Resultado a cachear
            filters: Filtros aplicados
            page: Página
            page_size: Tamaño de página
            order_by: Orden de resultados
            ttl: Tiempo de vida específico (override)
        """
        with self._lock:
            key = self._generate_key(query, filters, page, page_size, order_by)
            ttl = ttl or self._default_ttl
            
            if key in self._cache:
                self._cache.move_to_end(key)
            
            while len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats['evictions'] += 1
                logger.debug(f"Cache EVICT: oldest key removed")
            
            self._cache[key] = {
                'result': result.copy(),
                'expires_at': time.time() + ttl,
                'created_at': time.time(),
                'query': query
            }
            
            logger.debug(f"Cache SET: query='{query}', key={key[:8]}, ttl={ttl}s")
    
    def invalidate(self, query: str = None, filters: Dict = None) -> int:
        """
        Invalida entradas del cache.
        
        Args:
            query: Si se especifica, invalida solo esa query
            filters: Filtros a invalidar
            
        Returns:
            Número de entradas eliminadas
        """
        with self._lock:
            if query is None and filters is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cache invalidated: {count} entries cleared")
                return count
            
            keys_to_delete = []
            for key, entry in self._cache.items():
                if query and query.lower().strip() in entry['query'].lower():
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._cache[key]
            
            logger.debug(f"Cache invalidated: {len(keys_to_delete)} entries for query='{query}'")
            return len(keys_to_delete)
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Diccionario con estadísticas
        """
        with self._lock:
            total = self._stats['total_queries']
            hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'total_queries': total,
                'top_queries': sorted(self._hits_by_query.items(), 
                                     key=lambda x: x[1], reverse=True)[:10]
            }
    
    def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas del cache.
        
        Returns:
            Número de entradas eliminadas
        """
        with self._lock:
            current_time = time.time()
            keys_to_delete = [
                key for key, entry in self._cache.items()
                if entry['expires_at'] < current_time
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            if keys_to_delete:
                logger.debug(f"Cleanup: {len(keys_to_delete)} expired entries removed")
            
            return len(keys_to_delete)
    
    def prefetch(self, queries: List[str], search_func, filters: Dict = None) -> None:
        """
        Pre-carga resultados para queries frecuentes.
        
        Args:
            queries: Lista de queries a pre-cargar
            search_func: Función de búsqueda a ejecutar
            filters: Filtros base
        """
        for query in queries[:10]:
            if query.strip():
                try:
                    result = search_func(query=query, filters=filters or {}, 
                                         page=1, page_size=20)
                    if result and result.get('total', 0) > 0:
                        self.set(query, result, filters)
                except Exception as e:
                    logger.warning(f"Prefetch failed for '{query}': {e}")
        
        logger.info(f"Prefetch completed for {len(queries[:10])} queries")


class SearchCacheManager:
    """
    Gestor centralizado de caches de búsqueda por tipo de búsqueda.
    """
    
    def __init__(self):
        self._caches: Dict[str, SearchCache] = {
            'fts5': SearchCache(max_size=150, default_ttl=180),
            'bm25': SearchCache(max_size=100, default_ttl=120),
            'semantic': SearchCache(max_size=50, default_ttl=600),
            'filtered': SearchCache(max_size=100, default_ttl=300)
        }
        logger.info("SearchCacheManager inicializado")
    
    def get_cache(self, cache_type: str = 'fts5') -> SearchCache:
        """Obtiene el cache del tipo especificado."""
        return self._caches.get(cache_type, self._caches['fts5'])
    
    def invalidate_all(self) -> Dict[str, int]:
        """Invalida todos los caches."""
        results = {}
        for name, cache in self._caches.items():
            results[name] = cache.invalidate()
        return results
    
    def get_all_stats(self) -> Dict:
        """Obtiene estadísticas de todos los caches."""
        return {name: cache.get_stats() for name, cache in self._caches.items()}


_search_cache_manager = None


def get_search_cache_manager() -> SearchCacheManager:
    """Obtiene la instancia singleton del gestor de cache."""
    global _search_cache_manager
    if _search_cache_manager is None:
        _search_cache_manager = SearchCacheManager()
    return _search_cache_manager