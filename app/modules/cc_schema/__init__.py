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

Módulos FASE URL INTELLIGENCE - Lista 1 (Completados 1-10):
- syntax_validator: Validador de sintaxis RFC 3986
- video_id_extractor: Extrae IDs de video de diferentes formatos
- domain_whitelist: Valida dominios permitidos
- dns_resolver: Resuelve DNS con timeout configurable
- http_head_validator: HEAD request para verificar disponibilidad
- ssl_validator: Valida certificados SSL
- http_status_interpreter: Interpreta códigos HTTP
- redirect_chain: Sigue redirecciones hasta URL final
- user_agent_rotator: Rota User-Agents para evitar detección de bot
- connection_pool: Pool de conexiones HTTP reutilizables

Módulos FASE URL INTELLIGENCE - Lista 1 (Completados 11-20):
- rate_limit_detector: Detecta rate limiting 429
- proxy_config: Valida configuración de proxy
- response_time: Mide latencia de respuesta HTTP
- content_type_validator: Valida Content-Type de respuesta
- captcha_detector: Detecta CAPTCHA en páginas
- login_requirement: Detecta requisitos de autenticación
- age_restriction: Verifica restricción de edad
- region_restriction: Detecta bloqueos geográficos
- privacy_status: Verifica privacidad (público/privado)
- embed_restriction: Detecta restricciones de embed

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
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

from .syntax_validator import (
    URLSyntaxValidator,
    URLSyntaxStatus,
    SyntaxValidationResult,
    create_syntax_validator,
)

from .video_id_extractor import (
    VideoIDExtractor,
    Platform,
    VideoIDResult,
    create_video_id_extractor,
)

from .domain_whitelist import (
    DomainWhitelist,
    DomainStatus,
    DomainValidationResult,
    create_domain_whitelist,
)

from .dns_resolver import (
    DNSResolver,
    DNSStatus,
    DNSResult,
    create_dns_resolver,
)

from .http_head_validator import (
    HTTPHeadValidator,
    HTTPValidationStatus,
    HTTPHeadResult,
    create_http_head_validator,
)

from .ssl_validator import (
    SSLValidator,
    SSLStatus,
    SSLValidationResult,
    create_ssl_validator,
)

from .http_status_interpreter import (
    HTTPStatusInterpreter,
    HTTPStatusCategory,
    RecommendedAction,
    HTTPStatusInterpretation,
    create_http_status_interpreter,
)

from .redirect_chain import (
    RedirectChain,
    RedirectType,
    RedirectHop,
    RedirectChainResult,
    create_redirect_chain,
)

from .user_agent_rotator import (
    UserAgentRotator,
    UserAgentInfo,
    create_user_agent_rotator,
)

from .connection_pool import (
    ConnectionPool,
    PoolStats,
    ConnectionPoolRegistry,
    create_connection_pool,
)

from .rate_limit_detector import (
    RateLimitDetector,
    RateLimitInfo,
    create_rate_limit_detector,
)

from .proxy_config import (
    ProxyConfigValidator,
    ProxyConfig,
    ProxyStatus,
    ProxyValidationResult,
    create_proxy_config_validator,
)

from .response_time import (
    ResponseTimeMeasurer,
    ResponseSpeed,
    ResponseTimeResult,
    create_response_time_measurer,
)

from .content_type_validator import (
    ContentTypeValidator,
    ContentTypeStatus,
    ContentTypeResult,
    create_content_type_validator,
)

from .captcha_detector import (
    CaptchaDetector,
    CaptchaStatus,
    CaptchaResult,
    create_captcha_detector,
)

from .login_requirement import (
    LoginRequirementDetector,
    LoginStatus,
    LoginResult,
    create_login_requirement_detector,
)

from .age_restriction import (
    AgeRestrictionChecker,
    AgeRestrictionStatus,
    AgeRestrictionResult,
    create_age_restriction_checker,
)

from .region_restriction import (
    RegionRestrictionValidator,
    RegionRestrictionStatus,
    RegionRestrictionResult,
    create_region_restriction_validator,
)

from .privacy_status import (
    PrivacyStatusChecker,
    PrivacyStatus,
    PrivacyResult,
    create_privacy_status_checker,
)

from .embed_restriction import (
    EmbedRestrictionDetector,
    EmbedStatus,
    EmbedRestrictionResult,
    create_embed_restriction_detector,
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

def create_syntax_validator(strict: bool = False):
    return URLSyntaxValidator(strict_mode=strict)

def create_video_id_extractor():
    return VideoIDExtractor()

def create_domain_whitelist(whitelist=None, allow_subdomains=True):
    return DomainWhitelist(whitelist=whitelist, allow_subdomains=allow_subdomains)

def create_dns_resolver(timeout: float = 3.0, cache_ttl: int = 300):
    return DNSResolver(timeout=timeout, cache_ttl=cache_ttl)

def create_http_head_validator(timeout: float = 10.0, follow_redirects: bool = True):
    return HTTPHeadValidator(timeout=timeout, follow_redirects=follow_redirects)

def create_ssl_validator(timeout: float = 5.0, warning_days: int = 30):
    return SSLValidator(timeout=timeout, warning_days=warning_days)

def create_http_status_interpreter():
    return HTTPStatusInterpreter()

def create_redirect_chain(max_hops: int = 10, timeout: float = 10.0):
    return RedirectChain(max_hops=max_hops, timeout=timeout)

def create_user_agent_rotator(mobile_weight: float = 0.1, rotation_strategy: str = "round_robin"):
    return UserAgentRotator(mobile_weight=mobile_weight, rotation_strategy=rotation_strategy)

def create_connection_pool(pool_size: int = 10, max_retries: int = 3):
    return ConnectionPool(pool_size=pool_size, max_retries=max_retries)

def create_rate_limit_detector(requests_limit: int = 100, time_window: int = 60):
    return RateLimitDetector(requests_limit=requests_limit, time_window=time_window)

def create_proxy_config_validator():
    return ProxyConfigValidator()

def create_response_time_measurer(timeout: float = 10.0, slow_threshold_ms: int = 3000):
    return ResponseTimeMeasurer(timeout=timeout, slow_threshold_ms=slow_threshold_ms)

def create_content_type_validator():
    return ContentTypeValidator()

def create_captcha_detector():
    return CaptchaDetector()

def create_login_requirement_detector():
    return LoginRequirementDetector()

def create_age_restriction_checker():
    return AgeRestrictionChecker()

def create_region_restriction_validator():
    return RegionRestrictionValidator()

def create_privacy_status_checker():
    return PrivacyStatusChecker()

def create_embed_restriction_detector():
    return EmbedRestrictionDetector()


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
    'URLSyntaxValidator',
    'URLSyntaxStatus',
    'SyntaxValidationResult',
    'VideoIDExtractor',
    'Platform',
    'VideoIDResult',
    'DomainWhitelist',
    'DomainStatus',
    'DomainValidationResult',
    'DNSResolver',
    'DNSStatus',
    'DNSResult',
    'HTTPHeadValidator',
    'HTTPValidationStatus',
    'HTTPHeadResult',
    'SSLValidator',
    'SSLStatus',
    'SSLValidationResult',
    'HTTPStatusInterpreter',
    'HTTPStatusCategory',
    'RecommendedAction',
    'HTTPStatusInterpretation',
    'RedirectChain',
    'RedirectType',
    'RedirectHop',
    'RedirectChainResult',
    'UserAgentRotator',
    'UserAgentInfo',
    'ConnectionPool',
    'PoolStats',
    'ConnectionPoolRegistry',
    'RateLimitDetector',
    'RateLimitInfo',
    'ProxyConfigValidator',
    'ProxyConfig',
    'ProxyStatus',
    'ProxyValidationResult',
    'ResponseTimeMeasurer',
    'ResponseSpeed',
    'ResponseTimeResult',
    'ContentTypeValidator',
    'ContentTypeStatus',
    'ContentTypeResult',
    'CaptchaDetector',
    'CaptchaStatus',
    'CaptchaResult',
    'LoginRequirementDetector',
    'LoginStatus',
    'LoginResult',
    'AgeRestrictionChecker',
    'AgeRestrictionStatus',
    'AgeRestrictionResult',
    'RegionRestrictionValidator',
    'RegionRestrictionStatus',
    'RegionRestrictionResult',
    'PrivacyStatusChecker',
    'PrivacyStatus',
    'PrivacyResult',
    'EmbedRestrictionDetector',
    'EmbedStatus',
    'EmbedRestrictionResult',
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
    'create_syntax_validator',
    'create_video_id_extractor',
    'create_domain_whitelist',
    'create_dns_resolver',
    'create_http_head_validator',
    'create_ssl_validator',
    'create_http_status_interpreter',
    'create_redirect_chain',
    'create_user_agent_rotator',
    'create_connection_pool',
    'create_rate_limit_detector',
    'create_proxy_config_validator',
    'create_response_time_measurer',
    'create_content_type_validator',
    'create_captcha_detector',
    'create_login_requirement_detector',
    'create_age_restriction_checker',
    'create_region_restriction_validator',
    'create_privacy_status_checker',
    'create_embed_restriction_detector',
]

__version__ = '4.5.0'
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
    'config_validator',
    'syntax_validator',
    'video_id_extractor',
    'domain_whitelist',
    'dns_resolver',
    'http_head_validator',
    'ssl_validator',
    'http_status_interpreter',
    'redirect_chain',
    'user_agent_rotator',
    'connection_pool',
    'rate_limit_detector',
    'proxy_config',
    'response_time',
    'content_type_validator',
    'captcha_detector',
    'login_requirement',
    'age_restriction',
    'region_restriction',
    'privacy_status',
    'embed_restriction',
]