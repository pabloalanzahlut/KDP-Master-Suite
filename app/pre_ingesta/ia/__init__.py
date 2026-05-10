"""
KDP MASTER - Pre-Ingesta IA Modules
===============================
Módulos de inteligencia artificial con Ollama.

Autor: KDP Master System
Version: 1.0.0
"""

__version__ = "1.0.0"

from .relevance_analyzer import RelevanceAnalyzer
from .naming_engine import NamingEngine
from .category_classifier import CategoryClassifier
from .time_estimator import TimeEstimator
from .keypoints_extractor import KeypointsExtractor
from .batch_grouper import BatchGrouper
from .compliance_filter import ComplianceFilter
from .natural_ingest import NaturalIngestEngine
from .value_predictor import ValuePredictor

__all__ = [
    "RelevanceAnalyzer",
    "NamingEngine", 
    "CategoryClassifier",
    "TimeEstimator",
    "KeypointsExtractor",
    "BatchGrouper",
    "ComplianceFilter",
    "NaturalIngestEngine",
    "ValuePredictor"
]