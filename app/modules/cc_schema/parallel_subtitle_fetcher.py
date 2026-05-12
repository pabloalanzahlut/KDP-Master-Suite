"""
CC Schema Monitor con Auto-Adaptación de Parser
================================================
Módulo 2: Fetcher Paralelo de Subtítulos
Descarga múltiples formatos de subtítulos simultáneamente para fallback automático.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import re
import time
import asyncio
import logging
from typing import Optional, Dict, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue

logger = logging.getLogger(__name__)


class SubtitleFormat(Enum):
    VTT = "vtt"
    SRT = "srt"
    JSON = "json"
    TXT = "txt"
    BEST = "best"


@dataclass
class SubtitleDownloadResult:
    format: SubtitleFormat
    success: bool
    file_path: Optional[str]
    content: Optional[str]
    error: Optional[str]
    download_time: float
    file_size: int


@dataclass
class ParallelFetchConfig:
    max_workers: int = 3
    timeout_seconds: float = 30.0
    retry_count: int = 2
    retry_delay: float = 1.0
    preferred_formats: List[SubtitleFormat] = None

    def __post_init__(self):
        if self.preferred_formats is None:
            self.preferred_formats = [SubtitleFormat.VTT, SubtitleFormat.SRT, SubtitleFormat.JSON]


class ParallelSubtitleFetcher:
    """
    Fetcher Paralelo de Subtítulos/CC
    Descarga múltiples formatos simultáneamente con fallback automático.
    """

    DEFAULT_FORMATS = [
        SubtitleFormat.VTT,
        SubtitleFormat.SRT,
        SubtitleFormat.TXT
    ]

    def __init__(self, config: Optional[ParallelFetchConfig] = None):
        self.config = config or ParallelFetchConfig()
        self._executor = None
        self._active_requests = 0
        self._lock = threading.Lock()

    def fetch_all_formats(
        self,
        url: str,
        video_id: str,
        output_dir: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[SubtitleFormat, SubtitleDownloadResult]:
        """
        Descarga todos los formatos en paralelo.

        Args:
            url: URL del video
            video_id: ID del video
            output_dir: Directorio de salida
            progress_callback: Callback para reportar progreso

        Returns:
            Dict con resultados por formato
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

        results = {}
        futures = {}

        for fmt in self.config.preferred_formats:
            future = self._executor.submit(
                self._fetch_single_format,
                url, video_id, output_dir, fmt
            )
            futures[future] = fmt

        completed_count = 0
        total_formats = len(futures)

        for future in as_completed(futures):
            fmt = futures[future]
            try:
                result = future.result(timeout=self.config.timeout_seconds)
                results[fmt] = result

                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total_formats, fmt.value)

            except Exception as e:
                logger.error(f"Format {fmt.value} fetch failed: {e}")
                results[fmt] = SubtitleDownloadResult(
                    format=fmt,
                    success=False,
                    file_path=None,
                    content=None,
                    error=str(e),
                    download_time=0.0,
                    file_size=0
                )

        return results

    def _fetch_single_format(
        self,
        url: str,
        video_id: str,
        output_dir: str,
        target_format: SubtitleFormat
    ) -> SubtitleDownloadResult:
        """
        Descarga un único formato de subtítulo.
        """
        import yt_dlp

        start_time = time.time()
        output_template = os.path.join(output_dir, f"{video_id}.%(format)s")

        format_map = {
            SubtitleFormat.VTT: "vtt",
            SubtitleFormat.SRT: "srv1",
            SubtitleFormat.JSON: "json3",
            SubtitleFormat.TXT: "lrc",
        }

        ext = format_map.get(target_format, "vtt")

        ydl_opts = {
            'skip_download': True,
            'writeautomaticsub': False,
            'writesubtitles': True,
            'subtitlesformat': ext,
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)

            file_path = output_template.replace('%(format)s', ext)
            file_path = file_path.replace('.vtt.vtt', '.vtt')

            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                download_time = time.time() - start_time

                return SubtitleDownloadResult(
                    format=target_format,
                    success=True,
                    file_path=file_path,
                    content=content,
                    error=None,
                    download_time=download_time,
                    file_size=file_size
                )
            else:
                for guess in [f"{video_id}.vtt", f"{video_id}.srt", f"{video_id}.json"]:
                    guessed = os.path.join(output_dir, guess)
                    if os.path.exists(guessed):
                        file_size = os.path.getsize(guessed)
                        with open(guessed, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        return SubtitleDownloadResult(
                            format=target_format,
                            success=True,
                            file_path=guessed,
                            content=content,
                            error=None,
                            download_time=time.time() - start_time,
                            file_size=file_size
                        )

                return SubtitleDownloadResult(
                    format=target_format,
                    success=False,
                    file_path=None,
                    content=None,
                    error="File not created",
                    download_time=time.time() - start_time,
                    file_size=0
                )

        except Exception as e:
            logger.error(f"Fetch failed for {target_format.value}: {e}")
            return SubtitleDownloadResult(
                format=target_format,
                success=False,
                file_path=None,
                content=None,
                error=str(e),
                download_time=time.time() - start_time,
                file_size=0
            )

    def fetch_with_fallback(
        self,
        url: str,
        video_id: str,
        output_dir: str,
        quality_threshold: float = 0.6,
        progress_callback: Optional[Callable] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[SubtitleFormat]]:
        """
        Descarga con fallback: intenta formatos en orden de prioridad.

        Returns:
            (file_path, content, format_used)
        """
        all_results = self.fetch_all_formats(url, video_id, output_dir, progress_callback)

        priority_order = [
            SubtitleFormat.VTT,
            SubtitleFormat.SRT,
            SubtitleFormat.JSON,
            SubtitleFormat.TXT
        ]

        for fmt in priority_order:
            if fmt in all_results:
                result = all_results[fmt]
                if result.success and result.file_size > 100:
                    return result.file_path, result.content, fmt

        for fmt, result in all_results.items():
            if result.success:
                return result.file_path, result.content, fmt

        return None, None, None

    def prefetch_formats(
        self,
        urls: List[str],
        video_ids: List[str],
        output_dir: str
    ) -> List[Dict[SubtitleFormat, SubtitleDownloadResult]]:
        """
        Precarga múltiples videos en paralelo.
        Útil para batch processing.
        """
        if len(urls) != len(video_ids):
            raise ValueError("URLs and video_ids must have same length")

        results = []
        for url, vid_id in zip(urls, video_ids):
            result = self.fetch_all_formats(url, vid_id, output_dir)
            results.append(result)

        return results

    def cleanup_temp_files(self, output_dir: str, video_id: str):
        """
        Limpia archivos temporales de un video específico.
        """
        extensions = ['.vtt', '.srt', '.json', '.txt', '.lrc']
        for ext in extensions:
            file_path = os.path.join(output_dir, f"{video_id}{ext}")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Cleaned: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")

    def get_active_count(self) -> int:
        """Retorna el número de requests activos."""
        with self._lock:
            return self._active_requests

    def shutdown(self):
        """Libera recursos."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None


def create_fetcher(config: Optional[ParallelFetchConfig] = None) -> ParallelSubtitleFetcher:
    """
    Factory function para crear el fetcher paralelo.
    """
    return ParallelSubtitleFetcher(config=config)