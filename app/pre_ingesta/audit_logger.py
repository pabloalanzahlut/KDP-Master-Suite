"""
KDP MASTER - Audit Logger (Módulo 10)
===================================
Registro de auditoría de ingesta.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


class AuditLogger:
    """Módulo 10: Registro de auditoría de ingesta."""
    
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or self._get_default_path()
        self._ensure_directory()
    
    def _get_default_path(self) -> str:
        """Obtiene path por defecto."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data', 'logs')
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'pre_ingesta_audit.log')
    
    def _ensure_directory(self):
        """Asegura directorio."""
        dir_path = os.path.dirname(self.log_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
    
    def log(self, action: str, user: str = "system", source: str = "manual",
           url: str = "", details: Optional[Dict[str, Any]] = None) -> str:
        """
        Registra evento de auditoría.
        Returns: trace_id
        """
        trace_id = str(uuid4())[:8]
        
        entry = {
            'trace_id': trace_id,
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user': user,
            'source': source,
            'url': url,
            'details': details or {}
        }
        
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception:
            pass
        
        return trace_id
    
    def log_add_to_queue(self, url: str, source: str = "manual", user: str = "system",
                      success: bool = True, items_count: int = 1) -> str:
        """Log específico para añadir a cola."""
        return self.log(
            action="ADD_TO_QUEUE",
            source=source,
            url=url,
            details={
                'success': success,
                'items_count': items_count,
                'user': user
            }
        )
    
    def log_validation(self, url: str, validation_results: list, passed: bool) -> str:
        """Log de validación."""
        return self.log(
            action="VALIDATION",
            url=url,
            details={
                'passed': passed,
                'results': validation_results
            }
        )
    
    def log_error(self, action: str, error_message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """Log de error."""
        return self.log(
            action=action,
            details={
                'error': error_message,
                **(details or {})
            }
        )
    
    def get_recent_logs(self, count: int = 100) -> list:
        """Obtiene logs recientes."""
        if not os.path.exists(self.log_path):
            return []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            logs = []
            for line in lines[-count:]:
                try:
                    logs.append(json.loads(line.strip()))
                except Exception:
                    pass
            
            return logs
        
        except Exception:
            return []
    
    def get_user_activity(self, user: str = "system") -> list:
        """Obtiene actividad por usuario."""
        all_logs = self.get_recent_logs(1000)
        return [log for log in all_logs if log.get('user') == user]


def create_audit_logger(path: Optional[str] = None) -> AuditLogger:
    """Factory function."""
    return AuditLogger(path)