"""
KDP MASTER - Base Data Classes
==========================
Modelos de datos base para el Gateway de Pre-Ingesta.
"""

import json
import hashlib
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List


class QueuePriority(Enum):
    """Niveles de prioridad para la cola."""
    ALTA = 3
    MEDIA = 2
    BAJA = 1


class QueueState(Enum):
    """Estados del item en la cola."""
    PENDIENTE = "pendiente"
    VALIDANDO = "validando"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    FALLIDO = "fallido"
    DUPLICADO = "duplicado"
    BLOQUEADO = "bloqueado"


class ContentType(Enum):
    """Tipos de contenido origen."""
    VIDEO_SINGLE = "video_single"
    PLAYLIST = "playlist"
    CHANNEL = "channel"
    UNKNOWN = "unknown"


@dataclass
class QueueItem:
    """Item básico de la cola de pre-ingesta."""
    url: str
    source: str = "manual"
    priority: QueuePriority = QueuePriority.MEDIA
    state: QueueState = QueueState.PENDIENTE
    
    video_id: Optional[str] = None
    title: Optional[str] = None
    channel_name: Optional[str] = None
    category: Optional[str] = None
    
    relevance_score: float = 0.0
    strategic_score: float = 0.0
    value_score: float = 0.0
    
    estimated_duration: int = 0
    estimated_size_mb: float = 0.0
    
    compliance_status: str = "pending"
    compliance_issues: List[str] = field(default_factory=list)
    
    key_points: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    
    metadata_tags: Dict[str, Any] = field(default_factory=dict)
    project_label: Optional[str] = None
    
    error_message: Optional[str] = None
    retry_count: int = 0
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    processed_at: Optional[str] = None
    
    content_type: ContentType = ContentType.UNKNOWN
    
    _hash: Optional[str] = field(default_factory=None, repr=False)
    
    def __post_init__(self):
        if not self._hash:
            self._hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Genera hash único para el item."""
        content = f"{self.url}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()[:16]
    
    @property
    def hash_id(self) -> str:
        """ID único del item."""
        if not self._hash:
            self._hash = self._generate_hash()
        return self._hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['state'] = self.state.value
        data['content_type'] = self.content_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueItem':
        """Crea instancia desde diccionario."""
        if 'priority' in data and isinstance(data['priority'], int):
            data['priority'] = QueuePriority(data['priority'])
        if 'state' in data and isinstance(data['state'], str):
            data['state'] = QueueState(data['state'])
        if 'content_type' in data and isinstance(data['content_type'], str):
            data['content_type'] = ContentType(data['content_type'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serializa a JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'QueueItem':
        """Crea instancia desde JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class IngestaResult:
    """Resultado del proceso de pre-ingesta."""
    success: bool
    item: Optional[QueueItem] = None
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    modules_passed: List[str] = field(default_factory=list)
    modules_failed: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'item': self.item.to_dict() if self.item else None,
            'message': self.message,
            'warnings': self.warnings,
            'errors': self.errors,
            'modules_passed': self.modules_passed,
            'modules_failed': self.modules_failed,
            'processing_time_ms': self.processing_time_ms
        }