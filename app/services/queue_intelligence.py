"""
Queue Intelligence - Orquestador de Gestión de Cola
====================================================
Coordina todos los módulos de infraestructura para el vaciado inteligente de cola.

Módulos de Infraestructura (SIN IA) - v3.4.9
Autor: KDP_MASTER Team
Fecha: 2026-05-17

Filosofía UX para Principiantes:
================================
Este módulo es como un "director de orquesta". Imagina que tienes una banda musical
(los módulos de cola). Cada instrumento toca diferente (snapshot, auditoría, undo, etc.).
El director (este módulo) decide CUÁNDO y CÓMO toca cada uno para que la música suene bien.

Caso de uso real: Es como cuando ordenas tu habitación. No-botones lanzas todo a la basura.
Recoges primero la ropa sucia (filtro), guardas los objetos importantes (snapshot),
y luego barres el piso (limpieza). Este módulo hace exactamente eso pero para tu cola de videos.
"""

import json
import logging
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class ClearStrategy(Enum):
    """Estrategias de vaciado disponibles."""
    ALL = "all"
    FAILED_ONLY = "failed_only"
    COMPLETED_ONLY = "completed_only"
    PENDING_ONLY = "pending_only"
    OLDEST_50 = "oldest_50"
    OLDEST_75 = "oldest_75"
    CUSTOM_COUNT = "custom_count"
    BY_SIZE = "by_size"
    BY_DURATION = "by_duration"


class QueueItemStatus(Enum):
    """Estados posibles de un item en cola."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """Representa un item en la cola de descargas."""
    url: str
    status: QueueItemStatus = QueueItemStatus.PENDING
    title: str = ""
    channel: str = ""
    duration_seconds: int = 0
    file_size_mb: float = 0.0
    is_protected: bool = False
    metadata_enriched: bool = False
    added_at: Optional[datetime] = None
    last_error: str = ""

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "status": self.status.value,
            "title": self.title,
            "channel": self.channel,
            "duration_seconds": self.duration_seconds,
            "file_size_mb": self.file_size_mb,
            "is_protected": self.is_protected,
            "metadata_enriched": self.metadata_enriched,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "last_error": self.last_error
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QueueItem":
        status = QueueItemStatus(data.get("status", "pending"))
        added_at = None
        if data.get("added_at"):
            try:
                added_at = datetime.fromisoformat(data["added_at"])
            except:
                pass
        return cls(
            url=data["url"],
            status=status,
            title=data.get("title", ""),
            channel=data.get("channel", ""),
            duration_seconds=data.get("duration_seconds", 0),
            file_size_mb=data.get("file_size_mb", 0.0),
            is_protected=data.get("is_protected", False),
            metadata_enriched=data.get("metadata_enriched", False),
            added_at=added_at,
            last_error=data.get("last_error", "")
        )


@dataclass
class ClearResult:
    """Resultado de una operación de vaciado."""
    success: bool
    cleared_count: int = 0
    protected_count: int = 0
    snapshot_path: Optional[str] = None
    export_path: Optional[str] = None
    error_message: str = ""
    cleared_items: List[Dict] = field(default_factory=list)
    impact_mb: float = 0.0
    impact_processing_minutes: float = 0.0


class QueueIntelligence:
    """
    Orquestador central de gestión inteligente de cola.
    
    ¿Por qué existe este módulo? Imagina que tienes 50 videos en cola y quieres
    limpiarlos. Antes simplemente borrabas todo y rezabas para no arrepentirte.
    
    Ahora, este módulo te permite:
    - Ver qué vas a borrar ANTES de borrarlo (snapshot)
    - Recuperar lo que borraste por error (undo/papelera)
    - Elegir QUÉ borrar (solo fallidos, solo antiguos, etc.)
    - Proteger items importantes
    - Registrar qué borraste y cuándo (auditoría)
    - Exportar un reporte antes de borrar
    
    Es como tener un asistente personal que te ayuda a organizar tu cola.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Inicializa el orquestador.
        
        Args:
            data_dir: Directorio para guardar snapshots y exports.
                     Si es None, usa el directorio por defecto.
        """
        if data_dir is None:
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._snapshot_dir = self.data_dir / "queue_snapshots"
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        self._export_dir = self.data_dir / "queue_exports"
        self._export_dir.mkdir(parents=True, exist_ok=True)
        
        self._trash_bin: List[QueueItem] = []
        self._trash_timeout_seconds = 60
        self._last_clear_time = 0
        
        self._init_submodules()
        
        logger.info(f"QueueIntelligence inicializado: data_dir={self.data_dir}")

    def _init_submodules(self):
        """Inicializa los submódulos."""
        try:
            from app.modules.cc_schema.queue_snapshot_manager import QueueSnapshotManager
            from app.modules.cc_schema.queue_state_validator import QueueStateValidator
            from app.modules.cc_schema.queue_audit_logger import QueueAuditLogger
            from app.services.queue_trash_bin import QueueTrashBin
            from app.services.partial_clear_strategy import PartialClearStrategy
            from app.services.protected_item_marker import ProtectedItemMarker
            from app.services.conditional_clear_by_size import ConditionalClearBySize
            
            self.snapshot_manager = QueueSnapshotManager(self._snapshot_dir)
            self.state_validator = QueueStateValidator()
            self.audit_logger = QueueAuditLogger(self.data_dir)
            self.trash_bin = QueueTrashBin(timeout_seconds=self._trash_timeout_seconds)
            self.partial_strategy = PartialClearStrategy()
            self.protected_marker = ProtectedItemMarker()
            self.size_conditional = ConditionalClearBySize()
            
            logger.info("QueueIntelligence: Todos los submódulos inicializados")
        except ImportError as e:
            logger.warning(f"QueueIntelligence: Algunos submódulos no disponibles: {e}")
            self._create_fallback_submodules()

    def _create_fallback_submodules(self):
        """Crea versiones mínimas de los submódulos si no están disponibles."""
        self.snapshot_manager = self._FallbackSnapshotManager(self._snapshot_dir)
        self.state_validator = self._FallbackStateValidator()
        self.audit_logger = self._FallbackAuditLogger(self.data_dir)
        self.trash_bin = self._FallbackTrashBin(timeout_seconds=self._trash_timeout_seconds)
        self.partial_strategy = self._FallbackPartialStrategy()
        self.protected_marker = self._FallbackProtectedMarker()
        self.size_conditional = self._FallbackSizeConditional()

    def analyze_queue(self, items: List[QueueItem]) -> Dict[str, Any]:
        """
        Analiza la cola y devuelve estadísticas.
        
        Este método es como un "médico" que examina a tu paciente (la cola)
        y te dice qué tiene (estadísticas).
        
        Caso de uso real: Antes de limpiar tu habitación, miras qué tienes.
        ¿Cuántas cosas rotas? ¿Cuántas cosas útiles? ¿Cuánto espacio ocuparán?

        Args:
            items: Lista de items en la cola.

        Returns:
            Diccionario con estadísticas de la cola.
        """
        if not items:
            return {
                "total": 0,
                "by_status": {},
                "total_duration_minutes": 0,
                "total_size_mb": 0.0,
                "protected_count": 0,
                "enriched_count": 0,
                "oldest_item": None,
                "newest_item": None
            }

        by_status = {}
        total_duration = 0
        total_size = 0.0
        protected_count = 0
        enriched_count = 0
        oldest = None
        newest = None

        for item in items:
            status_key = item.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1
            
            total_duration += item.duration_seconds
            total_size += item.file_size_mb
            
            if item.is_protected:
                protected_count += 1
            if item.metadata_enriched:
                enriched_count += 1
            
            if oldest is None or (item.added_at and item.added_at < oldest):
                oldest = item.added_at
            if newest is None or (item.added_at and item.added_at > newest):
                newest = item.added_at

        return {
            "total": len(items),
            "by_status": by_status,
            "total_duration_minutes": total_duration / 60,
            "total_size_mb": total_size,
            "protected_count": protected_count,
            "enriched_count": enriched_count,
            "oldest_item": oldest.isoformat() if oldest else None,
            "newest_item": newest.isoformat() if newest else None,
            "failed_count": by_status.get("failed", 0),
            "completed_count": by_status.get("completed", 0),
            "pending_count": by_status.get("pending", 0)
        }

    def get_items_to_clear(
        self,
        items: List[QueueItem],
        strategy: ClearStrategy,
        custom_value: Optional[int] = None,
        protect_marked: bool = True,
        protect_enriched: bool = True
    ) -> tuple[List[QueueItem], List[QueueItem]]:
        """
        Determina qué items deben limpiarse y cuáles deben protegerse.
        
        Este método es como un "filtro" de agua. Coges agua sucia (la cola)
        y la pasas por filtros para separar lo que quieres de lo que no.
        
        Caso de uso real: Cuando haces limpieza profunda en casa:
        1. Separas la ropa que donas (failed)
        2. Guardas los objetos de valor (protected)
        3. Tiras lo que está roto (oldest 50%)

        Args:
            items: Lista completa de items.
            strategy: Estrategia de selección.
            custom_value: Valor personalizado para estrategias que lo requieran.
            protect_marked: Si True, protege items marcados.
            protect_enriched: Si True, protege items con metadata enriquecida.

        Returns:
            Tupla (items_a_limpiar, items_protegidos)
        """
        protected = []
        to_clear = []

        for item in items:
            is_protected = False
            
            if protect_marked and item.is_protected:
                is_protected = True
            if protect_enriched and item.metadata_enriched:
                is_protected = True
            
            if is_protected:
                protected.append(item)
            else:
                to_clear.append(item)

        selected_for_clear = self._apply_strategy(to_clear, strategy, custom_value)
        
        return selected_for_clear, protected

    def _apply_strategy(
        self,
        items: List[QueueItem],
        strategy: ClearStrategy,
        custom_value: Optional[int]
    ) -> List[QueueItem]:
        """Aplica la estrategia de selección."""
        
        if strategy == ClearStrategy.ALL:
            return items
        
        filtered = []
        
        for item in items:
            if strategy == ClearStrategy.FAILED_ONLY:
                if item.status == QueueItemStatus.FAILED:
                    filtered.append(item)
            elif strategy == ClearStrategy.COMPLETED_ONLY:
                if item.status == QueueItemStatus.COMPLETED:
                    filtered.append(item)
            elif strategy == ClearStrategy.PENDING_ONLY:
                if item.status == QueueItemStatus.PENDING:
                    filtered.append(item)
        
        if strategy in [ClearStrategy.OLDEST_50, ClearStrategy.OLDEST_75, ClearStrategy.CUSTOM_COUNT]:
            sorted_items = sorted(
                [i for i in items if i.added_at],
                key=lambda x: x.added_at
            )
            
            if strategy == ClearStrategy.OLDEST_50:
                count = len(sorted_items) // 2
            elif strategy == ClearStrategy.OLDEST_75:
                count = int(len(sorted_items) * 0.75)
            else:
                count = custom_value or len(sorted_items)
            
            filtered = sorted_items[:count]
        
        if strategy == ClearStrategy.BY_SIZE:
            sorted_by_size = sorted(items, key=lambda x: x.file_size_mb, reverse=True)
            threshold_mb = custom_value or 100
            filtered = [i for i in sorted_by_size if i.file_size_mb >= threshold_mb]
        
        if strategy == ClearStrategy.BY_DURATION:
            sorted_by_duration = sorted(items, key=lambda x: x.duration_seconds, reverse=True)
            threshold_seconds = (custom_value or 60) * 60
            filtered = [i for i in sorted_by_duration if i.duration_seconds >= threshold_seconds]
        
        return filtered

    def calculate_impact(self, items: List[QueueItem]) -> Dict[str, float]:
        """
        Calcula el impacto de limpiar ciertos items.
        
        Este método responde a la pregunta: "¿Cuánto espacio voy a ganar?"
        
        Caso de uso real: Antes de tirar cajas de tu apartamento, calculas
        cuánto espacio liberarás y si vale la pena el esfuerzo.
        
        Args:
            items: Items que se van a limpiar.

        Returns:
            Diccionario con impacto estimado.
        """
        total_mb = sum(i.file_size_mb for i in items)
        total_seconds = sum(i.duration_seconds for i in items)
        
        processing_time_per_mb = 0.5
        estimated_minutes = (total_mb * processing_time_per_mb) / 60

        return {
            "space_mb": total_mb,
            "space_gb": total_mb / 1024,
            "processing_time_minutes": estimated_minutes,
            "items_count": len(items)
        }

    def clear_queue(
        self,
        items: List[QueueItem],
        strategy: ClearStrategy,
        options: Optional[Dict[str, Any]] = None
    ) -> ClearResult:
        """
        Ejecuta el vaciado de la cola con todas las opciones de seguridad.
        
        Este es el método principal que orquesta toda la operación de limpieza.
        Es como el "chef" que cocina toda la receta, no solo un ingrediente.
        
        Args:
            items: Lista de items en la cola.
            strategy: Estrategia de vaciado.
            options: Opciones adicionales (generate_snapshot, export_csv, etc.).

        Returns:
            ClearResult con el resultado de la operación.
        """
        options = options or {}
        
        try:
            analysis = self.analyze_queue(items)
            
            protect_marked = options.get("protect_marked", True)
            protect_enriched = options.get("protect_enriched", True)
            custom_value = options.get("custom_value")
            
            to_clear, protected = self.get_items_to_clear(
                items, strategy, custom_value, protect_marked, protect_enriched
            )
            
            snapshot_path = None
            if options.get("generate_snapshot", True):
                snapshot_path = self.snapshot_manager.create_snapshot(
                    items=items,
                    cleared_items=to_clear,
                    strategy=strategy.value
                )
            
            export_path = None
            if options.get("export_csv", False):
                export_path = self._export_to_csv(to_clear)
            
            if options.get("log_audit", True):
                self.audit_logger.log_clear_action(
                    cleared_count=len(to_clear),
                    protected_count=len(protected),
                    strategy=strategy.value,
                    snapshot_path=snapshot_path
                )
            
            impact = self.calculate_impact(to_clear)
            
            if options.get("enable_undo", True):
                self.trash_bin.add_items(to_clear)
                self._last_clear_time = time.time()
            
            return ClearResult(
                success=True,
                cleared_count=len(to_clear),
                protected_count=len(protected),
                snapshot_path=snapshot_path,
                export_path=export_path,
                cleared_items=[i.to_dict() for i in to_clear],
                impact_mb=impact["space_mb"],
                impact_processing_minutes=impact["processing_time_minutes"]
            )

        except Exception as e:
            logger.error(f"Error en clear_queue: {e}")
            return ClearResult(
                success=False,
                error_message=str(e)
            )

    def undo_last_clear(self) -> Optional[List[QueueItem]]:
        """
        Recupera los últimos items borrados (si está dentro del timeout).
        
        Este método es como tener una "papelera de reciclaje" en tu computadora.
        Si borraste algo por accidente, tienes 60 segundos para recuperarlo.
        
        Caso de uso real: Cuando borras un archivo en Windows y luego
        presionas Ctrl+Z o lo recuperas de la papelera.

        Returns:
            Lista de items recuperados o None si timeout expiró.
        """
        elapsed = time.time() - self._last_clear_time
        
        if elapsed > self._trash_timeout_seconds:
            logger.info("Undo timeout expirado")
            self.trash_bin.clear()
            return None
        
        return self.trash_bin.get_items()

    def _export_to_csv(self, items: List[QueueItem]) -> str:
        """Exporta items a CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"queue_export_{timestamp}.csv"
        filepath = self._export_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("url,status,title,channel,duration_seconds,file_size_mb,added_at\n")
                for item in items:
                    added = item.added_at.strftime("%Y-%m-%d %H:%M:%S") if item.added_at else ""
                    f.write(f'"{item.url}","{item.status.value}","{item.title}","{item.channel}",{item.duration_seconds},{item.file_size_mb},"{added}"\n')
            
            logger.info(f"Exportado CSV: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error exportando CSV: {e}")
            return ""

    def get_audit_history(self, limit: int = 50) -> List[Dict]:
        """Obtiene el historial de auditorías."""
        if hasattr(self.audit_logger, 'get_history'):
            return self.audit_logger.get_history(limit)
        return []

    def get_trash_status(self) -> Dict[str, Any]:
        """Retorna el estado de la papelera."""
        return {
            "items_count": len(self.trash_bin.get_items()),
            "timeout_seconds": self._trash_timeout_seconds,
            "time_since_clear": time.time() - self._last_clear_time if self._last_clear_time > 0 else 0
        }


class _FallbackSnapshotManager:
    """Fallback si no está disponible el módulo real."""
    def __init__(self, snapshot_dir):
        self.snapshot_dir = snapshot_dir
    
    def create_snapshot(self, items, cleared_items, strategy):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.snapshot_dir / f"snapshot_{timestamp}.json"
        data = {
            "timestamp": timestamp,
            "strategy": strategy,
            "total_items": len(items),
            "cleared_items": [i.to_dict() for i in cleared_items]
        }
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return str(filepath)
        except:
            return None


class _FallbackStateValidator:
    """Fallback si no está disponible el módulo real."""
    def validate(self, items):
        return {"valid": True, "items": items}


class _FallbackAuditLogger:
    """Fallback si no está disponible el módulo real."""
    def __init__(self, data_dir):
        self.data_dir = data_dir
    
    def log_clear_action(self, **kwargs):
        pass
    
    def get_history(self, limit=50):
        return []


class _FallbackTrashBin:
    """Fallback si no está disponible el módulo real."""
    def __init__(self, timeout_seconds=60):
        self._items = []
        self._timeout = timeout_seconds
    
    def add_items(self, items):
        self._items = items
    
    def get_items(self):
        return self._items
    
    def clear(self):
        self._items = []


class _FallbackPartialStrategy:
    """Fallback si no está disponible el módulo real."""
    def apply(self, items, percentage):
        count = len(items) * percentage // 100
        return items[:count]


class _FallbackProtectedMarker:
    """Fallback si no está disponible el módulo real."""
    def mark(self, items, indices):
        for i in indices:
            if i < len(items):
                items[i].is_protected = True
    
    def unmark(self, items, indices):
        for i in indices:
            if i < len(items):
                items[i].is_protected = False


class _FallbackSizeConditional:
    """Fallback si no está disponible el módulo real."""
    def filter_by_size(self, items, min_mb):
        return [i for i in items if i.file_size_mb >= min_mb]


def create_queue_intelligence(data_dir: Optional[str] = None) -> QueueIntelligence:
    """
    Factory function para crear una instancia de QueueIntelligence.
    
    Uso:
        queue_intel = create_queue_intelligence()
        queue_intel.clear_queue(...)
    """
    return QueueIntelligence(data_dir=data_dir)