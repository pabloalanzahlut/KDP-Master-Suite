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
    def __init__(self, input_dir, optimize, secure_mode, ffmpeg_location, progress_callback=None, log_callback=None, batch_progress_callback=None):
        self.input_dir = input_dir
        self.optimize = optimize
        self.secure_mode = secure_mode
        self.ffmpeg_location = ffmpeg_location
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.batch_progress_callback = batch_progress_callback
        self._downloaded_count = 0
        self._consecutive_errors = 0
        self._last_request_time = 0
        self._batch_stats = {"new": 0, "existing": 0, "no_subs": 0, "errors": 0}

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
        Con protecciones anti-rate-limiting
        """
        url = self._normalize_channel_url(url)
        
        if self.log_callback:
            self.log_callback(f"📺 Canal: obteniendo lista de videos...")
            self.log_callback(f"   URL: {url}")
        
        # PASO 1: Obtener lista de videos
        video_ids = []
        try:
            list_opts = {
                'skip_download': True,
                'writeautomaticsub': False,
                'writesubtitles': False,
                'writeinfojson': False,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': 50,
            }
            
            with yt_dlp.YoutubeDL(list_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if self.log_callback:
                    self.log_callback(f"   📋 Info obtenida: {type(info)}")
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('id'):
                            video_ids.append(entry['id'])
                elif info and info.get('id'):
                    video_ids.append(info['id'])
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"   ⚠️ Error obteniendo lista de videos: {e}", level='warning')
                import traceback
                self.log_callback(f"   📜 Trace: {traceback.format_exc()[:200]}", level='warning')
            return False, f"Error obteniendo lista de videos: {e}"
        
        if not video_ids:
            if self.log_callback:
                self.log_callback(f"   ⚠️ No se encontraron videos en el canal")
            return False, "No se encontraron videos en el canal"
        
        total = len(video_ids)
        if self.log_callback:
            self.log_callback(f"   📊 {total} videos encontrados. Descargando transcripciones...")
            self.log_callback(f"   ⏱️ Pausas anti-bloqueo: {Config.YT_SLEEP_REQUESTS}s + jitter")
        
        self._reset_batch_stats()
        self._report_batch_progress(0, total, "discovering", f"{total} videos en canal")
        
        # === MODULO: PROGRESO_LOTES (INICIO) - LOOP DE DESCARGA ===
        # PASO 2: Descargar subtítulos de cada video
        success_count = 0
        no_subs_count = 0
        skipped_count = 0
        error_count = 0
        rate_limited_count = 0
        
        for idx, vid in enumerate(video_ids):
            video_url = f"https://www.youtube.com/watch?v={vid}"
            
            try:
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
                    # Pausa larga por rate limit
                    self._consecutive_errors += 1
                    wait = self._rate_limit_wait(base_delay=10)
                    if self.log_callback:
                        self.log_callback(f"   ⏳ Rate limit detectado, esperando {wait:.1f}s...")
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
                    self.log_callback(f"   ❌ Error video {idx+1}/{total}: {e}", level='warning')
            
            self._report_batch_progress(idx + 1, total, "downloading", f"video {idx + 1}")
            
            # Pausa anti-rate-limiting entre videos
            if idx < total - 1:
                delay = self._rate_limit_wait()
                if self.log_callback and idx % 5 == 0:
                    self.log_callback(f"   ⏱️ Pausa: {delay:.1f}s ({idx+1}/{total} procesados, {success_count} exitosos)")
        
        self._downloaded_count = success_count
        self._report_batch_progress(total, total, "completed", f"{success_count} nuevos, {skipped_count} existentes")
        # === MODULO: PROGRESO_LOTES (FIN) - LOOP DE DESCARGA ===
        
        msg = f"Canal: {success_count} subs, {no_subs_count} sin subs, {skipped_count} omitidos, {rate_limited_count} rate-limited, {error_count} errores de {total} videos"
        if self.log_callback:
            self.log_callback(f"✅ {msg}")
        
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
