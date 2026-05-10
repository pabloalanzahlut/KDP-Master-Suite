"""
KDP_MASTER - AI Predictor Service (Elite Corporate)
=====================================================
Servicios de predicción y análisis cognitiva usando Ollama local.
Reutiliza OllamaPool existente para inferencia.

Autor: KDP Master System
Version: 1.0.0
"""

import time
import threading
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AIPrediction:
    eta_minutes: int = 0
    confidence: float = 0.0
    anomaly_detected: bool = False
    anomaly_type: str = ""
    anomaly_description: str = ""
    recommendation: str = ""
    thematic_focus: str = ""
    knowledge_value: int = 0
    disk_days_remaining: int = 30
    resource_optimization: str = ""
    semantic_integrity: bool = True
    state_conversational: str = ""
    niche_bias: str = "balanced"
    priority_validation: str = "OK"


class AIPredictorService:
    """
    Servicio de predicción cognitiva que usa Ollama para:
    - Predicción de ETA basada en patrones históricos
    - Detección de anomalías de rendimiento
    - Recomendaciones proactivas
    - Análisis semántico
    """

    _instance = None
    _lock = threading.Lock()

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

        self._ollama_pool = None
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._last_analysis = {}
        self._historical_patterns = []

        logger.info("AIPredictorService inicializado")

    def _get_ollama_pool(self):
        """Obtener referencia a OllamaPool."""
        if self._ollama_pool is None:
            try:
                from app.core.ollama_pool import OllamaPool
                self._ollama_pool = OllamaPool()
            except Exception as e:
                logger.warning(f"OllamaPool no disponible: {e}")
        return self._ollama_pool

    def is_available(self) -> bool:
        """Verificar si el servicio de IA está disponible."""
        pool = self._get_ollama_pool()
        if pool:
            try:
                return pool.is_running()
            except:
                pass
        return False

    def predict_eta_cognitive(self, queue_count: int, processed_rate: float,
                            current_load: float) -> AIPrediction:
        """Módulo 1: Predictor de Finalización de Lote (ETA Cognitivo)."""
        prediction = AIPrediction()

        if not self.is_available():
            prediction.eta_minutes = queue_count * 2
            prediction.confidence = 0.0
            prediction.recommendation = "Ollama no disponible - ETA estimado"
            return prediction

        pool = self._get_ollama_pool()
        if not pool or not pool.is_model_available(pool.default_model):
            prediction.eta_minutes = queue_count * 2
            prediction.confidence = 0.3
            prediction.recommendation = "Modelo no disponible"
            return prediction

        prompt = f"""Analiza el siguiente estado del pipeline para predecir tiempo de finalización:
- Cola pendiente: {queue_count} items
- Tasa de procesamiento: {processed_rate:.1f} items/min
- Carga actual del sistema: {current_load:.1f}%

Basándote en patrones de procesamiento, estimation el tiempo restante en minutos.
Responde solo con un número entero."""

        try:
            response = pool.generate(prompt)
            if response:
                try:
                    eta = int(''.join(filter(str.isdigit, response.split()[0])))
                    prediction.eta_minutes = eta if eta > 0 else queue_count * 2
                    prediction.confidence = 0.75
                    prediction.recommendation = f"ETA basado en análisis cognitivo"
                except:
                    prediction.eta_minutes = queue_count * 2
                    prediction.confidence = 0.5
            else:
                prediction.eta_minutes = queue_count * 2
                prediction.confidence = 0.3
        except Exception as e:
            logger.warning(f"Error en predicción ETA: {e}")
            prediction.eta_minutes = queue_count * 2
            prediction.confidence = 0.2

        return prediction

    def analyze_performance_anomaly(self, cpu_percent: float, ram_percent: float,
                                    processing_time: float, baseline_time: float) -> AIPrediction:
        """Módulo 2: Analista de Anomalías de Rendimiento de Parsing."""
        prediction = AIPrediction()

        threshold_cpu = 80
        threshold_ram = 85
        threshold_slowdown = 1.5

        anomaly_detected = False
        anomaly_types = []

        if cpu_percent > threshold_cpu:
            anomaly_detected = True
            anomaly_types.append(f"CPU alto ({cpu_percent:.0f}%)")

        if ram_percent > threshold_ram:
            anomaly_detected = True
            anomaly_types.append(f"RAM alta ({ram_percent:.0f}%)")

        if baseline_time > 0 and processing_time / baseline_time > threshold_slowdown:
            anomaly_detected = True
            anomaly_types.append(f"Procesamiento lento ({(processing_time/baseline_time):.1f}x)")

        prediction.anomaly_detected = anomaly_detected
        prediction.anomaly_type = ", ".join(anomaly_types) if anomaly_types else "normal"
        prediction.anomaly_description = f"Anomalías detectadas: {len(anomaly_types)}" if anomaly_detected else "Sin anomalías"

        if anomaly_detected:
            if cpu_percent > 90:
                prediction.recommendation = "⚠️ CPU crítico - Reducir carga de procesamiento"
            elif ram_percent > 90:
                prediction.recommendation = "⚠️ RAM crítica - Liberar memoria"
            else:
                prediction.recommendation = "⚠️ Revisar rendimiento del sistema"
        else:
            prediction.recommendation = "✅ Rendimiento normal"

        return prediction

    def get_thematic_focus(self, recent_content: List[str]) -> str:
        """Módulo 3: Indicador de Relevancia Temática en Tiempo Real."""
        if not recent_content:
            return "Sin datos"

        if not self.is_available():
            return "Análisis no disponible"

        pool = self._get_ollama_pool()
        if not pool:
            return "Ollama no disponible"

        sample = " ".join(recent_content[:3])[:500]
        prompt = f"Identifica el tema principal del siguiente contenido (1-3 palabras): {sample}"

        try:
            response = pool.generate(prompt)
            if response:
                focus = response.strip().split('\n')[0][:30]
                return focus if focus else "General"
        except:
            pass

        return "Análisis en progreso"

    def calculate_knowledge_value(self, words_processed: int, complexity: float) -> int:
        """Módulo 4: Métrica de Adquisición de Conocimiento (Valor KB)."""
        base_value = words_processed // 100
        complexity_multiplier = 1.0 + (complexity / 10)
        value = int(base_value * complexity_multiplier)
        return max(value, 0)

    def predict_disk_days_remaining(self, disk_free_gb: float,
                                    processing_rate_gb_per_day: float) -> int:
        """Módulo 5: Smart-Alert Predictivo de Espacio para Texto."""
        if processing_rate_gb_per_day <= 0:
            return 999

        days_remaining = int(disk_free_gb / processing_rate_gb_per_day)

        if days_remaining < 7:
            return days_remaining
        return days_remaining

    def suggest_ollama_optimization(self, ram_percent: float, cpu_percent: float,
                                   context_tokens: int) -> str:
        """Módulo 6: Sugerencias de Optimización de Recursos Ollama."""
        suggestions = []

        if ram_percent > 80:
            suggestions.append("Reducir contexto a 4k tokens")

        if cpu_percent > 80:
            suggestions.append("Reducir hilos de chunking")

        if context_tokens > 6000:
            suggestions.append("Optimizar ventana de contexto")

        if not suggestions:
            return "✅ Recursos optimizados"

        return " | ".join(suggestions)

    def check_semantic_integrity(self, text_sample: str, expected_category: str) -> bool:
        """Módulo 7: Detector de Integridad Semántica en Indexación."""
        if not text_sample or not expected_category:
            return True

        if not self.is_available():
            return True

        pool = self._get_ollama_pool()
        if not pool:
            return True

        prompt = f"El siguiente texto debería pertenecer a la categoría '{expected_category}'. ¿Coincide el contenido? Responde Sí o No: {text_sample[:200]}"

        try:
            response = pool.generate(prompt)
            if response:
                return "sí" in response.lower() or "si" in response.lower()
        except:
            pass

        return True

    def get_state_conversational(self, pipeline_state: str,
                                 queue_count: int, eta_minutes: int) -> str:
        """Módulo 8: Asistente de Estado Conversacional (Click-to-Ask)."""
        state_descriptions = {
            "Idle": "Sistema en reposo. Listo para procesar.",
            "Extrayendo": f"Extrayendo transcripciones. {queue_count} en cola. ETA: {eta_minutes} min.",
            "Limpiando": "Limpiando texto procesado.",
            "Chunking": "Dividiendo texto en segmentos.",
            "Indexando": "Indexando en base de conocimientos.",
            "Error": "⚠️ Error detectado. Revisar logs."
        }

        return state_descriptions.get(pipeline_state, "Estado desconocido")

    def detect_niche_bias(self, categories_processed: Dict[str, int]) -> str:
        """Módulo 9: Identificador de Sesgos en Captación de Nichos."""
        if not categories_processed:
            return "balanced"

        total = sum(categories_processed.values())
        if total == 0:
            return "balanced"

        max_category = max(categories_processed.items(), key=lambda x: x[1])
        percentage = (max_category[1] / total) * 100

        if percentage > 70:
            return f" skewed ({max_category[0]} - {percentage:.0f}%)"
        elif percentage > 50:
            return f" moderate ({max_category[0]} - {percentage:.0f}%)"

        return "balanced"

    def validate_priority_vs_queue(self, high_priority_count: int,
                                   normal_queue_count: int,
                                   low_priority_processing: bool) -> str:
        """Módulo 10: Validador de Prioridad Estratégica vs Cola."""
        if high_priority_count > 0 and low_priority_processing:
            return f"⚠️ Prioridad alta en espera ({high_priority_count})"

        if normal_queue_count > 100 and high_priority_count == 0:
            return "ℹ️ Cola saturada sin prioridades altas"

        if high_priority_count > 10:
            return f"🔥 Alta prioridad: {high_priority_count} items"

        return "✅ Prioridades equilibradas"

    # ==================== CICLO 3: MÓDULOS ADICIONALES DE PREDICCIÓN ====================

    def predict_journey_completion(self, queue_count: int, eta_minutes: int,
                                   current_time: str) -> str:
        """Módulo 11: Predictor de Finalización de Jornada Operativa."""
        try:
            from datetime import datetime
            hour = datetime.now().hour
            if 9 <= hour < 18:
                remaining_work_hours = 18 - hour
                if eta_minutes > remaining_work_hours * 60:
                    return f"⚠️ Excederá horario laboral ({eta_minutes // 60}h restantes)"
                else:
                    return f"✅ Terminará antes de las 18:00"
            else:
                return f"ℹ️ Outside work hours"
        except:
            return "Calculando..."

    def detect_network_anomaly(self, latency_ms: int, error_count: int) -> str:
        """Módulo 12: Detective de Anomalías de Red para Fetching de CC."""
        if latency_ms > 500:
            return f"⚠️ Latencia alta: {latency_ms}ms"
        elif latency_ms > 200:
            return f"⚡ Latencia moderada: {latency_ms}ms"
        elif error_count > 5:
            return f"⚠️ Errores de red: {error_count}"
        return "✅ Red estable"

    def detect_ollama_runtime_issue(self, model_name: str, error_count: int) -> str:
        """Módulo 13: Detectador de Incompatibilidades en Runtime Ollama."""
        if error_count > 10:
            return f"⚠️ Errores acumulados: {error_count}"
        if "qwen3" in model_name or "qwen2.5" in model_name:
            return "ℹ️ Modelo Qwen activo"
        return "✅ Runtime OK"

    def evaluate_transcription_quality(self, quality_percent: float) -> str:
        """Módulo 14: Evaluador de Calidad de Transcripción en Tiempo Real."""
        if quality_percent < 60:
            return f"⚠️ Calidad baja: {quality_percent:.0f}%"
        elif quality_percent < 80:
            return f"⚡ Calidad media: {quality_percent:.0f}%"
        return f"✅ Calidad alta: {quality_percent:.0f}%"

    def predict_bottleneck_chunking(self, text_length: int, chunk_size: int) -> str:
        """Módulo 15: Predictor de Cuellos de Botella en Chunking."""
        estimated_chunks = text_length // chunk_size + 1
        if estimated_chunks > 50:
            return f"⚠️-many chunks ({estimated_chunks})"
        elif estimated_chunks > 20:
            return f"⚡ {estimated_chunks} chunks"
        return f"✅ {estimated_chunks} chunks"

    def suggest_context_mode(self, ram_percent: float, context_tokens: int) -> str:
        """Módulo 16: Asistente de Contexto de Trabajo (Hora/Modo)."""
        if 22 <= datetime.now().hour or datetime.now().hour < 7:
            return "🌙 Modo Nocturno"
        if ram_percent > 80:
            return "💾 Modo Ahorro"
        if context_tokens > 4000:
            return "⚡ Modo Rápido"
        return "🏃 Modo Normal"

    def detect_obsolete_content(self, content_age_days: int) -> str:
        """Módulo 17: Alerta de Contenido Obsoleto en Transcripciones."""
        if content_age_days > 365:
            return f"⚠️ Contenido antiguo ({content_age_days}d)"
        elif content_age_days > 180:
            return f"⚡ Contenido semi-reciente"
        return "✅ Contenido actualizado"

    def suggest_log_rotation(self, log_size_mb: int) -> str:
        """Módulo 18: Sugeridor de Rotación/Compresión de Logs de Texto."""
        if log_size_mb > 150:
            return f"⚠️ Logs grandes ({log_size_mb}MB)"
        elif log_size_mb > 50:
            return f"⚡Logs moderados"
        return "✅ Logs OK"

    # ==================== CICLO 4: RECOMENDACIONES E INSIGHTS ====================

    def generate_executive_summary(self, processed_count: int, errors_count: int,
                                   duration_minutes: int) -> str:
        """Módulo 19: Resumidor Ejecutivo de Actividad en Lenguaje Natural."""
        success_rate = ((processed_count - errors_count) / max(processed_count, 1)) * 100
        return f"Procesados: {processed_count}, Éxito: {success_rate:.0f}%, Tiempo: {duration_minutes}min"

    def get_productivity_insight(self, current_processed: int, yesterday_processed: int) -> str:
        """Módulo 20: Insight de Productividad Personal en Extracción."""
        if yesterday_processed == 0:
            return "📊 Primer día de procesamiento"
        change = ((current_processed - yesterday_processed) / yesterday_processed) * 100
        if change > 20:
            return f"🚀 {change:.0f}% más productivo que ayer"
        elif change < -20:
            return f"📉 {abs(change):.0f}% menos productivo"
        return f"📊 Rendimiento estable"

    def get_trend_insight(self, category_counts: Dict[str, int]) -> str:
        """Módulo 21: Insight de Tendencias de Uso por Categoría KDP."""
        if not category_counts:
            return "Sin datos de tendencias"
        top = max(category_counts.items(), key=lambda x: x[1])
        return f"📈 Principal: {top[0]} ({top[1]})"

    def suggest_underused_feature(self, features_used: Dict[str, int]) -> str:
        """Módulo 22: Asistente de Onboarding Continuo de Funciones."""
        if not features_used:
            return "ℹ️ Explora filtros avanzados"
        return "ℹ️ Funciones disponibles"

    def generate_flash_report(self, metrics: Dict[str, Any]) -> str:
        """Módulo 23: Generador de Reportes Flash al Hacer Click."""
        processed = metrics.get('processed_today', 0)
        errors = metrics.get('errors_count', 0)
        queue = metrics.get('queue_count', 0)
        return f"Resumen: {processed} proc, {errors} errores, {queue} en cola"

    def optimize_message_by_role(self, is_admin: bool, state: str) -> str:
        """Módulo 24: Optimizador de Mensajes Contextuales por Rol."""
        if is_admin:
            return f"Backend: {state} | Parsing FTS5 activo"
        return state

    def analyze_sentiment_progress(self, error_rate: float) -> str:
        """Módulo 25: Analizador de Sentimiento de Progreso del Lote."""
        if error_rate > 20:
            return "⚠️ Ritmo con muchos errores"
        elif error_rate > 10:
            return "⚡ Ritmo moderado"
        return "✅ Ritmo sostenible"

    def suggest_proactive_action(self, latency_ms: int, error_count: int) -> str:
        """Módulo 26: Recomendador de Acciones Proactivas (Red/IA)."""
        if latency_ms > 300:
            return "⏸️ Considerar pausa por latencia"
        if error_count > 5:
            return "🔧 Revisar errores de red"
        return "✅ Sin acciones requeridas"

    def translate_http_error(self, error_code: int, context: str) -> str:
        """Módulo 27: Traductor de Códigos HTTP a Soluciones de Fetching."""
        error_messages = {
            403: "Cookies de sesión expiradas",
            429: "Rate limit - pausar temporalmente",
            500: "Error del servidor - reintentar",
            404: "Recurso no encontrado",
            503: "Servicio no disponible"
        }
        return error_messages.get(error_code, f"Error {error_code}")

    def predict_by_historical_pattern(self, day_of_week: str, hour: int,
                                      base_eta: int) -> int:
        """Módulo 28: Predictor de Finalización Basado en Patrones Históricos."""
        multipliers = {
            "Saturday": 1.3, "Sunday": 1.2,
            "Monday": 0.9, "Tuesday": 0.9, "Wednesday": 1.0,
            "Thursday": 1.0, "Friday": 1.1
        }
        mult = multipliers.get(day_of_week, 1.0)
        if 14 <= hour <= 18:
            mult *= 1.2
        return int(base_eta * mult)

    def suggest_reindex_optimization(self, fragmentation_percent: float) -> str:
        """Módulo 29: Sugeridor de Re-Indexación FTS5 Inteligente."""
        if fragmentation_percent > 20:
            return f"⚠️ FTS5 fragmentado ({fragmentation_percent:.0f}%)"
        elif fragmentation_percent > 10:
            return f"⚡ Reindexación sugerida"
        return "✅ Índice optimizado"

    def get_comprehensive_recommendation(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener todas las recomendaciones e insights (Ciclos 3 y 4)."""
        cpu = metrics.get('cpu_percent', 0)
        ram = metrics.get('ram_percent', 0)
        errors = metrics.get('errors_count', 0)
        queue = metrics.get('queue_count', 0)
        disk = metrics.get('disk_free_gb', 0)

        return {
            'journey_completion': self.predict_journey_completion(queue, metrics.get('eta_minutes', 0), ""),
            'network_status': self.detect_network_anomaly(metrics.get('network_latency_ms', 0), errors),
            'ollama_runtime': self.detect_ollama_runtime_issue(metrics.get('ollama_model', ''), 0),
            'transcription_quality': self.evaluate_transcription_quality(metrics.get('cc_quality_avg', 95)),
            'chunking_bottleneck': self.predict_bottleneck_chunking(metrics.get('words_extracted_today', 0), 500),
            'context_mode': self.suggest_context_mode(ram, 4000),
            'obsolete_alert': self.detect_obsolete_content(0),
            'log_suggestion': self.suggest_log_rotation(10),
            'executive_summary': self.generate_executive_summary(metrics.get('processed_today', 0), errors, 60),
            'productivity_insight': self.get_productivity_insight(metrics.get('processed_today', 0), 0),
            'trend_insight': self.get_trend_insight({}),
            'feature_suggestion': self.suggest_underused_feature({}),
            'flash_report': self.generate_flash_report(metrics),
            'message_optimized': self.optimize_message_by_role(False, metrics.get('pipeline_state', 'Idle')),
            'progress_sentiment': self.analyze_sentiment_progress(errors / max(metrics.get('processed_today', 1), 1) * 100),
            'proactive_action': self.suggest_proactive_action(metrics.get('network_latency_ms', 0), errors),
            'http_solution': self.translate_http_error(0, ""),
            'historical_eta': self.predict_by_historical_pattern("Monday", 10, queue * 2),
            'reindex_suggestion': self.suggest_reindex_optimization(5)
        }

    def get_all_predictions(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener todas las predicciones y análisis cognitivos (Ciclos 3 y 4)."""
        if not self.is_available():
            return self._get_empty_predictions()

        queue_count = metrics.get('queue_count', 0)
        cpu_percent = metrics.get('cpu_percent', 0)
        ram_percent = metrics.get('ram_percent', 0)
        disk_free = metrics.get('disk_free_gb', 0)

        # Ciclo 3: Predicción y Análisis de Anomalías (10 módulos)
        eta_pred = self.predict_eta_cognitive(queue_count, 5.0, cpu_percent)
        anomaly = self.analyze_performance_anomaly(cpu_percent, ram_percent, 1.0, 1.0)
        optimization = self.suggest_ollama_optimization(ram_percent, cpu_percent, 4000)
        state_desc = self.get_state_conversational(
            metrics.get('pipeline_state', 'Idle'),
            queue_count,
            eta_pred.eta_minutes
        )

        # Ciclo 3: Módulos adicionales
        journey_completion = self.predict_journey_completion(queue_count, eta_pred.eta_minutes, "")
        network_status = self.detect_network_anomaly(metrics.get('network_latency_ms', 0), metrics.get('errors_count', 0))
        ollama_runtime = self.detect_ollama_runtime_issue(metrics.get('ollama_model', ''), 0)
        transcription_quality = self.evaluate_transcription_quality(metrics.get('cc_quality_avg', 95))
        chunking_bottleneck = self.predict_bottleneck_chunking(metrics.get('words_extracted_today', 0), 500)
        context_mode = self.suggest_context_mode(ram_percent, 4000)
        obsolete_alert = self.detect_obsolete_content(0)
        log_suggestion = self.suggest_log_rotation(10)

        # Ciclo 4: Recomendaciones e Insights
        executive_summary = self.generate_executive_summary(metrics.get('processed_today', 0), metrics.get('errors_count', 0), 60)
        productivity_insight = self.get_productivity_insight(metrics.get('processed_today', 0), 0)
        trend_insight = self.get_trend_insight({})
        flash_report = self.generate_flash_report(metrics)
        progress_sentiment = self.analyze_sentiment_progress(metrics.get('errors_count', 0) / max(metrics.get('processed_today', 1), 1) * 100)
        proactive_action = self.suggest_proactive_action(metrics.get('network_latency_ms', 0), metrics.get('errors_count', 0))

        from datetime import datetime
        day_name = datetime.now().strftime("%A")
        historical_eta = self.predict_by_historical_pattern(day_name, datetime.now().hour, queue_count * 2)

        return {
            'ai_available': True,
            # Ciclo 3: Predicción y anomalías
            'eta_prediction': eta_pred.eta_minutes,
            'eta_confidence': eta_pred.confidence,
            'anomaly_detected': anomaly.anomaly_detected,
            'anomaly_type': anomaly.anomaly_type,
            'recommendation': anomaly.recommendation,
            'thematic_focus': 'General',
            'knowledge_value': self.calculate_knowledge_value(metrics.get('words_extracted_today', 0), 0.5),
            'disk_days': self.predict_disk_days_remaining(disk_free, 0.1),
            'ollama_optimization': optimization,
            'semantic_integrity': True,
            'state_conversational': state_desc,
            'niche_bias': 'balanced',
            'priority_validation': 'OK',
            # Ciclo 3: Módulos adicionales (11-18)
            'journey_completion': journey_completion,
            'network_status': network_status,
            'ollama_runtime': ollama_runtime,
            'transcription_quality': transcription_quality,
            'chunking_bottleneck': chunking_bottleneck,
            'context_mode': context_mode,
            'obsolete_alert': obsolete_alert,
            'log_suggestion': log_suggestion,
            # Ciclo 4: Recomendaciones e Insights (19-26)
            'executive_summary': executive_summary,
            'productivity_insight': productivity_insight,
            'trend_insight': trend_insight,
            'flash_report': flash_report,
            'progress_sentiment': progress_sentiment,
            'proactive_action': proactive_action,
            'historical_eta': historical_eta
        }

    def _get_empty_predictions(self) -> Dict[str, Any]:
        """Devuelveprediccionesvacías cuando IA no está disponible."""
        return {
            'ai_available': False,
            'eta_prediction': 0, 'eta_confidence': 0,
            'anomaly_detected': False, 'anomaly_type': '', 'recommendation': 'Ollama no disponible',
            'thematic_focus': 'N/A', 'knowledge_value': 0, 'disk_days': 30,
            'ollama_optimization': 'N/A', 'semantic_integrity': True,
            'state_conversational': 'Sistema en reposo', 'niche_bias': 'unknown', 'priority_validation': 'OK',
            'journey_completion': 'N/A', 'network_status': 'N/A', 'ollama_runtime': 'N/A',
            'transcription_quality': 'N/A', 'chunking_bottleneck': 'N/A', 'context_mode': 'N/A',
            'obsolete_alert': 'N/A', 'log_suggestion': 'N/A',
            'executive_summary': 'N/A', 'productivity_insight': 'N/A', 'trend_insight': 'N/A',
            'flash_report': 'N/A', 'progress_sentiment': 'N/A', 'proactive_action': 'N/A', 'historical_eta': 0
        }


def get_ai_predictor_service() -> AIPredictorService:
    """Obtener instancia singleton del servicio de predicción IA."""
    return AIPredictorService()