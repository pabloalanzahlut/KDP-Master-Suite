"""
AI Analysis - Wrapper Base para Ollama Local
=============================================
Wrapper centralizado para usar Ollama en módulos de IA cognición textual.
Integra con OllamaPool existente de app/core/.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OllamaProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass
class AIAnalysisResult:
    success: bool
    content: str
    score: float
    metadata: Dict[str, Any]
    error: Optional[str] = None
    processing_time_ms: float = 0.0
    model_used: Optional[str] = None


class OllamaAIClient:
    """
    Wrapper base para Ollama local - Módulo 21-40
    Proporciona interface unificada para análisis de IA.
    """

    DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")

    SYSTEM_PROMPTS = {
        "density": "Eres un clasificador de densidad informativa. Analiza el texto y asigna un score 1-10 basado en utilidad para nicho KDP. Responde SOLO con JSON: {\"score\": X, \"reason\": \"...\"}",
        "noise": "Eres un detector de ruido vs señal. Identifica si el texto es contenido educativo real o spam/promocional. Responde SOLO con JSON: {\"signal\": true/false, \"reason\": \"...\"}",
        "chunk": "Eres un chunker inteligente. Divide el texto en segmentos óptimos por ideas. Responde SOLO con JSON: {\"chunks\": [\"...\"], \"count\": N}",
        "jargon": "Eres un traductor de jerga técnica a términos KDP estándar. Responde SOLO con JSON: {\"translated\": \"...\", \"terms_mapped\": N}",
        "ner": "Eres un extractor de entidades nombradas. Identifica herramientas, plataformas, métricas y personas. Responde SOLO con JSON: {\"entities\": [{\"type\": \"...\", \"value\": \"...\"}]}",
        "type": "Eres un clasificador de tipo de contenido. Determina si es Tutorial, Caso de Estudio, Teoría, Lista, Entrevista. Responde SOLO con JSON: {\"type\": \"...\", \"confidence\": X}",
        "manual": "Eres un predictor de valor para manual. Evalúa si el contenido merece ser incluido en Legalidad, Fórmulas o Matriz. Responde SOLO con JSON: {\"manual\": \"...\", \"priority\": \"high/medium/low\"}",
        "bias": "Eres un detector de sesgo en fuente. Alerta si hay tono promocional excesivo. Responde SOLO con JSON: {\"biased\": true/false, \"reason\": \"...\"}",
        "tags": "Eres un generador de tags semánticos. Crea 5-10 tags relevantes basados en contenido real. Responde SOLO con JSON: {\"tags\": [\"...\"], \"count\": N}",
        "coherence": "Eres un validador de coherencia temática. Verifica que el texto mantenga foco en un solo tema. Responde SOLO con JSON: {\"coherent\": true/false, \"focus\": \"...\"}",
        "fusion": "Eres un asistente de fusión con contenido existente. Sugiere cómo integrar con KB. Responde SOLO con JSON: {\"action\": \"fuse/complement/separate\", \"reason\": \"...\"}",
        "plagiarism": "Eres un detectivo de plagio interno. Compara con KB existente. Responde SOLO con JSON: {\"duplicate\": true/false, \"similarity\": X}",
        "summary": "Eres un generador de resumen ejecutivo. Crea abstract de 3 líneas. Responde SOLO con JSON: {\"summary\": \"...\", \"key_points\": [\"...\"]}",
        "urgency": "Eres un clasificador de urgencia de procesamiento. Decide si procesar ahora o en lote nocturno. Responde SOLO con JSON: {\"urgency\": \"now/batch\", \"reason\": \"...\"}",
        "error": "Eres un traductor de errores de extracción a soluciones. Responde SOLO con JSON: {\"solution\": \"...\", \"action\": \"...\"}",
        "time": "Eres un predictor de tiempo de chunking. Estima minutos necesarios. Responde SOLO con JSON: {\"estimated_minutes\": X, \"factors\": [\"...\"]}",
        "stale": "Eres un detectivo de información obsoleta. Alerta si hay fechas/políticas desactualizadas. Responde SOLO con JSON: {\"stale\": true/false, \"outdated_items\": [\"...\"]}",
        "quiz": "Eres un generador de preguntas de validación. Crea 3 preguntas quiz. Responde SOLO con JSON: {\"questions\": [{\"q\": \"...\", \"a\": \"...\"}]}",
        "action": "Eres un recomendador de acción post-extracción. Sugiere indexar, revisar o descartar. Responde SOLO con JSON: {\"action\": \"index/review/discard\", \"reason\": \"...\"}",
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 180
    ):
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self._available = self._check_availability()
        self._stats = {
            'total_calls': 0,
            'successful': 0,
            'failed': 0,
            'total_latency_ms': 0.0
        }

    def _check_availability(self) -> bool:
        """Verifica si Ollama está disponible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama no disponible: {e}")
            return False

    def is_available(self) -> bool:
        """Retorna si Ollama está disponible."""
        return self._available

    def analyze(
        self,
        text: str,
        analysis_type: str,
        custom_prompt: Optional[str] = None
    ) -> AIAnalysisResult:
        """
        Ejecuta análisis de IA en texto.

        Args:
            text: Texto a analizar
            analysis_type: Tipo de análisis (density, noise, chunk, etc.)
            custom_prompt: Prompt personalizado (opcional)

        Returns:
            AIAnalysisResult con resultado del análisis
        """
        import time
        start_time = time.time()

        self._stats['total_calls'] += 1

        if not self._available:
            return AIAnalysisResult(
                success=False,
                content="",
                score=0.0,
                metadata={},
                error="Ollama no disponible",
                processing_time_ms=time.time() - start_time
            )

        system_prompt = custom_prompt or self.SYSTEM_PROMPTS.get(
            analysis_type,
            "Analiza el siguiente texto y responde en JSON."
        )

        truncated_text = text[:4000]

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\nTexto:\n{truncated_text}",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 512
                    }
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '').strip()

                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    parsed = {"raw": content}

                latency = time.time() - start_time
                self._stats['successful'] += 1
                self._stats['total_latency_ms'] += latency * 1000

                return AIAnalysisResult(
                    success=True,
                    content=content,
                    score=parsed.get('score', parsed.get('confidence', 0.5)),
                    metadata=parsed,
                    processing_time_ms=latency * 1000,
                    model_used=self.model
                )
            else:
                self._stats['failed'] += 1
                return AIAnalysisResult(
                    success=False,
                    content="",
                    score=0.0,
                    metadata={},
                    error=f"HTTP {response.status_code}",
                    processing_time_ms=time.time() - start_time
                )

        except requests.exceptions.Timeout:
            self._stats['failed'] += 1
            return AIAnalysisResult(
                success=False,
                content="",
                score=0.0,
                metadata={},
                error="Timeout esperando respuesta de Ollama",
                processing_time_ms=time.time() - start_time
            )
        except Exception as e:
            self._stats['failed'] += 1
            logger.error(f"Ollama error: {e}")
            return AIAnalysisResult(
                success=False,
                content="",
                score=0.0,
                metadata={},
                error=str(e),
                processing_time_ms=time.time() - start_time
            )

    def batch_analyze(
        self,
        texts: List[str],
        analysis_type: str,
        callback: Optional[Callable] = None
    ) -> List[AIAnalysisResult]:
        """
        Ejecuta análisis en lote.

        Args:
            texts: Lista de textos a analizar
            analysis_type: Tipo de análisis
            callback: Callback para cada resultado (opcional)

        Returns:
            Lista de AIAnalysisResult
        """
        results = []

        for text in texts:
            result = self.analyze(text, analysis_type)
            results.append(result)

            if callback:
                callback(result)

        return results

    def get_stats(self) -> Dict:
        """Retorna estadísticas del cliente."""
        stats = self._stats.copy()
        if stats['total_calls'] > 0:
            stats['success_rate'] = stats['successful'] / stats['total_calls']
            stats['avg_latency_ms'] = stats['total_latency_ms'] / stats['total_calls']
        else:
            stats['success_rate'] = 0.0
            stats['avg_latency_ms'] = 0.0
        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_calls': 0,
            'successful': 0,
            'failed': 0,
            'total_latency_ms': 0.0
        }


def create_ai_client(
    base_url: Optional[str] = None,
    model: Optional[str] = None
) -> OllamaAIClient:
    """
    Factory function para crear cliente IA.
    """
    return OllamaAIClient(base_url=base_url, model=model)


def quick_analyze(text: str, analysis_type: str) -> AIAnalysisResult:
    """
    Función de conveniencia para análisis rápido.
    """
    client = OllamaAIClient()
    return client.analyze(text, analysis_type)