# KDP_MASTER - Project Context
## Last Updated: 2026-05-12

## Goal
Implementar los 64 módulos de inteligencia (20 sin IA + 20 con IA + 4 hardening crítico) para KDP_MASTER, integrándolos al código existente sin eliminar funcionalidad precedente, testeando cada módulo y subiendo a GitHub.

## Constraints & Preferences
- Usar enfoque híbrido: módulos sin IA primero, luego progresión IA
- Ollama local ya configurado disponible
- No eliminar funcionalidades precedentes existentes
- Seguir reglas de arquitectura KDP-RULES.md
- Indentar según estándares del proyecto
- Reutilizar botones/modales existentes del frontend

## Progress
### Done
- FASE 1 (Módulos 1-5): CCAvailabilityValidator, ParallelSubtitleFetcher, TextNormalizer, SpaceValidator, ContentDeduplicator
- FASE 2 (Módulos 6-10): SubtitleQualityFilter, PostExtractionValidator, ImmutableAuditLedger, DomainRateLimiter, User-Agent Rotator (integrado en DownloadService)
- FASE 3 (Módulos 11-15): CCMetadataCacheManager, ThumbnailOCRExtractor, LogCompressor, ParagraphStructureValidator, LanguageDetector
- FASE 4 (Módulos 16-20): NoiseCleaner, RetryHandler, FTS5Validator, ManifestGenerator, AtomicPersistenceManager
- **20/20 módulos sin IA COMPLETADOS**
- FASE IA (Módulos 21-40): Todos los 20 módulos de IA completados
  - Módulos 21-25: OllamaAIClient, InfoDensityClassifier, NoiseSignalDetector, SemanticChunker, JargonTranslator, NERExtractor
  - Módulos 26-30: ContentTypeClassifier, ManualPredictor, BiasDetector, TagGenerator, CoherenceValidator
  - Módulos 31-35: PlagiarismDetector, ExecSummaryGenerator, UrgencyClassifier, ErrorTranslator, TimePredictor
  - Módulos 36-40: KBFusion, StaleDetector, ValidationQuizGenerator, ActionRecommender, PipelineOptimizer
- **222+ tests passing** (FASE 1-4 + AI)
- Commits push a GitHub: `0bb9102`, `f0f14da`, `390a2be`, `0586687`, `3df3fdc`
- CC Schema Monitor v4.0.0 liberado

### In Progress
- (none) - FASE IA completa

### Blocked
- (none)

## Key Decisions
- Usar OllamaPool existente en `app/core/ollama_pool.py` como base para módulos IA
- Crear wrapper centralizado OllamaAIClient en ai_client.py con system prompts predefinidos
- Cada módulo IA tiene fallback local (regex/heurísticas) cuando Ollama no disponible
- Estructura: `app/modules/ai_analysis/` para módulos IA vs `app/modules/cc_schema/` para módulos sin IA

## Next Steps
1. Implementar Módulos 41-44: Hardening modules (si aplica según contexto)
2. Integrar módulos IA en pipeline de descarga existente
3. Documentar uso de módulos en README

## Critical Context
- Rama actual: `v3.4.7-elite`
- Repo: `https://github.com/pabloalanzahlut/KDP-Master-Suite.git`
- Ollama configurado en `http://localhost:11434` con modelo `deepseek-r1:1.5b`
- Sistema de prompts IA diseñado para respuestas JSON estructuradas

## Relevant Files
- `app/modules/cc_schema/__init__.py`: Paquete 20 módulos sin IA (v4.0.0)
- `app/modules/cc_schema/`: 20 módulos deterministas para extracción CC
- `app/modules/ai_analysis/__init__.py`: Paquete 20 módulos IA (v1.0.0)
- `app/modules/ai_analysis/`: 20 módulos de IA con fallback local
- `app/core/ollama_pool.py`: Pool Ollama existente a reutilizar
- `tests/test_cc_extraction*.py`: Tests para módulos sin IA
- `tests/test_ai_analysis.py`: Tests para módulos IA (89 tests)