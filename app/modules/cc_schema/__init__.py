"""
CC Schema Monitor - Paquete de Extracción de Subtítulos/CC
=========================================================
Conjunto de módulos para validación, fetcheo paralelo y auto-adaptación
de parsers de subtítulos de YouTube.

Módulos FASE 1 (Completados 1-5):
- cc_availability_validator: Validador de disponibilidad de CC
- parallel_subtitle_fetcher: Fetcher paralelo de múltiples formatos
- space_validator: Pre-verificador de espacio en disco
- content_deduplicator: Deduplicador por hash SHA-256

Módulos FASE 2 (Completados 6-10):
- quality_filter: Filtro de calidad de subtítulos
- integrity_validator: Validador de integridad post-extracción
- audit_ledger: Registro de auditoría inmutable
- rate_limiter: Limiter de requests con backoff exponencial

Módulos FASE 3 (Completados 11-15):
- cc_metadata_cache: Cache de metadatos CC (24h TTL)
- ocr_fallback: Fallback OCR de miniaturas
- log_compressor: Compresor LZ4 para logs
- structure_validator: Validador de estructura de párrafos
- language_detector: Detector de idioma automático

Módulos FASE 4 (Completados 16-20):
- noise_cleaner: Protocolo de limpieza de ruido
- retry_handler: Sistema de reintentos con backoff
- fts5_validator: Validador de compatibilidad FTS5
- manifest_generator: Generador de manifest de extracción
- atomic_persistence: Persistencia atómica de transcripción

Módulos FASE HARDENING (Completados 41-44):
- rate_limit_enforcer: Limitador de rate entre módulos
- circuit_breaker: Previene cascadas de errores
- health_checker: Monitor de salud de módulos
- config_validator: Validador de configs antes de ejecutar

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

from .cc_availability_validator import (
    CCAvailabilityValidator,
    CCCheckResult,
    CCFormat,
)

from .parallel_subtitle_fetcher import (
    ParallelSubtitleFetcher,
    SubtitleFormat,
    SubtitleDownloadResult,
    ParallelFetchConfig,
)

from .space_validator import (
    SpaceValidator,
    SpaceCheckResult,
)

from .content_deduplicator import (
    ContentDeduplicator,
    ContentHasher,
    DeduplicationResult,
)

from .quality_filter import (
    SubtitleQualityFilter,
    QualityLevel,
    QualityMetrics,
    QualityFilterResult,
)

from .integrity_validator import (
    PostExtractionValidator,
    IntegrityStatus,
    IntegrityIssue,
    IntegrityValidationResult,
)

from .audit_ledger import (
    ImmutableAuditLedger,
    ExtractionAuditEntry,
)

from .rate_limiter import (
    DomainRateLimiter,
    AdaptiveRateLimiter,
    DomainStats,
    RateLimitResult,
)

from .cc_metadata_cache import (
    CCMetadataCacheManager,
    CCMetadataCache,
)

from .ocr_fallback import (
    ThumbnailOCRExtractor,
    LightweightOCRExtractor,
    OCRFrameResult,
    OCRExtractionResult,
)

from .log_compressor import (
    LogCompressor,
    CompressionResult,
    LogFileInfo,
)

from .structure_validator import (
    ParagraphStructureValidator,
    ParagraphInfo,
    StructureValidationResult,
)

from .language_detector import (
    LanguageDetector,
    LanguageInfo,
    DetectionResult,
    MultiLanguageSegmenter,
)

from .noise_cleaner import (
    NoiseCleaner,
    NoiseType,
    CleaningResult,
)

from .retry_handler import (
    RetryHandler,
    RetryConfig,
    RetryResult,
    RetryStrategy,
)

from .fts5_validator import (
    FTS5Validator,
    FTS5ValidationResult,
)

from .manifest_generator import (
    ManifestGenerator,
    ExtractionMetadata,
)

from .atomic_persistence import (
    AtomicPersistenceManager,
    PersistedTranscription,
    TransactionState,
)

from .rate_limit_enforcer import (
    RateLimitEnforcer,
    RateLimitConfig,
    RateLimitMetrics,
    RateLimitRegistry,
    create_rate_limiter,
)

from .circuit_breaker import (
    CircuitBreaker,
    CircuitConfig,
    CircuitMetrics,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerRegistry,
    create_circuit_breaker,
)

from .health_checker import (
    HealthChecker,
    HealthCheck,
    HealthStatus,
    SystemHealth,
    create_health_checker,
)

from .config_validator import (
    ConfigValidator,
    ValidationLevel,
    ValidationResult,
    create_config_validator,
)


def create_validator():
    return CCAvailabilityValidator()

def create_fetcher(config=None):
    return ParallelSubtitleFetcher(config=config)

def create_space_validator():
    return SpaceValidator()

def create_deduplicator(db_path=None):
    return ContentDeduplicator(db_path=db_path)

def create_filter(strict=False):
    return SubtitleQualityFilter(strict_mode=strict)

def create_integrity_validator(strict=False):
    return PostExtractionValidator(strict_mode=strict)

def create_ledger(db_path=None):
    return ImmutableAuditLedger(db_path=db_path)

def create_limiter(adaptive=False):
    if adaptive:
        return AdaptiveRateLimiter()
    return DomainRateLimiter()

def create_cache_manager(db_path=None, ttl=86400):
    return CCMetadataCacheManager(db_path=db_path, ttl_seconds=ttl)

def create_ocr_extractor(min_confidence=0.70):
    return ThumbnailOCRExtractor(min_confidence=min_confidence)

def create_compressor(compression_level=3):
    return LogCompressor(compression_level=compression_level)

def create_structure_validator(strict=False):
    return ParagraphStructureValidator(strict_mode=strict)

def create_detector():
    return LanguageDetector()

def create_cleaner(aggressive=False):
    return NoiseCleaner(aggressive=aggressive)

def create_retry_handler(config=None):
    return RetryHandler(config=config)

def create_fts5_validator():
    return FTS5Validator()

def create_manifest_generator(output_dir=None):
    return ManifestGenerator(output_dir=output_dir)

def create_persistence_manager(db_path=None):
    return AtomicPersistenceManager(db_path=db_path)


__all__ = [
    'CCAvailabilityValidator',
    'CCCheckResult',
    'CCFormat',
    'ParallelSubtitleFetcher',
    'SubtitleFormat',
    'SubtitleDownloadResult',
    'ParallelFetchConfig',
    'SpaceValidator',
    'SpaceCheckResult',
    'ContentDeduplicator',
    'ContentHasher',
    'DeduplicationResult',
    'SubtitleQualityFilter',
    'QualityLevel',
    'QualityMetrics',
    'QualityFilterResult',
    'PostExtractionValidator',
    'IntegrityStatus',
    'IntegrityIssue',
    'IntegrityValidationResult',
    'ImmutableAuditLedger',
    'ExtractionAuditEntry',
    'DomainRateLimiter',
    'AdaptiveRateLimiter',
    'DomainStats',
    'RateLimitResult',
    'CCMetadataCacheManager',
    'CCMetadataCache',
    'ThumbnailOCRExtractor',
    'LightweightOCRExtractor',
    'OCRFrameResult',
    'OCRExtractionResult',
    'LogCompressor',
    'CompressionResult',
    'LogFileInfo',
    'ParagraphStructureValidator',
    'ParagraphInfo',
    'StructureValidationResult',
    'LanguageDetector',
    'LanguageInfo',
    'DetectionResult',
    'MultiLanguageSegmenter',
    'NoiseCleaner',
    'NoiseType',
    'CleaningResult',
    'RetryHandler',
    'RetryConfig',
    'RetryResult',
    'RetryStrategy',
    'FTS5Validator',
    'FTS5ValidationResult',
    'ManifestGenerator',
    'ExtractionMetadata',
    'AtomicPersistenceManager',
    'PersistedTranscription',
    'TransactionState',
    'create_validator',
    'create_fetcher',
    'create_space_validator',
    'create_deduplicator',
    'create_filter',
    'create_integrity_validator',
    'create_ledger',
    'create_limiter',
    'create_cache_manager',
    'create_ocr_extractor',
    'create_compressor',
    'create_structure_validator',
    'create_detector',
    'create_cleaner',
    'create_retry_handler',
    'create_fts5_validator',
    'create_manifest_generator',
    'create_persistence_manager',
    'create_rate_limiter',
    'create_circuit_breaker',
    'create_health_checker',
    'create_config_validator',
]

__version__ = '4.4.0'
__all_modules__ = [
    'cc_availability_validator',
    'parallel_subtitle_fetcher',
    'space_validator',
    'content_deduplicator',
    'quality_filter',
    'integrity_validator',
    'audit_ledger',
    'rate_limiter',
    'cc_metadata_cache',
    'ocr_fallback',
    'log_compressor',
    'structure_validator',
    'language_detector',
    'noise_cleaner',
    'retry_handler',
    'fts5_validator',
    'manifest_generator',
    'atomic_persistence',
    'rate_limit_enforcer',
    'circuit_breaker',
    'health_checker',
    'config_validator'
]