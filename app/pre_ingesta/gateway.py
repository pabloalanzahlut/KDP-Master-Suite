"""
KDP MASTER - Pre-Ingesta Gateway
============================
Orquestador principal del Gateway de Pre-Ingesta.
Integra los 22 módulos de análisis predictivo.

Autor: KDP Master System
Version: 1.0.0
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..pre_ingesta.base import (
    QueueItem, QueuePriority, QueueState, ContentType, IngestaResult
)
from ..pre_ingesta.validators import (
    CompositeValidator, create_validator
)
from ..pre_ingesta.priority_manager import PriorityEngine
from ..pre_ingesta.deduplicator import DeduplicatorEngine
from ..pre_ingesta.bulk_processor import BulkIngestProcessor
from ..pre_ingesta.metadata_tagger import MetadataTagger
from ..pre_ingesta.source_monitor import SourceMonitor
from ..pre_ingesta.queue_persister import QueuePersister
from ..pre_ingesta.audit_logger import AuditLogger
from ..pre_ingesta.retry_engine import RetryEngine
from ..pre_ingesta.load_balancer import LoadBalancer

from ..pre_ingesta.ia.relevance_analyzer import RelevanceAnalyzer
from ..pre_ingesta.ia.naming_engine import NamingEngine
from ..pre_ingesta.ia.category_classifier import CategoryClassifier
from ..pre_ingesta.ia.time_estimator import TimeEstimator
from ..pre_ingesta.ia.keypoints_extractor import KeypointsExtractor
from ..pre_ingesta.ia.compliance_filter import ComplianceFilter
from ..pre_ingesta.ia.natural_ingest import NaturalIngestEngine
from ..pre_ingesta.ia.value_predictor import ValuePredictor

logger = logging.getLogger(__name__)


class PreIngestaGateway:
    """
    Gateway de Pre-Ingesta Inteligente.
    Coordina los 22 módulos para análisis predictivo.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.validator = create_validator()
        self.priority_engine = PriorityEngine()
        self.deduplicator = DeduplicatorEngine()
        self.bulk_processor = BulkIngestProcessor()
        self.metadata_tagger = MetadataTagger()
        self.source_monitor = SourceMonitor()
        self.persister = QueuePersister()
        self.audit_logger = AuditLogger()
        self.retry_engine = RetryEngine()
        self.load_balancer = LoadBalancer()
        
        self.relevance_analyzer = RelevanceAnalyzer()
        self.naming_engine = NamingEngine()
        self.category_classifier = CategoryClassifier()
        self.time_estimator = TimeEstimator()
        self.keypoints_extractor = KeypointsExtractor()
        self.compliance_filter = ComplianceFilter()
        self.natural_ingest = NaturalIngestEngine()
        self.value_predictor = ValuePredictor()
        
        self.ollama_enabled = self._check_ollama()
        self.modules_passed = []
        self.modules_failed = []
    
    def _check_ollama(self) -> bool:
        """Verifica conexión con Ollama."""
        try:
            import requests
            response = requests.get(
                "http://localhost:11434/api/tags", 
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def process(self, url: str, source: str = "manual",
              use_ai: bool = True, use_ollama: bool = True) -> IngestaResult:
        """
        Procesa URL a través del Gateway completo.
        Flujo: Validación → Deduplicación → IA → Cola
        """
        start_time = time.time()
        result = IngestaResult(success=False)
        
        try:
            item = QueueItem(url=url, source=source)
            
            is_valid, metadata, validations = self.validator.validate_all(url)
            result.modules_passed.extend([v for v in validations if 'PASS' in v])
            result.modules_failed.extend([v for v in validations if 'FAIL' in v])
            
            if not is_valid:
                item.state = QueueState.FALLIDO
                item.error_message = metadata.get('error', 'Validación fallida')
                result.success = False
                result.message = item.error_message
                result.item = item
                result.processing_time_ms = int((time.time() - start_time) * 1000)
                return result
            
            is_duplicate, dup_msg = self.deduplicator.check_duplicate(url)
            if is_duplicate:
                item.state = QueueState.DUPLICADO
                item.error_message = dup_msg
                result.success = False
                result.message = dup_msg
                result.item = item
                result.warnings.append(dup_msg)
                result.processing_time_ms = int((time.time() - start_time) * 1000)
                return result
            
            video_info = metadata.get('video_info')
            if video_info:
                item.video_id = video_info.get('id')
                item.title = video_info.get('title')
                item.channel_name = video_info.get('channel')
                item.estimated_duration = video_info.get('duration', 0)
                item.estimated_size_mb = self.time_estimator.estimate(
                    item.estimated_duration
                ).get('estimated_size_mb', 0)
            
            if use_ai and video_info:
                relevance = self.relevance_analyzer.analyze(
                    video_info, use_ollama=use_ollama and self.ollama_enabled
                )
                item.relevance_score = relevance.get('relevance_score', 0)
                item.strategic_score = relevance.get('strategic_score', 0)
                
                category, confidence, subs = self.category_classifier.classify(
                    item.title or "", 
                    video_info.get('description', ''),
                    video_info.get('tags', [])
                )
                item.category = category
                
                compliance = self.compliance_filter.check_compliance(
                    item.title or "",
                    video_info.get('description', ''),
                    item.channel_name or ""
                )
                item.compliance_status = compliance.get('status', 'pending')
                item.compliance_issues = compliance.get('reasons', [])
                
                value_pred = self.value_predictor.predict(
                    item.title or "",
                    video_info.get('description', ''),
                    item.estimated_duration
                )
                item.value_score = value_pred.get('value_score', 0)
                
                if value_pred.get('recommended_action') == 'skip':
                    item.state = QueueState.BLOQUEADO
                    result.success = False
                    result.message = "Valor de contenido demasiado bajo"
                    result.item = item
                    result.processing_time_ms = int((time.time() - start_time) * 1000)
                    return result
            
            item.state = QueueState.PENDIENTE
            result.success = True
            result.message = "Procesado correctamente"
            result.item = item
            
            self.deduplicator.mark_as_seen(item)
            self.audit_logger.log_add_to_queue(url, source=source, success=True)
        
        except Exception as e:
            logger.error(f"Error procesando {url}: {e}")
            result.success = False
            result.message = f"Error: {str(e)}"
            result.errors.append(str(e))
            result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        return result
    
    def process_batch(self, urls: List[str], source: str = "bulk",
                   use_ai: bool = True, max_workers: int = 2) -> List[IngestaResult]:
        """Procesa múltiples URLs."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process, url, source, use_ai): url 
                for url in urls
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error en batch: {e}")
        
        return results
    
    def natural_command(self, command: str) -> Dict[str, Any]:
        """Procesa comando en lenguaje natural."""
        return self.natural_ingest.parse_command(command)
    
    def add_bulk(self, raw_input: str, source: str = "bulk") -> Tuple[int, List[str]]:
        """Añade múltiples URLs desde input masivo."""
        items, errors = self.bulk_processor.process_batch(raw_input, source)
        
        urls = [item.url for item in items]
        results = self.process_batch(urls, source=source)
        
        successful = sum(1 for r in results if r.success)
        return successful, errors
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Obtiene estado de la cola."""
        items = self.persister.load()
        
        return {
            'total_items': len(items),
            'by_state': self._count_by_state(items),
            'ollama_enabled': self.ollama_enabled,
            'deduplicator_stats': self.deduplicator.get_stats()
        }
    
    def _count_by_state(self, items: List[QueueItem]) -> Dict[str, int]:
        """Cuenta items por estado."""
        counts = {}
        for item in items:
            state = item.state.value
            counts[state] = counts.get(state, 0) + 1
        return counts
    
    def get_available_categories(self) -> List[str]:
        """Categorías KDP disponibles."""
        return self.category_classifier.get_available_categories()


def create_gateway(config: Optional[Dict[str, Any]] = None) -> PreIngestaGateway:
    """Factory function."""
    return PreIngestaGateway(config)


_global_gateway: Optional[PreIngestaGateway] = None


def get_gateway() -> PreIngestaGateway:
    """Obtiene instancia global del Gateway."""
    global _global_gateway
    if _global_gateway is None:
        _global_gateway = create_gateway()
    return _global_gateway


def process_url(url: str, source: str = "manual", use_ai: bool = True) -> IngestaResult:
    """Función de conveniencia."""
    gateway = get_gateway()
    return gateway.process(url, source, use_ai)


def add_to_queue(url: str, source: str = "manual") -> Tuple[bool, str]:
    """Añade URL directamente a la cola."""
    gateway = get_gateway()
    result = gateway.process(url, source, use_ai=True)
    return result.success, result.message