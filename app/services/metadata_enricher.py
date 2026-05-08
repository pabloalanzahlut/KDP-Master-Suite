import os
import json
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime, date

try:
    from app.config import config
except ImportError:
    config = None


class YouTubeAPIClient:
    """Cliente para YouTube Data API v3."""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self.api_key = api_key
        elif config and config.general.ai_api_key:
            self.api_key = config.general.ai_api_key
        else:
            self.api_key = os.getenv('YOUTUBE_API_KEY')
        self._service = None
        
    @property
    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            from googleapiclient.discovery import build
            self._service = build('youtube', 'v3', developerKey=self.api_key)
            return True
        except ImportError:
            print("[WARN] google-api-python-client no instalado")
            return False
        except Exception as e:
            print(f"[WARN] Error inicializando YouTube API: {e}")
            return False
    
    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene metadatos extendidos via API (consume cuota)."""
        if not self._service:
            if not self.is_available:
                return None
        
        try:
            response = self._service.videos().list(
                part='snippet,contentDetails,statistics,status',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return None
            
            item = response['items'][0]
            snippet = item.get('snippet', {})
            content = item.get('contentDetails', {})
            stats = item.get('statistics', {})
            status = item.get('status', {})
            
            return {
                'api_title': snippet.get('title'),
                'api_description': snippet.get('description'),
                'api_tags': snippet.get('tags', []),
                'api_category_id': snippet.get('categoryId'),
                'api_default_language': snippet.get('defaultLanguage'),
                'api_published_at': snippet.get('publishedAt'),
                'licensed_content': status.get('licensedContent'),
                'definition': content.get('definition'),
                'caption': content.get('caption'),
                'projection': content.get('projection'),
                'view_count_api': int(stats.get('viewCount', 0)) if stats.get('viewCount') else None,
                'like_count_api': int(stats.get('likeCount', 0)) if stats.get('likeCount') else None,
                'favorite_count': int(stats.get('favoriteCount', 0)) if stats.get('favoriteCount') else None,
                'comment_count_api': int(stats.get('commentCount', 0)) if stats.get('commentCount') else None,
            }
        except Exception as e:
            print(f"[ERROR] YouTube API: {e}")
            return None
    
    def get_quota_usage(self) -> Dict[str, Any]:
        """Retorna informacion de cuota (simulado, API no provee esto directamente)."""
        return {
            'api_key_configured': bool(self.api_key),
            'service_available': self._service is not None,
            'note': 'YouTube API no provee consumo de cuota. Monitorear manualmente.'
        }


class MetadataEnricher:
    """
    Decide cuando enriquecer activamente via API.
    Implementa logica hibrida: pasivo por defecto, activo opcional.
    """
    
    DEFAULT_CONFIG = {
        'enrichment_mode': 'passive',
        'enrich_if_missing_tags': True,
        'enrich_high_value': True,
        'enrich_short_descriptions': True,
        'short_description_threshold': 100,
        'high_value_threshold': 8.0,
        'max_api_calls_per_day': 100,
        'priority_channels': [],
        'track_quota_usage': True,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._api_client = None
        self._api_calls_today = 0
        self._last_reset = date.today()
        
        if self.config.get('enrichment_mode') in ['active', 'hybrid']:
            api_key = self.config.get('api_key')
            if not api_key and config and hasattr(config, 'get'):
                api_key = config.get('api_key')
            if not api_key and config and hasattr(config, 'general'):
                api_key = config.general.ai_api_key
            if not api_key:
                api_key = os.getenv('YOUTUBE_API_KEY')
            self._api_client = YouTubeAPIClient(api_key)
    
    def _reset_daily_counter(self):
        today = date.today()
        if today > self._last_reset:
            self._api_calls_today = 0
            self._last_reset = today
    
    def should_enrich_via_api(self, metadata: Dict[str, Any]) -> bool:
        """Determina si vale la pena gastar cuota API."""
        self._reset_daily_counter()
        
        mode = self.config.get('enrichment_mode', 'passive')
        if mode == 'passive':
            return False
        
        if self._api_calls_today >= self.config.get('max_api_calls_per_day', 100):
            return False
        
        if not self._api_client or not self._api_client.is_available:
            return False
        
        if not metadata.get('video_id'):
            return False
        
        missing_critical = self._check_missing_critical_fields(metadata)
        if missing_critical and self.config.get('enrich_if_missing_tags'):
            return True
        
        if metadata.get('description_length', 0) < self.config.get('short_description_threshold', 100):
            if self.config.get('enrich_short_descriptions'):
                return True
        
        value_score = metadata.get('value_score', 0)
        if value_score >= self.config.get('high_value_threshold', 8.0):
            if self.config.get('enrich_high_value'):
                return True
        
        channel_id = metadata.get('channel_id')
        if channel_id and channel_id in self.config.get('priority_channels', []):
            return True
        
        return False
    
    def _check_missing_critical_fields(self, metadata: Dict[str, Any]) -> bool:
        """Verifica si faltan campos criticos."""
        missing = []
        
        if not metadata.get('tags') or len(metadata.get('tags', [])) == 0:
            missing.append('tags')
        
        if not metadata.get('description'):
            missing.append('description')
        
        if not metadata.get('duration_seconds'):
            missing.append('duration')
        
        return len(missing) > 0
    
    def enrich_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intenta enriquecimiento activo si es necesario y esta configurado.
        Retorna metadatos fusionados.
        """
        if not self.should_enrich_via_api(metadata):
            metadata['enriched_via_api'] = False
            return metadata
        
        video_id = metadata.get('video_id')
        if not video_id:
            metadata['enriched_via_api'] = False
            return metadata
        
        api_data = self._api_client.get_video_details(video_id)
        
        if api_data:
            self._api_calls_today += 1
            metadata = self._merge_metadata(metadata, api_data)
            metadata['enriched_via_api'] = True
            metadata['api_calls_used'] = self._api_calls_today
        else:
            metadata['enriched_via_api'] = False
        
        return metadata
    
    def _merge_metadata(self, passive: Dict[str, Any], active: Dict[str, Any]) -> Dict[str, Any]:
        """Fusiona metadatos: API tiene prioridad si hay conflicto."""
        merged = passive.copy()
        
        for field in ['title', 'description', 'tags']:
            api_field = f'api_{field}'
            if active.get(api_field) and active[api_field] != passive.get(field):
                merged[field] = active[api_field]
        
        for field in ['category_id', 'licensed_content', 'definition', 'caption', 'comment_count']:
            if field in active:
                merged[field] = active[field]
        
        return merged
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna estado actual del enriquecimiento."""
        return {
            'mode': self.config.get('enrichment_mode'),
            'api_available': self._api_client.is_available if self._api_client else False,
            'api_calls_today': self._api_calls_today,
            'max_api_calls': self.config.get('max_api_calls_per_day'),
            'quota_remaining': self.config.get('max_api_calls_per_day') - self._api_calls_today,
        }


def test_enricher():
    """Test basico del enricher."""
    config = {
        'enrichment_mode': 'passive',
    }
    
    enricher = MetadataEnricher(config)
    
    sample_metadata = {
        'video_id': 'test123',
        'title': 'Test Video',
        'description': 'Short',
        'tags': [],
        'duration_seconds': 300,
    }
    
    result = enricher.enrich_metadata(sample_metadata)
    print(f"Mode: {result.get('enriched_via_api')}")
    print(f"Status: {enricher.get_status()}")


if __name__ == "__main__":
    test_enricher()