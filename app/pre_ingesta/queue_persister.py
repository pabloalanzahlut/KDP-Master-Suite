"""
KDP MASTER - Queue Persister (Módulo 8)
====================================
Persistencia atómica de cola.
"""

import json
import os
import shutil
from typing import List, Optional
from datetime import datetime

from ..pre_ingesta.base import QueueItem


class QueuePersister:
    """Módulo 8: Persistencia atómica de cola."""
    
    def __init__(self, queue_path: Optional[str] = None):
        self.queue_path = queue_path or self._get_default_path()
        self.backup_path = self.queue_path + '.bak'
        self._ensure_directory()
    
    def _get_default_path(self) -> str:
        """Obtiene path por defecto."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data', 'queue')
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'pre_ingesta_queue.json')
    
    def _ensure_directory(self):
        """Asegura que existe el directorio."""
        dir_path = os.path.dirname(self.queue_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
    
    def save(self, items: List[QueueItem]) -> bool:
        """
        Guarda cola de forma atómica.
        1. Escribe a archivo temporal
        2. Renombra a archivo final
        """
        try:
            temp_path = self.queue_path + '.tmp'
            
            data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'item_count': len(items),
                'items': [item.to_dict() for item in items]
            }
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(self.queue_path):
                shutil.copy2(self.queue_path, self.backup_path)
            
            shutil.move(temp_path, self.queue_path)
            
            return True
        
        except Exception as e:
            if os.path.exists(self.backup_path):
                shutil.move(self.backup_path, self.queue_path)
            return False
    
    def load(self) -> List[QueueItem]:
        """Carga cola desde archivo."""
        if not os.path.exists(self.queue_path):
            return []
        
        try:
            with open(self.queue_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items_data = data.get('items', [])
            items = [QueueItem.from_dict(d) for d in items_data]
            
            return items
        
        except Exception:
            if os.path.exists(self.backup_path):
                try:
                    with open(self.backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    items_data = data.get('items', [])
                    items = [QueueItem.from_dict(d) for d in items_data]
                    return items
                except Exception:
                    pass
        
        return []
    
    def append(self, item: QueueItem) -> bool:
        """Añade item a cola existente."""
        items = self.load()
        items.append(item)
        return self.save(items)
    
    def remove(self, item_hash: str) -> bool:
        """Remove item por hash."""
        items = self.load()
        items = [i for i in items if i.hash_id != item_hash]
        return self.save(items)
    
    def clear(self) -> bool:
        """Limpia cola."""
        return self.save([])
    
    def get_backup_path(self) -> str:
        """Obtiene path del backup."""
        return self.backup_path
    
    def restore_from_backup(self) -> bool:
        """Restaura desde backup."""
        if not os.path.exists(self.backup_path):
            return False
        
        try:
            shutil.copy2(self.backup_path, self.queue_path)
            return True
        except Exception:
            return False


def create_persister(path: Optional[str] = None) -> QueuePersister:
    """Factory function."""
    return QueuePersister(path)