"""
KDP MASTER - Search Package
============================
Paquete para módulos avanzados de búsqueda.
"""

from .search_cache import SearchCache, SearchCacheManager, get_search_cache_manager

__all__ = [
    'SearchCache',
    'SearchCacheManager', 
    'get_search_cache_manager'
]