"""
Batch Processor con IA
====================
Procesa múltiples URLs con módulos IA en paralelo.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    max_workers: int = 4
    max_parallel_videos: int = 10
    ai_analysis_enabled: bool = True
    pre_analysis: bool = True
    post_analysis: bool = True
    priority_boost_for_urgent: bool = True
    min_density_threshold: float = 5.0
    skip_low_density: bool = False


@dataclass
class BatchItem:
    url: str
    video_id: str
    priority: int = 1
    transcript: str = ""
    pre_analysis: Optional[Dict] = None
    post_analysis: Optional[Dict] = None
    status: str = "pending"
    processing_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class BatchResult:
    total_items: int
    processed: int
    successful: int
    failed: int
    skipped: int
    total_time_ms: float
    avg_time_per_item: float
    results: List[BatchItem]


class BatchProcessor:
    """
    Procesador batch con análisis IA.
    Soporta pre-análisis y post-análisis de contenido.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        self._orchestrator = None
        self._progress_callback = None
        self._stats = {
            'total_batches': 0,
            'total_processed': 0,
            'total_skipped': 0,
            'total_failed': 0
        }

    def set_orchestrator(self, orchestrator):
        """Inyecta orquestador IA."""
        self._orchestrator = orchestrator

    def set_progress_callback(self, callback: Callable):
        """Setea callback de progreso."""
        self._progress_callback = callback

    def process_batch(self, items: List[Dict], progress_callback: Optional[Callable] = None) -> BatchResult:
        """
        Procesa lote de URLs con análisis IA.

        Args:
            items: Lista de dicts {url, video_id, priority, transcript}
            progress_callback: Callback opcional de progreso

        Returns:
            BatchResult con estadísticas
        """
        start_time = time.time()
        batch_items = []

        for item in items:
            bi = BatchItem(
                url=item.get('url', ''),
                video_id=item.get('video_id', ''),
                priority=item.get('priority', 1),
                transcript=item.get('transcript', '')
            )
            batch_items.append(bi)

        batch_items.sort(key=lambda x: x.priority, reverse=True)

        successful = 0
        failed = 0
        skipped = 0

        if self.config.ai_analysis_enabled and self._orchestrator:
            if self.config.max_workers > 1:
                successful, failed, skipped = self._process_parallel(batch_items, progress_callback)
            else:
                successful, failed, skipped = self._process_sequential(batch_items, progress_callback)
        else:
            for bi in batch_items:
                bi.status = "skipped_no_ia"
                skipped += 1

        total_time = (time.time() - start_time) * 1000

        self._stats['total_batches'] += 1
        self._stats['total_processed'] += len(batch_items)
        self._stats['total_skipped'] += skipped
        self._stats['total_failed'] += failed

        return BatchResult(
            total_items=len(batch_items),
            processed=len(batch_items) - skipped,
            successful=successful,
            failed=failed,
            skipped=skipped,
            total_time_ms=total_time,
            avg_time_per_item=total_time / max(len(batch_items), 1),
            results=batch_items
        )

    def _process_sequential(self, items: List[BatchItem], callback: Optional[Callable]) -> tuple:
        """Procesa secuencialmente."""
        successful = 0
        failed = 0
        skipped = 0

        for i, bi in enumerate(items):
            try:
                if self._should_process(bi):
                    result = self._orchestrator.analyze_video(
                        bi.video_id, bi.url, bi.transcript
                    )
                    bi.pre_analysis = {'density': result.density_score}

                    if self.config.skip_low_density and result.density_score < self.config.min_density_threshold:
                        bi.status = "skipped_low_density"
                        skipped += 1
                    else:
                        bi.status = "completed"
                        successful += 1

                    bi.processing_time_ms = result.processing_time_ms
                else:
                    bi.status = "skipped"
                    skipped += 1

                if callback:
                    callback(i + 1, len(items), bi.status)

            except Exception as e:
                logger.error(f"Error procesando {bi.video_id}: {e}")
                bi.status = "failed"
                bi.error = str(e)
                failed += 1

        return successful, failed, skipped

    def _process_parallel(self, items: List[BatchItem], callback: Optional[Callable]) -> tuple:
        """Procesa en paralelo."""
        successful = 0
        failed = 0
        skipped = 0
        processed_count = 0

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {}

            for bi in items:
                if self._should_process(bi):
                    future = executor.submit(self._orchestrator.analyze_video, bi.video_id, bi.url, bi.transcript)
                    futures[future] = bi
                else:
                    bi.status = "skipped"
                    skipped += 1
                    processed_count += 1
                    if callback:
                        callback(processed_count, len(items), bi.status)

            for future in as_completed(futures):
                bi = futures[future]
                processed_count += 1

                try:
                    result = future.result()
                    bi.pre_analysis = {'density': result.density_score}

                    if self.config.skip_low_density and result.density_score < self.config.min_density_threshold:
                        bi.status = "skipped_low_density"
                        skipped += 1
                    else:
                        bi.status = "completed"
                        successful += 1

                    bi.processing_time_ms = result.processing_time_ms

                except Exception as e:
                    logger.error(f"Error en paralelo {bi.video_id}: {e}")
                    bi.status = "failed"
                    bi.error = str(e)
                    failed += 1

                if callback:
                    callback(processed_count, len(items), bi.status)

        return successful, failed, skipped

    def _should_process(self, item: BatchItem) -> bool:
        """Determina si debe procesar el item."""
        if not self.config.ai_analysis_enabled:
            return False

        if not item.transcript:
            return False

        if self.config.pre_analysis and item.priority < 1:
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas."""
        return self._stats.copy()


def create_batch_processor(config: Optional[BatchConfig] = None) -> BatchProcessor:
    """Factory function."""
    return BatchProcessor(config)