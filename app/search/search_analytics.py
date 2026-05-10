"""
KDP MASTER - Search Analytics & Governance Module
====================================================
Módulos 49-60: Estadísticas, Auditoría, Permisos, Cuotas, Backup
"""

import os
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchStats:
    total_searches: int = 0
    total_results: int = 0
    avg_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    zero_result_searches: int = 0
    top_queries: List[Dict] = field(default_factory=list)


class SearchAnalytics:
    """
    Módulos 49-55: Estadísticas, Tiempos, Logs de Búsqueda
    """
    
    def __init__(self):
        self._stats = SearchStats()
        self._search_log: List[Dict] = []
        self._max_log_size = 1000
        self._lock = threading.Lock()
        
        self._zero_result_queries: Dict[str, int] = {}
        self._queries_by_category: Dict[str, int] = {}
    
    def log_search(self, query: str, filters: Dict, result_count: int, 
                   elapsed_ms: float, algorithm: str, cache_hit: bool = False):
        """
        Registra una búsqueda en el log de estadísticas.
        
        Args:
            query: Query de búsqueda
            filters: Filtros aplicados
            result_count: Número de resultados
            elapsed_ms: Tiempo de ejecución
            algorithm: Algoritmo usado
            cache_hit: Si fue cache hit
        """
        with self._lock:
            entry = {
                'query': query,
                'filters': filters,
                'result_count': result_count,
                'elapsed_ms': elapsed_ms,
                'algorithm': algorithm,
                'cache_hit': cache_hit,
                'timestamp': datetime.now().isoformat()
            }
            
            self._search_log.insert(0, entry)
            
            if len(self._search_log) > self._max_log_size:
                self._search_log = self._search_log[:self._max_log_size]
            
            self._stats.total_searches += 1
            self._stats.total_results += result_count
            
            if result_count == 0 and query:
                self._zero_result_queries[query] = self._zero_result_queries.get(query, 0) + 1
                self._stats.zero_result_searches += 1
            
            self._update_avg_time(elapsed_ms)
    
    def _update_avg_time(self, elapsed_ms: float):
        n = self._stats.total_searches
        current_avg = self._stats.avg_time_ms
        self._stats.avg_time_ms = ((current_avg * (n - 1)) + elapsed_ms) / n
    
    def get_stats(self) -> SearchStats:
        """Retorna estadísticas globales."""
        with self._lock:
            top_queries = []
            
            query_counts: Dict[str, int] = {}
            for entry in self._search_log:
                q = entry.get('query', '')
                if q:
                    query_counts[q] = query_counts.get(q, 0) + 1
            
            top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            self._stats.top_queries = [{'query': q, 'count': c} for q, c in top_queries]
            
            total = self._stats.total_searches
            if total > 0:
                cache_hits = sum(1 for e in self._search_log if e.get('cache_hit'))
                self._stats.cache_hit_rate = (cache_hits / total) * 100
            
            return self._stats
    
    def get_search_log(self, limit: int = 50) -> List[Dict]:
        """Retorna log de búsquedas recientes."""
        with self._lock:
            return self._search_log[:limit]
    
    def get_zero_result_queries(self, limit: int = 20) -> List[Dict]:
        """Retorna queries sin resultados."""
        with self._lock:
            sorted_queries = sorted(self._zero_result_queries.items(), 
                                  key=lambda x: x[1], reverse=True)[:limit]
            return [{'query': q, 'attempts': c} for q, c in sorted_queries]
    
    def get_results_by_algorithm(self) -> Dict:
        """Retorna distribución de resultados por algoritmo."""
        with self._lock:
            algo_counts: Dict[str, Dict] = {}
            
            for entry in self._search_log:
                algo = entry.get('algorithm', 'unknown')
                if algo not in algo_counts:
                    algo_counts[algo] = {'count': 0, 'results': 0, 'avg_time': 0}
                
                algo_counts[algo]['count'] += 1
                algo_counts[algo]['results'] += entry.get('result_count', 0)
            
            for algo, data in algo_counts.items():
                if data['count'] > 0:
                    data['avg_time'] = data['results'] / data['count']
            
            return algo_counts
    
    def get_time_distribution(self) -> Dict:
        """Retorna distribución de tiempos de búsqueda."""
        with self._lock:
            buckets = {
                '< 50ms': 0,
                '50-100ms': 0,
                '100-200ms': 0,
                '200-500ms': 0,
                '500ms-1s': 0,
                '> 1s': 0
            }
            
            for entry in self._search_log:
                t = entry.get('elapsed_ms', 0)
                
                if t < 50:
                    buckets['< 50ms'] += 1
                elif t < 100:
                    buckets['50-100ms'] += 1
                elif t < 200:
                    buckets['100-200ms'] += 1
                elif t < 500:
                    buckets['200-500ms'] += 1
                elif t < 1000:
                    buckets['500ms-1s'] += 1
                else:
                    buckets['> 1s'] += 1
            
            return buckets


class SearchPermissions:
    """
    Módulos 56-57: Validación de Permisos y Enmascaramiento de Resultados
    """
    
    def __init__(self):
        self._role_permissions: Dict[str, List[str]] = {
            'admin': ['all'],
            'editor': ['read', 'write', 'export'],
            'viewer': ['read']
        }
        
        self._sensitive_keywords = [
            'password', 'secret', 'token', 'api_key', 'credential',
            'private_key', 'admin', 'root', 'config'
        ]
    
    def check_permission(self, user_role: str, action: str) -> bool:
        """Verifica si el usuario tiene permiso para la acción."""
        role_perms = self._role_permissions.get(user_role, [])
        
        if 'all' in role_perms:
            return True
        
        return action in role_perms
    
    def filter_results_by_permission(self, results: List[Dict], user_role: str) -> List[Dict]:
        """Filtra resultados según permisos del usuario."""
        if user_role == 'admin':
            return results
        
        allowed = []
        for r in results:
            if self.check_access_to_entry(r, user_role):
                allowed.append(r)
        
        return allowed
    
    def check_access_to_entry(self, entry: Dict, user_role: str) -> bool:
        """Verifica acceso a una entrada específica."""
        if user_role == 'admin':
            return True
        
        sensitive_content = entry.get('content', '').lower()
        
        for keyword in self._sensitive_keywords:
            if keyword in sensitive_content:
                return user_role == 'admin'
        
        return True
    
    def mask_sensitive_data(self, content: str) -> str:
        """Enmasca datos sensibles en el contenido."""
        masked = content
        
        import re
        
        patterns = [
            (r'(password\s*[=:]\s*)[^\s]+', r'\1***'),
            (r'(api[_-]?key\s*[=:]\s*)[^\s]+', r'\1***'),
            (r'(token\s*[=:]\s*)[^\s]+', r'\1***'),
            (r'(secret\s*[=:]\s*)[^\s]+', r'\1***'),
        ]
        
        for pattern, replacement in patterns:
            masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
        
        return masked


class SearchQuota:
    """
    MÓDULO 58: Cuota de Búsquedas por Usuario/Sesión
    """
    
    def __init__(self):
        self._user_quotas: Dict[str, Dict] = {}
        self._default_quota = 100
        self._default_window = 3600
    
    def check_quota(self, user_id: str, search_cost: int = 1) -> bool:
        """
        Verifica si el usuario tiene cuota disponible.
        
        Args:
            user_id: Identificador de usuario
            search_cost: Costo de la búsqueda (default 1)
            
        Returns:
            True si tiene cuota disponible
        """
        now = time.time()
        
        if user_id not in self._user_quotas:
            self._user_quotas[user_id] = {
                'used': 0,
                'window_start': now,
                'total_used': 0
            }
        
        quota = self._user_quotas[user_id]
        
        if now - quota['window_start'] > self._default_window:
            quota['used'] = 0
            quota['window_start'] = now
        
        return quota['used'] < self._default_quota
    
    def consume_quota(self, user_id: str, search_cost: int = 1):
        """Consume cuota del usuario."""
        if user_id in self._user_quotas:
            self._user_quotas[user_id]['used'] += search_cost
            self._user_quotas[user_id]['total_used'] += search_cost
    
    def get_quota_status(self, user_id: str) -> Dict:
        """Retorna estado de cuota del usuario."""
        if user_id not in self._user_quotas:
            return {
                'available': self._default_quota,
                'used': 0,
                'limit': self._default_quota,
                'reset_in_seconds': self._default_window
            }
        
        quota = self._user_quotas[user_id]
        now = time.time()
        
        return {
            'available': max(0, self._default_quota - quota['used']),
            'used': quota['used'],
            'limit': self._default_quota,
            'total_used': quota.get('total_used', 0),
            'reset_in_seconds': max(0, self._default_window - (now - quota['window_start']))
        }
    
    def set_quota(self, user_id: str, limit: int, window_seconds: int):
        """Establece cuota personalizada para usuario."""
        self._user_quotas[user_id] = {
            'used': 0,
            'window_start': time.time(),
            'total_used': 0
        }
        self._default_quota = limit
        self._default_window = window_seconds


class SearchBackup:
    """
    MÓDULO 59: Backup de Índices de Búsqueda
    """
    
    def __init__(self, backup_dir: str = None):
        self.backup_dir = backup_dir or os.path.expanduser("~/Documents/KDP_Master/backups")
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def backup_index(self, db_path: str, index_name: str = "search_index") -> str:
        """
        Realiza backup del índice de búsqueda.
        
        Args:
            db_path: Ruta a la base de datos
            index_name: Nombre del índice
            
        Returns:
            Ruta del archivo de backup
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{index_name}_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            
            logger.info(f"Backup creado: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error en backup: {e}")
            raise
    
    def list_backups(self, index_name: str = None) -> List[Dict]:
        """Lista backups disponibles."""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db'):
                if index_name and not filename.startswith(index_name):
                    continue
                
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """Restaura un backup."""
        try:
            import shutil
            shutil.copy2(backup_path, target_path)
            logger.info(f"Backup restaurado: {target_path}")
            return True
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False
    
    def delete_old_backups(self, keep_last: int = 5) -> int:
        """Elimina backups antiguos, manteniendo los últimos N."""
        backups = self.list_backups()
        
        if len(backups) <= keep_last:
            return 0
        
        deleted = 0
        for backup in backups[keep_last:]:
            try:
                os.remove(backup['path'])
                deleted += 1
            except Exception as e:
                logger.warning(f"No se pudo eliminar {backup['path']}: {e}")
        
        return deleted


class SearchHealthCheck:
    """
    MÓDULO 60: Reporte de Salud de Búsqueda
    """
    
    def __init__(self, knowledge_db):
        self.db = knowledge_db
    
    def get_health_report(self) -> Dict:
        """
        Genera reporte de diagnóstico de rendimiento de búsqueda.
        
        Returns:
            Diccionario con estado de salud del sistema de búsqueda
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'OK',
            'checks': [],
            'overall': 'healthy'
        }
        
        try:
            validation = self.db.validate_fts_integrity()
            report['checks'].append({
                'name': 'FTS_Integrity',
                'status': validation.get('status', 'UNKNOWN'),
                'details': validation
            })
            
            if validation.get('status') != 'OK':
                report['overall'] = 'warning'
        
        except Exception as e:
            report['checks'].append({
                'name': 'FTS_Integrity',
                'status': 'ERROR',
                'error': str(e)
            })
            report['overall'] = 'unhealthy'
        
        try:
            import os
            db_path = self.db.db_path
            if os.path.exists(db_path):
                db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
                report['checks'].append({
                    'name': 'Database_Size',
                    'status': 'OK',
                    'size_mb': round(db_size_mb, 2)
                })
                
                if db_size_mb > 1000:
                    report['overall'] = 'warning'
        
        except Exception as e:
            report['checks'].append({
                'name': 'Database_Size',
                'status': 'ERROR',
                'error': str(e)
            })
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            total_entries = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM knowledge_fts")
            fts_count = cursor.fetchone()[0]
            conn.close()
            
            report['checks'].append({
                'name': 'Index_Coverage',
                'status': 'OK' if total_entries == fts_count else 'MISMATCH',
                'entries': total_entries,
                'indexed': fts_count
            })
            
            if total_entries != fts_count:
                report['overall'] = 'warning'
        
        except Exception as e:
            report['checks'].append({
                'name': 'Index_Coverage',
                'status': 'ERROR',
                'error': str(e)
            })
        
        if report['overall'] != 'healthy':
            report['status'] = 'WARNING'
        if report['overall'] == 'unhealthy':
            report['status'] = 'ERROR'
        
        return report