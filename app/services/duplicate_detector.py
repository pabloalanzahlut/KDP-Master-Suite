"""
KDP_MASTER - Duplicate Detector Service
=========================================
Motor híbrido de detección de contenido duplicado entre canales.
Estrategia: Hash → Duration Window → Title Similarity → Tags → IA (opcional)
"""

import logging
from typing import List, Dict, Optional, Tuple
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class DuplicateType(Enum):
    """Tipos de duplicado detectados."""
    EXACT_CONTENT = "exact_content"       # Mismo hash de contenido
    REPOST = "repost"                     # Título similar (repost)
    SIMILAR_DURATION = "similar_duration" # Duración similar + ventana de tiempo
    SIMILAR_TAGS = "similar_tags"         # Tags en común
    SEMANTIC_SIMILAR = "semantic_similar" # Similitud semántica por IA


class DuplicateLevel(Enum):
    """Nivel de certeza del duplicado."""
    HIGH = "high"       # >90% seguro
    MEDIUM = "medium"   # 60-90% seguro
    LOW = "low"         # <60% seguro


class DuplicateDetector:
    """
    Motor de detección de duplicados con estrategia híbrida.
    
    Capas de detección (en orden de costo computacional):
    1. Hash MD5 (O(1)) - Duplicado exacto
    2. Duration + Time Window (O(n)) - Rápido
    3. Title Similarity (O(n)) - Local
    4. Tags Matching (O(n)) - Si disponible
    5. IA Semantic (O(n*m)) - Solo si necesario
    """
    
    def __init__(self, db_manager=None, ai_wrapper=None):
        """
        Inicializa el detector de duplicados.
        
        Args:
            db_manager: Instancia de DatabaseManager
            ai_wrapper: Instancia de AI wrapper para similitud semántica (opcional)
        """
        self.db = db_manager
        self.ai_wrapper = ai_wrapper
        
        # Configuración por defecto
        self.config = {
            'duration_tolerance': 5,      # segundos
            'time_window_days': 7,         # días hacia atrás
            'title_threshold': 0.80,       # 80% similitud
            'min_common_tags': 3,          # mínimo tags en común
            'tags_window_days': 30,        # ventana para tags
            'ia_threshold': 0.75,          # umbral para usar IA
            'max_ia_comparisons': 5,       # máximo comparaciones IA por video
        }
        
        # Cache en memoria para evitar re-computación
        self._hash_cache = set()
        self._title_cache = {}
    
    def set_config(self, **kwargs):
        """Actualiza la configuración del detector."""
        self.config.update(kwargs)
        logger.info(f"DuplicateDetector config updated: {self.config}")
    
    def check_duplicate(self, video_info: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Ejecuta la detección de duplicados para un video.
        
        Args:
            video_info: Diccionario con información del video
                - video_id: ID de YouTube
                - title: Título del video
                - duration: Duración en segundos (opcional)
                - tags: Lista de tags (opcional)
                - content_preview: Preview del contenido (opcional)
        
        Returns:
            Tupla (is_duplicate, duplicate_info)
            - is_duplicate: True si se detectó duplicado
            - duplicate_info: Diccionario con detalles del duplicado o None
        """
        video_id = video_info.get('video_id')
        title = video_info.get('title', '')
        duration = video_info.get('duration')
        tags = video_info.get('tags', [])
        
        if not video_id:
            return False, None
        
        # Capa 1: Hash exacto (si tenemos content hash)
        content_hash = video_info.get('content_hash')
        if content_hash:
            if self._check_exact_duplicate(content_hash):
                return True, {
                    'type': DuplicateType.EXACT_CONTENT,
                    'level': DuplicateLevel.HIGH,
                    'message': 'Contenido exacto ya procesado',
                    'video_id': video_id
                }
        
        # Capa 2: Duración + Ventana de tiempo
        if duration:
            similar_by_duration = self._check_duration_window(duration)
            if similar_by_duration:
                return True, {
                    'type': DuplicateType.SIMILAR_DURATION,
                    'level': DuplicateLevel.MEDIUM,
                    'message': f"Duración similar ({duration}s) a video reciente",
                    'similar_videos': similar_by_duration
                }
        
        # Capa 3: Similitud de título
        if title:
            similar_by_title = self._check_title_similarity(title)
            if similar_by_title:
                return True, {
                    'type': DuplicateType.REPOST,
                    'level': DuplicateLevel.MEDIUM,
                    'message': f"Título similar a otros videos del canal",
                    'similar_videos': similar_by_title
                }
        
        # Capa 4: Tags (si disponibles)
        if tags and len(tags) >= self.config['min_common_tags']:
            similar_by_tags = self._check_tags_match(tags)
            if similar_by_tags:
                return True, {
                    'type': DuplicateType.SIMILAR_TAGS,
                    'level': DuplicateLevel.MEDIUM,
                    'message': f"Tags en común con otros videos",
                    'similar_videos': similar_by_tags
                }
        
        # Capa 5: Similitud semántica con IA (solo si disponible y necesario)
        if self.ai_wrapper and video_info.get('content_preview'):
            similar_semantic = self._check_semantic_similarity(
                video_info['content_preview'],
                max_results=self.config['max_ia_comparisons']
            )
            if similar_semantic and similar_semantic['max_similarity'] >= self.config['ia_threshold']:
                return True, {
                    'type': DuplicateType.SEMANTIC_SIMILAR,
                    'level': DuplicateLevel.LOW,
                    'message': f"Similitud semántica detectada por IA ({similar_semantic['max_similarity']:.0%})",
                    'similar_videos': similar_semantic['similar']
                }
        
        return False, None
    
    def _check_exact_duplicate(self, content_hash: str) -> bool:
        """Verifica hash exacto contra DB y cache."""
        if not content_hash:
            return False
        
        # Check cache primero
        if content_hash in self._hash_cache:
            return True
        
        # Check DB
        if self.db and hasattr(self.db, 'check_content_hash_exists'):
            if self.db.check_content_hash_exists(content_hash):
                self._hash_cache.add(content_hash)
                return True
        
        return False
    
    def _check_duration_window(self, duration: int) -> List[Dict]:
        """Busca videos con duración similar en ventana de tiempo reciente."""
        if not self.db or not hasattr(self.db, 'find_duplicates_by_duration_and_window'):
            return []
        
        return self.db.find_duplicates_by_duration_and_window(
            duration=duration,
            window_days=self.config['time_window_days'],
            tolerance_seconds=self.config['duration_tolerance']
        )
    
    def _check_title_similarity(self, title: str, channel_id: int = None) -> List[Dict]:
        """Busca videos con títulos similares."""
        if not self.db or not hasattr(self.db, 'find_similar_titles'):
            return []
        
        return self.db.find_similar_titles(
            title=title,
            channel_id=channel_id,
            threshold=self.config['title_threshold'],
            limit=5
        )
    
    def _check_tags_match(self, tags: List[str]) -> List[Dict]:
        """Busca videos con tags en común."""
        if not self.db or not hasattr(self.db, 'find_duplicates_by_tags'):
            return []
        
        return self.db.find_duplicates_by_tags(
            tags=tags,
            min_common=self.config['min_common_tags'],
            window_days=self.config['tags_window_days']
        )
    
    def _check_semantic_similarity(self, content_preview: str, max_results: int = 5) -> Optional[Dict]:
        """
        Compara contenido con IA usando embeddings.
        
        Args:
            content_preview: Preview del contenido a comparar
            max_results: Máximo de resultados a retornar
        
        Returns:
            Diccionario con similitud o None si falla
        """
        if not self.ai_wrapper:
            return None
        
        try:
            # Obtener embedding del nuevo contenido
            new_embedding = self.ai_wrapper.get_embedding(content_preview)
            if not new_embedding:
                return None
            
            # Obtener videos recientes de la DB para comparar
            if not hasattr(self.db, 'get_recent_videos_for_comparison'):
                return None
            
            recent_videos = self.db.get_recent_videos_for_comparison(
                limit=50,
                window_days=self.config['time_window_days']
            )
            
            similar = []
            for video in recent_videos:
                if not video.get('content_preview'):
                    continue
                
                # Comparar embeddings
                existing_embedding = self.ai_wrapper.get_embedding(video['content_preview'])
                if not existing_embedding:
                    continue
                
                similarity = self._cosine_similarity(new_embedding, existing_embedding)
                
                if similarity >= self.config['ia_threshold']:
                    similar.append({
                        'video_id': video['video_id'],
                        'title': video['title'],
                        'similarity': round(similarity, 2)
                    })
            
            if similar:
                similar.sort(key=lambda x: x['similarity'], reverse=True)
                return {
                    'similar': similar[:max_results],
                    'max_similarity': similar[0]['similarity'] if similar else 0
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Error en similitud semántica: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_detection_summary(self, video_info: Dict) -> Dict:
        """
        Retorna un resumen de todas las comprobaciones de detección (sin bloquear).
        
        Args:
            video_info: Información del video
        
        Returns:
            Diccionario con estado de cada capa
        """
        summary = {
            'video_id': video_info.get('video_id'),
            'checks': {},
            'would_detect': False,
            'detection_type': None
        }
        
        # Ejecutar cada check silenciosamente
        try:
            content_hash = video_info.get('content_hash')
            if content_hash:
                summary['checks']['exact_hash'] = self._check_exact_duplicate(content_hash)
            
            duration = video_info.get('duration')
            if duration:
                summary['checks']['duration_match'] = bool(
                    self._check_duration_window(duration)
                )
            
            title = video_info.get('title')
            if title:
                summary['checks']['title_match'] = bool(
                    self._check_title_similarity(title)
                )
            
            tags = video_info.get('tags', [])
            if len(tags) >= self.config['min_common_tags']:
                summary['checks']['tags_match'] = bool(
                    self._check_tags_match(tags)
                )
            
            # Determinar si detectaría
            summary['would_detect'] = any(summary['checks'].values())
            
        except Exception as e:
            logger.error(f"Error en get_detection_summary: {e}")
        
        return summary
    
    def clear_cache(self):
        """Limpia el cache en memoria."""
        self._hash_cache.clear()
        self._title_cache.clear()
        logger.info("DuplicateDetector cache cleared")