"""
KDP Master - Modules
===================
Interfaz de comunicación entre islas.
Expone los servicios públicos disponibles.
"""

from app.modules.processing.services import DownloadService, ProcessingService
from app.modules.processing.pipeline import PipelineOrchestrator
from app.modules.processing.integrate_knowledge import KnowledgeIntegrator

__all__ = [
    'DownloadService',
    'ProcessingService',
    'PipelineOrchestrator',
    'KnowledgeIntegrator',
]