"""
KDP MASTER - Pre-Ingesta Gateway
============================
Sistema de Gateway Inteligente para Pre-Validación de Contenido YouTube.
22 módulos de análisis predictivo y gestión técnica con IA local (Ollama).

Autor: KDP Master System
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "KDP Master System"

from .gateway import PreIngestaGateway
from .base import QueueItem, QueuePriority, QueueState

__all__ = [
    "PreIngestaGateway",
    "QueueItem", 
    "QueuePriority",
    "QueueState"
]