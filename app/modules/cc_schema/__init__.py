"""
CC Schema Monitor - Paquete de Extracción de Subtítulos/CC
=========================================================
Conjunto de módulos para validación, fetcheo paralelo y auto-adaptación
de parsers de subtítulos de YouTube.

Módulos FASE 1 (Completados):
- cc_availability_validator: Validador de disponibilidad de CC
- parallel_subtitle_fetcher: Fetcher paralelo de múltiples formatos
- space_validator: Pre-verificador de espacio en disco
- content_deduplicator: Deduplicador por hash SHA-256

Módulos FASE 2 (Completados):
- quality_filter: Filtro de calidad de subtítulos (<80% auto-captions)
- integrity_validator: Validador de integridad post-extracción
- audit_ledger: Registro de auditoría inmutable
- rate_limiter: Limiter de requests con backoff exponencial
- (Módulo 7 integrado en DownloadService: Rotador User-Agent)

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

from .quality_filter import (
    SubtitleQualityFilter,
    QualityLevel,
    QualityMetrics,
    QualityFilterResult,
    create_filter,
    quick_quality_check
)

from .integrity_validator import (
    PostExtractionValidator,
    IntegrityStatus,
    IntegrityIssue,
    IntegrityValidationResult,
    create_validator as create_integrity_validator,
    quick_integrity_check
)

from .audit_ledger import (
    ImmutableAuditLedger,
    ExtractionAuditEntry,
    create_ledger,
    quick_log
)

from .rate_limiter import (
    DomainRateLimiter,
    AdaptiveRateLimiter,
    DomainStats,
    RateLimitResult,
    create_limiter,
    quick_throttle
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
    'compute_content_hash',
    'SubtitleQualityFilter',
    'QualityLevel',
    'QualityMetrics',
    'QualityFilterResult',
    'create_filter',
    'quick_quality_check',
    'PostExtractionValidator',
    'IntegrityStatus',
    'IntegrityIssue',
    'IntegrityValidationResult',
    'create_integrity_validator',
    'quick_integrity_check',
    'ImmutableAuditLedger',
    'ExtractionAuditEntry',
    'create_ledger',
    'quick_log',
    'DomainRateLimiter',
    'AdaptiveRateLimiter',
    'DomainStats',
    'RateLimitResult',
    'create_limiter',
    'quick_throttle'
]

__version__ = '2.0.0'
__all_modules__ = [
    'cc_availability_validator',
    'parallel_subtitle_fetcher',
    'space_validator',
    'content_deduplicator',
    'quality_filter',
    'integrity_validator',
    'audit_ledger',
    'rate_limiter'
]