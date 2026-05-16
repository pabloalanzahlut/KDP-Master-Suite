"""
AI Orchestrator - Módulo Central de IA
======================================
Coordina todos los módulos IA y decide qué analizar según contenido.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AnalysisStage(Enum):
    PRE_EXTRACTION = "pre_extraction"
    POST_EXTRACTION = "post_extraction"
    QUALITY_CHECK = "quality_check"
    ENRICHMENT = "enrichment"


@dataclass
class AnalysisConfig:
    enable_density: bool = True
    enable_noise: bool = True
    enable_coherence: bool = True
    enable_bias: bool = True
    enable_tags: bool = True
    enable_type_classify: bool = True
    enable_manual_predict: bool = False
    enable_plagiarism: bool = True
    enable_stale: bool = False
    enable_action_recommend: bool = True
    max_analysis_time_ms: int = 2000
    batch_mode: bool = False


@dataclass
class AnalysisResult:
    video_id: str
    url: str
    density_score: float = 0.0
    is_signal: bool = True
    content_type: str = "unknown"
    tags: List[str] = None
    manual_priority: str = "low"
    is_plagiarism: bool = False
    action_recommendation: str = "review"
    processing_time_ms: float = 0.0
    modules_used: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.modules_used is None:
            self.modules_used = []


class IAOrchestrator:
    """
    Orquestador central de análisis IA.
    Coordina todos los módulos y decide qué analizar.
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self._modules = {}
        self._ai_client = None
        self._stats = {
            'total_analyzed': 0,
            'total_time_ms': 0.0,
            'modules_called': {}
        }
        self._init_modules()

    def _init_modules(self):
        """Inicializa módulos IA con fallback local."""
        try:
            from app.modules.ai_analysis import (
                OllamaAIClient, InfoDensityClassifier, NoiseSignalDetector,
                ContentTypeClassifier, TagGenerator, BiasDetector,
                PlagiarismDetector, CoherenceValidator, ManualPredictor,
                ActionRecommender, StaleDetector
            )

            self._ai_client = OllamaAIClient()

            self._modules = {
                'density': InfoDensityClassifier(self._ai_client),
                'noise': NoiseSignalDetector(self._ai_client),
                'type': ContentTypeClassifier(self._ai_client),
                'tags': TagGenerator(self._ai_client),
                'bias': BiasDetector(self._ai_client),
                'plagiarism': PlagiarismDetector(self._ai_client),
                'coherence': CoherenceValidator(self._ai_client),
                'manual': ManualPredictor(self._ai_client),
                'action': ActionRecommender(self._ai_client),
                'stale': StaleDetector(self._ai_client)
            }

            logger.info(f"IAOrchestrator: {len(self._modules)} módulos inicializados")
            logger.info(f"Ollama disponible: {self._ai_client.is_available()}")

        except ImportError as e:
            logger.warning(f"IAOrchestrator: Módulos IA no disponibles: {e}")
            self._modules = {}

    def is_available(self) -> bool:
        """Verifica si IA está disponible."""
        return len(self._modules) > 0

    def analyze_video(self, video_id: str, url: str, transcript: str = "", metadata: Optional[Dict] = None) -> AnalysisResult:
        """
        Analiza un video con módulos IA.

        Args:
            video_id: ID del video
            url: URL del video
            transcript: Transcripción (opcional)
            metadata: Metadata adicional

        Returns:
            AnalysisResult con resultados de análisis
        """
        start_time = time.time()
        result = AnalysisResult(video_id=video_id, url=url)

        if not transcript:
            logger.debug(f"Video {video_id}: Sin transcripción para análisis")
            return result

        try:
            if self.config.enable_density and 'density' in self._modules:
                density_result = self._modules['density'].classify(transcript)
                result.density_score = density_result.score
                result.modules_used.append('density')

            if self.config.enable_noise and 'noise' in self._modules:
                noise_result = self._modules['noise'].detect(transcript)
                result.is_signal = noise_result.is_signal
                result.modules_used.append('noise')

            if self.config.enable_type_classify and 'type' in self._modules:
                type_result = self._modules['type'].classify(transcript)
                result.content_type = type_result.content_type.value
                result.modules_used.append('type')

            if self.config.enable_tags and 'tags' in self._modules:
                tags_result = self._modules['tags'].generate(transcript, max_tags=10)
                result.tags = tags_result.tags[:10]
                result.modules_used.append('tags')

            if self.config.enable_bias and 'bias' in self._modules:
                bias_result = self._modules['bias'].analyze(transcript)
                if bias_result.is_biased:
                    result.tags.append('biased_content')
                result.modules_used.append('bias')

            if self.config.enable_manual_predict and 'manual' in self._modules:
                manual_result = self._modules['manual'].predict(transcript)
                result.manual_priority = manual_result.priority.value
                result.modules_used.append('manual')

            if self.config.enable_plagiarism and 'plagiarism' in self._modules:
                plagi_result = self._modules['plagiarism'].detect(transcript)
                result.is_plagiarism = plagi_result.is_duplicate
                result.modules_used.append('plagiarism')

            if self.config.enable_action_recommend and 'action' in self._modules:
                action_result = self._modules['action'].recommend({
                    'content': transcript,
                    'quality': result.density_score / 10,
                    'completeness': 0.7,
                    'duplicate_score': 0.1 if result.is_plagiarism else 0.0
                })
                result.action_recommendation = action_result.action.value
                result.modules_used.append('action')

            result.processing_time_ms = (time.time() - start_time) * 1000
            self._stats['total_analyzed'] += 1
            self._stats['total_time_ms'] += result.processing_time_ms

            for mod in result.modules_used:
                self._stats['modules_called'][mod] = self._stats['modules_called'].get(mod, 0) + 1

        except Exception as e:
            logger.error(f"IAOrchestrator: Error en análisis {video_id}: {e}")
            result.error = str(e)

        return result

    def batch_analyze(self, items: List[Dict]) -> List[AnalysisResult]:
        """
        Analiza múltiples videos.

        Args:
            items: Lista de dicts con {video_id, url, transcript}

        Returns:
            Lista de AnalysisResult
        """
        results = []
        for item in items:
            result = self.analyze_video(
                item.get('video_id', ''),
                item.get('url', ''),
                item.get('transcript', '')
            )
            results.append(result)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del orquestador."""
        stats = self._stats.copy()
        if stats['total_analyzed'] > 0:
            stats['avg_time_ms'] = stats['total_time_ms'] / stats['total_analyzed']
        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_analyzed': 0,
            'total_time_ms': 0.0,
            'modules_called': {}
        }


def create_orchestrator(config: Optional[AnalysisConfig] = None) -> IAOrchestrator:
    """Factory function para crear orquestador."""
    return IAOrchestrator(config)