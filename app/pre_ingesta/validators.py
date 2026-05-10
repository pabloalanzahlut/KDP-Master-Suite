"""
KDP MASTER - Validators (Módulos 1, 4, 9)
=====================================
Validador de esquemas multiorigen y pre-verificador de cuotas.

Módulo 1: Validador de Esquemas Multiorigen
Módulo 4: Pre-verificador de Cuotas
Módulo 9: Validador de Subtítulos
"""

import re
import os
import yt_dlp
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlparse

from ..pre_ingesta.base import ContentType, QueueItem


class URLSchemaValidator:
    """Módulo 1: Validador de esquemas multiorigen."""
    
    YOUTUBE_URL_PATTERNS = {
        'video': r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]{11}',
        'short': r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]{11}',
        'playlist': r'(?:https?://)?(?:www\.)?youtube\.com/(?:playlist|watch)\?.*list=([\w-]+)',
        'channel': r'(?:https?://)?(?:www\.)?youtube\.com/@[\w-]+',
        'channel_alt': r'(?:https?://)?(?:www\.)?youtube\.com/c/[\w-]+',
        'channel_alt2': r'(?:https?://)?(?:www\.)?youtube\.com/channel/[\w-]+',
    }
    
    def detect_content_type(self, url: str) -> Tuple[ContentType, str]:
        """
        Detecta automáticamente el tipo de contenido de la URL.
        Returns: (ContentType, cleaned_url)
        """
        url = url.strip()
        
        for pattern in [self.YOUTUBE_URL_PATTERNS['short']]:
            if re.match(pattern, url, re.IGNORECASE):
                video_id = self._extract_video_id(url, 'shorts')
                return ContentType.VIDEO_SINGLE, url
        
        for pattern in [self.YOUTUBE_URL_PATTERNS['video']]:
            if re.match(pattern, url, re.IGNORECASE):
                return ContentType.VIDEO_SINGLE, url
        
        for pattern in [self.YOUTUBE_URL_PATTERNS['playlist']]:
            if re.match(pattern, url, re.IGNORECASE):
                return ContentType.PLAYLIST, url
        
        for pattern in [self.YOUTUBE_URL_PATTERNS['channel'], 
                       self.YOUTUBE_URL_PATTERNS['channel_alt'],
                       self.YOUTUBE_URL_PATTERNS['channel_alt2']]:
            if re.match(pattern, url, re.IGNORECASE):
                return ContentType.CHANNEL, url
        
        return ContentType.UNKNOWN, url
    
    def _extract_video_id(self, url: str, url_type: str = 'video') -> Optional[str]:
        """Extrae el video ID de la URL."""
        patterns = {
            'video': r'v=([\w-]{11})',
            'shorts': r'shorts/([\w-]{11})',
            'playlist': r'list=([\w-]+)',
            'channel': r'/@([\w-]+)',
        }
        
        pattern = patterns.get(url_type, patterns['video'])
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def validate(self, url: str) -> Tuple[bool, str, ContentType]:
        """
        Valida la URL y retorna (is_valid, cleaned_url, content_type).
        """
        content_type, cleaned = self.detect_content_type(url)
        
        if content_type == ContentType.UNKNOWN:
            return False, url, content_type
        
        return True, cleaned, content_type
    
    async def get_video_info_basic(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información básica del video sin descargar.
        Usa yt-dlp en modo información_only.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration', 0),
                    'channel': info.get('channel'),
                    'uploader': info.get('uploader'),
                    'description': info.get('description', '')[:500],
                    'tags': info.get('tags', []),
                    'categories': info.get('categories', []),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                }
        except Exception:
            return None


class StorageQuotaChecker:
    """Módulo 4: Pre-verificador de cuotar de almacenamiento."""
    
    MIN_FREE_SPACE_MB = 500
    ESTIMATED_SIZE_PER_VIDEO_MB = 150
    
    def check_available_space(self, path: Optional[str] = None) -> Tuple[bool, float, float]:
        """
        Verifica espacio disponible en disco.
        Returns: (has_sufficient_space, free_mb, required_mb)
        """
        if not path:
            path = os.getcwd()
        
        try:
            import shutil
            stats = shutil.disk_usage(path)
            free_mb = stats.free / (1024 * 1024)
            required_mb = self.MIN_FREE_SPACE_MB
            
            return free_mb >= required_mb, free_mb, required_mb
        except Exception:
            return False, 0.0, self.MIN_FREE_SPACE_MB
    
    def estimate_video_size(self, duration_seconds: int) -> float:
        """
        Estima el tamaño aproximada de descarga basedo en duración.
        """
        return (duration_seconds / 60) * self.ESTIMATED_SIZE_PER_VIDEO_MB
    
    def can_store(self, video_count: int, duration_seconds: int = 0) -> Tuple[bool, str]:
        """
        Verifica si se puede almacenar el número de videos.
        """
        estimated = duration_seconds * self.ESTIMATED_SIZE_PER_VIDEO_MB / 60 if duration_seconds > 0 else video_count * self.ESTIMATED_SIZE_PER_VIDEO_MB
        
        has_space, free_mb, required_mb = self.check_available_space()
        
        if not has_space:
            return False, f"Espacio insuficiente: {free_mb:.0f}MB disponibles, {required_mb:.0f}MB mínimos requeridos"
        
        if estimated > free_mb * 0.8:
            return False, f" Espacio insuficiente para {video_count} videos (~{estimated:.0f}MB necesarios, {free_mb:.0f}MB disponibles)"
        
        return True, f"Espacio OK: {free_mb:.0f}MB disponibles"


class SubtitlePreferenceValidator:
    """Módulo 9: Validador de preferencia de subtítulos."""
    
    SUBTITLE_EXTENSIONS = ['.vtt', '.srt', '.ttml', '.ass']
    SUBTITLE_LANGUAGE_CODES = ['es', 'en', 'en-US', 'en-GB']
    
    def __init__(self):
        self.preferred_format = 'vtt'
        self.preferred_language = 'es'
    
    def set_preferences(self, format: str = 'vtt', language: str = 'es'):
        """Configura preferencias de subtítulos."""
        self.preferred_format = format
        self.preferred_language = language
    
    def select_best_subtitle(self, available_subtitles: Dict[str, Any]) -> Optional[str]:
        """
        Selecciona el mejor subtítulo disponible.
        Prioriza: manual > auto, idioma preferido > otros, formato preferido
        """
        if not available_subtitles:
            return None
        
        targets = []
        
        for lang, subtitle_data in available_subtitles.items():
            if isinstance(subtitle_data, dict):
                is_manual = subtitle_data.get('ext', '') in self.SUBTITLE_EXTENSIONS
                
                if self._language_matches(lang):
                    score = 100 if is_manual else 50
                else:
                    score = 30 if is_manual else 10
                
                targets.append((score, lang, subtitle_data))
        
        if not targets:
            return None
        
        targets.sort(reverse=True)
        return targets[0][1]
    
    def _language_matches(self, lang: str) -> bool:
        """Verifica si el idioma coincide con el preferido."""
        lang_lower = lang.lower()
        pref_lower = self.preferred_language.lower()
        
        if lang_lower == pref_lower:
            return True
        if pref_lower in lang_lower or lang_lower in pref_lower:
            return True
        return False
    
    def validate_subtitle_availability(self, info: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida disponibilidad de subtítulos y retorna metadata.
        """
        subtitles = info.get('subtitles') or info.get('automatic_captions') or {}
        
        if not subtitles:
            return False, "Sin subtítulos disponibles", {}
        
        best = self.select_best_subtitle(subtitles)
        
        if not best:
            return False, "Sin subtítulos en idioma preferido", subtitles
        
        return True, f"Subtítulos disponibles: {best}", subtitles


class CompositeValidator:
    """Validador compuesto que orchestration todos los validadores."""
    
    def __init__(self):
        self.url_validator = URLSchemaValidator()
        self.quota_checker = StorageQuotaChecker()
        self.subtitle_validator = SubtitlePreferenceValidator()
    
    async def validate_all(self, url: str, video_count: int = 1) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Ejecuta todas las validaciones.
        Returns: (is_valid, metadata, validation_results)
        """
        results = []
        metadata = {}
        
        is_valid, cleaned_url, content_type = self.url_validator.validate(url)
        results.append(f"URL_VALIDATOR: {'PASS' if is_valid else 'FAIL'}")
        
        if not is_valid:
            return False, {"error": "URL inválida"}, results
        
        metadata['cleaned_url'] = cleaned_url
        metadata['content_type'] = content_type.value
        
        has_space, free_mb, _ = self.quota_checker.check_available_space()
        results.append(f"QUOTA_CHECKER: {'PASS' if has_space else 'FAIL'}")
        
        if not has_space:
            return False, metadata, results
        
        video_info = await self.url_validator.get_video_info_basic(url)
        
        if video_info:
            metadata['video_info'] = video_info
            
            if video_info.get('subtitles'):
                has_subtitles, msg, _ = self.subtitle_validator.validate_subtitle_availability(video_info)
                results.append(f"SUBTITLE_VALIDATOR: {'PASS' if has_subtitles else 'WARN'}")
            else:
                results.append("SUBTITLE_VALIDATOR: SKIP (sin información)")
        
        return True, metadata, results


def create_validator() -> CompositeValidator:
    """Factory function."""
    return CompositeValidator()