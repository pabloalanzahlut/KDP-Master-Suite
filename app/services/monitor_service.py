"""
KDP_MASTER - Channel Monitor Service
====================================
Servicio principal de monitoreo automático de canales de YouTube.
Detecta nuevos videos y los procesa automáticamente.
"""

import os
import sys
import time
import logging
import threading
import json
import re
import hashlib
import shutil
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import yt_dlp
from app.services.retry_decorator import retry_yt_dlp
from app.services.yt_dlp_errors import RateLimitError, AuthRequiredError, NetworkError, VideoUnavailableError

GET_CONTEXT = lambda *a, **kw: {
    "url": kw.get("url") or (a[1] if len(a) > 1 else "unknown"),
    "video_id": kw.get("video_id") or (a[2] if len(a) > 2 else None)
}

# Importar sistema de notificaciones toast
try:
    import tkinter as tk
    from app.ui.components.notifications import ToastNotification
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

# Importar NotificationRouter
try:
    from app.core.notification_router import NotificationRouter
    NOTIFICATION_ROUTER_AVAILABLE = True
except ImportError:
    NOTIFICATION_ROUTER_AVAILABLE = False

# Importar módulos del proyecto
from app.database.db_manager import DatabaseManager
from app.database.knowledge_db import KnowledgeDBManager
from app.services.download_service import DownloadService
from app.services.processing_service import ProcessingService
from app.services.knowledge_integrator import KnowledgeIntegrator
from app.services.duplicate_detector import DuplicateDetector
from app.core.utils import normalize_youtube_url
from app.core.config import Config
from app.core.keyword_filter import KeywordFilter

logger = logging.getLogger(__name__)


class ChannelMonitorService:
    """Servicio de monitoreo automático de canales de YouTube."""
    
    def __init__(self, 
                 db_manager: DatabaseManager = None,
                 download_service: DownloadService = None,
                 processing_service: ProcessingService = None,
                 knowledge_integrator: KnowledgeIntegrator = None,
                 video_tracker=None,
                 manual_merger=None,
                 notifier=None,
                 interval_minutes: int = 60,
                 max_videos_per_check: int = 10):
        """
        Inicializa el servicio de monitoreo.
        
        Args:
            db_manager: Gestor de base de datos
            download_service: Servicio de descarga
            processing_service: Servicio de procesamiento
            knowledge_integrator: Integrador de conocimiento
            video_tracker: Tracker JSON indestructible de videos procesados
            manual_merger: Sistema de fusión de manuales protegidos
            interval_minutes: Intervalo de verificación en minutos
            max_videos_per_check: Máximo de videos a procesar por ciclo
        """
        self.db = db_manager or DatabaseManager()
        self.download_service = download_service
        self.processing_service = processing_service or ProcessingService()
        self.knowledge_db = KnowledgeDBManager() if KnowledgeDBManager else None
        self.knowledge_integrator = knowledge_integrator or KnowledgeIntegrator(db_manager=self.knowledge_db)
        self.video_tracker = video_tracker
        self.manual_merger = manual_merger
        
        # Inicializar detector de duplicados
        self.duplicate_detector = DuplicateDetector(db_manager=self.db)
        
        # Callback para cuando se detecta duplicado (para preguntar al usuario)
        self.on_duplicate_detected_callback = None
        
        self.interval_minutes = interval_minutes
        self.max_videos_per_check = max_videos_per_check
        
        # Control del scheduler
        self.monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks para la GUI
        self.on_new_video_callback = None
        self.on_processing_complete_callback = None
        self.on_error_callback = None
        self.on_log_callback = None
        
        # NotificationRouter inyectado
        self.notifier = notifier
        
        # Configuración de directorios
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        self.input_dir = base_dir / "data" / "transcriptions"
        self.output_dir = base_dir / "outputs" / "transcriptions_processed"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Circuit Breaker para rate limiting
        self.failure_count = 0
        self.max_failures = 5
        self.circuit_open_until = None
        self.last_request_time = None
        self.min_request_interval = 1.0  # segundos entre requests
        
        # Configuración de detección mejorada
        self.max_results_per_check = 50  # Optimizado para cuota API
        self.max_age_days = 7  # Ignorar videos mayores a 7 días
        self.enable_video_cache = True  # Usar caché de videos por canal
        self.video_cache = {}  # Caché de video_ids por canal (etag_like)
        
        # Filtro de palabras clave (thread-safe)
        self._filter_lock = threading.Lock()
        self.keyword_filter = KeywordFilter()
        self._load_keyword_filter_from_db()
        
        # Lock para logging de escaneos
        self._scan_log_lock = threading.Lock()
    
    def set_detection_config(self, max_results: int = None, max_age_days: int = None):
        """Configura los parámetros de detección de videos."""
        if max_results is not None:
            self.max_results_per_check = max_results
        if max_age_days is not None:
            self.max_age_days = max_age_days
        self._log(f"Configuración de detección: max_results={self.max_results_per_check}, max_age_days={self.max_age_days}", 'info')
    
    def set_callbacks(self, 
                     on_new_video: Callable = None,
                     on_processing_complete: Callable = None,
                     on_error: Callable = None,
                     on_log: Callable = None,
                     on_duplicate_detected: Callable = None):
        """Configura callbacks para eventos del monitor."""
        self.on_new_video_callback = on_new_video
        self.on_processing_complete_callback = on_processing_complete
        self.on_error_callback = on_error
        self.on_log_callback = on_log
        self.on_duplicate_detected_callback = on_duplicate_detected
    
    def _load_keyword_filter_from_db(self):
        """Carga la configuración del filtro desde la base de datos."""
        try:
            filter_config = self.db.get_keyword_filter()
            if filter_config:
                self.keyword_filter = KeywordFilter(
                    include_keywords=filter_config.get('include_keywords', []),
                    exclude_keywords=filter_config.get('exclude_keywords', []),
                    mode=filter_config.get('mode', 'OR'),
                    metadata_fetcher=self._fetch_video_metadata
                )
                self.keyword_filter.enabled = filter_config.get('enabled', False)
                self._log(f"Filtro cargado desde BD: enabled={self.keyword_filter.enabled}, include={self.keyword_filter.include_keywords}, exclude={self.keyword_filter.exclude_keywords}", 'info')
        except Exception as e:
            self._log(f"Error cargando filtro desde BD: {e}", 'warning')
    
    def _fetch_video_metadata(self, video_id: str, timeout: float = 8.0) -> dict:
        """Obtiene metadata completa de un video (incluyendo tags) usando yt-dlp."""
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': timeout,
            'nocheckcertificate': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                if info:
                    return {
                        'tags': info.get('tags', []),
                        'description': info.get('description', ''),
                        'title': info.get('title', ''),
                        'categories': info.get('categories', []),
                        'uploader': info.get('uploader', '')
                    }
        except Exception as e:
            self._log(f"Error fetch metadata video {video_id}: {e}", 'debug')
        
        return None
    
    def set_keyword_filter(self, 
                          include_keywords: List[str] = None, 
                          exclude_keywords: List[str] = None,
                          mode: str = "OR",
                          enabled: bool = False) -> bool:
        """
        Configura el filtro de palabras clave.
        
        Args:
            include_keywords: Palabras que deben coincidir (lista blanca)
            exclude_keywords: Palabras que excluyen (lista negra)
            mode: Modo de comparación ("OR" o "AND")
            enabled: Si el filtro está activo
        
        Returns:
            True se configur correctamente
        """
        self.keyword_filter = KeywordFilter(
            include_keywords=include_keywords or [],
            exclude_keywords=exclude_keywords or [],
            mode=mode,
            metadata_fetcher=self._fetch_video_metadata
        )
        self.keyword_filter.enabled = enabled
        
        success = self.db.save_keyword_filter(
            include_keywords=include_keywords or [],
            exclude_keywords=exclude_keywords or [],
            mode=mode,
            enabled=enabled
        )
        
        if success:
            self._log(f"Filtro configurado: enabled={enabled}, mode={mode}, include={include_keywords}, exclude={exclude_keywords}", 'info')
        else:
            self._log(f"Error guardando filtro en BD", 'error')
        
        return success
    
    def reload_keyword_filter(self):
        """
        Recarga el filtro desde la base de datos de forma thread-safe.
        Útil después de guardar configuración para garantizar que el monitor use los valores actualizados.
        """
        with self._filter_lock:
            try:
                filter_config = self.db.get_keyword_filter()
                if filter_config:
                    self.keyword_filter = KeywordFilter(
                        include_keywords=filter_config.get('include_keywords', []),
                        exclude_keywords=filter_config.get('exclude_keywords', []),
                        mode=filter_config.get('mode', 'OR'),
                        metadata_fetcher=self._fetch_video_metadata
                    )
                    self.keyword_filter.enabled = filter_config.get('enabled', False)
                    self._log(f"Filtro recargado desde BD: enabled={self.keyword_filter.enabled}", 'info')
            except Exception as e:
                self._log(f"Error recargando filtro: {e}", 'error')
    
    def get_keyword_filter_config(self) -> Dict:
        """Obtiene la configuración actual del filtro."""
        return self.keyword_filter.to_dict()
    
    def test_keyword_filter(self, test_title: str) -> Dict:
        """Prueba el filtro con un título de ejemplo."""
        return self.keyword_filter.test_filter(test_title)
    
    def _log(self, message: str, level: str = 'info'):
        """Registra un mensaje en el log y llama al callback si existe."""
        if level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
        
        if self.on_log_callback:
            try:
                self.on_log_callback(message, level)
            except Exception as e:
                logger.error(f"Error en callback de log: {e}")
    
    def _notify_videos_detected(self, channel_name: str, count: int, channel_id: str = None):
        """Envía notificación de nuevos videos detectados."""
        if not self.notifier:
            return
        
        notif_settings = self.notifier.settings.get("notifications", {})
        if not notif_settings.get("notify_on_new_video", True):
            return
        
        title = f"📥 {count} video{'s' if count > 1 else ''} nuevo{'s' if count > 1 else ''}"
        message = f"Canal: {channel_name}"
        
        self.notifier.notify(
            title=title,
            message=message,
            type="info",
            event_type="new_video",
            channel_id=channel_id
        )
    
    def _notify_processing_complete(self, video_title: str, status: str, channel_id: str = None):
        """Envía notificación de procesamiento completado."""
        if not self.notifier:
            return
        
        notif_settings = self.notifier.settings.get("notifications", {})
        if not notif_settings.get("notify_on_processing_complete", True):
            return
        
        title = "✅ Procesamiento completado"
        message = f"{video_title[:40]} → {status.upper()}"
        
        self.notifier.notify(
            title=title,
            message=message,
            type="success",
            event_type="processing_complete",
            channel_id=channel_id
        )
    
    def _log_structured(self, event: str, **kwargs):
        """Registra un evento estructurado en formato JSON."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **kwargs
        }
        logger.info(json.dumps(log_entry))
    
    def _validate_youtube_url(self, url: str) -> bool:
        """Valida que la URL sea de YouTube."""
        if url.startswith('@'):
            return True
        pattern = r'^https?://(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/'
        if not re.match(pattern, url):
            return False
        if '/channel/' in url or '/c/' in url or '/@' in url:
            return True
        return bool(re.match(pattern, url))
    
    def _expand_url(self, url: str) -> str:
        """
        Expande handles (@nombre) a URLs completas de YouTube.
        Asegura que siempre termine en /videos para el descubrimiento.
        """
        url = url.strip()
        if url.startswith('@'):
            full_url = f"https://www.youtube.com/{url}"
        elif not url.startswith('http'):
            full_url = f"https://www.youtube.com/{url}"
        else:
            full_url = url
            
        if "/videos" not in full_url and "/playlist" not in full_url:
            full_url = full_url.rstrip("/") + "/videos"
            
        return full_url

    def _check_circuit_breaker(self) -> bool:
        """Verifica si el circuit breaker está abierto."""
        if self.circuit_open_until:
            if datetime.now() < self.circuit_open_until:
                return False  # Circuit abierto, no permitir requests
            else:
                # Resetear circuit breaker
                self.circuit_open_until = None
                self.failure_count = 0
        return True
    
    def _record_failure(self):
        """Registra un fallo y abre el circuit breaker si es necesario."""
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            # Abrir circuit por 5 minutos
            self.circuit_open_until = datetime.now() + timedelta(minutes=5)
            self._log_structured("circuit_breaker_opened", 
                               failure_count=self.failure_count,
                               open_until=self.circuit_open_until.isoformat())
    
    def _record_success(self):
        """Registra un éxito y resetea el contador de fallos."""
        self.failure_count = 0
    
    def _rate_limit(self):
        """Implementa rate limiting entre requests."""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcula MD5 checksum de un archivo."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _check_disk_space(self, required_mb: int = 100) -> bool:
        """Verifica que haya suficiente espacio en disco."""
        try:
            total, used, free = shutil.disk_usage(self.input_dir)
            free_mb = free / (1024 * 1024)
            return free_mb >= required_mb
        except Exception as e:
            logger.warning(f"No se pudo verificar espacio en disco: {e}")
            return True  # Asumir que hay espacio si no se puede verificar

    @retry_yt_dlp(max_attempts=2, base_delay=3.0, get_context=GET_CONTEXT)
    def _call_ytdlp_raw(self, url, opts):
        """Llamada directa a yt-dlp, protegida por el decorador."""
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)
    
    # ==================== GESTIÓN DE CANALES ====================
    
    def add_channel(self, channel_url: str, channel_name: str) -> Optional[int]:
        """
        Añade un nuevo canal a monitorear.
        
        Args:
            channel_url: URL del canal de YouTube
            channel_name: Nombre descriptivo del canal
        
        Returns:
            ID del canal o None si hubo error
        """
        # Normalizar URL
        channel_url = normalize_youtube_url(channel_url)
        if not self._validate_youtube_url(channel_url):
            # Si no es una URL válida de YT, podría ser un handle @ que convertiremos
            if channel_url.startswith('@'):
                channel_url = f"https://www.youtube.com/{channel_url}"
            else:
                self._log_structured("invalid_url", url=channel_url, channel_name=channel_name)
                self._log(f"URL inválida: {channel_url}", 'error')
                return None
        
        try:
            # Extraer información del canal
            channel_id = self._extract_channel_id(channel_url)
            
            # Añadir a la base de datos
            db_id = self.db.add_channel(channel_url, channel_name, channel_id)
            
            if db_id:
                self._log_structured("channel_added", 
                                   channel_id=db_id, 
                                   channel_name=channel_name,
                                   url=channel_url)
                self._log(f"Canal añadido: {channel_name}", 'info')
                return db_id
            else:
                self._log(f"El canal ya existe: {channel_name}", 'warning')
                return None
        except Exception as e:
            self._log_structured("channel_add_error", 
                               error=str(e), 
                               channel_name=channel_name)
            self._log(f"Error añadiendo canal: {e}", 'error')
            if self.on_error_callback:
                self.on_error_callback(str(e))
            return None
    
    def remove_channel(self, channel_id: int) -> bool:
        """Elimina un canal del monitoreo."""
        try:
            success = self.db.remove_channel(channel_id)
            if success:
                self._log(f"Canal eliminado: ID {channel_id}", 'info')
            return success
        except Exception as e:
            self._log(f"Error eliminando canal: {e}", 'error')
            return False
    
    def get_all_channels(self) -> List[Dict]:
        """Obtiene todos los canales monitoreados."""
        return self.db.get_all_channels()
    
    def toggle_channel(self, channel_id: int, active: bool) -> bool:
        return self.db.toggle_channel_active(channel_id, active)
    
    def update_channel(self, channel_id: int, name: str = None, url: str = None, active: bool = None) -> bool:
        return self.db.update_channel(channel_id, name=name, url=url, active=active)
    
    # ==================== DETECCIÓN DE VIDEOS ====================
    
    def _extract_channel_id(self, channel_url: str) -> Optional[str]:
        """
        Extrae el ID del canal o playlist desde la URL.
        
        Soporta:
        - Canales: https://youtube.com/@channel
        - Playlists: https://youtube.com/playlist?list=PL...
        """
        if not self._check_circuit_breaker():
            self._log("Circuit breaker abierto, operación cancelada", 'warning')
            return None
        
        self._rate_limit()
        
        # Verificar si es una playlist
        is_playlist = 'playlist?list=' in channel_url
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'socket_timeout': 30,
                'retries': 3,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                self._record_success()
                
                if is_playlist:
                    # Para playlists, usamos el ID de la lista
                    return info.get('id')
                else:
                    # Para canales, intentamos obtener el channel_id
                    return info.get('channel_id') or info.get('id')
                    
        except Exception as e:
            self._record_failure()
            logger.warning(f"No se pudo extraer channel_id (Playlist={is_playlist}): {e}")
            return None
    
    def _get_channel_videos(self, channel_url: str, max_results: int = None) -> List[Dict]:
        """
        Obtiene los videos más recientes de un canal con paginación inteligente.
        
        Args:
            channel_url: URL del canal
            max_results: Número máximo de videos a obtener (default: max_results_per_check)
        
        Returns:
            Lista de diccionarios con información de videos
        """
        if max_results is None:
            max_results = self.max_results_per_check
            
        if not self._check_circuit_breaker():
            self._log("Circuit breaker abierto, operación cancelada", 'warning')
            return []
        
        self._rate_limit()

        # Expandir y normalizar para descubrimiento
        channel_url = self._expand_url(channel_url)
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': max_results,  # Optimizado para cuota API
                'socket_timeout': 30,
                'retries': 3,
                'nocheckcertificate': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Obtener información del canal
                info = ydl.extract_info(channel_url, download=False)
                
                # Guardar video_ids en caché para detección rápida de cambios
                if self.enable_video_cache and info:
                    channel_id = info.get('id') or info.get('channel_id')
                    if channel_id:
                        current_video_ids = {entry.get('id') for entry in info.get('entries', []) if entry}
                        cached_ids = self.video_cache.get(channel_id, set())
                        # Solo hay nuevos si la diferencia no es vacía
                        has_new = bool(current_video_ids - cached_ids)
                        self.video_cache[channel_id] = current_video_ids
                
                if 'entries' not in info:
                    self._record_success()
                    return []
                
                videos = []
                cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
                
                for entry in info['entries']:
                    if entry:
                        # Filtrar por fecha de publicación
                        upload_date = entry.get('upload_date')
                        if upload_date:
                            try:
                                video_date = datetime.strptime(upload_date, '%Y%m%d')
                                if video_date < cutoff_date:
                                    continue  # Video más antiguo que max_age_days
                            except ValueError:
                                pass  # Si no se puede parsear, incluir de todos modos
                        
                        video_info = {
                            'video_id': entry.get('id'),
                            'video_url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'title': entry.get('title'),
                            'published_at': upload_date,
                            'duration': entry.get('duration'),
                            'is_shorts': entry.get('duration', 0) < 60 if entry.get('duration') else False,
                        }
                        videos.append(video_info)
                
                self._record_success()
                self._log(f"Obtenidos {len(videos)} videos (filtrados por fecha < {self.max_age_days} días)", 'info')
                return videos
        except Exception as e:
            self._record_failure()
            self._log_structured("channel_videos_error", 
                               channel_url=channel_url, 
                               error=str(e))
            logger.error(f"Error obteniendo videos del canal: {e}")
            return []
    
    def check_for_new_videos(self, channel_id: int = None) -> int:
        """
        Verifica si hay nuevos videos en los canales monitoreados.
        
        Args:
            channel_id: ID de un canal específico, o None para verificar todos
        
        Returns:
            Número de videos nuevos detectados
        """
        self._log("Verificando nuevos videos...", 'info')
        
        # Obtener canales a verificar
        if channel_id:
            channels = [ch for ch in self.db.get_all_channels() if ch['id'] == channel_id]
        else:
            channels = self.db.get_all_channels(active_only=True)
        
        total_new_videos = 0
        
        for channel in channels:
            try:
                self._log(f"Verificando canal: {channel['channel_name']}", 'info')
                
                # Obtener videos recientes del canal
                videos = self._get_channel_videos(channel['channel_url'], self.max_videos_per_check)
                
                new_videos = []
                for video in videos:
                    if not self.db.video_exists(video['video_id']):
                        new_videos.append((
                            channel['id'],
                            video['video_id'],
                            video['video_url'],
                            video['title'],
                            video.get('published_at')
))

                if new_videos:
                    video_map = self.db.add_videos_batch(new_videos)
                    for video in new_videos:
                        video_id = video[1]
                        if video_id in video_map:
                            total_new_videos += 1
                            self._log_structured("video_detected",
                                               video_id=video_id,
                                               channel_id=channel['id'],
                                               title=video[3])
                            self._log(f"Nuevo video detectado: {video[3]}", 'info')

                            if self.on_new_video_callback:
                                self.on_new_video_callback({
                                    'video_id': video_id,
                                    'title': video[3],
'channel_name': channel['channel_name']
                                })

                        if TOAST_AVAILABLE and self.on_log_callback:
                            class MockParent:
                                def winfo_screenwidth(self):
                                    return 1920
                            try:
                                ToastNotification.show(
                                    MockParent(),
                                    f"Nuevo video detectado: {video['title'][:50]}{'...' if len(video['title']) > 50 else ''}",
                                    type="info",
                                    duration=5000
                                )
                            except Exception as e:
                                if self.on_log_callback:
                                    self.on_log_callback(f"Toast notification error: {e}", 'warning')

                        # Actualizar última verificación
                self.db.update_channel_last_checked(channel['id'])
                
                self._log_structured("channel_check_complete",
                                   channel_id=channel['id'],
                                   new_videos=total_new_videos)
                
            except Exception as e:
                self._log(f"Error verificando canal {channel['channel_name']}: {e}", 'error')
                self._log_structured("channel_check_error",
                                   channel_id=channel.get('id'),
                                   error=str(e))
        
        self._log(f"Verificación completada. {total_new_videos} videos nuevos detectados.", 'info')
        
        if total_new_videos > 0 and self.notifier:
            channel_names = [ch['channel_name'] for ch in channels]
            channel_name = channel_names[0] if channel_names else "Canales"
            yt_channel_id = channels[0].get('channel_id') if channels else None
            self._notify_videos_detected(channel_name, total_new_videos, yt_channel_id)
        
        return total_new_videos

    def _check_single_channel(self, channel: Dict) -> int:
        """Verifica un solo canal y retorna el número de videos nuevos (Auto-Healing incl)."""
        scan_start = time.time()
        new_videos_count = 0
        try:
            self._log(f"Verificando canal: {channel['channel_name']}", 'info')
            
            c_url = self._expand_url(channel['channel_url'])

            # Obtener videos recientes del canal (esto también nos da metadatos del canal)
            ydl_opts = {
                'quiet': True, 'no_warnings': True, 'extract_flat': True,
                'playlistend': self.max_results_per_check,  # Optimizado para cuota API
                'socket_timeout': 30, 'retries': 3,
                'nocheckcertificate': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(c_url, download=False)
                
                # Auto-Healing: Verificar si el nombre ha cambiado
                current_yt_name = info.get('uploader') or info.get('title')
                if current_yt_name and current_yt_name != channel['channel_name']:
                    self._log(f"Auto-Healing: Actualizando nombre de canal {channel['channel_name']} -> {current_yt_name}", 'info')
                    self.db.update_channel_name(channel['id'], current_yt_name)
                
                if 'entries' not in info:
                    return 0
                
                # Filtrar por fecha
                cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
                
                for entry in info['entries']:
                    if entry:
                        # Filtrar por fecha de publicación
                        upload_date = entry.get('upload_date')
                        if upload_date:
                            try:
                                video_date = datetime.strptime(upload_date, '%Y%m%d')
                                if video_date < cutoff_date:
                                    continue  # Video más antiguo
                            except ValueError:
                                pass
                        
                        video_id = entry.get('id')
                        video_title = entry.get('title', '')
                        video_description = entry.get('description', '')
                        video_duration = entry.get('duration')  # seconds
                        
                        # Aplicar filtro de palabras clave (híbrido: título + descripción + tags si es necesario)
                        should_process, filter_reason = self.keyword_filter.should_process(
                            video_title, 
                            video_description,
                            video_id
                        )
                        
                        if not should_process:
                            self._log(f"Video ignorado por filtro: {video_title} ({filter_reason})", 'info')
                            self.db.increment_ignored_count(1)
                            continue
                        
                        if not self.db.video_exists(video_id):
                            # Verificar duplicados con el nuevo detector híbrido
                            video_info = {
                                'video_id': video_id,
                                'title': video_title,
                                'duration': video_duration,
                            }
                            
                            is_duplicate, duplicate_info = self.duplicate_detector.check_duplicate(video_info)
                            
                            if is_duplicate:
                                # Marcar como repost y notificar
                                self.db.mark_as_repost(video_id)
                                
                                # Registrar relación de duplicado
                                if duplicate_info.get('similar_videos'):
                                    original_video = duplicate_info['similar_videos'][0]
                                    self.db.add_video_relation(
                                        video_id, 
                                        original_video.get('video_id'),
                                        duplicate_info['type'].value,
                                        confidence=1.0 if duplicate_info['level'].value == 'high' else 0.7
                                    )
                                
                                # Notificar callback si existe
                                if self.on_duplicate_detected_callback:
                                    self.on_duplicate_detected_callback({
                                        'video_id': video_id,
                                        'title': video_title,
                                        'duplicate_info': duplicate_info,
                                        'channel': channel['channel_name']
                                    })
                                
                                self._log(f"⚠️ Duplicado detectado: {video_title} ({duplicate_info['type'].value})", 'warning')
                            
                            # Guardar duración si está disponible
                            if video_duration:
                                self.db.add_video_metadata(video_id, duration_seconds=video_duration)
                            
                            video_db_id = self.db.add_video(
                                channel_id=channel['id'],
                                video_id=video_id,
                                video_url=f"https://www.youtube.com/watch?v={video_id}",
                                title=video_title,
                                published_at=entry.get('upload_date')
                            )
                            if video_db_id:
                                new_videos_count += 1
                                repost_label = " [DUPLICADO]" if is_duplicate else ""
                                self._log(f"Nuevo video detectado: {video_title}{repost_label}", 'info')
                                if self.on_new_video_callback:
                                    self.on_new_video_callback({
                                        'video_id': video_id, 
                                        'title': video_title,
                                        'is_repost': is_duplicate,
                                        'is_duplicate': is_duplicate,
                                        'duplicate_info': duplicate_info
                                    })

            # Actualizar última verificación
            self.db.update_channel_last_checked(channel['id'])
            
            # MÓDULO 3: Log del escaneo completado
            with self._scan_log_lock:
                self.db.log_scan(
                    channel_id=channel['id'],
                    duration_seconds=time.time() - scan_start,
                    videos_found=new_videos_count,
                    errors=None,
                    status='success'
                )
            
            return new_videos_count
            
        except Exception as e:
            error_msg = str(e)
            self._log(f"Error verificando canal {channel['channel_name']}: {error_msg}", 'error')
            
            # MÓDULO 3: Log del escaneo con error
            with self._scan_log_lock:
                self.db.log_scan(
                    channel_id=channel['id'],
                    duration_seconds=time.time() - scan_start,
                    videos_found=0,
                    errors=error_msg,
                    status='error'
                )
            
            return 0
    
    def _check_single_channel_original(self, channel: Dict) -> int:
        """Versión original (sin timing) - mantener para compatibilidad."""
        scan_start = time.time()

    def check_for_new_videos_parallel(self, channel_id: int = None) -> int:
        """Versión optimizada en paralelo de check_for_new_videos."""
        self._log("Iniciando verificación paralela de canales...", 'info')
        
        if channel_id:
            channels = [ch for ch in self.db.get_all_channels() if ch['id'] == channel_id]
        else:
            channels = self.db.get_all_channels(active_only=True)
            
        total_new_videos = 0
        max_workers = min(len(channels), 5) if channels else 1
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._check_single_channel, channel): channel for channel in channels}
            for future in concurrent.futures.as_completed(futures):
                total_new_videos += future.result()
                
        self._log(f"Verificación paralela completada. {total_new_videos} videos nuevos detectados.", 'info')
        return total_new_videos
    
    # ==================== PROCESAMIENTO DE VIDEOS ====================
    
    def process_pending_videos(self, max_videos: int = None) -> int:
        """
        Procesa videos pendientes en la cola.
        
        Args:
            max_videos: Número máximo de videos a procesar
        
        Returns:
            Número de videos procesados exitosamente
        """
        if max_videos is None:
            max_videos = self.max_videos_per_check
        
        pending_videos = self.db.get_pending_videos(limit=max_videos)
        
        if not pending_videos:
            self._log("No hay videos pendientes de procesar.", 'info')
            return 0
        
        self._log(f"Procesando {len(pending_videos)} videos pendientes...", 'info')
        processed_count = 0
        
        for video in pending_videos:
            try:
                # Actualizar estado a 'processing'
                self.db.update_video_status(video['id'], 'processing')
                
                self._log(f"Procesando: {video['title']}", 'info')
                
                # 1. Descargar transcripción
                success = self._download_video_transcription(video)
                
                if not success:
                    self.db.update_video_status(video['id'], 'failed', 
                                               'Error descargando transcripción')
                    if self.video_tracker:
                        self.video_tracker.update_video_status(
                            video.get('video_id', ''), 
                            video.get('channel_id', ''), 
                            'failed'
                        )
                    continue
                
                # 2. Procesar y limpiar transcripción
                transcription_file = self._find_transcription_file(video['video_id'])
                
                if not transcription_file:
                    self.db.update_video_status(video['id'], 'failed', 
                                               'Archivo de transcripción no encontrado')
                    if self.video_tracker:
                        self.video_tracker.update_video_status(
                            video.get('video_id', ''), 
                            video.get('channel_id', ''), 
                            'failed'
                        )
                    continue
                
                # 3. Integrar en base de conocimiento
                self._integrate_to_knowledge_base(video, transcription_file)
                
                # 4. Escanear transcripción para manuales protegidos (auto-merge)
                if self.manual_merger:
                    try:
                        with open(transcription_file, 'r', encoding='utf-8') as f:
                            raw_text = f.read()
                        clean_text = self.processing_service.clean_content(raw_text)
                        self.manual_merger.scan_transcription_for_manuals(
                            clean_text,
                            source_name=f"{video.get('channel_name', '')} - {video.get('title', '')}"
                        )
                    except Exception as e:
                        self._log(f"Error en auto-merge de manuales: {e}", 'warning')
                
                # 5. Marcar como completado
                self.db.update_video_status(video['id'], 'completed')
                if self.video_tracker:
                    self.video_tracker.update_video_status(
                        video.get('video_id', ''), 
                        video.get('channel_id', ''), 
                        'downloaded'
                    )
                processed_count += 1
                
                self._log(f"Video procesado exitosamente: {video['title']}", 'info')
                
                if self.on_processing_complete_callback:
                    self.on_processing_complete_callback(video)
                
                if self.notifier:
                    self._notify_processing_complete(video.get('title', ''), 'completado')
                
                # Pequeña pausa adicional entre videos para no saturar
                time.sleep(Config.YT_SLEEP_REQUESTS)
                
                
            except Exception as e:
                error_msg = f"Error procesando video: {e}"
                self._log(error_msg, 'error')
                self.db.update_video_status(video['id'], 'failed', str(e))
                
                if self.on_error_callback:
                    self.on_error_callback(error_msg)
        
        self._log(f"Procesamiento completado. {processed_count}/{len(pending_videos)} videos procesados.", 'info')
        return processed_count
    
    def _download_video_transcription(self, video: Dict) -> bool:
        """Descarga la transcripción de un video."""
        # Verificar espacio en disco
        if not self._check_disk_space():
            self._log_structured("disk_space_low", video_id=video.get('video_id'))
            self._log("Espacio en disco insuficiente", 'error')
            return False
        
        # Check deduplicación: si ya tiene hash_raw, no descargar de nuevo
        existing_hash_raw = self.db.get_video_hash_raw(video.get('video_id', ''))
        if existing_hash_raw:
            self._log(f"⏭️ Video ya descargado y validado (hash_raw existe): {video.get('title', '')}", 'info')
            return True
        
        start_time = time.time()
        
        try:
            if self.download_service:
                success, message = self.download_service.perform_download(video['video_url'])
                return success
            else:
                ydl_opts = {
                    'skip_download': True,
                    'writeautomaticsub': True,
                    'writesub': True,
                    'subtitleslangs': ['es', 'en'],
                    'outtmpl': f'{self.input_dir}/%(title)s [%(id)s].%(ext)s',
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 30,
                    'retries': 3,
                    'restrictfilenames': True,
                }
                self._call_ytdlp_raw(video['video_url'], ydl_opts)
                
                elapsed = time.time() - start_time
                self._log_structured("transcription_downloaded",
                                   video_id=video.get('video_id'),
                                   duration_seconds=round(elapsed, 2))
                return True
        except (RateLimitError, NetworkError) as e:
            elapsed = time.time() - start_time
            self._log_structured("transcription_download_error",
                               video_id=video.get('video_id'),
                               error=f"{type(e).__name__}: {str(e)}",
                               duration_seconds=round(elapsed, 2))
            self._log(f"⚠️ Error de red: {type(e).__name__}", 'warning')
            return False
        except (VideoUnavailableError, SubtitleMissingError) as e:
            elapsed = time.time() - start_time
            self._log_structured("transcription_download_skipped",
                               video_id=video.get('video_id'),
                               reason=str(e),
                               duration_seconds=round(elapsed, 2))
            self._log(f"⏭️ Video no disponible o sin subtítulos: {video.get('title')}", 'info')
            return None
        except Exception as e:
            elapsed = time.time() - start_time
            self._log_structured("transcription_download_error",
                               video_id=video.get('video_id'),
                               error=str(e),
                               duration_seconds=round(elapsed, 2))
            logger.error(f"Error descargando transcripción: {e}")
            return False
    
    def _find_transcription_file(self, video_id: str) -> Optional[Path]:
        """Busca el archivo de transcripción de un video."""
        # Buscar archivos .vtt o .srt que contengan el video_id
        for ext in ['.vtt', '.srt']:
            for file in self.input_dir.glob(f"*[{video_id}]*{ext}"):
                return file
        return None
    
    def _integrate_to_knowledge_base(self, video: Dict, transcription_file: Path):
        """Integra la transcripción en la base de conocimiento."""
        start_time = time.time()
        
        try:
            # Calcular checksum del archivo
            checksum = self._calculate_checksum(transcription_file)
            
            # Guardar hash_raw del VTT para deduplicación en descarga
            self.db.update_video_content_hash_raw(video['video_id'], checksum)
            
            # Leer transcripción con fallback de encoding
            try:
                with open(transcription_file, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
            except UnicodeDecodeError:
                # Fallback a latin-1
                self._log(f"Fallback a latin-1 para {transcription_file.name}", 'warning')
                with open(transcription_file, 'r', encoding='latin-1') as f:
                    raw_text = f.read()
            
            file_size = transcription_file.stat().st_size
            
            # Limpiar texto
            clean_text = self.processing_service.clean_content(raw_text)
            
            # Verificar si el contenido ya existe por checksum (Enterprise Deduplication)
            content_checksum = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
            
            # Deduplicación: verificar si este contenido ya fue procesado
            if self.db.check_content_hash_exists(content_checksum):
                self._log_structured("content_duplicate_detected",
                                   video_id=video.get('video_id'),
                                   content_hash=content_checksum[:16])
                self._log(f"Contenido duplicado detectado, omitiendo procesamiento: {video.get('title')}", 'warning')
                # Marcar como completado pero sin integrar
                self.db.update_video_status(video['id'], 'completed')
                return
            
            # Guardar content_hash en BD para futuras deduplicaciones
            self.db.update_video_content_hash(video['video_id'], content_checksum)
            
            # Integrar en KB
            source_name = f"{video['channel_name']} - {video['title']}"
            result = self.knowledge_integrator.analyze_text(clean_text, source_name)
            
            elapsed = time.time() - start_time
            self._log_structured("kb_integration_complete",
                               video_id=video.get('video_id'),
                               file_size_bytes=file_size,
                               checksum=checksum,
                               content_hash=content_checksum[:16],
                               duration_seconds=round(elapsed, 2),
                               result=str(result))
            
            logger.info(f"Integración KB: {result}")
            
        except Exception as e:
            elapsed = time.time() - start_time
            self._log_structured("kb_integration_error",
                               video_id=video.get('video_id'),
                               error=str(e),
                               duration_seconds=round(elapsed, 2))
            logger.error(f"Error integrando a KB: {e}")
            raise
    
    # ==================== SCHEDULER AUTOMÁTICO ====================
    
    def start_monitoring(self):
        """Inicia el monitoreo automático en segundo plano."""
        if self.monitoring:
            self._log("El monitoreo ya está activo.", 'warning')
            return
        
        self.monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self._log(f"Monitoreo automático iniciado (intervalo: {self.interval_minutes} min)", 'info')
    
    def stop_monitoring(self):
        """Detiene el monitoreo automático."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self._log("Monitoreo automático detenido.", 'info')
    
    def _monitor_loop(self):
        """Loop principal del monitor (ejecutado en thread separado)."""
        while self.monitoring and not self.stop_event.is_set():
            try:
                # Limpiar videos huérfanos en estado 'processing'
                self.db.reset_stale_processing_videos(hours_threshold=1)
                
                # Verificar nuevos videos (versión paralela)
                new_count = self.check_for_new_videos_parallel()
                
                # Procesar videos pendientes
                if new_count > 0:
                    self.process_pending_videos()
                
            except Exception as e:
                self._log_structured("monitor_loop_error", error=str(e))
                self._log(f"Error en ciclo de monitoreo: {e}", 'error')
                if self.on_error_callback:
                    self.on_error_callback(str(e))
            
            # Esperar el intervalo configurado
            self.stop_event.wait(self.interval_minutes * 60)
    
    def is_monitoring(self) -> bool:
        """Retorna True si el monitoreo está activo."""
        return self.monitoring
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del sistema de monitoreo."""
        return self.db.get_statistics()
