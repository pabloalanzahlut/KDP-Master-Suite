"""
OllamaPool - Elite Premium Corporate
Pool centralizado para gestión de Ollama con auto-inicio, balanceo, métricas y API interna.

Autor: KDP Master System
Version: 1.0.0
"""

import os
import sys
import socket
import shutil
import logging
import threading
import time
import json
import requests
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# ==================== CONFIGURACIÓN ====================

DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
DEFAULT_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))

OLLAMA_PATHS = [
    os.path.expandvars("%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe"),
    os.path.expandvars("%PROGRAMFILES%\\Ollama\\ollama.exe"),
    os.path.join(os.environ.get("USERPROFILE", ""), ".local", "bin", "ollama.exe"),
    "ollama.exe"
]

# ==================== DATA CLASSES ====================

@dataclass
class ModelInfo:
    name: str
    size: int
    modified_at: str
    family: str
    parameter_size: str
    quantization: str

@dataclass
class PoolMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    by_model: Dict[str, int] = field(default_factory=dict)

@dataclass
class HealthStatus:
    is_running: bool
    api_available: bool
    models_count: int
    last_check: str
    uptime_seconds: float = 0

# ==================== NIVEL 1: BÁSICO ====================

class OllamaPool:
    """
    Pool centralizado para Ollama - Nivel 1: Básico
    Funcionalidades de auto-inicio y verificación.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # --- Singleton ---
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Configuración
        self.base_url = DEFAULT_BASE_URL
        self.default_model = DEFAULT_MODEL
        self.timeout = DEFAULT_TIMEOUT
        self._process = None
        self._start_time = None
        
        # Estado del pool
        self._models: Dict[str, ModelInfo] = {}
        self._metrics = PoolMetrics()
        self._cache: Dict[str, tuple] = {}  # prompt -> (response, timestamp)
        
        # Thread safety
        self._request_lock = threading.Lock()
        self._cache_lock = threading.Lock()
        self._metrics_lock = threading.Lock()
        
        # Circuit breaker
        self._circuit_open = False
        self._circuit_last_failure = 0
        self._circuit_retry_after = 30
        
        # API Server
        self._api_server = None
        self._api_thread = None
        
        # Logs
        self._logs: List[Dict] = []
        self._logs_lock = threading.Lock()
        
        logger.info(f"OllamaPool inicializado - URL: {self.base_url}, Modelo: {self.default_model}")
    
    # ==================== NIVEL 1: DETECCIÓN E INSTALACIÓN ====================
    
    def is_installed(self) -> bool:
        """Nivel 1 - Detectar si Ollama está instalado."""
        for path in OLLAMA_PATHS:
            if os.path.exists(path):
                return True
        return shutil.which("ollama.exe") is not None or shutil.which("ollama") is not None
    
    def get_install_path(self) -> Optional[str]:
        """Nivel 1 - Obtener ruta del ejecutable."""
        for path in OLLAMA_PATHS:
            if os.path.exists(path):
                return path
        found = shutil.which("ollama.exe") or shutil.which("ollama")
        if found:
            return found
        return None
    
    # ==================== NIVEL 1: VERIFICACIÓN DE SERVICIO ====================
    
    def is_running(self) -> bool:
        """Nivel 1 - Verificar si el servicio está corriendo."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 11434))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _auto_start_ollama(self) -> bool:
        """Nivel 1 - Auto-iniciar Ollama si no está corriendo."""
        if self.is_running():
            return True
        
        ollama_cmd = self.get_install_path()
        if not ollama_cmd:
            logger.warning("Ollama no encontrado en rutas conocidas")
            return False
        
        try:
            import subprocess
            self._process = subprocess.Popen(
                [ollama_cmd, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            # Esperar a que-start
            for _ in range(10):
                time.sleep(1)
                if self.is_running():
                    self._start_time = datetime.now()
                    logger.info("Ollama iniciado automáticamente")
                    return True
            logger.warning("Ollama no respondió después de 10 segundos")
            return False
        except Exception as e:
            logger.error(f"Error al iniciar Ollama: {e}")
            return False
    
    def start_service(self) -> bool:
        """Nivel 1 - Iniciar servicio (punto de entrada público)."""
        return self._auto_start_ollama()
    
    def health_check(self) -> HealthStatus:
        """Nivel 1 - Verificar salud del servicio."""
        is_running = self.is_running()
        api_available = False
        models_count = 0
        
        if is_running:
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    api_available = True
                    data = response.json()
                    models_count = len(data.get("models", []))
            except Exception:
                pass
        
        uptime = 0
        if self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()
        
        return HealthStatus(
            is_running=is_running,
            api_available=api_available,
            models_count=models_count,
            last_check=datetime.now().isoformat(),
            uptime_seconds=uptime
        )
    
    # ==================== NIVEL 1: MODELOS ====================
    
    def get_available_models(self) -> List[ModelInfo]:
        """Nivel 1 - Listar modelos disponibles."""
        if not self.is_running():
            return []
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = []
                for m in response.json().get("models", []):
                    details = m.get("details", {})
                    models.append(ModelInfo(
                        name=m.get("name", ""),
                        size=m.get("size", 0),
                        modified_at=m.get("modified_at", ""),
                        family=details.get("family", details.get("format", "unknown")),
                        parameter_size=details.get("parameter_size", "unknown"),
                        quantization=details.get("quantization_level", "unknown")
                    ))
                self._models = {m.name: m for m in models}
                return models
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
        return []
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Nivel 1 - Obtener info de un modelo específico."""
        if not self._models:
            self.get_available_models()
        return self._models.get(model)
    
    def get_default_model(self) -> str:
        """Nivel 1 - Obtener modelo por defecto."""
        return self.default_model
    
    def set_default_model(self, model: str) -> bool:
        """Nivel 1 - Establecer modelo por defecto."""
        if model in self._models or self.is_model_available(model):
            self.default_model = model
            return True
        return False
    
    def is_model_available(self, model: str) -> bool:
        """Nivel 1 - Verificar si un modelo está disponible."""
        if not self._models:
            self.get_available_models()
        return model in self._models
    
    # ==================== HELPER: LOGS ====================
    
    def _add_log(self, level: str, message: str, data: Dict = None):
        """Añadir entrada al log."""
        with self._logs_lock:
            self._logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "data": data or {}
            })
            # Mantener solo últimos 500
            if len(self._logs) > 500:
                self._logs = self._logs[-500:]
    
    # ==================== METADATOS ====================
    
    def get_info(self) -> Dict:
        """Obtener información general del pool."""
        health = self.health_check()
        return {
            "version": "1.0.0",
            "is_installed": self.is_installed(),
            "install_path": self.get_install_path(),
            "is_running": health.is_running,
            "api_available": health.api_available,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "available_models": len(self._models),
            "uptime_seconds": health.uptime_seconds,
            "last_check": health.last_check
        }
    
    def get_dashboard_stats(self) -> Dict:
        """Nivel 4 - Stats para dashboard."""
        health = self.health_check()
        with self._metrics_lock:
            metrics = {
                "total_requests": self._metrics.total_requests,
                "successful": self._metrics.successful_requests,
                "failed": self._metrics.failed_requests,
                "avg_latency": self._metrics.total_latency / max(self._metrics.total_requests, 1),
                "cache_hits": self._metrics.cache_hits,
                "cache_misses": self._metrics.cache_misses,
                "by_model": self._metrics.by_model.copy()
            }
        
        return {
            "health": {
                "is_running": health.is_running,
                "api_available": health.api_available,
                "models_count": health.models_count,
                "uptime_seconds": health.uptime_seconds
            },
            "metrics": metrics,
            "models": [
                {"name": m.name, "size_mb": m.size / (1024*1024), "family": m.family}
                for m in self._models.values()
            ],
            "cache_size": len(self._cache),
            "circuit_breaker": {
                "is_open": self._circuit_open,
                "last_failure": self._circuit_last_failure
            }
        }
    
    def get_logs(self, count: int = 100) -> List[Dict]:
        """Nivel 4 - Obtener logs recientes."""
        with self._logs_lock:
            return self._logs[-count:]


# ==================== NIVEL 2: POOL BÁSICO ====================
    
    # ==================== GENERACIÓN BÁSICA ====================
    
    def _do_generate(self, prompt: str, model: str, timeout: int = None) -> Optional[Dict]:
        """Nivel 2 - Realizar generación real a Ollama."""
        if self._circuit_open:
            # Check si podemos reintentar
            if time.time() - self._circuit_last_failure > self._circuit_retry_after:
                self._circuit_open = False
                self._add_log("INFO", "Circuit breaker: reintentando")
            else:
                return None
        
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=timeout or self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "model": model,
                    "done": result.get("done", True),
                    "duration": result.get("total_duration", 0) / 1e9
                }
            else:
                self._circuit_last_failure = time.time()
                self._add_log("WARNING", f"Generate failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self._circuit_last_failure = time.time()
            self._add_log("WARNING", "Generate timeout")
        except Exception as e:
            self._circuit_last_failure = time.time()
            self._add_log("ERROR", f"Generate error: {e}")
        
        return None
    
    def generate(self, prompt: str, model: str = None) -> Optional[str]:
        """Nivel 2 - Generación básica."""
        model = model or self.default_model
        
        if not self.is_running():
            self._add_log("WARNING", "Ollama no disponible")
            return None
        
        result = self._do_generate(prompt, model)
        
        with self._metrics_lock:
            self._metrics.total_requests += 1
            if result:
                self._metrics.successful_requests += 1
                self._metrics.by_model[model] = self._metrics.by_model.get(model, 0) + 1
            else:
                self._metrics.failed_requests += 1
        
        return result.get("response") if result else None
    
    # ==================== GENERACIÓN CON RETRY ====================
    
    def generate_with_retry(self, prompt: str, model: str = None, max_retries: int = 3) -> Optional[str]:
        """Nivel 2 - Generación con retry exponencial."""
        model = model or self.default_model
        
        if not self.is_running():
            self._add_log("WARNING", "Ollama no disponible para retry")
            return None
        
        for attempt in range(max_retries):
            result = self._do_generate(prompt, model)
            
            if result:
                with self._metrics_lock:
                    self._metrics.total_requests += 1
                    self._metrics.successful_requests += 1
                    self._metrics.by_model[model] = self._metrics.by_model.get(model, 0) + 1
                return result.get("response")
            
            # Espera exponencial: 1s, 2s, 4s
            wait_time = 2 ** attempt
            self._add_log("INFO", f"Retry {attempt + 1}/{max_retries}, esperando {wait_time}s")
            time.sleep(wait_time)
        
        with self._metrics_lock:
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1
        
        self._circuit_open = True
        self._add_log("ERROR", f"Fallo después de {max_retries} intentos")
        return None
    
    # ==================== FALLBACK ENTRE MODELOS ====================
    
    def generate_with_fallback(self, prompt: str, preferred_model: str = None, 
                                 fallback_models: List[str] = None) -> Optional[str]:
        """Nivel 2 - Fallback automático entre modelos."""
        preferred_model = preferred_model or self.default_model
        fallback_models = fallback_models or []
        
        models_to_try = [preferred_model] + [m for m in fallback_models if m != preferred_model]
        
        for model in models_to_try:
            if not self.is_model_available(model):
                continue
            
            self._add_log("INFO", f"Intentando modelo: {model}")
            result = self._do_generate(prompt, model)
            
            if result:
                with self._metrics_lock:
                    self._metrics.total_requests += 1
                    self._metrics.successful_requests += 1
                    self._metrics.by_model[model] = self._metrics.by_model.get(model, 0) + 1
                return result.get("response")
        
        with self._metrics_lock:
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1
        
        return None
    
    # ==================== GENERACIÓN POR LOTES ====================
    
    def batch_generate(self, prompts: List[str], model: str = None, 
                        max_workers: int = 3) -> List[Optional[str]]:
        """Nivel 2 - Generación por lotes con thread pool."""
        model = model or self.default_model
        
        if not self.is_running():
            return [None] * len(prompts)
        
        results = [None] * len(prompts)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(self._do_generate, p, model): i 
                for i, p in enumerate(prompts)
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    results[idx] = result.get("response") if result else None
                except Exception:
                    results[idx] = None
        
        with self._metrics_lock:
            self._metrics.total_requests += len(prompts)
            successful = sum(1 for r in results if r is not None)
            self._metrics.successful_requests += successful
            self._metrics.failed_requests += (len(prompts) - successful)
        
        return results
    
    # ==================== CONFIGURACIÓN ====================
    
    def set_timeout(self, seconds: int):
        """Nivel 2 - Configurar timeout."""
        self.timeout = max(10, min(seconds, 600))
    
    def get_timeout(self) -> int:
        """Nivel 2 - Obtener timeout actual."""
        return self.timeout
    
    def get_status(self) -> Dict:
        """Nivel 2 - Estado del pool."""
        health = self.health_check()
        
        with self._metrics_lock:
            metrics = {
                "total_requests": self._metrics.total_requests,
                "successful": self._metrics.successful_requests,
                "failed": self._metrics.failed_requests,
                "success_rate": self._metrics.successful_requests / max(self._metrics.total_requests, 1),
                "avg_latency": self._metrics.total_latency / max(self._metrics.total_requests, 1)
            }
        
        return {
            "health": {
                "running": health.is_running,
                "api_available": health.api_available,
                "models": health.models_count
            },
            "config": {
                "base_url": self.base_url,
                "default_model": self.default_model,
                "timeout": self.timeout
            },
            "metrics": metrics,
            "cache_size": len(self._cache),
            "circuit_breaker": "OPEN" if self._circuit_open else "CLOSED"
        }


# ==================== NIVEL 3: AVANZADO - ELITE PREMIUM ====================
    
    # ==================== SELECCIÓN AUTOMÁTICA DE MODELO ====================
    
    MODEL_TASKS = {
        "classification": ["qwen3:8b", "qwen2.5:14b", "llama3.1:8b"],
        "analysis": ["qwen3:14b", "qwen2.5:14b", "gemma3:12b"],
        "summarization": ["qwen3:8b", "phi4", "llama3.1:8b"],
        "generation": ["qwen3:14b", "gemma3:12b", "qwen2.5:14b"],
        "fast": ["deepseek-r1:1.5b", "phi3.5:latest", "phi4-mini-reasoning"],
        "reasoning": ["phi4", "deepseek-r1:1.5b", "qwen3:14b"],
        "coding": ["qwen2.5-coder:1.5b-base", "qwen3:8b", "phi4"],
        "default": ["qwen3:8b", "deepseek-r1:1.5b"]
    }
    
    def select_best_model(self, task_type: str = "default") -> Optional[str]:
        """Nivel 3 - Seleccionar mejor modelo según tipo de tarea."""
        candidates = self.MODEL_TASKS.get(task_type, self.MODEL_TASKS["default"])
        
        for model in candidates:
            if self.is_model_available(model):
                return model
        
        # Fallback al default
        return self.default_model
    
    def get_least_loaded_model(self) -> Optional[str]:
        """Nivel 3 - Seleccionar modelo con menos carga."""
        with self._metrics_lock:
            model_counts = self._metrics.by_model.copy()
        
        # Obtener todos los modelos disponibles
        if not self._models:
            self.get_available_models()
        
        # Excluir embeddings y modelos muy grandes
        skip_models = ["nomic-embed-text", "gemma3:12b", "qwen3:14b", "qwen2.5:14b", "phi4"]
        
        available = [m for m in self._models.keys() 
                     if not any(s in m for s in skip_models)]
        
        if not available:
            return self.default_model
        
        # Encontrar el menos usado
        min_count = float('inf')
        best_model = available[0]
        
        for model in available:
            count = model_counts.get(model, 0)
            if count < min_count:
                min_count = count
                best_model = model
        
        return best_model
    
    # ==================== MÉTRICAS ====================
    
    def get_metrics(self) -> Dict:
        """Nivel 3 - Obtener métricas detalladas."""
        with self._metrics_lock:
            total = self._metrics.total_requests
            success = self._metrics.successful_requests
            failed = self._metrics.failed_requests
            
            return {
                "total_requests": total,
                "successful_requests": success,
                "failed_requests": failed,
                "success_rate": success / max(total, 1),
                "avg_latency": self._metrics.total_latency / max(total, 1),
                "cache_hits": self._metrics.cache_hits,
                "cache_misses": self._metrics.cache_misses,
                "cache_hit_rate": self._metrics.cache_hits / max(
                    self._metrics.cache_hits + self._metrics.cache_misses, 1),
                "by_model": self._metrics.by_model.copy()
            }
    
    def reset_metrics(self):
        """Nivel 3 - Resetear métricas."""
        with self._metrics_lock:
            self._metrics = PoolMetrics()
        self._add_log("INFO", "Metricas reseteadas")
    
    def _record_latency(self, duration: float):
        """Nivel 3 - Registrar latencia."""
        with self._metrics_lock:
            self._metrics.total_latency += duration
    
    # ==================== CACHE ====================
    
    def _generate_cache_key(self, prompt: str, model: str) -> str:
        """Nivel 3 - Generar clave para cache."""
        import hashlib
        key = f"{model}:{prompt[:200]}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def cache_response(self, prompt: str, response: str, ttl: int = 3600):
        """Nivel 3 - Guardar respuesta en cache."""
        key = self._generate_cache_key(prompt, self.default_model)
        
        with self._cache_lock:
            self._cache[key] = (response, time.time() + ttl)
        
        self._add_log("INFO", f"Cache: guardando respuesta (TTL={ttl}s)")
    
    def get_cached_response(self, prompt: str, model: str = None) -> Optional[str]:
        """Nivel 3 - Obtener respuesta cacheada."""
        model = model or self.default_model
        key = self._generate_cache_key(prompt, model)
        
        with self._cache_lock:
            if key in self._cache:
                response, expiry = self._cache[key]
                if time.time() < expiry:
                    with self._metrics_lock:
                        self._metrics.cache_hits += 1
                    return response
                else:
                    del self._cache[key]
        
        with self._metrics_lock:
            self._metrics.cache_misses += 1
        
        return None
    
    def clear_cache(self):
        """Nivel 3 - Limpiar cache."""
        with self._cache_lock:
            self._cache.clear()
        self._add_log("INFO", "Cache limpiado")
    
    def get_cache_stats(self) -> Dict:
        """Nivel 3 - Stats del cache."""
        with self._cache_lock:
            expired = sum(1 for _, exp in self._cache.values() if time.time() >= exp)
            return {
                "total_entries": len(self._cache),
                "expired_entries": expired,
                "valid_entries": len(self._cache) - expired
            }
    
    # ==================== CIRCUIT BREAKER ====================
    
    def is_circuit_open(self) -> bool:
        """Nivel 3 - Verificar estado del circuit breaker."""
        if self._circuit_open:
            if time.time() - self._circuit_last_failure > self._circuit_retry_after:
                self._circuit_open = False
                self._add_log("INFO", "Circuit breaker: cerrado automaticamente")
                return False
            return True
        return False
    
    def reset_circuit_breaker(self):
        """Nivel 3 - Resetear circuit breaker."""
        self._circuit_open = False
        self._circuit_last_failure = 0
        self._add_log("INFO", "Circuit breaker reseteado")
    
    # ==================== PRIORITY QUEUE ====================
    
    def generate_with_priority(self, prompt: str, priority: str = "normal",
                               model: str = None) -> Optional[str]:
        """Nivel 3 - Generación con prioridad (high/normal/low)."""
        # Ajustar timeout según prioridad
        original_timeout = self.timeout
        
        if priority == "high":
            self.timeout = min(self.timeout, 30)  # Mas rapido para alta prioridad
        elif priority == "low":
            self.timeout = max(self.timeout, 300)  # Mas lento para baja prioridad
        
        try:
            result = self.generate(prompt, model)
            return result
        finally:
            self.timeout = original_timeout
    
    # ==================== GENERACIÓN CON CACHE ====================
    
    def generate_with_cache(self, prompt: str, model: str = None, 
                            use_cache: bool = True) -> Optional[str]:
        """Nivel 3 - Generación con cache opcional."""
        model = model or self.default_model
        
        if use_cache:
            cached = self.get_cached_response(prompt, model)
            if cached:
                self._add_log("INFO", "Cache: hit")
                return cached
        
        result = self.generate(prompt, model)
        
        if use_cache and result:
            self.cache_response(prompt, result)
        
        return result
    
    # ==================== MÉTRICAS AVANZADAS ====================
    
    def get_performance_report(self) -> Dict:
        """Nivel 3 - Reporte de rendimiento."""
        metrics = self.get_metrics()
        
        # Calcular percentiles aproximados
        with self._metrics_lock:
            model_stats = []
            for model, count in self._metrics.by_model.items():
                model_stats.append({
                    "model": model,
                    "requests": count,
                    "percentage": (count / max(self._metrics.total_requests, 1)) * 100
                })
        
        return {
            "summary": {
                "total_requests": metrics["total_requests"],
                "success_rate": f"{metrics['success_rate']*100:.1f}%",
                "avg_latency_ms": f"{metrics['avg_latency']*1000:.0f}"
            },
            "cache": {
                "hit_rate": f"{metrics['cache_hit_rate']*100:.1f}%",
                "hits": metrics["cache_hits"],
                "misses": metrics["cache_misses"]
            },
            "models": sorted(model_stats, key=lambda x: x["requests"], reverse=True),
            "circuit_breaker": {
                "is_open": self._circuit_open,
                "last_failure": self._circuit_last_failure
            }
        }


# ==================== NIVEL 4: CORPORATIVO - DASHBOARD Y API ====================
    
    # ==================== DASHBOARD STATS ====================
    
    def get_full_dashboard(self) -> Dict:
        """Nivel 4 - Dashboard completo."""
        health = self.health_check()
        metrics = self.get_metrics()
        cache_stats = self.get_cache_stats()
        
        return {
            "status": {
                "running": health.is_running,
                "api_available": health.api_available,
                "models_count": health.models_count,
                "uptime_seconds": health.uptime_seconds,
                "last_check": health.last_check
            },
            "config": {
                "base_url": self.base_url,
                "default_model": self.default_model,
                "timeout": self.timeout
            },
            "metrics": {
                "total_requests": metrics["total_requests"],
                "success_rate": f"{metrics['success_rate']*100:.1f}%",
                "avg_latency_ms": f"{metrics['avg_latency']*1000:.0f}",
                "by_model": metrics["by_model"]
            },
            "cache": cache_stats,
            "circuit_breaker": {
                "open": self._circuit_open,
                "last_failure": self._circuit_last_failure
            },
            "models": [
                {
                    "name": m.name,
                    "size_mb": round(m.size / (1024*1024), 1),
                    "family": m.family,
                    "parameters": m.parameter_size,
                    "quantization": m.quantization
                }
                for m in self._models.values()
            ],
            "logs_count": len(self._logs)
        }
    
    # ==================== API REST INTERNA ====================
    
    def start_api_server(self, port: int = 11435) -> bool:
        """Nivel 4 - Iniciar servidor API REST."""
        if self._api_server is not None:
            self._add_log("WARNING", "API server ya esta corriendo")
            return False
        
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import json
            
            pool = self  # Reference for handlers
            
            class OllamaAPIHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/health':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        health = pool.health_check()
                        self.wfile.write(json.dumps({
                            'status': 'ok' if health.is_running else 'error',
                            'running': health.is_running,
                            'api': health.api_available,
                            'models': health.models_count
                        }).encode())
                    
                    elif self.path == '/metrics':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(pool.get_metrics()).encode())
                    
                    elif self.path == '/models':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        models = pool.get_available_models()
                        self.wfile.write(json.dumps([{
                            'name': m.name,
                            'size_mb': round(m.size / (1024*1024), 1)
                        } for m in models]).encode())
                    
                    elif self.path == '/status':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(pool.get_status()).encode())
                    
                    elif self.path == '/dashboard':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(pool.get_full_dashboard()).encode())
                    
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def do_POST(self):
                    if self.path == '/generate':
                        content_length = int(self.headers.get('Content-Length', 0))
                        body = self.rfile.read(content_length)
                        data = json.loads(body)
                        
                        prompt = data.get('prompt', '')
                        model = data.get('model')
                        use_cache = data.get('use_cache', False)
                        
                        if use_cache:
                            response = pool.generate_with_cache(prompt, model)
                        else:
                            response = pool.generate(prompt, model)
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'response': response,
                            'model': model or pool.default_model
                        }).encode())
                    
                    elif self.path == '/stop':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        pool.stop_api_server()
                        self.wfile.write(json.dumps({'status': 'stopped'}).encode())
                    
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def log_message(self, format, *args):
                    pass  # Suppress logs
            
            self._api_server = HTTPServer(('127.0.0.1', port), OllamaAPIHandler)
            
            self._api_thread = threading.Thread(
                target=self._api_server.serve_forever,
                daemon=True
            )
            self._api_thread.start()
            
            self._add_log("INFO", f"API server iniciado en puerto {port}")
            return True
            
        except Exception as e:
            self._add_log("ERROR", f"Error iniciando API: {e}")
            return False
    
    def stop_api_server(self):
        """Nivel 4 - Detener servidor API."""
        if self._api_server:
            self._api_server.shutdown()
            self._api_server = None
            self._api_thread = None
            self._add_log("INFO", "API server detenido")
    
    def is_api_server_running(self) -> bool:
        """Nivel 4 - Verificar si API server está corriendo."""
        return self._api_server is not None
    
    # ==================== ALERTAS ====================
    
    def register_alert(self, name: str, condition_fn: Callable, callback: Callable):
        """Nivel 4 - Registrar una alerta."""
        if not hasattr(self, '_alerts'):
            self._alerts = []
        
        self._alerts.append({
            "name": name,
            "condition": condition_fn,
            "callback": callback,
            "triggered": False
        })
        self._add_log("INFO", f"Alerta registrada: {name}")
    
    def check_alerts(self) -> List[Dict]:
        """Nivel 4 - Verificar condiciones de alertas."""
        triggered = []
        
        if not hasattr(self, '_alerts'):
            return triggered
        
        metrics = self.get_metrics()
        
        for alert in self._alerts:
            try:
                if alert["condition"](metrics):
                    if not alert["triggered"]:
                        alert["triggered"] = True
                        alert["callback"](metrics)
                        triggered.append({
                            "name": alert["name"],
                            "timestamp": datetime.now().isoformat()
                        })
                        self._add_log("WARNING", f"Alerta activada: {alert['name']}")
            except Exception as e:
                self._add_log("ERROR", f"Error en alerta {alert['name']}: {e}")
        
        return triggered
    
    def get_alerts(self) -> List[Dict]:
        """Nivel 4 - Listar alertas registradas."""
        if not hasattr(self, '_alerts'):
            return []
        return [{"name": a["name"], "triggered": a["triggered"]} for a in self._alerts]
    
    def clear_alerts(self):
        """Nivel 4 - Limpiar alertas."""
        if hasattr(self, '_alerts'):
            self._alerts = []
        self._add_log("INFO", "Alertas limpiadas")
    
    # ==================== EXPORTAR CONFIGURACIÓN ====================
    
    def export_config(self) -> Dict:
        """Nivel 4 - Exportar configuración actual."""
        return {
            "base_url": self.base_url,
            "default_model": self.default_model,
            "timeout": self.timeout,
            "cache_ttl": 3600,
            "max_retries": 3,
            "circuit_breaker_timeout": self._circuit_retry_after,
            "batch_workers": 3,
            "api_port": 11435,
            "version": "1.0.0"
        }
    
    # ==================== UTILIDADES ====================
    
    def full_reset(self):
        """Nivel 4 - Reset completo del pool."""
        self.stop_api_server()
        self.clear_cache()
        self.reset_metrics()
        self.reset_circuit_breaker()
        self.clear_alerts()
        with self._logs_lock:
            self._logs.clear()
        self._add_log("INFO", "Pool reseteado completamente")
    
    def shutdown(self):
        """Nivel 4 - Apagar el pool completamente."""
        self.full_reset()
        OllamaPool._instance = None
        self._add_log("INFO", "OllamaPool apagado")


# ==================== INSTALACIÓN COMPLETA ====================
# Todos los niveles implementados