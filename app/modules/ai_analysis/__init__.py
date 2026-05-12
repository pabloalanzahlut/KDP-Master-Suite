"""
AI Analysis Module
==================
Módulos 21-40: Análisis de IA para KDP Master Suite.
Usa Ollama local para procesamiento cognitivo.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

from app.modules.ai_analysis.ai_client import (
    OllamaAIClient,
    OllamaProvider,
    AIAnalysisResult,
    create_ai_client,
    quick_analyze
)

from app.modules.ai_analysis.info_density_classifier import (
    InfoDensityClassifier,
    DensityResult
)

from app.modules.ai_analysis.noise_signal_detector import (
    NoiseSignalDetector,
    NoiseSignalResult
)

from app.modules.ai_analysis.semantic_chunker import (
    SemanticChunker,
    ChunkResult
)

from app.modules.ai_analysis.jargon_translator import (
    JargonTranslator,
    TranslationResult
)

from app.modules.ai_analysis.ner_extractor import (
    LocalNERExtractor as NERExtractor,
    Entity,
    EntityType,
    NERResult
)

from app.modules.ai_analysis.content_type_classifier import (
    ContentTypeClassifier,
    ContentType,
    ContentTypeResult
)

from app.modules.ai_analysis.manual_predictor import (
    ManualPredictor,
    ManualCategory,
    Priority,
    ManualPrediction
)

from app.modules.ai_analysis.bias_detector import (
    BiasDetector,
    BiasAnalysis
)

from app.modules.ai_analysis.tag_generator import (
    TagGenerator,
    TagGenerationResult
)

from app.modules.ai_analysis.coherence_validator import (
    CoherenceValidator,
    CoherenceResult
)

from app.modules.ai_analysis.plagiarism_detector import (
    PlagiarismDetector,
    PlagiarismResult,
    KBStorage
)

from app.modules.ai_analysis.exec_summary_generator import (
    ExecSummaryGenerator,
    SummaryResult
)

from app.modules.ai_analysis.urgency_classifier import (
    UrgencyClassifier,
    ProcessingUrgency,
    UrgencyResult
)

from app.modules.ai_analysis.error_translator import (
    ErrorTranslator,
    ErrorCategory,
    ActionType as ErrorActionType,
    ErrorTranslation
)

from app.modules.ai_analysis.time_predictor import (
    TimePredictor,
    TimePrediction
)

from app.modules.ai_analysis.kb_fusion import (
    KBFusion,
    FusionAction,
    KBEntry,
    FusionResult
)

from app.modules.ai_analysis.stale_detector import (
    StaleDetector,
    StaleItem,
    StaleDetectionResult
)

from app.modules.ai_analysis.validation_quiz import (
    ValidationQuizGenerator,
    QuizQuestion,
    QuizResult
)

from app.modules.ai_analysis.action_recommender import (
    ActionRecommender,
    ActionType,
    ActionRecommendation
)

from app.modules.ai_analysis.pipeline_optimizer import (
    PipelineOptimizer,
    PipelineStage,
    PipelineConfig,
    PipelineStep,
    OptimizationResult
)

__all__ = [
    'OllamaAIClient',
    'OllamaProvider',
    'AIAnalysisResult',
    'create_ai_client',
    'quick_analyze',
    'InfoDensityClassifier',
    'DensityResult',
    'NoiseSignalDetector',
    'NoiseSignalResult',
    'SemanticChunker',
    'ChunkResult',
    'JargonTranslator',
    'TranslationResult',
    'Entity',
    'EntityType',
    'NERResult',
    'ContentTypeClassifier',
    'ContentType',
    'ContentTypeResult',
    'ManualPredictor',
    'ManualCategory',
    'Priority',
    'ManualPrediction',
    'BiasDetector',
    'BiasAnalysis',
    'TagGenerator',
    'TagGenerationResult',
    'CoherenceValidator',
    'CoherenceResult',
    'PlagiarismDetector',
    'PlagiarismResult',
    'KBStorage',
    'ExecSummaryGenerator',
    'SummaryResult',
    'UrgencyClassifier',
    'ProcessingUrgency',
    'UrgencyResult',
    'ErrorTranslator',
    'ErrorCategory',
    'ErrorActionType',
    'ErrorTranslation',
    'TimePredictor',
    'TimePrediction',
    'KBFusion',
    'FusionAction',
    'KBEntry',
    'FusionResult',
    'StaleDetector',
    'StaleItem',
    'StaleDetectionResult',
    'ValidationQuizGenerator',
    'QuizQuestion',
    'QuizResult',
    'ActionRecommender',
    'ActionType',
    'ActionRecommendation',
    'PipelineOptimizer',
    'PipelineStage',
    'PipelineConfig',
    'PipelineStep',
    'OptimizationResult'
]

__version__ = '1.0.0'
__ai_modules__ = 20
__status__ = 'ready'