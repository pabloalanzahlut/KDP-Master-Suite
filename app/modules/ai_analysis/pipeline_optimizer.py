"""
AI Analysis - Pipeline Optimizer
================================
Módulo 40: Optimizador de pipeline de extracción con IA.
Usa análisis para decidir orden y configuración óptima.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    EXTRACT = "extract"
    CLEAN = "clean"
    ANALYZE = "analyze"
    VALIDATE = "validate"
    STORE = "store"
    ENRICH = "enrich"


class PipelineConfig:
    def __init__(self):
        self.stages = []
        self.enable_parallel = True
        self.max_workers = 4
        self.timeout_seconds = 300
        self.retry_count = 3
        self.enable_caching = True


@dataclass
class PipelineStep:
    stage: PipelineStage
    module_name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    estimated_time: float = 0.0


@dataclass
class OptimizationResult:
    recommended_config: PipelineConfig
    stage_order: List[PipelineStage]
    estimated_total_time: float
    parallel_opportunities: List[str]
    bottlenecks: List[str]
    savings_percent: float
    reasoning: List[str]


class PipelineOptimizer:
    """
    Optimizador de pipeline de extracción.
    Analiza y optimiza configuración de módulos.
    """

    STAGE_DEPENDENCIES = {
        PipelineStage.EXTRACT: [],
        PipelineStage.CLEAN: [PipelineStage.EXTRACT],
        PipelineStage.VALIDATE: [PipelineStage.EXTRACT, PipelineStage.CLEAN],
        PipelineStage.ANALYZE: [PipelineStage.VALIDATE],
        PipelineStage.ENRICH: [PipelineStage.ANALYZE],
        PipelineStage.STORE: [PipelineStage.ENRICH]
    }

    STAGE_TIMES = {
        PipelineStage.EXTRACT: 5.0,
        PipelineStage.CLEAN: 2.0,
        PipelineStage.VALIDATE: 1.5,
        PipelineStage.ANALYZE: 3.0,
        PipelineStage.ENRICH: 2.5,
        PipelineStage.STORE: 0.5
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self._metrics_history = []
        self._performance_baseline = {
            PipelineStage.EXTRACT: 5.0,
            PipelineStage.CLEAN: 2.0,
            PipelineStage.VALIDATE: 1.5,
            PipelineStage.ANALYZE: 3.0,
            PipelineStage.ENRICH: 2.5,
            PipelineStage.STORE: 0.5
        }

    def optimize(self, content_characteristics: Dict, current_config: Optional[PipelineConfig] = None) -> OptimizationResult:
        """
        Optimiza configuración de pipeline.

        Args:
            content_characteristics: Características del contenido
            current_config: Configuración actual (opcional)

        Returns:
            OptimizationResult con configuración optimizada
        """
        word_count = content_characteristics.get('word_count', 1000)
        has_media = content_characteristics.get('has_media', False)
        content_quality = content_characteristics.get('quality', 0.5)
        is_trusted = content_characteristics.get('from_trusted_source', False)

        stage_times = self._estimate_stage_times(word_count, has_media, content_quality)

        parallel_ops = self._find_parallel_opportunities(stage_times)

        bottlenecks = self._identify_bottlenecks(stage_times)

        recommended_config = self._build_optimized_config(stage_times, is_trusted)

        stage_order = self._calculate_optimal_order()

        estimated_time = sum(stage_times.values())
        baseline_time = sum(self._performance_baseline.values())

        savings = ((baseline_time - estimated_time) / baseline_time) * 100 if baseline_time > 0 else 0

        reasoning = []
        if bottlenecks:
            reasoning.append(f"Cuellos de botella identificados: {', '.join(bottlenecks)}")
        if savings > 10:
            reasoning.append(f"Optimización reduce tiempo en {savings:.0f}%")
        if parallel_ops:
            reasoning.append(f"Operaciones paralelas posibles: {len(parallel_ops)}")

        return OptimizationResult(
            recommended_config=recommended_config,
            stage_order=stage_order,
            estimated_total_time=estimated_time,
            parallel_opportunities=parallel_ops,
            bottlenecks=bottlenecks,
            savings_percent=round(savings, 1),
            reasoning=reasoning
        )

    def _estimate_stage_times(self, word_count: int, has_media: bool, quality: float) -> Dict[PipelineStage, float]:
        """Estima tiempos por etapa."""
        times = {}

        times[PipelineStage.EXTRACT] = self.STAGE_TIMES[PipelineStage.EXTRACT] * (1 + word_count / 10000)
        if has_media:
            times[PipelineStage.EXTRACT] *= 1.5

        times[PipelineStage.CLEAN] = self.STAGE_TIMES[PipelineStage.CLEAN]
        if quality < 0.4:
            times[PipelineStage.CLEAN] *= 1.3

        times[PipelineStage.VALIDATE] = self.STAGE_TIMES[PipelineStage.VALIDATE]
        times[PipelineStage.ANALYZE] = self.STAGE_TIMES[PipelineStage.ANALYZE]
        if quality > 0.8:
            times[PipelineStage.ANALYZE] *= 0.8

        times[PipelineStage.ENRICH] = self.STAGE_TIMES[PipelineStage.ENRICH]
        times[PipelineStage.STORE] = self.STAGE_TIMES[PipelineStage.STORE]

        return times

    def _find_parallel_opportunities(self, stage_times: Dict[PipelineStage, float]) -> List[str]:
        """Encuentra oportunidades de paralelismo."""
        opportunities = []

        independent_stages = [
            (PipelineStage.ANALYZE, PipelineStage.ENRICH),
        ]

        for stage1, stage2 in independent_stages:
            if stage1 in stage_times and stage2 in stage_times:
                if stage_times[stage1] < stage_times[stage2] * 0.8:
                    opportunities.append(f"{stage1.value} y {stage2.value} pueden ejecutarse en paralelo")

        if stage_times.get(PipelineStage.VALIDATE, 0) < 1.0:
            opportunities.append("Validación puede ejecutarse en paralelo con extracción")

        return opportunities

    def _identify_bottlenecks(self, stage_times: Dict[PipelineStage, float]) -> List[str]:
        """Identifica cuellos de botella."""
        bottlenecks = []
        max_time = max(stage_times.values()) if stage_times else 0

        for stage, time in stage_times.items():
            if time > max_time * 0.5:
                bottlenecks.append(f"{stage.value} ({time:.1f}s)")

        return bottlenecks

    def _build_optimized_config(self, stage_times: Dict[PipelineStage, float], is_trusted: bool) -> PipelineConfig:
        """Construye configuración optimizada."""
        config = PipelineConfig()

        config.stages = [
            PipelineStep(stage=PipelineStage.EXTRACT, module_name="DownloadService"),
            PipelineStep(stage=PipelineStage.CLEAN, module_name="NoiseCleaner"),
            PipelineStep(stage=PipelineStage.VALIDATE, module_name="PostExtractionValidator"),
            PipelineStep(stage=PipelineStage.ANALYZE, module_name="InfoDensityClassifier"),
            PipelineStep(stage=PipelineStage.ENRICH, module_name="TagGenerator"),
            PipelineStep(stage=PipelineStage.STORE, module_name="AtomicPersistenceManager")
        ]

        config.enable_parallel = len(self._find_parallel_opportunities(stage_times)) > 0

        config.max_workers = 4 if is_trusted else 2

        config.timeout_seconds = int(max(stage_times.values()) * 2 + 60)

        return config

    def _calculate_optimal_order(self) -> List[PipelineStage]:
        """Calcula orden óptimo de etapas."""
        order = []
        for stage in PipelineStage:
            if stage in self.STAGE_DEPENDENCIES:
                deps = self.STAGE_DEPENDENCIES[stage]
                if all(d in order or d == stage for d in deps):
                    if stage not in order:
                        order.append(stage)

        for stage in self.STAGE_DEPENDENCIES:
            if stage not in order:
                order.append(stage)

        return order

    def record_execution(self, stage: PipelineStage, actual_time: float):
        """Registra ejecución para aprendizaje."""
        self._metrics_history.append({
            'stage': stage.value,
            'actual_time': actual_time,
            'timestamp': datetime.now().isoformat()
        })

    def get_performance_report(self) -> Dict[str, Any]:
        """Genera reporte de rendimiento."""
        if not self._metrics_history:
            return {'status': 'no_data'}

        stage_metrics = {}
        for entry in self._metrics_history:
            stage = entry['stage']
            if stage not in stage_metrics:
                stage_metrics[stage] = {'times': [], 'count': 0}
            stage_metrics[stage]['times'].append(entry['actual_time'])
            stage_metrics[stage]['count'] += 1

        for stage, metrics in stage_metrics.items():
            times = metrics['times']
            metrics['avg'] = sum(times) / len(times)
            metrics['min'] = min(times)
            metrics['max'] = max(times)

        return {
            'total_executions': len(self._metrics_history),
            'stages': stage_metrics
        }

    def suggest_reconfiguration(self, current: PipelineConfig) -> Dict[str, Any]:
        """Sugiere reconfiguración basada en historial."""
        report = self.get_performance_report()

        suggestions = []

        if report.get('status') == 'no_data':
            return {'suggestions': [], 'reason': 'Sin datos suficientes'}

        for stage, metrics in report.get('stages', {}).items():
            if metrics['avg'] > self.STAGE_TIMES.get(PipelineStage[stage.upper()], 5) * 1.5:
                suggestions.append({
                    'stage': stage,
                    'issue': 'Tiempo mayor al esperado',
                    'suggestion': 'Revisar configuración o agregar caching'
                })

        return {
            'suggestions': suggestions,
            'report': report
        }