"""
KDP MASTER - Search Facets Module
===================================
Módulos 25-36: Sistema de Filtrado, Facetas Dinámicas y Refinamiento Progresivo
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Facet:
    name: str
    value: str
    count: int
    selected: bool = False


@dataclass
class FacetGroup:
    name: str
    facets: List[Facet]
    display_name: str


class SearchFacets:
    """
    Sistema de facetas dinámicas con conteos en tiempo real.
    Módulos 31-33: Facetas Dinámicas
    """
    
    def __init__(self, knowledge_db):
        self.db = knowledge_db
        self._cache = {}
        self._cache_ttl = 60
    
    def get_category_facets(self, query: str = None, filters: Dict = None) -> List[Facet]:
        """
        MÓDULO 31: Facetas Dinámicas - Conteo por Categoría
        
        Returns:
            Lista de facetas de categoría con conteos
        """
        cache_key = f"cat_facets_{query or 'all'}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            where_clause = "1=1"
            params = []
            
            if query:
                where_clause += " AND content LIKE ?"
                params.append(f"%{query}%")
            
            if filters:
                if filters.get('type') and filters['type'] != 'Todos':
                    where_clause += " AND tipo = ?"
                    params.append(filters['type'])
                if filters.get('date_from'):
                    where_clause += " AND timestamp >= ?"
                    params.append(filters['date_from'])
                if filters.get('date_to'):
                    where_clause += " AND timestamp <= ?"
                    params.append(filters['date_to'])
            
            cursor.execute(f"""
                SELECT category, COUNT(*) as count 
                FROM knowledge_entries
                WHERE {where_clause}
                GROUP BY category
                ORDER BY count DESC
            """, params)
            
            facets = [
                Facet(name="category", value=row[0], count=row[1])
                for row in cursor.fetchall()
            ]
            
            self._cache[cache_key] = facets
            return facets
            
        except Exception as e:
            logger.error(f"Error getting category facets: {e}")
            return []
        finally:
            conn.close()
    
    def get_type_facets(self, query: str = None, filters: Dict = None) -> List[Facet]:
        """
        MÓDULO 31: Facetas Dinómicas - Conteo por Tipo Documental
        
        Returns:
            Lista de facetas de tipo con conteos
        """
        cache_key = f"type_facets_{query or 'all'}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            where_clause = "1=1"
            params = []
            
            if query:
                where_clause += " AND content LIKE ?"
                params.append(f"%{query}%")
            
            if filters:
                if filters.get('category') and filters['category'] != 'Todos':
                    where_clause += " AND category = ?"
                    params.append(filters['category'])
            
            cursor.execute(f"""
                SELECT COALESCE(tipo, 'Artículo') as tipo, COUNT(*) as count 
                FROM knowledge_entries
                WHERE {where_clause}
                GROUP BY tipo
                ORDER BY count DESC
            """, params)
            
            facets = [
                Facet(name="tipo", value=row[0], count=row[1])
                for row in cursor.fetchall()
            ]
            
            self._cache[cache_key] = facets
            return facets
            
        except Exception as e:
            logger.error(f"Error getting type facets: {e}")
            return []
        finally:
            conn.close()
    
    def get_temporal_facets(self, query: str = None) -> Dict:
        """
        MÓDULO 33: Facetas Temporales - Distribución por Mes/Año
        
        Returns:
            Diccionario con facetas temporales
        """
        cache_key = f"temp_facets_{query or 'all'}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            where_clause = "WHERE timestamp IS NOT NULL"
            params = []
            
            if query:
                where_clause += " AND content LIKE ?"
                params.append(f"%{query}%")
            
            cursor.execute(f"""
                SELECT strftime('%Y', timestamp) as year, 
                       strftime('%m', timestamp) as month,
                       COUNT(*) as count
                FROM knowledge_entries
                {where_clause}
                GROUP BY year, month
                ORDER BY year DESC, month DESC
            """, params)
            
            monthly = [
                {'year': row[0], 'month': row[1], 'count': row[2]}
                for row in cursor.fetchall()
            ]
            
            cursor.execute(f"""
                SELECT strftime('%Y', timestamp) as year, COUNT(*) as count
                FROM knowledge_entries
                {where_clause}
                GROUP BY year
                ORDER BY year DESC
            """, params)
            
            yearly = [
                {'year': row[0], 'count': row[1]}
                for row in cursor.fetchall()
            ]
            
            result = {'monthly': monthly, 'yearly': yearly}
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error getting temporal facets: {e}")
            return {'monthly': [], 'yearly': []}
        finally:
            conn.close()
    
    def get_source_facets(self, query: str = None) -> List[Facet]:
        """
        MÓDULO 32: Facetas por Autor/Canal
        
        Returns:
            Lista de facetas de fuente/canal
        """
        cache_key = f"source_facets_{query or 'all'}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            where_clause = ""
            params = []
            
            if query:
                where_clause = "WHERE content LIKE ?"
                params.append(f"%{query}%")
            
            cursor.execute(f"""
                SELECT source, COUNT(*) as count 
                FROM knowledge_entries
                {where_clause}
                GROUP BY source
                HAVING source IS NOT NULL AND source != ''
                ORDER BY count DESC
                LIMIT 20
            """, params)
            
            facets = [
                Facet(name="source", value=row[0] or "Desconocido", count=row[1])
                for row in cursor.fetchall()
            ]
            
            self._cache[cache_key] = facets
            return facets
            
        except Exception as e:
            logger.error(f"Error getting source facets: {e}")
            return []
        finally:
            conn.close()
    
    def get_all_facets(self, query: str = None, current_filters: Dict = None) -> Dict:
        """
        Obtiene todas las facetas disponibles con conteos.
        
        Returns:
            Diccionario con todas las facetas
        """
        return {
            'categories': self.get_category_facets(query, current_filters),
            'types': self.get_type_facets(query, current_filters),
            'temporal': self.get_temporal_facets(query),
            'sources': self.get_source_facets(query)
        }
    
    def invalidate_cache(self):
        """Invalida el cache de facetas."""
        self._cache.clear()


class SearchFilters:
    """
    Sistema de filtros avanzados.
    Módulos 25-30: Filtros por Categoría, Fecha, Canal, Tipo, Longitud, Idioma
    """
    
    CATEGORY_VALUES = [
        "Todos", "Amazon Ads", "Amazon KDP", "Amazon SEO", "Amazon Kindle",
        "Legalidad y Compliance", "Marketing Digital", "Escritura Creativa",
        "Diseño de Portadas", "Pricing y Estrategias", "Kindle Unlimited",
        "Promociones", "Métricas y Analytics", "Internacionalización",
        "Herramientas y Software", "Productividad", "Case Studies", "Entrevistas"
    ]
    
    TYPE_VALUES = [
        "Todos", "Tutorial", "Artículo", "Investigación", "Lista", "Legal", "Fórmulas"
    ]
    
    ORDER_VALUES = [
        "Nuevos primero", "Antiguos primero", "Por categoría", 
        "Más relevantes", "Más palabras", "Menos palabras"
    ]
    
    def __init__(self):
        self._active_filters: Dict = {}
        self._filter_history: List[Dict] = []
        self._max_history = 50
    
    def apply_filters(self, filters: Dict) -> Dict:
        """
        Aplica filtros y retorna SQL WHERE clause.
        
        Args:
            filters: Diccionario de filtros
            
        Returns:
            Diccionario con conditions y params
        """
        conditions = []
        params = []
        
        category = filters.get('category', 'Todos')
        if category and category != 'Todos':
            conditions.append("category = ?")
            params.append(category)
        
        tipo = filters.get('type', 'Todos')
        if tipo and tipo != 'Todos':
            conditions.append("tipo = ?")
            params.append(tipo)
        
        source = filters.get('source')
        if source:
            conditions.append("source = ?")
            params.append(source)
        
        date_from = filters.get('date_from')
        if date_from:
            conditions.append("timestamp >= ?")
            params.append(f"{date_from}-01")
        
        date_to = filters.get('date_to')
        if date_to:
            conditions.append("timestamp <= ?")
            params.append(f"{date_to}-31")
        
        min_words = filters.get('min_words', 0)
        if min_words > 0:
            conditions.append("palabras >= ?")
            params.append(min_words)
        
        max_words = filters.get('max_words')
        if max_words and max_words > 0:
            conditions.append("palabras <= ?")
            params.append(max_words)
        
        language = filters.get('language')
        if language and language != 'Todos':
            conditions.append("language = ?")
            params.append(language)
        
        status = filters.get('status')
        if status and status != 'Todos':
            conditions.append("status = ?")
            params.append(status)
        
        self._active_filters = filters.copy()
        
        if filters:
            self._filter_history.append({
                'filters': filters.copy(),
                'timestamp': self._get_timestamp()
            })
            if len(self._filter_history) > self._max_history:
                self._filter_history = self._filter_history[-self._max_history:]
        
        return {
            'conditions': conditions,
            'params': params,
            'where_clause': " AND ".join(conditions) if conditions else "1=1"
        }
    
    def get_active_filters(self) -> Dict:
        """Retorna los filtros activos actualmente."""
        return self._active_filters.copy()
    
    def get_filter_summary(self) -> str:
        """Retorna resumen legible de filtros activos."""
        if not self._active_filters:
            return "Sin filtros activos"
        
        parts = []
        
        if self._active_filters.get('category') and self._active_filters['category'] != 'Todos':
            parts.append(f"Categoría: {self._active_filters['category']}")
        
        if self._active_filters.get('type') and self._active_filters['type'] != 'Todos':
            parts.append(f"Tipo: {self._active_filters['type']}")
        
        if self._active_filters.get('date_from') or self._active_filters.get('date_to'):
            date_range = f"{self._active_filters.get('date_from', '')} - {self._active_filters.get('date_to', '')}"
            parts.append(f"Fecha: {date_range}")
        
        if self._active_filters.get('source'):
            parts.append(f"Fuente: {self._active_filters['source']}")
        
        return ", ".join(parts) if parts else "Filtros activos"
    
    def get_filter_history(self) -> List[Dict]:
        """Retorna historial de filtros usados."""
        return self._filter_history.copy()
    
    def clear_filters(self):
        """Limpia todos los filtros activos."""
        self._active_filters.clear()
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SearchPreferences:
    """
    MÓDULO 35: Guardado de Filtros Favoritos
    """
    
    def __init__(self):
        self._saved_preferences: Dict[str, Dict] = {}
        self._max_preferences = 20
    
    def save_preference(self, name: str, filters: Dict, order_by: str = "timestamp DESC") -> bool:
        """
        Guarda una combinación de filtros como favorito.
        
        Args:
            name: Nombre del filtro favorito
            filters: Diccionario de filtros
            order_by: Orden preferido
            
        Returns:
            True si se guardó exitosamente
        """
        if len(self._saved_preferences) >= self._max_preferences:
            oldest = next(iter(self._saved_preferences))
            del self._saved_preferences[oldest]
        
        self._saved_preferences[name] = {
            'filters': filters,
            'order_by': order_by,
            'saved_at': self._get_timestamp()
        }
        
        return True
    
    def get_preference(self, name: str) -> Optional[Dict]:
        """Obtiene un filtro favorito por nombre."""
        return self._saved_preferences.get(name)
    
    def list_preferences(self) -> List[Dict]:
        """Lista todos los filtros favoritos."""
        return [
            {'name': name, **pref}
            for name, pref in self._saved_preferences.items()
        ]
    
    def delete_preference(self, name: str) -> bool:
        """Elimina un filtro favorito."""
        if name in self._saved_preferences:
            del self._saved_preferences[name]
            return True
        return False
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SearchHistory:
    """
    MÓDULO 36: Historial de Búsquedas Recientes
    """
    
    def __init__(self, max_entries: int = 50):
        self._history: List[Dict] = []
        self._max_entries = max_entries
    
    def add_search(self, query: str, filters: Dict, result_count: int, elapsed_ms: float):
        """
        Añade una búsqueda al historial.
        
        Args:
            query: Query de búsqueda
            filters: Filtros usados
            result_count: Número de resultados
            elapsed_ms: Tiempo de ejecución
        """
        entry = {
            'query': query,
            'filters': filters,
            'result_count': result_count,
            'elapsed_ms': elapsed_ms,
            'timestamp': self._get_timestamp()
        }
        
        self._history.insert(0, entry)
        
        if len(self._history) > self._max_entries:
            self._history = self._history[:self._max_entries]
    
    def get_history(self, limit: int = None) -> List[Dict]:
        """Obtiene historial de búsquedas."""
        if limit:
            return self._history[:limit]
        return self._history.copy()
    
    def clear_history(self):
        """Limpia el historial."""
        self._history.clear()
    
    def get_top_queries(self, limit: int = 10) -> List[Dict]:
        """Obtiene las queries más frecuentes."""
        from collections import Counter
        
        queries = [entry['query'] for entry in self._history if entry['query']]
        counter = Counter(queries)
        
        return [
            {'query': q, 'count': c}
            for q, c in counter.most_common(limit)
        ]
    
    def get_zero_result_queries(self) -> List[str]:
        """Obtiene queries que no devolvieron resultados."""
        return [
            entry['query'] for entry in self._history 
            if entry['query'] and entry['result_count'] == 0
        ]
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")