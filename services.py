import os
import re
import shutil
import yt_dlp
from pathlib import Path
import time
import sys
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
    def __init__(self, input_dir, optimize, secure_mode, ffmpeg_location, progress_callback=None, log_callback=None):
        self.input_dir = input_dir
        self.optimize = optimize
        self.secure_mode = secure_mode
        self.ffmpeg_location = ffmpeg_location
        self.progress_callback = progress_callback
        self.log_callback = log_callback

    def _progress_hook(self, d):
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

    def perform_download(self, url):
        """
        Realiza la descarga de una única URL.
        Retorna (bool_success, message).
        """
        max_retries = 3
        try:
            ydl_opts = {
                'skip_download': self.optimize,
                'writeautomaticsub': True,
                'writesub': True,
                'writeinfojson': True,
                'subtitleslangs': ['es', 'en'],
                'outtmpl': f'{self.input_dir}/%(title)s [%(id)s].%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'download_archive': os.path.join(self.input_dir, 'downloaded_history.txt'),
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
            if self.log_callback: self.log_callback(f"Error descargando {url}: {e}", level='error')
            return False, str(e)

class ProcessingService:
    """
    Encapsula la lógica de limpieza y procesamiento de archivos de transcripción.
    """
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

    def process_files(self, input_dir, output_dir, files_to_process, progress_callback=None, log_callback=None):
        """
        Procesa una lista de archivos, los limpia y los guarda en el directorio de salida.
        Retorna el número de archivos procesados exitosamente.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        count = 0
        total = len(files_to_process)
        if log_callback: log_callback("=== Iniciando Procesamiento ===")
        
        for i, fname in enumerate(files_to_process):
            try:
                with open(os.path.join(input_dir, fname), 'r', encoding='utf-8') as f:
                    raw = f.read()
                
                clean = self.clean_content(raw)
                out_name = f"CLEAN_{Path(fname).stem}.txt"
                
                with open(os.path.join(output_dir, out_name), 'w', encoding='utf-8') as f:
                    f.write(clean)
                
                count += 1
                if log_callback: log_callback(f"Procesado: {fname}")
            except Exception as e:
                if log_callback: log_callback(f"Error en {fname}: {e}", level='error')
            
            if progress_callback: progress_callback(((i + 1) / total) * 100)
        
        if log_callback: log_callback(f"=== Finalizado. {count} archivos procesados. ===")
        return count
