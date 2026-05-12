import os
import re
import yt_dlp
from pathlib import Path
import time
import random
import hashlib
from app.core.config import Config
from app.services.retry_decorator import retry_yt_dlp
from app.services.yt_dlp_errors import RateLimitError, AuthRequiredError, NetworkError, VideoUnavailableError, SubtitleMissingError

GET_CONTEXT = lambda *a, **kw: {
    "url": kw.get("url") or (a[1] if len(a) > 1 else "unknown"),
    "video_id": kw.get("video_id") or (a[2] if len(a) > 2 else None)
}

class DownloadService:
    """
    Servicio de descarga de transcripciones de YouTube.
    
    MODO DESCARGA TRANSCRIPCIONES (optimize=False, DEFAULT):
    - Paso 1: Obtiene lista de videos del canal
    - Paso 2: Descarga SOLO subtítulos .vtt + metadatos .json por video
    - NO descarga video ni audio
    - Protecciones anti-rate-limiting incluidas
    
    MODO SOLO VERIFICAR (optimize=True):
    - Solo comprueba que la URL responde
    """
    def __init__(self, input_dir, optimize, secure_mode, ffmpeg_location, progress_callback=None, log_callback=None, batch_progress_callback=None, db_manager=None):
        self.input_dir = input_dir
        self.optimize = optimize
        self.secure_mode = secure_mode
        self.ffmpeg_location = ffmpeg_location
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.batch_progress_callback = batch_progress_callback
        self.db_manager = db_manager
        self._downloaded_count = 0
        self._consecutive_errors = 0
        self._last_request_time = 0
        self._batch_stats = {"new": 0, "existing": 0, "no_subs": 0, "errors": 0}
        # Scoring IA
        self._scoring_enabled = False
        self._scoring_service = None
        self._scoring_min_score = 50
        # Configuración de descarga masiva
        self._video_limit = 50  # Límite de videos por defecto
        self._page_offset = 0   # Offset para paginación
        self._min_duration = 0  # Duración mínima en segundos (0 = sin límite)
        self._max_duration = 0  # Duración máxima en segundos (0 = sin límite)
        self._date_from = None  # Fecha desde (YYYYMMDD)
        self._date_to = None    # Fecha hasta (YYYYMMDD)
        # Módulos A3, A6: Validación de Región + Proxy Rotativo
        self._geo_check_enabled = True
        self._proxy_list = []
        self._proxy_index = 0
        self._proxy_enabled = False
        # Módulo A4: Check de Licencia
        self._license_check_enabled = True
    
    def enable_scoring(self, min_score: int = 50, db_manager=None) -> bool:
        """
        Habilita el scoring IA para el flujo de descarga.
        
        Args:
            min_score: Score mínimo (0-100) para descargar
            db_manager: Instancia de DBManager para persistir scores
            
        Returns:
            True si se habilitó correctamente
        """
        if db_manager:
            self.db_manager = db_manager
        if self._scoring_service is None:
            try:
                from app.services.kdp_scoring_service import create_scoring_service
                self._scoring_service = create_scoring_service()
                self._scoring_min_score = min_score
                self._scoring_enabled = True
                if self.log_callback:
                    self.log_callback("🎯 Scoring IA habilitado (KDP Relevance Filter)")
                return True
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"⚠️ No se pudo habilitar scoring: {e}", level='warning')
                return False
        else:
            self._scoring_enabled = True
            return True
    
    def disable_scoring(self):
        """Deshabilita el scoring IA."""
        self._scoring_enabled = False
        if self.log_callback:
            self.log_callback("🎯 Scoring IA deshabilitado")
    
    # === MÉTODOS DE CONFIGURACIÓN DE DESCARGA MASIVA ===
    
    def set_video_limit(self, limit: int):
        """Configura el límite de videos a procesar (0 = sin límite)."""
        self._video_limit = max(0, limit)
        if self.log_callback:
            self.log_callback(f"📊 Límite de videos configurado: {limit or 'Sin límite'}")
    
    def set_pagination(self, offset: int = 0, limit: int = 50):
        """
        Configura paginación para descargas masivas.
        
        Args:
            offset: Número de videos a saltar desde el inicio
            limit: Número máximo de videos a procesar
        """
        self._page_offset = max(0, offset)
        self._video_limit = max(0, limit)
        if self.log_callback:
            self.log_callback(f"📄 Paginación: offset={offset}, limit={limit}")
    
    def set_duration_filter(self, min_seconds: int = 0, max_seconds: int = 0):
        """
        Configura filtro de duración.
        
        Args:
            min_seconds: Duración mínima en segundos (0 = sin mínimo)
            max_seconds: Duración máxima en segundos (0 = sin máximo)
        """
        self._min_duration = max(0, min_seconds)
        self._max_duration = max(0, max_seconds)
        if self.log_callback:
            min_str = f"{min_seconds//60}min" if min_seconds else "0"
            max_str = f"{max_seconds//60}min" if max_seconds else "∞"
            self.log_callback(f"⏱️ Filtro duración: {min_str} - {max_str}")
    
    def set_date_filter(self, date_from: str = None, date_to: str = None):
        """
        Configura filtro por fecha de publicación.
        
        Args:
            date_from: Fecha desde en formato YYYYMMDD (ej: "20240101")
            date_to: Fecha hasta en formato YYYYMMDD (ej: "20241231")
        """
        self._date_from = date_from
        self._date_to = date_to
        if self.log_callback:
            self.log_callback(f"📅 Filtro fecha: {date_from or '∞'} - {date_to or '∞'}")
    
    def get_batch_config(self) -> dict:
        """Retorna la configuración actual de descarga masiva."""
        return {
            "video_limit": self._video_limit,
            "page_offset": self._page_offset,
            "min_duration": self._min_duration,
            "max_duration": self._max_duration,
            "date_from": self._date_from,
            "date_to": self._date_to,
            "scoring_enabled": self._scoring_enabled
        }
    
    def _filter_video_by_metadata(self, entry: dict) -> tuple[bool, str]:
        """
        Filtra un video según criterios de duración y fecha.
        
        Returns:
            (should_include, reason)
        """
        if not entry:
            return False, "empty_entry"
        
        # Filtrar por duración
        duration = entry.get('duration') or 0
        if self._min_duration > 0 and duration < self._min_duration:
            return False, f"duration_short:{duration}s < {self._min_duration}s"
        if self._max_duration > 0 and duration > self._max_duration:
            return False, f"duration_long:{duration}s > {self._max_duration}s"
        
        # Filtrar por fecha
        upload_date = entry.get('upload_date') or entry.get('published') or ''
        if upload_date:
            if self._date_from and upload_date < self._date_from:
                return False, f"date_before:{upload_date} < {self._date_from}"
            if self._date_to and upload_date > self._date_to:
                return False, f"date_after:{upload_date} > {self._date_to}"
        
        return True, "passed"
    
    def _should_download_video(self, title: str, description: str = "", 
                              channel_name: str = "") -> tuple[bool, str]:
        """
        Determina si un video debe descargarse según scoring IA.
        
        Returns:
            (should_download, reason)
        """
        if not self._scoring_enabled or self._scoring_service is None:
            return True, "scoring_disabled"
        
        try:
            score_result = self._scoring_service.score_video(
                title=title,
                description=description,
                channel_name=channel_name
            )
            
            if score_result.recommended_action == "download":
                return True, f"score:{score_result.kdp_relevance_score}"
            elif score_result.recommended_action == "review":
                if self.log_callback:
                    self.log_callback(f"   🔍 Revisar: {title[:50]}... (score: {score_result.kdp_relevance_score})", level='info')
                return False, "needs_review"
            else:
                return False, f"skipped:{score_result.reasoning[:50]}"
        except Exception as e:
            # En caso de error, permitir descarga
            return True, f"scoring_error:{e}"
    
    # ==================== MÓDULOS A3, A4, A6: VALIDACIÓN ====================
    
    def _check_geo_restriction(self, video_url: str) -> tuple[bool, str]:
        """
        Módulo A3: Validación de Región (Geo-Block)
        Verifica si el video está bloqueado por región.
        
        Returns:
            (is_available, reason)
        """
        if not self._geo_check_enabled:
            return True, "geo_check_disabled"
        
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if not info:
                    return False, "video_info_unavailable"
                
                # yt-dlp detecta restricciones de región en 'availability'
                availability = info.get('availability', '')
                
                # Verificar restricciones conocidas
                restricted = ['private', 'members_only', 'needs_auth', 'unlisted']
                if availability in restricted:
                    return False, f"geo_restricted:{availability}"
                
                # Verificar si hay mensajes de restricción en descripción
                description = info.get('description', '') or ''
                geo_keywords = ['not available in your country', 'geo-blocked', 'unavailable in your region']
                if any(kw in description.lower() for kw in geo_keywords):
                    return False, "geo_restricted:description"
                
                return True, "geo_ok"
        except Exception as e:
            error_str = str(e).lower()
            if 'geo' in error_str or 'region' in error_str or 'country' in error_str:
                return False, f"geo_blocked:{e}"
            # Si hay error pero no es de geo, permitir descarga (fallback)
            return True, f"geo_check_error:{e}"
    
    def _check_video_license(self, video_url: str) -> tuple[bool, str]:
        """
        Módulo A4: Check de Licencia (Creative Commons)
        Verifica el tipo de licencia del video.
        
        Returns:
            (is_allowed, reason) - False si licencia restrictiva
        """
        if not self._license_check_enabled:
            return True, "license_check_disabled"
        
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if not info:
                    return True, "license_unknown"
                
                # Verificar licencia
                license_ = info.get('license', '') or ''
                
                # Licencias restrictivas que bloqueamos
                restrictive_licenses = [
                    'youtube',
                    'standard youtube',
                ]
                
                if license_.lower() in restrictive_licenses:
                    # YouTube Standard - permitir pero marcar
                    return True, "license_standard"
                
                # Creative Commons - permitido
                if 'cc' in license_.lower() or 'creative commons' in license_.lower():
                    return True, "license_cc"
                
                return True, "license_ok"
        except Exception as e:
            # Si no se puede determinar, permitir
            return True, f"license_check_error:{e}"
    
    def set_proxy_list(self, proxy_list: list):
        """
        Módulo A6: Proxy Rotativo
        Configura lista de proxies para rotación.
        
        Args:
            proxy_list: Lista de URLs de proxy (e.g., ['http://ip:port', ...])
        """
        self._proxy_list = proxy_list
        self._proxy_enabled = bool(proxy_list)
        self._proxy_index = 0
        if self.log_callback and self._proxy_enabled:
            self.log_callback(f"🔄 Proxy rotativo habilitado: {len(proxy_list)} proxies")
    
    def _get_next_proxy(self) -> str:
        """
        Obtiene el siguiente proxy de la lista (rotación circular).
        
        Returns:
            URL del proxy o empty string si no hay proxy configurado
        """
        if not self._proxy_enabled or not self._proxy_list:
            return ""
        
        proxy = self._proxy_list[self._proxy_index]
        self._proxy_index = (self._proxy_index + 1) % len(self._proxy_list)
        return proxy
    
    def _apply_proxy_config(self, ydl_opts: dict):
        """Aplica configuración de proxy al opts de yt-dlp."""
        if self._proxy_enabled and self._proxy_list:
            proxy = self._get_next_proxy()
            if proxy:
                ydl_opts['proxy'] = proxy
                if self.log_callback:
                    self.log_callback(f"   🌐 Usando proxy: {proxy[:50]}...")
    
    def enable_geo_check(self, enabled: bool = True):
        """Habilita/deshabilita validación de geo-restricciones."""
        self._geo_check_enabled = enabled
    
    def enable_license_check(self, enabled: bool = True):
        """Habilita/deshabilita validación de licencias."""
        self._license_check_enabled = enabled
    
    # ==================== FIN MÓDULOS DE VALIDACIÓN ====================
    
    def _rate_limit_wait(self, base_delay=None):
        """Espera variable anti-rate-limiting con jitter."""
        if base_delay is None:
            base_delay = Config.YT_SLEEP_REQUESTS
        
        # Jitter aleatorio para simular comportamiento humano
        jitter = random.uniform(0.5, 2.0)
        delay = base_delay * jitter
        
        # Backoff exponencial si hay errores consecutivos
        if self._consecutive_errors > 0:
            delay *= (2 ** min(self._consecutive_errors, 5))
        
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < delay:
                time.sleep(delay - elapsed)
        
        self._last_request_time = time.time()
        return delay

    def _progress_hook(self, d):
        if self.progress_callback:
            if d['status'] == 'downloading':
                p_str = d.get('_percent_str', '0%').replace('%', '')
                try:
                    self.progress_callback(float(p_str))
                except (ValueError, TypeError):
                    pass

    # === MODULO: PROGRESO_LOTES (INICIO) ===
    def _report_batch_progress(self, current, total, status, detail=None):
        """Reporta progreso global del lote al UI."""
        if not self.batch_progress_callback:
            return
        
        stats = {
            "current": current,
            "total": total,
            "new": self._batch_stats["new"],
            "existing": self._batch_stats["existing"],
            "no_subs": self._batch_stats["no_subs"],
            "errors": self._batch_stats["errors"],
            "status": status,
            "detail": detail or ""
        }
        
        try:
            self.batch_progress_callback(stats)
        except Exception:
            pass
    
    def _reset_batch_stats(self):
        """Resetea estadísticas del lote."""
        self._batch_stats = {"new": 0, "existing": 0, "no_subs": 0, "errors": 0}
    # === MODULO: PROGRESO_LOTES (FIN) ===

    @retry_yt_dlp(max_attempts=2, base_delay=3.0, get_context=GET_CONTEXT)
    def _call_ytdlp_raw(self, url, opts):
        """Llamada directa a yt-dlp, protegida por el decorador de reintentos."""
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    def _is_channel_url(self, url):
        url_lower = url.lower()
        indicators = ['/videos', '/playlist', '/channel/', '/c/', '/@', 'youtube.com/@']
        return any(ind in url_lower for ind in indicators) or url.startswith('@')

    def _normalize_channel_url(self, url):
        url = url.strip()
        if url.startswith('@'):
            url = f"https://www.youtube.com/{url}"
        if '/videos' not in url and '/playlist' not in url and 'watch?' not in url:
            url = url.rstrip('/') + '/videos'
        return url

    def perform_download(self, url):
        """
        Descarga transcripciones .vtt.
        Retorna (success, message).
        """
        self._downloaded_count = 0
        
        if self.optimize:
            return self._verify_url_only(url)
        
        if self._is_channel_url(url):
            return self._download_channel_transcriptions(url)
        else:
            return self._download_single_video_transcription(url)

    def _verify_url_only(self, url):
        """Solo verifica que la URL responde."""
        url = url.strip()
        if url.startswith('@'):
            url = f"https://www.youtube.com/{url}"
        if '/videos' not in url and '/playlist' not in url and 'watch?' not in url:
            url = url.rstrip('/') + '/videos'
        
        if self.log_callback: 
            self.log_callback(f"🔍 Verificando URL (sin descargar): {url}")
        
        try:
            ydl_opts = {
                'skip_download': True,
                'writeautomaticsub': False,
                'writesubtitles': False,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': 1,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    title = info.get('title') or info.get('channel', 'Canal')
                    if self.log_callback:
                        self.log_callback(f"  ✅ URL válida: {title}")
                    return True, f"URL verificada: {title}"
            
            return False, "No se pudo obtener información de la URL"
        except Exception as e:
            return False, str(e)

    def _download_channel_transcriptions(self, url):
        """
        PASO 1: Obtiene lista de video IDs del canal
        PASO 2: Descarga subtítulos .vtt de cada video individualmente
        Con protecciones anti-rate-limiting y filtros configurables
        """
        url = self._normalize_channel_url(url)

        if self.log_callback:
            self.log_callback("Canal: obtaining video list...")
            self.log_callback(f"   URL: {url}")

        # PASO 1: Obtener lista de videos CON METADATA para filtrado
        video_entries = []
        skipped_by_filter = 0
        try:
            # Configurar paginación
            playlist_start = self._page_offset + 1  # yt-dlp es 1-indexed
            playlist_end = self._page_offset + self._video_limit if self._video_limit > 0 else None

            list_opts = {
                'skip_download': True,
                'writeautomaticsub': False,
                'writesubtitles': False,
                'writeinfojson': False,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,  # Necesitamos metadata completa para filtrado
                'playliststart': playlist_start,
                'playlistend': playlist_end,
            }

            if self.log_callback:
                self.log_callback(f"   Pagination: start={playlist_start}, end={playlist_end or 'all'}")

            with yt_dlp.YoutubeDL(list_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if self.log_callback:
                    self.log_callback(f"   Info obtained: {type(info)}")
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('id'):
                            # Verificar si pasa los filtros de duración/fecha
                            should_include, reason = self._filter_video_by_metadata(entry)
                            if should_include:
                                video_entries.append(entry)
                            else:
                                skipped_by_filter += 1
                                if self.log_callback and skipped_by_filter <= 5:
                                    title = entry.get('title', 'Unknown')[:40]
                                    self.log_callback(f"   Filtered ({reason}): {title}")
                elif info and info.get('id'):
                    should_include, _ = self._filter_video_by_metadata(info)
                    if should_include:
                        video_entries.append(info)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"   Warning: Error getting video list: {e}", level='warning')
            return False, f"Error getting video list: {e}"

        if not video_entries:
            filter_msg = f" ({skipped_by_filter} filtered)" if skipped_by_filter > 0 else ""
            if self.log_callback:
                self.log_callback(f"   Warning: No videos found{filter_msg}")
            return False, "No videos in channel after filtering"

        # Extraer IDs de videos válidos
        video_ids = [e.get('id') for e in video_entries if e.get('id')]

        total = len(video_ids)
        if self.log_callback:
            filter_info = f" | {skipped_by_filter} filtered by duration/date" if skipped_by_filter > 0 else ""
            self.log_callback(f"   Stats: {total} videos to process{filter_info}")
            self.log_callback(f"   Anti-block delays: {Config.YT_SLEEP_REQUESTS}s + jitter")

        self._reset_batch_stats()
        self._report_batch_progress(0, total, "discovering", f"{total} videos in channel")

        # LOOP DE DESCARGA
        success_count = 0
        no_subs_count = 0
        skipped_count = 0
        error_count = 0
        rate_limited_count = 0

        for idx, vid in enumerate(video_ids):
            video_url = f"https://www.youtube.com/watch?v={vid}"

            try:
                # Scoring y filtrado pre-descarga
                should_download = True
                scoring_info = None

                if self._scoring_enabled and self._scoring_service:
                    try:
                        preview_opts = {
                            'skip_download': True,
                            'quiet': True,
                            'no_warnings': True,
                            'extract_flat': True,
                        }
                        with yt_dlp.YoutubeDL(preview_opts) as ydl:
                            vid_info = ydl.extract_info(video_url, download=False)
                            if vid_info:
                                title = vid_info.get('title', '')
                                channel = vid_info.get('channel', vid_info.get('uploader', ''))
                                scoring_info = self._scoring_service.score_video(
                                    title=title, description='', channel_name=channel
                                )
                                if scoring_info.recommended_action in ['skip', 'watch_later']:
                                    if self.log_callback:
                                        self.log_callback(f"   Skipped (score: {scoring_info.kdp_relevance_score}/100): {title[:50]}")
                                    skipped_count += 1
                                    self._batch_stats["existing"] += 1
                                    continue
                    except Exception as e:
                        if self.log_callback:
                            self.log_callback(f"   Warning: Scoring error: {e}", level='warning')

                result = self._download_video_subs(video_url, idx + 1, total)
                if result == 'downloaded':
                    success_count += 1
                    self._batch_stats["new"] += 1
                    self._consecutive_errors = 0
                elif result == 'no_subs':
                    no_subs_count += 1
                    self._batch_stats["no_subs"] += 1
                elif result == 'skipped':
                    skipped_count += 1
                    self._batch_stats["existing"] += 1
                elif result == 'rate_limited':
                    rate_limited_count += 1
                    error_count += 1
                    self._batch_stats["errors"] += 1
                    self._consecutive_errors += 1
                    wait = self._rate_limit_wait(base_delay=10)
                    if self.log_callback:
                        self.log_callback(f"   Rate limit, waiting {wait:.1f}s")
                    time.sleep(wait)
                else:
                    error_count += 1
                    self._batch_stats["errors"] += 1
                    self._consecutive_errors += 1
            except Exception as e:
                error_count += 1
                self._batch_stats["errors"] += 1
                self._consecutive_errors += 1
                if self.log_callback:
                    self.log_callback(f"   Error video {idx+1}/{total}: {e}", level='warning')

            self._report_batch_progress(idx + 1, total, "downloading", f"video {idx + 1}")

            # Pausa anti-rate-limiting
            if idx < total - 1:
                delay = self._rate_limit_wait()
                if self.log_callback and idx % 5 == 0:
                    self.log_callback(f"   Pause: {delay:.1f}s ({idx+1}/{total}, {success_count} ok)")

        self._downloaded_count = success_count
        self._report_batch_progress(total, total, "completed", f"{success_count} new, {skipped_count} skipped")

        msg = f"Channel: {success_count} subs, {no_subs_count} no-subs, {skipped_count} skipped, {rate_limited_count} rate-limited, {error_count} errors of {total} videos"
        if self.log_callback:
            self.log_callback(f"Done: {msg}")

        return True, msg

    def _download_video_subs(self, video_url, current=0, total=0):
        """
        Descarga SOLO subtítulos .vtt + metadatos .json de un video.
        Retorna: 'downloaded', 'no_subs', 'rate_limited', 'skipped', o 'error'
        """
        label = f"[{current}/{total}] " if current and total else ""
        
        # SECURE_MODE: Verificar si ya existe antes de descargar
        if self.secure_mode:
            try:
                check_opts = {
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                }
                with yt_dlp.YoutubeDL(check_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    if info and info.get('id'):
                        vid_id = info['id']
                        channel = info.get('channel', info.get('uploader', ''))
                        if channel:
                            channel_dir = Path(self.input_dir) / channel
                            if channel_dir.exists():
                                existing = list(channel_dir.glob(f"*[{vid_id}]*.vtt"))
                                if existing:
                                    title = info.get('title', video_url)[:80]
                                    if self.log_callback:
                                        self.log_callback(f"   ⏭️ {label}Ya existe (secure_mode): {title}")
                                    return 'skipped'
            except Exception:
                pass
        
        return self._download_with_retry(video_url, label)

    def _download_with_retry(self, video_url, label, max_retries=2):
        """
        Descarga con reintentos automáticos si la validación falla.
        """
        ydl_opts = {
            'skip_download': True,
            'writeautomaticsub': True,
            'writesubtitles': True,
            'subtitlesformat': 'vtt',
            'subtitleslangs': ['es', 'en'],
            'writeinfojson': True,
            'write_description': False,
            'write_thumbnail': False,
            'outtmpl': f'{self.input_dir}/%(channel)s/%(upload_date)s_%(title)s [%(id)s].%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'restrictfilenames': True,
            'windowsfilenames': True,
            'progress_hooks': [self._progress_hook],
            'sleep_interval': Config.YT_SLEEP_INTERVAL,
            'max_sleep_interval': Config.YT_MAX_SLEEP_INTERVAL,
        }
        
        for attempt in range(max_retries + 1):
            try:
                info = self._call_ytdlp_raw(video_url, ydl_opts)
                    
                if info is None:
                    if self.log_callback:
                        self.log_callback(f"   ❌ {label}Error: sin respuesta de yt-dlp", level='warning')
                    return 'error'
                    
                subs_downloaded = False
                if info:
                    requested_subs = info.get('requested_subtitles', {})
                    if requested_subs:
                        subs_downloaded = True
                    
                    vid_id = info.get('id', '') if info else ''
                    if vid_id:
                        channel = info.get('channel', info.get('uploader', ''))
                        if channel:
                            search_dir = Path(self.input_dir) / channel
                            if search_dir.exists():
                                vtt_files = list(search_dir.glob(f"*[{vid_id}]*.vtt"))
                            else:
                                vtt_files = list(Path(self.input_dir).glob(f"**/*[{vid_id}]*.vtt"))
                            if vtt_files:
                                subs_downloaded = True
                    
                if subs_downloaded:
                    is_valid, md5_hash = self._validate_downloaded_file(video_url, info)
                        
                    if is_valid:
                        title = info.get('title', video_url)[:80] if info else video_url
                        if self.log_callback:
                            self.log_callback(f"   ✅ {label}{title}")
                        
                        if self._scoring_enabled and self._scoring_service:
                            score_result = self._scoring_service.score_video(
                                title=info.get('title', ''),
                                description=info.get('description', ''),
                                channel_name=info.get('channel', '')
                            )
                            if self.log_callback:
                                self.log_callback(f"   🎯 Relevance Score: {score_result.kdp_relevance_score}/100 ({score_result.relevance_level.value})")
                            if self.db_manager and info:
                                video_id = info.get('id', '')
                                if video_id:
                                    try:
                                        self.db_manager.update_video_kdp_score(video_id, score_result.kdp_relevance_score)
                                    except Exception as e:
                                        if self.log_callback:
                                            self.log_callback(f"   ⚠️ Error guardando score: {e}", level='warning')
                        return 'downloaded'
                    else:
                        if attempt < max_retries:
                            vid_id = info.get('id', '') if info else ''
                            channel = info.get('channel', info.get('uploader', '')) if info else ''
                            if channel and vid_id:
                                search_dir = Path(self.input_dir) / channel
                                if search_dir.exists():
                                    for f in search_dir.glob(f"*[{vid_id}]*.vtt"):
                                        try:
                                            f.unlink()
                                        except:
                                            pass
                            if self.log_callback:
                                self.log_callback(f"   ⚠️ {label}Archivo corrupto, reintento {attempt + 1}/{max_retries}...", level='warning')
                            continue
                        else:
                            title = info.get('title', video_url)[:80] if info else video_url
                            if self.log_callback:
                                self.log_callback(f"   ❌ {label}Archivo corrupto tras {max_retries} reintentos: {title}", level='warning')
                            return 'error'
                else:
                    title = info.get('title', video_url)[:80] if info else video_url
                    if self.log_callback:
                        self.log_callback(f"   ⏭️ {label}Sin subtítulos disponibles: {title}")
                    return 'no_subs'
                        
            except (RateLimitError, NetworkError) as e:
                if attempt < max_retries:
                    if self.log_callback:
                        self.log_callback(f"   ⚠️ {label}{type(e).__name__}: {str(e)[:80]}, reintento {attempt + 1}/{max_retries}", level='warning')
                    continue
                if self.log_callback:
                    self.log_callback(f"   ❌ {label}{type(e).__name__}: {str(e)[:80]}", level='warning')
                return 'error'
            except (SubtitleMissingError, VideoUnavailableError) as e:
                if self.log_callback:
                    self.log_callback(f"   ⏭️ {label}{type(e).__name__}: {str(e)[:80]}")
                return 'no_subs'
            except Exception as e:
                error_str = str(e)
                if self.log_callback:
                    self.log_callback(f"   ❌ {label}Error: {error_str[:100]}", level='warning')
                return 'error'
        
        return 'error'

    def _validate_downloaded_file(self, video_url, info):
         """
         Valida el archivo VTT descargado.
         Retorna: (is_valid, md5_hash)
         - is_valid: True si el archivo es un VTT válido
         - md5_hash: Hash MD5 del archivo si es válido, None si no
         """
         try:
             vid_id = info.get('id', '') if info else ''
             channel = info.get('channel', info.get('uploader', '')) if info else ''
             
             if not vid_id or not channel:
                 return True, None
             
             search_dir = Path(self.input_dir) / channel
             if not search_dir.exists():
                 return True, None
             
             vtt_files = list(search_dir.glob(f"*[{vid_id}]*.vtt"))
             if not vtt_files:
                 return True, None
             
             latest_file = max(vtt_files, key=lambda f: f.stat().st_mtime)
             
             file_size = latest_file.stat().st_size
             if file_size < 50:
                 if self.log_callback:
                     self.log_callback(f"   ⚠️ Archivo muy pequeño ({file_size} bytes), probable corrupto", level='warning')
                 return False, None
             
             with open(latest_file, 'r', encoding='utf-8', errors='ignore') as f:
                 header = f.read(100)
                 if 'WEBVTT' not in header:
                     if self.log_callback:
                         self.log_callback(f"   ⚠️ Archivo no es VTT válido (header incorrecto)", level='warning')
                     return False, None
             
             with open(latest_file, 'rb') as f:
                 file_hash = hashlib.md5()
                 for chunk in iter(lambda: f.read(4096), b""):
                     file_hash.update(chunk)
                 md5_hash = file_hash.hexdigest()
             
             return True, md5_hash
             
         except Exception as e:
             if self.log_callback:
                 self.log_callback(f"   ⚠️ Validation error: {str(e)[:50]}", level='warning')
             return True, None

    def _calculate_file_md5(self, file_path):
         """Calcula el hash MD5 de un archivo."""
         try:
             hash_md5 = hashlib.md5()
             with open(file_path, 'rb') as f:
                 for chunk in iter(lambda: f.read(4096), b""):
                     hash_md5.update(chunk)
             return hash_md5.hexdigest()
         except Exception:
             return None

    def _download_single_video_transcription(self, url):
        """Descarga transcripción de un video individual."""
        if self.log_callback:
            self.log_callback(f"🎬 Descargando transcripción: {url}")
        
        result = self._download_video_subs(url)
        
        if result == 'downloaded':
            return True, "Transcripción descargada."
        elif result == 'no_subs':
            return True, "Video sin subtítulos disponibles."
        elif result == 'rate_limited':
            return False, "YouTube bloqueó la solicitud (429). Intenta más tarde."
        else:
            return False, "Error descargando transcripción."
