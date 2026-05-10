"""
KDP MASTER - Priority Manager (Módulo 2)
====================================
Sistema de priorización dinámica de la cola.
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime

from ..pre_ingesta.base import QueueItem, QueuePriority


class PriorityEngine:
    """Módulo 2: Motor de priorización dinámica."""
    
    FACTOR_VIEW_COUNT = 0.25
    FACTOR_RECENT = 0.20
    FACTOR_DURATION = 0.15
    FACTOR_CHANNEL = 0.20
    FACTOR_MANUAL = 0.20
    
    def __init__(self):
        self.manual_overrides = {}
    
    def calculate_priority(self, item: QueueItem, video_metadata: Optional[dict] = None) -> QueuePriority:
        """Calcula la prioridad basada en factores."""
        score = 0.0
        
        item_priority = item.priority.value * self.FACTOR_MANUAL
        score += item_priority
        
        if video_metadata:
            view_count = video_metadata.get('view_count', 0)
            if view_count > 1000000:
                score += self.FACTOR_VIEW_COUNT * 3
            elif view_count > 100000:
                score += self.FACTOR_VIEW_COUNT * 2
            elif view_count > 10000:
                score += self.FACTOR_VIEW_COUNT * 1
            
            duration_sec = video_metadata.get('duration', 0)
            if 300 <= duration_sec <= 1800:
                score += self.FACTOR_DURATION * 2
            
            upload_date = video_metadata.get('upload_date')
            if upload_date:
                try:
                    if isinstance(upload_date, str):
                        upload_dt = datetime.strptime(upload_date, '%Y%m%d')
                    else:
                        upload_dt = upload_date
                    
                    days_old = (datetime.now() - upload_dt).days
                    if days_old < 7:
                        score += self.FACTOR_RECENT * 3
                    elif days_old < 30:
                        score += self.FACTOR_RECENT * 2
                    elif days_old < 90:
                        score += self.FACTOR_RECENT * 1
                except Exception:
                    pass
        
        if score >= 2.5:
            return QueuePriority.ALTA
        elif score >= 1.5:
            return QueuePriority.MEDIA
        else:
            return QueuePriority.BAJA
    
    def set_manual_priority(self, url: str, priority: QueuePriority):
        """Sobrescribe prioridad manual."""
        self.manual_overrides[url] = priority
    
    def get_priority(self, url: str) -> Optional[QueuePriority]:
        """Obtiene prioridad manual."""
        return self.manual_overrides.get(url)
    
    def reorder_by_priority(self, items: List[QueueItem]) -> List[QueueItem]:
        """Reordena lista por prioridad."""
        priority_map = {QueuePriority.ALTA: 3, QueuePriority.MEDIA: 2, QueuePriority.BAJA: 1}
        
        return sorted(items, key=lambda x: (priority_map.get(x.priority, 0), x.created_at), reverse=True)