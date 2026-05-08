import json
import logging
import threading
import time
from typing import List, Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class KeywordFilter:
    """Filtro de palabras clave para el Monitor de Canales."""
    
    def __init__(self, 
                 include_keywords: Optional[List[str]] = None, 
                 exclude_keywords: Optional[List[str]] = None,
                 mode: str = "OR",
                 metadata_fetcher: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
                 metadata_cache_ttl: float = 3600.0,
                 metadata_cache_maxsize: int = 500):
        """
        Inicializa el filtro de palabras clave.
        
        Args:
            include_keywords: Lista de palabras que deben coincidir (Lista Blanca)
            exclude_keywords: Lista de palabras que excluyen inmediatamente (Lista Negra)
            mode: Modo de comparación - "OR" (cualquiera) o "AND" (todas)
            metadata_fetcher: Callable que retorna metadata completa (con tags) dado un video_id
            metadata_cache_ttl: TTL del cache de metadata en segundos (default 1h)
            metadata_cache_maxsize: Máximo tamaño del cache de metadata
        """
        self.include_keywords = []
        self.exclude_keywords = []
        self.mode = mode.upper() if mode.upper() in ["OR", "AND"] else "OR"
        self.enabled = False
        
        self._metadata_fetcher = metadata_fetcher
        self._cache_ttl = metadata_cache_ttl
        self._cache_maxsize = metadata_cache_maxsize
        self._metadata_cache: Dict[str, tuple[Dict[str, Any], float]] = {}
        self._cache_lock = threading.Lock()
        
        if include_keywords:
            self.include_keywords = [k.strip().lower() for k in include_keywords if k.strip()]
        if exclude_keywords:
            self.exclude_keywords = [k.strip().lower() for k in exclude_keywords if k.strip()]
    
    def should_process(self, title: str, description: str = "", video_id: str = None) -> tuple[bool, str]:
        """
        Determina si un video debe ser procesado basándose en las palabras clave.
        
        Args:
            title: Título del video
            description: Descripción del video (opcional)
            video_id: ID del video para fetch de metadata extendido (opcional)
            
        Returns:
            Tupla (debe_procesar, razon)
            - debe_procesar: True si el video debe procesarse
            - razon: Razón de la decisión (para logs)
        """
        if not self.enabled:
            return True, "filtros_deshabilitados"
        
        text = f"{title} {description}".lower()
        
        if not self.include_keywords and not self.exclude_keywords:
            return True, "sin_filtros_configurados"
        
        if self.exclude_keywords:
            for word in self.exclude_keywords:
                if word in text:
                    return False, f"excluido_por_blacklist:{word}"
        
        if not self.include_keywords:
            return True, "sin_lista_blanca"
        
        should_process, reason = self._check_text_fields(title, description)
        
        if should_process:
            return True, reason
        
        if self._is_borderline(should_process, reason, title, description) and video_id and self._metadata_fetcher:
            full_metadata = self._fetch_full_metadata(video_id)
            if full_metadata:
                tags = full_metadata.get('tags', [])
                if tags:
                    should_process, reason = self._check_tags(tags, reason)
        
        return should_process, reason
    
    def _check_text_fields(self, title: str, description: str) -> tuple[bool, str]:
        """Fase 1: Verifica coincidencia en título y descripción."""
        text = f"{title} {description}".lower()
        
        if self.mode == "OR":
            matches = any(word in text for word in self.include_keywords)
            reason = f"or_coincidencia:{','.join([w for w in self.include_keywords if w in text])}" if matches else "or_sin_coincidencia"
            return matches, reason
        else:
            matches = all(word in text for word in self.include_keywords)
            reason = f"and_todas_coinciden" if matches else "and_faltan_coincidencias"
            return matches, reason
    
    def _is_borderline(self, match: bool, reason: str, title: str, description: str) -> bool:
        """
        Detecta casos que merecen evaluación extendida de metadata.
        
        Args:
            match: Resultado del check de texto
            reason: Razón del resultado
            title: Título del video
            description: Descripción del video
            
        Returns:
            True si debe evaluarse metadata extendida
        """
        if match:
            return False
        
        if len(description) < 100 and not match:
            return True
        
        title_lower = title.lower()
        partial_keywords = [kw for kw in self.include_keywords if kw in title_lower]
        if partial_keywords and len(partial_keywords) < len(self.include_keywords):
            return True
        
        if any(c in title for c in "#[]()"):
            return True
        
        return False
    
    def _fetch_full_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene metadata completa (con tags) con cache para evitar llamadas repetidas.
        
        Args:
            video_id: ID del video de YouTube
            
        Returns:
            Metadata completa con tags o None si falla
        """
        if not self._metadata_fetcher:
            return None
        
        now = time.time()
        
        with self._cache_lock:
            if video_id in self._metadata_cache:
                data, ts = self._metadata_cache[video_id]
                if now - ts < self._cache_ttl:
                    return data
        
        try:
            full_info = self._metadata_fetcher(video_id)
            if full_info:
                with self._cache_lock:
                    if len(self._metadata_cache) >= self._cache_maxsize:
                        self._cleanup_metadata_cache()
                    self._metadata_cache[video_id] = (full_info, now)
            return full_info
        except Exception as e:
            logger.debug(f"Metadata fetch falló para {video_id}: {e}")
            return None
    
    def _check_tags(self, tags: List[str], previous_reason: str) -> tuple[bool, str]:
        """Fase 2: Verifica coincidencia en tags."""
        if not tags:
            return False, f"{previous_reason}_sin_tags"
        
        tags_lower = [t.lower() for t in tags]
        
        if self.mode == "OR":
            matches = any(word in tags_lower for word in self.include_keywords)
            matched = [w for w in self.include_keywords if w in tags_lower]
            reason = f"or_tags_coincidencia:{','.join(matched)}" if matches else f"{previous_reason}_tags_no_coinciden"
            return matches, reason
        else:
            matches = all(word in tags_lower for word in self.include_keywords)
            reason = f"and_tags_todas_coinciden" if matches else f"{previous_reason}_tags_faltan"
            return matches, reason
    
    def _cleanup_metadata_cache(self, max_age_multiplier: float = 2.0):
        """Limpia entradas expiradas del cache de metadata."""
        now = time.time()
        threshold = self._cache_ttl * max_age_multiplier
        expired = [k for k, (data, ts) in self._metadata_cache.items() if now - ts > threshold]
        for k in expired:
            del self._metadata_cache[k]
        
        if len(self._metadata_cache) >= self._cache_maxsize:
            sorted_cache = sorted(self._metadata_cache.items(), key=lambda x: x[1][1])
            to_remove = len(self._metadata_cache) - self._cache_maxsize + 100
            for k, (data, ts) in sorted_cache[:to_remove]:
                del self._metadata_cache[k]
    
    def clear_metadata_cache(self):
        """Limpia el cache de metadata."""
        with self._cache_lock:
            self._metadata_cache.clear()
    
    def to_dict(self) -> dict:
        """Serializa el filtro a diccionario."""
        return {
            "include_keywords": self.include_keywords,
            "exclude_keywords": self.exclude_keywords,
            "mode": self.mode,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "KeywordFilter":
        """Deserializa un filtro desde diccionario."""
        filter_obj = cls(
            include_keywords=data.get("include_keywords", []),
            exclude_keywords=data.get("exclude_keywords", []),
            mode=data.get("mode", "OR")
        )
        filter_obj.enabled = data.get("enabled", False)
        return filter_obj
    
    @classmethod
    def from_json(cls, json_str: str) -> "KeywordFilter":
        """Crea un filtro desde string JSON."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Error al parsear JSON de filtro: {e}")
            return cls()
    
    def to_json(self) -> str:
        """Serializa el filtro a string JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def test_filter(self, test_title: str, test_description: str = "") -> dict:
        """
        Prueba el filtro con un título de ejemplo.
        
        Args:
            test_title: Título de prueba
            test_description: Descripción de prueba (opcional)
            
        Returns:
            Diccionario con el resultado de la prueba
        """
        should_process, reason = self.should_process(test_title, test_description)
        
        return {
            "title": test_title,
            "description": test_description,
            "should_process": should_process,
            "reason": reason,
            "config": self.to_dict()
        }
    
    @staticmethod
    def parse_keywords(keywords_str: str) -> List[str]:
        """
        Parsea un string de palabras clave separadas por coma.
        
        Args:
            keywords_str: String con palabras separadas por coma
            
        Returns:
            Lista de palabras clave limpiadas
        """
        if not keywords_str:
            return []
        return [k.strip() for k in keywords_str.split(",") if k.strip()]
    
    def __repr__(self) -> str:
        return f"KeywordFilter(enabled={self.enabled}, include={self.include_keywords}, exclude={self.exclude_keywords}, mode={self.mode})"