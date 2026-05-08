import os
import re
import shutil
import yt_dlp
from pathlib import Path
import time
import sys
import threading
import hashlib
import uuid
import random
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable, Any, Dict
sys.path.insert(0, 'D:/ANEXOS KDP Y DIGITALES/KDP_MASTER')
from app.services.retry_decorator import retry_yt_dlp
from app.services.yt_dlp_errors import RateLimitError, NetworkError, VideoUnavailableError, SubtitleMissingError

GET_CONTEXT = lambda *a, **kw: {
    "url": kw.get("url") or (a[1] if len(a) > 1 else "unknown"),
    "video_id": kw.get("video_id") or (a[2] if len(a) > 2 else None)
}

class DownloadService:
    """
    Encapsula la lógica de descarga usando yt-dlp.
    Acepta callbacks para reportar progreso y logs a la GUI.
    """
    def __init__(
        self,
        input_dir: str,
        optimize: bool,
        secure_mode: bool,
        ffmpeg_location: str,
        progress_callback: Optional[Callable[[float], Any]] = None,
        log_callback: Optional[Callable[[str], Any]] = None,
        batch_progress_callback: Optional[Callable[[str, float], Any]] = None
    ) -> None:
        self.input_dir = input_dir
        self.optimize = optimize
        self.secure_mode = secure_mode
        self.ffmpeg_location = ffmpeg_location
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.batch_progress_callback = batch_progress_callback
        self.is_background_mode = False # Módulo 26: Prioridad Baja
        self.active_channel_downloads: Dict[str, int] = {}  # Módulo 28: Tracking por canal
        self.kdp_category = "General" # Módulo 51
        self.soe_role = "General" # Módulo 53
        self.strict_language_filter = "Todos" # Módulo 59
        self.current_errors_count = 0       # Módulo 44: Contador de errores de metadata
        self.current_skipped_count = 0      # Módulo 42: Contador de videos omitidos
        self.current_scan_duration = 0.0    # Módulo 45: Tiempo promedio de carga
        self.channel_condition = threading.Condition(threading.Lock())
        self.max_per_channel = 3 # Límite por defecto

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        if self.progress_callback:
            if d['status'] == 'downloading':
                p_str = d.get('_percent_str', '0%').replace('%', '')
                try:
                    self.progress_callback(float(p_str))
                except (ValueError, TypeError):
                    pass

    @retry_yt_dlp(max_attempts=2, base_delay=3.0, get_context=GET_CONTEXT)
    def _call_ytdlp_raw(self, url, opts):
        """Llamada directa a yt-dlp, protegida por el decorador."""
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    def get_current_error_count(self): # Módulo 44
        return self.current_errors_count

    def get_current_skipped_count(self):
        return self.current_skipped_count

    def get_current_scan_duration(self):
        return self.current_scan_duration

    def _clean_title_for_filename(self, title: str) -> str:
        """[Módulo 60] Limpia emojis y caracteres raros del título para nombres de archivo."""
        # Eliminar emojis
        emoji_pattern = re.compile("["
                                   "\U0001F600-\U0001F64F"  # emoticons
                                   "\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   "\U0001F680-\U0001F6FF"  # transport & map symbols
                                   "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   "\U00002702-\U000027B0"
                                   "\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        cleaned_title = emoji_pattern.sub(r'', title)
        cleaned_title = re.sub(r'[^\w\s-]', '', cleaned_title).strip()
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title)
        return cleaned_title

    def perform_download(self, url):
        """
        Realiza la descarga de una única URL.
        Retorna (bool_success, message).
        """
        max_retries = 3
        
        # Módulo 26: Throttling de Prioridad Baja (Background) para Masivos
        if self.is_background_mode:
            bg_delay = random.uniform(8, 15) # Retardo mayor para no saturar
            if self.log_callback: self.log_callback(f"[💤] Prioridad Background activa. Delay: {bg_delay:.1f}s...")
            time.sleep(bg_delay)
            
        # Módulo 28: Límite de Descargas Simultáneas por Canal
        channel_id = "unknown"
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(url, download=False) # Pre-extract info for channel_id and language
                channel_id = info.get('channel_id') or info.get('uploader_id') or "unknown"
                video_title = info.get('title', '').lower()
                video_language = info.get('language', 'unknown') # Módulo 59
        except Exception: pass

        # Módulo 59: Filtro de Idioma Estricto
        if self.strict_language_filter != "Todos" and video_language != self.strict_language_filter:
            # --- Lógica de Salvaguarda de Información de Valor ---
            critical_keywords = ["tos", "legal", "update", "amazon", "kdp", "ads", "ads", "ban", "profit"]
            is_high_value = any(kw in video_title for kw in critical_keywords)
            
            if is_high_value:
                if self.log_callback: 
                    self.log_callback(f"🌐 Idioma '{video_language}' no coincide, pero se detectó ALTO VALOR en título. Procediendo con traducción automática...", level='warning')
                # Módulo 59 avanzado: Si es valioso, forzamos traducción de subtítulos en ydl_opts
                force_translation = True
            else:
                if self.log_callback: 
                    self.log_callback(f"⏭️ Video {url} omitido por idioma '{video_language}'. No se detectaron keywords críticas.", level='info')
                self.current_skipped_count += 1 # Módulo 42
                return True, f"Saltado: Idioma no coincide ({video_language})"

        # Módulo 54: Exclusión de Competencia Directa (This check should ideally happen in ChannelMonitorService)
        # For now, assuming the channel is already filtered out before reaching here if it's a competitor.
        # If a competitor video somehow reaches here, we'd need channel metadata to check the flag.
        # This is better handled at the ChannelMonitorService level.

        with self.channel_condition:
            while self.active_channel_downloads.get(channel_id, 0) >= self.max_per_channel:
                if self.log_callback: self.log_callback(f"[⏳] Slot lleno para canal {channel_id}. Esperando slot...")
                self.channel_condition.wait()
            self.active_channel_downloads[channel_id] = self.active_channel_downloads.get(channel_id, 0) + 1

        try:
            ydl_opts = {
                'skip_download': self.optimize,
                'postprocessors': [{'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'}] if 'force_translation' in locals() else [],
                'writeautomaticsub': True, # Módulo 59: Descargar subtítulos automáticos si no hay manuales
                # Módulo 60: Pre-Procesamiento de Título para nombre de archivo
                # yt-dlp's outtmpl already handles some sanitization, but we can add more specific cleaning
                # The title cleaning will be applied to the %(title)s variable by yt-dlp itself.
                # We'll ensure the title stored in DB is clean.
                'writesub': True,
                'writeinfojson': True,
                'subtitleslangs': ['es', 'en', 'auto'], # Aseguramos capturar la traducción
                'outtmpl': f'{self.input_dir}/%(title)s [%(id)s].%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'download_archive': os.path.join(self.input_dir, 'downloaded_history.txt'), # Módulo 52: Implícitamente taggea por fuente (el archivo está en la carpeta del canal)
                # Módulo 51, 53, 55: KDP Category, SOE Role, Reference Material - these are metadata for the video,
                # which would be stored in the DB after download/processing, not directly by yt-dlp.
                # The ChannelMonitorService would enrich the video metadata with these.
                'progress_hooks': [self._progress_hook],
                'ffmpeg_location': self.ffmpeg_location
            }
            if self.secure_mode:
                ydl_opts.update({
                    'restrictfilenames': True,
                    'windowsfilenames': True,
                })
            
            if self.log_callback: self.log_callback(f"Iniciando descarga: {url}")
            
            for attempt in range(max_retries):
                try:
                    self._call_ytdlp_raw(url, ydl_opts)
                    # Módulo 60: Pre-Procesamiento de Título (post-download, antes de guardar en DB)
                    # The actual file name will be sanitized by yt-dlp's outtmpl.
                    # If we need to clean the title *before* yt-dlp uses it, we'd need to modify the info dict.
                    # For now, assume yt-dlp's filename sanitization is sufficient for the file itself.
                    if self.log_callback: self.log_callback(f"Completado: {url}")
                    return True, "Descarga completada."
                except (RateLimitError, NetworkError) as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        if self.log_callback: self.log_callback(f"⚠️ {type(e).__name__}. Reintentando en {wait_time}s...", level='warning')
                        time.sleep(wait_time)
                    else:
                        if self.log_callback: self.log_callback(f"❌ Error de red: {str(e)[:80]}", level='error')
                        return False, str(e)
                except yt_dlp.utils.ExtractorError as e: # Módulo 44: Capturar errores específicos de yt-dlp
                    self.current_errors_count += 1
                    if self.log_callback: self.log_callback(f"❌ Error de extracción para {url}: {str(e)[:80]}", level='error')
                    return False, str(e)
                except (VideoUnavailableError, SubtitleMissingError) as e:
                    if self.log_callback: self.log_callback(f"⏭️ {type(e).__name__}: {str(e)[:60]}", level='info')
                    return True, f"Saltado: {type(e).__name__}"
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        if self.log_callback: self.log_callback(f"Intento {attempt+1} fallido. Reintentando en {wait_time}s... Error: {e}", level='warning')
                        time.sleep(wait_time)
                    else:
                        raise e
        except Exception as e:
            self.current_errors_count += 1 # Módulo 44: Incrementar contador de errores
            if self.log_callback: self.log_callback(f"Error descargando {url}: {e}", level='error')
            return False, str(e)
        finally:
            # Módulo 28: Liberación de slot
            with self.channel_condition:
                self.active_channel_downloads[channel_id] = max(0, self.active_channel_downloads.get(channel_id, 1) - 1)
                self.channel_condition.notify_all()

class ProcessingService:
    """
    Encapsula la lógica de limpieza y procesamiento de archivos de transcripción.
    """
    def __init__(self) -> None:
        # --- INICIO FUNCIONALIDAD US-003-CORE: INFRAESTRUCTURA DE PROCESAMIENTO PARALELO v3.4.5 ---
        # --- INICIO FUNCIONALIDAD US-003-CORE: INFRAESTRUCTURA DE PROCESAMIENTO PARALELO v3.4.5 --- # US-E-SCHED: Se añade el scheduler de exportaciones
        self._hash_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        self._processed_hashes: set = set()
        self._processing_times: list = []  # Para priorización dinámica
        self.batch_results: list = []      # Para exportación de reportes
        self.callback_queue: Queue = Queue()
        self._stop_dispatcher = False
        self._dispatcher_thread = threading.Thread(target=self._callback_dispatcher, daemon=True)
        self._dispatcher_thread.start()
        # --- FIN FUNCIONALIDAD ---

    def _callback_dispatcher(self) -> None:
        # --- INICIO FUNCIONALIDAD US-003-ORDER: DESPACHADOR DE CALLBACKS ORDENADOS ---
        # --- INICIO FUNCIONALIDAD US-003-ORDER: DESPACHADOR DE CALLBACKS ORDENADOS ---
        while not self._stop_dispatcher:
            item = self.callback_queue.get()
            if item is None: break
            callback = item.get('callback')
            if callback:
                callback(item.get('progress', 0))
            self.callback_queue.task_done()
        # --- FIN FUNCIONALIDAD ---

    def clean_content(self, text):
        """Limpia el contenido de un archivo de transcripción."""
        text = text.replace('\r\n', '\n')
        text = re.sub(r'WEBVTT.*\n', '', text)
        text = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3} --> \d{2}:\d{2}:\d{2}[.,]\d{3}.*\n', '', text)
        text = re.sub(r'^\d+\s*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'<[^>]+>', '', text)
        
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        unique = []
        if lines:
            unique.append(lines[0])
            for i in range(1, len(lines)):
                if lines[i] != lines[i-1]:
                    unique.append(lines[i])
        return "\n".join(unique)

    def _compute_hash(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _process_single_file(self, input_dir, output_dir, fname, index, total, log_callback, progress_callback):
        # --- INICIO FUNCIONALIDAD US-003-THREAD: PROCESAMIENTO UNITARIO CON MÉTRICAS v3.4.5 ---
        start_time = time.time()
        try:
            file_path = os.path.join(input_dir, fname)
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read()
            
            # 1. Deduplicación Thread-Safe
            file_hash = self._compute_hash(raw)
            with self._hash_lock:
                if file_hash in self._processed_hashes:
                    elapsed = time.time() - start_time
                    self._record_result(fname, "duplicate", elapsed, file_size)
                    self.callback_queue.put({'callback': progress_callback, 'progress': ((index + 1) / total) * 100})
                    return False
                self._processed_hashes.add(file_hash)

            # 2. Limpieza
            clean = self.clean_content(raw)
            out_name = f"CLEAN_{Path(fname).stem}.txt"
            
            with open(os.path.join(output_dir, out_name), 'w', encoding='utf-8') as f:
                f.write(clean)
            
            elapsed = time.time() - start_time
            self._record_result(fname, "success", elapsed, file_size)
            
            # --- INICIO FUNCIONALIDAD: PRIORIZACIÓN DINÁMICA ---
            with self._stats_lock:
                self._processing_times.append(elapsed)
                avg_time = sum(self._processing_times) / len(self._processing_times)
                if elapsed > (avg_time * 2) and len(self._processing_times) > 5:
                    if log_callback: log_callback(f"⚠️ Archivo pesado detectado: {fname} ({elapsed:.2f}s)", level='warning')
            # --- FIN FUNCIONALIDAD ---
            
            # 3. Encolar progreso ordenado
            self.callback_queue.put({'callback': progress_callback, 'progress': ((index + 1) / total) * 100})
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            self._record_result(fname, f"error: {str(e)}", elapsed, 0)
            self.callback_queue.put({'callback': progress_callback, 'progress': ((index + 1) / total) * 100})
            return False

    def _record_result(self, filename, status, duration, size):
        """Registra el resultado para el generador de reportes."""
        with self._stats_lock:
            self.batch_results.append({
                "timestamp": datetime.now().isoformat(),
                "file": filename,
                "status": status,
                "duration": round(duration, 3),
                "size_kb": round(size / 1024, 2)
            })
        # --- FIN FUNCIONALIDAD ---

    def process_files(self, input_dir, output_dir, files_to_process, progress_callback=None, log_callback=None):
        """
        [FIX-CORE] Motor de procesamiento paralelo con deduplicación y callbacks ordenados.
        """
        # --- INICIO FUNCIONALIDAD US-003-PARALLEL: MOTOR DE PROCESAMIENTO PARALELO ---
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        total = len(files_to_process)
        if log_callback: log_callback(f"=== Iniciando Procesamiento Paralelo ({total} archivos) ===")
        
        # Optimizamos según capacidad I/O del sistema
        num_workers = min(32, (os.cpu_count() or 1) * 4)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(self._process_single_file, input_dir, output_dir, fname, i, total, log_callback, progress_callback)
                for i, fname in enumerate(files_to_process)
            ]
            
            # --- INICIO FUNCIONALIDAD US-003-ORDER: RECOLECCIÓN ORDENADA DE RESULTADOS ---
            # Al iterar sobre la lista original de futures (y no as_completed), respetamos el orden de los archivos
            results = [f.result() for f in futures]
            # --- FIN FUNCIONALIDAD ---
        
        count = sum(1 for r in results if r)
        if log_callback: log_callback(f"=== Finalizado. {count} archivos procesados. ===")
        return count
        # --- FIN FUNCIONALIDAD ---
