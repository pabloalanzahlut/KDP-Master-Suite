# KDP_MASTER - Project Context
## Last Updated: 2026-05-12

## Goal
Implementar los 64 módulos de inteligencia (20 sin IA + 20 con IA + 4 hardening crítico) para KDP_MASTER, integrándolos al código existente sin eliminar funcionalidad precedente, testeando cada módulo y subiendo a GitHub.

## Constraints & Preferences
- Usar enfoque híbrido: módulos sin IA primero, luego progresión IA
- Ollama local en **producción** disponible en `http://localhost:11434`
- No eliminar funcionalidades precedentes existentes
- Seguir reglas de arquitectura KDP-RULES.md
- Indentar según estándares del proyecto
- Reutilizar botones/modales existentes del frontend
- Aceptar +2s por video para análisis IA
- UI y backend en paralelo siempre

## Progress
### Done (v3.4.7)
- FASE 1 (Módulos 1-5): CCAvailabilityValidator, ParallelSubtitleFetcher, TextNormalizer, SpaceValidator, ContentDeduplicator
- FASE 2 (Módulos 6-10): SubtitleQualityFilter, PostExtractionValidator, ImmutableAuditLedger, DomainRateLimiter, User-Agent Rotator
- FASE 3 (Módulos 11-15): CCMetadataCacheManager, ThumbnailOCRExtractor, LogCompressor, ParagraphStructureValidator, LanguageDetector
- FASE 4 (Módulos 16-20): NoiseCleaner, RetryHandler, FTS5Validator, ManifestGenerator, AtomicPersistenceManager
- **20/20 módulos sin IA COMPLETADOS**
- FASE IA (Módulos 21-40): Todos los 20 módulos de IA con Ollama
- **222+ tests passing**
- Commits push a GitHub: `0bb9102`, `f0f14da`, `390a2be`, `0586687`, `3df3fdc`, `5f86e51`
- CC Schema Monitor v4.0.0 liberado
- **main** actualizado con todos los cambios de v3.4.7-elite

### In Progress (v3.4.8-dev)
- Módulos Hardening (41-44): ✅ Completados
  - rate_limit_enforcer: Token bucket rate limiter
  - circuit_breaker: Pattern para prevenir cascadas de errores
  - health_checker: Monitor de salud de módulos
  - config_validator: Validador de configs
- IA Orchestrator: ✅ Creado e integrado en DownloadService
- Batch Processor: ✅ Creado
- AI Stats Panel UI: ✅ Creado
- **113 tests passing**

### Next Steps (v3.4.8-dev)
1. ✅ Integrar IA Orchestrator en DownloadService
2. ✅ Crear panel UI para stats de módulos IA
3. ⏳ Integration tests end-to-end
4. ⏳ Performance benchmarks
5. ⏳ Merge a main cuando estable

## Key Decisions
- Usar OllamaPool existente en `app/core/ollama_pool.py` como base para módulos IA
- Crear wrapper centralizado OllamaAIClient en ai_client.py con system prompts predefinidos
- Cada módulo IA tiene fallback local (regex/heurísticas) cuando Ollama no disponible
- Estructura: `app/modules/ai_analysis/` para módulos IA vs `app/modules/cc_schema/` para módulos sin IA
- Rama de desarrollo: `v3.4.8-dev`
- Rama estable: `main`

## Critical Context
- Rama actual: `v3.4.8-dev`
- Rama estable: `main` (contiene v3.4.7 completa)
- Repo: `https://github.com/pabloalanzahlut/KDP-Master-Suite.git`
- Ollama en **producción**: `http://localhost:11434` con modelo `deepseek-r1:1.5b`
- Sistema de prompts IA diseñado para respuestas JSON estructuradas

## Relevant Files
- `app/modules/cc_schema/__init__.py`: Paquete 24 módulos (v4.4.0)
- `app/modules/cc_schema/`: Módulos sin IA + hardening
- `app/modules/ai_analysis/__init__.py`: Paquete 20 módulos IA (v1.0.0)
- `app/modules/ai_analysis/`: Módulos de IA con fallback local
- `app/services/ia_orchestrator.py`: Orquestador IA
- `app/services/batch_processor.py`: Processor batch con IA
- `app/services/download_service.py`: DownloadService con IA integrado
- `app/ui/components/ai_stats_panel.py`: Panel UI de stats IA
- `app/core/ollama_pool.py`: Pool Ollama existente
- `tests/test_ai_analysis.py`: Tests para módulos IA (89 tests)
- `tests/test_hardening_modules.py`: Tests para hardening (24 tests)
- `tests/test_cc_extraction*.py`: Tests para módulos sin IA