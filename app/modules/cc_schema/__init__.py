"""
CC Schema Monitor - Paquete de Extracción de Subtítulos/CC
=========================================================
Conjunto de módulos para validación, fetcheo paralelo y auto-adaptación
de parsers de subtítulos de YouTube.

Módulos:
- cc_availability_validator: Validador de disponibilidad de CC
- parallel_subtitle_fetcher: Fetcher paralelo de múltiples formatos
- space_validator: Pre-verificador de espacio en disco
- content_deduplicator: Deduplicador por hash SHA-256
- cc_schema_monitor: Monitor de cambios en estructura de subtítulos

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

from .cc_availability_validator import (
    CCAvailabilityValidator,
    CCCheckResult,
    CCFormat,
    create_validator
)

from .parallel_subtitle_fetcher import (
    ParallelSubtitleFetcher,
    SubtitleFormat,
    SubtitleDownloadResult,
    ParallelFetchConfig,
    create_fetcher
)

from .space_validator import (
    SpaceValidator,
    SpaceCheckResult,
    create_validator as create_space_validator
)

from .content_deduplicator import (
    ContentDeduplicator,
    ContentHasher,
    DeduplicationResult,
    create_deduplicator,
    compute_content_hash
)

__all__ = [
    'CCAvailabilityValidator',
    'CCCheckResult',
    'CCFormat',
    'create_validator',
    'ParallelSubtitleFetcher',
    'SubtitleFormat',
    'SubtitleDownloadResult',
    'ParallelFetchConfig',
    'create_fetcher',
    'SpaceValidator',
    'SpaceCheckResult',
    'create_space_validator',
    'ContentDeduplicator',
    'ContentHasher',
    'DeduplicationResult',
    'create_deduplicator',
    'compute_content_hash'
]

__version__ = '1.0.0'