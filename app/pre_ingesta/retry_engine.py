"""
KDP MASTER - Retry Engine (Módulo 11)
===================================
Sistema de reintentos inteligente con backoff exponencial.
"""

import time
import random
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class RetryStrategy(Enum):
    """Estrategias de reintento."""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


class RetryEngine:
    """Módulo 11: Sistema de reintentos con backoff."""
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0
    DEFAULT_MAX_DELAY = 60.0
    
    def __init__(self):
        self.retry_history: Dict[str, Dict[str, Any]] = {}
        self.error_patterns = {}
    
    def should_retry(self, url: str, error_type: str, attempt: int, 
                max_retries: int = DEFAULT_MAX_RETRIES) -> bool:
        """
        Determina si debe reintentar.
        """
        if attempt >= max_retries:
            return False
        
        non_retryable = ['auth', 'permission', 'quota_exceeded']
        if any(pattern in error_type.lower() for pattern in non_retryable):
            return False
        
        return True
    
    def calculate_delay(self, attempt: int, base_delay: float = DEFAULT_BASE_DELAY,
                   strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                   max_delay: float = DEFAULT_MAX_DELAY) -> float:
        """
        Calcula delay con backoff.
        """
        if strategy == RetryStrategy.FIXED:
            return base_delay
        
        elif strategy == RetryStrategy.LINEAR:
            return base_delay * attempt
        
        elif strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (2 ** (attempt - 1))
            jitter = random.uniform(0, delay * 0.1)
            return min(delay + jitter, max_delay)
        
        elif strategy == RetryStrategy.FIBONACCI:
            a, b = 1, 1
            for _ in range(attempt - 1):
                a, b = b, a + b
            return min(base_delay * b, max_delay)
        
        return base_delay
    
    def execute_with_retry(self, func: Callable, url: str, 
                          max_retries: int = DEFAULT_MAX_RETRIES,
                          base_delay: float = DEFAULT_BASE_DELAY) -> tuple:
        """
        Ejecuta función con retry.
        Returns: (success, result, error)
        """
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                result = func()
                return True, result, None
            
            except Exception as e:
                last_error = str(e)
                
                if not self.should_retry(url, type(e).__name__, attempt, max_retries):
                    return False, None, last_error
                
                delay = self.calculate_delay(attempt, base_delay)
                time.sleep(delay)
        
        return False, None, last_error
    
    def record_attempt(self, url: str, success: bool, error: Optional[str] = None):
        """Registra intento en historial."""
        if url not in self.retry_history:
            self.retry_history[url] = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'last_error': None,
                'last_attempt': None
            }
        
        history = self.retry_history[url]
        history['attempts'] += 1
        
        if success:
            history['successes'] += 1
        else:
            history['failures'] += 1
            history['last_error'] = error
        
        history['last_attempt'] = datetime.now().isoformat()
    
    def get_stats(self, url: str) -> Dict[str, Any]:
        """Obtiene estadísticas de reintentos."""
        return self.retry_history.get(url, {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'last_error': None
        })
    
    def clear_history(self, url: Optional[str] = None):
        """Limpia historial."""
        if url:
            self.retry_history.pop(url, None)
        else:
            self.retry_history.clear()


def create_retry_engine() -> RetryEngine:
    """Factory function."""
    return RetryEngine()