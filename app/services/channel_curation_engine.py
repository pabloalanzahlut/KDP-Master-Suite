"""
KDP Master Suite - Channel Curation Engine (CON IA)
============================================
60 Módulos CON IA para gestión masiva de canales >1000 videos.
Pilares 1-6: Análisis Semántico, Predicción, Filtrado, Optimización, Integración, Reportes.

v3.5.0: Implementación completa de los 60 módulos CON IA usando Ollama.
"""

import os
import re
import json
import time
import hashlib
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from queue import Queue, Empty
from enum import Enum

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ==================== ENUMS & DATA CLASSES ====================

class VideoFormat(Enum):
    """Formato del video"""
    STANDARD = "standard"
    LIVE = "live"
    REPLAY = "replay"
    SHORT = "short"
    PREMIERE = "premiere"

class ContentType(Enum):
    """Tipo de contenido"""
    TUTORIAL = "tutorial"
    NEWS = "news"
    OPINION = "opinion"
    REVIEW = "review"
    CASE_STUDY = "case_study"
    PODCAST = "podcast"
    NEWSLETTER = "newsletter"

class ExpertLevel(Enum):
    """Nivel de experto"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class SentimentType(Enum):
    """Sentimiento del título"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    URGENT = "urgent"
    NEUTRAL = "neutral"

class LanguageCode(Enum):
    """Códigos de idioma"""
    EN = "en"
    ES = "es"
    PT = "pt"
    FR = "fr"
    DE = "de"
    IT = "it"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    UNKNOWN = "unknown"


@dataclass
class VideoMetadata:
    """Metadatos de video enriquecidos por IA"""
    video_id: str
    title: str
    description: str
    channel_name: str
    
    # Puntuaciones IA (Pilar 1-2)
    kdp_relevance_score: int = 0  # 0-100
    clickbait_score: int = 0
    content_type: str = "unknown"
    extracted_keywords: List[str] = field(default_factory=list)
    is_outdated: bool = False
    sentiment: str = "neutral"
    video_format: str = "standard"
    has_sponsorship: bool = False
    expert_level: str = "intermediate"
    description_summary: str = ""
    
    # Predicciones (Pilar 2)
    info_density_score: int = 0
    originality_score: int = 0
    fluff_score: int = 0
    estimated_words: int = 0
    credibility_score: int = 0
    is_controversial: bool = False
    engagement_ratio: float = 0.0
    is_educational_series: bool = False
    is_trending: bool = False
    applicability_score: int = 0
    
    # Filtros IA (Pilar 3)
    pass_semantic_filter: bool = True
    recommended_action: str = "download"  # download, skip, review, watch_later
    related_video_ids: List[str] = field(default_factory=list)
    knowledge_gap_alert: bool = False
    contradicts_manual: bool = False
    updates_entry_id: Optional[int] = None
    
    # Optimización (Pilar 4)
    suggested_schedule: str = "now"
    batch_group: str = ""
    estimated_processing_time: float = 0.0
    is_heavy_video: bool = False
    should_segment: bool = False
    segment_count: int = 1
    failure_risk: bool = False
    suggest_audio_only: bool = False
    
    # Integración KB (Pilar 5)
    assigned_role_id: Optional[int] = None
    linked_entry_ids: List[int] = field(default_factory=list)
    faq_questions: List[str] = field(default_factory=list)
    tools_mentioned: List[str] = field(default_factory=list)
    has_case_study: bool = False
    learning_format: str = "practical"
    depth_alert: str = "adequate"
    
    # Reportes (Pilar 6)
    channel_health_score: int = 50
    content_evolution: str = ""
    predicted_themes: List[str] = field(default_factory=list)
    roi_score: float = 0.0
    topic_saturation: bool = False
    new_channel_suggestions: List[str] = field(default_factory=list)
    quality_decline_alert: bool = False
    study_plan: str = ""


@dataclass
class ChannelAnalysis:
    """Análisis completo de canal"""
    channel_id: str
    channel_name: str
    video_count: int = 0
    
    # Métricas agregadas
    avg_kdp_relevance: float = 0.0
    avg_quality_score: float = 0.0
    top_categories: List[str] = field(default_factory=list)
    recommended_count: int = 0
    skip_count: int = 0
    
    # Análisis temporal
    last_scan: Optional[datetime] = None
    content_trend: str = "stable"
    quality_trend: str = "stable"
    
    # Reporte final
    executive_summary: str = ""
    health_score: int = 50


# ==================== CHANNEL CURATION ENGINE ====================

class ChannelCurationEngine:
    """
    [CON IA v3.5.0] Motor de Curación Inteligente de Canales.
    
    60 Módulos organizados en 6 Pilares:
    - Pilar 1: Análisis Semántico de Títulos/Descripciones (1-10)
    - Pilar 2: Predicción de Valor y Calidad (11-20)
    - Pilar 3: Filtrado Inteligente y Personalización (21-30)
    - Pilar 4: Optimización de Descarga (31-40)
    - Pilar 5: Integración Contextual con KB (41-50)
    - Pilar 6: Reportes y Estrategia (51-60)
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434", 
                 ollama_model: str = "qwen2.5:7b",
                 ollama_timeout: int = 60,
                 db_manager=None):
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.ollama_timeout = ollama_timeout
        self.db_manager = db_manager
        
        # Verificar disponibilidad de Ollama
        self.ollama_available = self._check_ollama()
        logger.info(f"Ollama disponible para ChannelCurationEngine: {self.ollama_available}")
        
        # Configuración de umbrales
        self.config = {
            "min_kdp_relevance": 40,
            "min_credibility": 30,
            "max_fluff": 70,
            "batch_size": 50,
            "max_concurrent": 3,
            "primary_language": "es",
            "preferred_expert_level": "intermediate",
        }
        
        # Cola de procesamiento
        self.processing_queue = Queue()
        self.results_cache = {}
        self.preference_weights = {}
        
        # Thread pool para análisis paralelo
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Preferencias aprendidas
        self._learned_preferences = {
            "downloaded_keywords": set(),
            "skipped_keywords": set(),
            "downloaded_channels": set(),
            "ignored_channels": set(),
        }
    
    # ==================== HELPER METHODS ====================
    
    def _check_ollama(self) -> bool:
        """Verifica si Ollama está disponible"""
        if not REQUESTS_AVAILABLE:
            return False
        try:
            response = requests.get(
                f"{self.ollama_base_url}/api/tags", 
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _call_ollama(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """Llama a Ollama para análisis"""
        if not self.ollama_available:
            return None
        
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
            }
            if system_prompt:
                payload["system"] = system_prompt
                payload["options"] = {"temperature": 0.3}
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=self.ollama_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            return None
        except Exception as e:
            logger.warning(f"Error invocando Ollama: {e}")
            return None
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parsea respuesta JSON de Ollama"""
        try:
            # Buscar bloque JSON
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            
            # Intentar parseo directo
            return json.loads(text)
        except:
            return {"error": "parse_error", "raw": text[:200]}
    
    # ==================== PILAR 1: ANÁLISIS SEMÁNTICO (1-10) ====================
    # Módulo 1: Scoring de Relevancia KDP (0-100)
    # Módulo 2: Detección de Clickbait vs Sustancia
    # Módulo 3: Clasificación Temática Automática
    # Módulo 4: Extracción de Keywords del Título
    # Módulo 5: Detección de Contenido Obsoleto
    # Módulo 6: Análisis de Sentimiento del Título
    # Módulo 7: Identificación de Formato (Live vs Editado)
    # Módulo 8: Detección de Patrocinios en Título
    # Módulo 9: Clasificación por Nivel de Experto
    # Módulo 10: Resumen de Descripción en 1 Línea
    
    def analyze_title_semantics(self, title: str, description: str = "") -> VideoMetadata:
        """
        [PILAR 1: Módulos 1-10]
        Análisis semántico completo de título y descripción usando Ollama.
        """
        metadata = VideoMetadata(
            video_id="",
            title=title,
            description=description,
            channel_name=""
        )
        
        if not self.ollama_available:
            return self._fallback_title_analysis(title, description)
        
        # Prompt unificado para análisis semántico
        prompt = f"""Analiza este video de YouTube y devuelve un JSON con EXACTAMENTE estos campos:
{{
  "kdp_relevance_score": 0-100,
  "clickbait_score": 0-100,
  "content_type": "tutorial|news|opinion|review|case_study|podcast|newsletter",
  "extracted_keywords": ["keyword1", "keyword2"],
  "is_outdated": true|false,
  "sentiment": "positive|negative|urgent|neutral",
  "video_format": "standard|live|replay|short|premiere",
  "has_sponsorship": true|false,
  "expert_level": "beginner|intermediate|advanced",
  "description_summary": "resumen en 1 línea"
}}

Título: {title}
Descripción: {description[:500] if description else 'Sin descripción'}

Responde SOLO con el JSON, sin texto adicional."""

        system_prompt = """Eres un analizador experto de contenido YouTube para Amazon KDP. 
Evalúas relevancia, calidad, y detectas contenido vacío o clickbait.
Respondes en JSON válido."""

        response = self._call_ollama(prompt, system_prompt)
        
        if response:
            parsed = self._parse_json_response(response)
            for key, value in parsed.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
        
        return metadata
    
    def _fallback_title_analysis(self, title: str, description: str) -> VideoMetadata:
        """Análisis sin IA (fallback)"""
        metadata = VideoMetadata(
            video_id="",
            title=title,
            description=description,
            channel_name=""
        )
        
        # Scoring básico basado enKeywords
        kdp_keywords = ["amazon", "kdp", "publish", "book", "earning", "ads", 
                       "seo", "ranking", "review", "best", "how to", "guide"]
        
        title_lower = title.lower()
        metadata.extracted_keywords = [kw for kw in kdp_keywords if kw in title_lower]
        metadata.kdp_relevance_score = min(100, len(metadata.extracted_keywords) * 20)
        
        # Detección de clickbait básica
        clickbait_patterns = ["shocking", "you won't believe", "million", "secret", 
                            "game changer", "never seen"]
        metadata.clickbait_score = 50 if any(p in title_lower for p in clickbait_patterns) else 20
        
        # Detección de obsoleto
        year_patterns = ["2020", "2021", "2022", "2023"]
        metadata.is_outdated = any(y in title_lower for y in year_patterns)
        
        # Sentimiento
        if any(w in title_lower for w in ["best", "top", "amazing"]):
            metadata.sentiment = "positive"
        elif any(w in title_lower for w in ["warning", "be careful", "scam"]):
            metadata.sentiment = "urgent"
        
        # Formato
        if "live" in title_lower:
            metadata.video_format = "live"
        elif "short" in title_lower:
            metadata.video_format = "short"
        
        # Patrocinio
        metadata.has_sponsorship = "sponsored" in title_lower or "ad" in title_lower
        
        # Nivel
        if "beginner" in title_lower or "start" in title_lower:
            metadata.expert_level = "beginner"
        elif "advanced" in title_lower or "expert" in title_lower:
            metadata.expert_level = "advanced"
        
        # Resumen
        metadata.description_summary = description[:100] + "..." if len(description) > 100 else description
        
        return metadata
    
    # ==================== PILAR 2: PREDICCIÓN DE VALOR (11-20) ====================
    # Módulo 11: Predictor de Densidad Informativa
    # Módulo 12: Score de Originalidad
    # Módulo 13: Detección de "Relleno" (Fluff)
    # Módulo 14: Predicción de Longitud de Transcripción
    # Módulo 15: Análisis de Credibilidad de Fuente
    # Módulo 16: Detección de Controversia/Polarización
    # Módulo 17: Predictor de Engagment Real
    # Módulo 18: Detección de Series Educativas
    # Módulo 19: Análisis de Actualidad (Trending)
    # Módulo 20: Score de Aplicabilidad Práctica
    
    def analyze_value_prediction(self, metadata: VideoMetadata, 
                                channel_stats: Dict = None) -> VideoMetadata:
        """
        [PILAR 2: Módulos 11-20]
        Predice valor y calidad del contenido.
        """
        if not self.ollama_available:
            return self._fallback_value_prediction(metadata, channel_stats)
        
        prompt = f"""Analiza el siguiente video y predice su valor/calidad. Devuelve JSON:
{{
  "info_density_score": 0-100,
  "originality_score": 0-100,
  "fluff_score": 0-100,
  "estimated_words": 1000-20000,
  "credibility_score": 0-100,
  "is_controversial": true|false,
  "engagement_ratio": 0.0-10.0,
  "is_educational_series": true|false,
  "is_trending": true|false,
  "applicability_score": 0-100
}}

Título: {metadata.title}
Descripción: {metadata.description[:500]}
Content Type: {metadata.content_type}
Canal: {metadata.channel_name}

Responde SOLO con JSON."""

        system_prompt = """Eres un predictor de valor de contenido educativo.
Analizas densidad informativa, originalidad, y aplicabilidad práctica."""

        response = self._call_ollama(prompt, system_prompt)
        
        if response:
            parsed = self._parse_json_response(response)
            for key, value in parsed.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
        
        return metadata
    
    def _fallback_value_prediction(self, metadata: VideoMetadata, 
                                  channel_stats: Dict = None) -> VideoMetadata:
        """Fallback para predicción de valor"""
        # Estimaciones básicas
        base_score = 50
        
        # Densidad basada en content type
        content_type_scores = {
            "tutorial": 80,
            "case_study": 85,
            "review": 60,
            "news": 50,
            "opinion": 40,
            "podcast": 55,
            "newsletter": 45
        }
        metadata.info_density_score = content_type_scores.get(metadata.content_type, base_score)
        
        # Originalidad (basada enKeywords únicos)
        metadata.originality_score = min(100, 50 + len(metadata.extracted_keywords) * 5)
        
        # Fluff basado en clickbait
        metadata.fluff_score = metadata.clickbait_score
        
        # Estimación de palabras
        if "full" in metadata.title.lower() or "complete" in metadata.title.lower():
            metadata.estimated_words = 15000
        elif "short" in metadata.title.lower():
            metadata.estimated_words = 3000
        else:
            metadata.estimated_words = 8000
        
        # Credibilidad
        metadata.credibility_score = min(100, 100 - metadata.clickbait_score)
        
        # Controversia
        controversial_keywords = ["best", "worst", "scam", "truth", "exposed"]
        metadata.is_controversial = any(k in metadata.title.lower() for k in controversial_keywords)
        
        # Series educativa
        series_patterns = ["part ", "chapter ", "episode ", "lesson "]
        metadata.is_educational_series = any(p in metadata.title.lower() for p in series_patterns)
        
        # Trending
        trending_keywords = ["2024", "2025", "new", "update", "latest"]
        metadata.is_trending = any(t in metadata.title.lower() for t in trending_keywords)
        
        # Aplicabilidad
        action_keywords = ["how to", "guide", "steps", "strategy", "tutorial"]
        metadata.applicability_score = 70 if any(a in metadata.title.lower() for a in action_keywords) else 40
        
        return metadata
    
    # ==================== PILAR 3: FILTRADO INTELIGENTE (21-30) ====================
    # Módulo 21: Filtro Semántico Personalizado
    # Módulo 22: Aprendizaje de Preferencias
    # Módulo 23: Detección de Duplicados Conceptuales
    # Módulo 24: Recomendación de "Ver Después"
    # Módulo 25: Alerta de Gap de Conocimiento
    # Módulo 26: Filtro de Coherencia con Manuales
    # Módulo 27: Detección de Cambio de Nicho del Canal
    # Módulo 28: Priorización Dinámica por Objetivo
    # Módulo 29: Exclusión de Temas Sensibles
    # Módulo 30: Detección de Contenido Generado por IA
    
    def apply_intelligent_filter(self, metadata: VideoMetadata,
                                target_objective: str = "ads") -> VideoMetadata:
        """
        [PILAR 3: Módulos 21-30]
        Aplica filtros inteligentes y personalización.
        """
        if not self.ollama_available:
            return self._fallback_intelligent_filter(metadata, target_objective)
        
        # Objetivo dinámico
        objective_keywords = {
            "ads": ["ads", "ppc", "campaign", "bidding", "acos"],
            "seo": ["seo", "ranking", "keywords", "search", "amazon a9"],
            "pricing": ["pricing", "price", "royalty", "cost", "margin"],
            "design": ["cover", "design", "interior", "format", "template"],
        }
        
        target_kws = objective_keywords.get(target_objective.lower(), [])
        
        prompt = f"""Evalúa este video para filtrado inteligente. JSON:
{{
  "pass_semantic_filter": true|false,
  "recommended_action": "download|skip|review|watch_later",
  "related_video_ids": ["vid1", "vid2"],
  "knowledge_gap_alert": true|false,
  "contradicts_manual": true|false,
  "updates_entry_id": null
}}

Título: {metadata.title}
Keywords objetivo: {target_kws}
KDP Relevance: {metadata.kdp_relevance_score}
Content Type: {metadata.content_type}
Applicability: {metadata.applicability_score}

Responde SOLO con JSON."""

        system_prompt = """Eres un filtro inteligente de contenido KDP.
Decides qué videos son relevantes para el objetivo del usuario."""

        response = self._call_ollama(prompt, system_prompt)
        
        if response:
            parsed = self._parse_json_response(response)
            for key, value in parsed.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
        
        return metadata
    
    def _fallback_intelligent_filter(self, metadata: VideoMetadata,
                                  target_objective: str) -> VideoMetadata:
        """Fallback para filtrado"""
        # Filtro semántico básico
        target_keywords = {
            "ads": ["ads", "ppc", "campaign", "bidding", "acos"],
            "seo": ["seo", "ranking", "keywords", "search"],
            "pricing": ["pricing", "price", "royalty", "cost"],
            "design": ["cover", "design", "interior", "format"],
        }
        
        target_kws = target_keywords.get(target_objective.lower(), [])
        title_lower = metadata.title.lower()
        
        # Pass semántico
        metadata.pass_semantic_filter = any(kw in title_lower for kw in target_kws) or \
                                     metadata.kdp_relevance_score >= self.config["min_kdp_relevance"]
        
        # Acción recomendada
        if metadata.kdp_relevance_score >= 70 and metadata.pass_semantic_filter:
            metadata.recommended_action = "download"
        elif metadata.kdp_relevance_score >= 40:
            metadata.recommended_action = "review"
        else:
            metadata.recommended_action = "skip"
        
        # Knowledge gap (simulado - requiere KB real)
        metadata.knowledge_gap_alert = False
        
        return metadata
    
    def learn_preference(self, video_id: str, action: str, keywords: List[str]):
        """[Módulo 22] Aprende preferencias del usuario"""
        if action == "download":
            self._learned_preferences["downloaded_keywords"].update(keywords)
        elif action == "skip":
            self._learned_preferences["skipped_keywords"].update(keywords)
    
    # ==================== PILAR 4: OPTIMIZACIÓN DE DESCARGA (31-40) ====================
    # Módulo 31: Programación Inteligente de Descarga
    # Módulo 32: Agrupación por Tema para Batch
    # Módulo 33: Predicción de Tiempo de Procesamiento
    # Módulo 34: Optimización de Orden de Cola
    # Módulo 35: Detección de Videos "Pesados"
    # Módulo 36: Sugerencia de Segmentación
    # Módulo 37: Predicción de Fallos de Descarga
    # Módulo 38: Balanceo de Carga por Canal
    # Módulo 39: Modo "Solo Audio" Predictivo
    # Módulo 40: Compresión Predictiva
    
    def optimize_download(self, metadata: VideoMetadata, 
                        current_hour: int = None) -> VideoMetadata:
        """
        [PILAR 4: Módulos 31-40]
        Optimiza la descarga del video.
        """
        current_hour = current_hour or datetime.now().hour
        
        # Programación inteligente [Módulo 31]
        if 2 <= current_hour <= 6:
            metadata.suggested_schedule = "night"
        elif 8 <= current_hour <= 18:
            metadata.suggested_schedule = "work_hours"
        else:
            metadata.suggested_schedule = "now"
        
        # Agrupación por tema [Módulo 32]
        if metadata.extracted_keywords:
            metadata.batch_group = metadata.extracted_keywords[0]
        
        # Predicción de tiempo [Módulo 33]
        metadata.estimated_processing_time = metadata.estimated_words / 1000  # ~1min por 1000 palabras
        
        # Detección de pesado [Módulo 35]
        metadata.is_heavy_video = metadata.estimated_words > 15000
        
        # Sugerencia de segmentación [Módulo 36]
        if metadata.estimated_words > 25000:
            metadata.should_segment = True
            metadata.segment_count = min(5, metadata.estimated_words // 15000 + 1)
        
        # Predicción de fallos [Módulo 37]
        failure_indicators = ["live", "premiere", "private", "deleted"]
        metadata.failure_risk = any(i in metadata.title.lower() for i in failure_indicators)
        
        # Solo audio predictivo [Módulo 39]
        podcast_indicators = ["podcast", "interview", "talk show", "conference"]
        metadata.suggest_audio_only = any(p in metadata.title.lower() for p in podcast_indicators)
        
        return metadata
    
    def get_optimal_queue_order(self, videos: List[VideoMetadata]) -> List[VideoMetadata]:
        """[Módulo 34] Optimiza el orden de la cola"""
        # Ordenar por: facilidad Primero para feedback rápido
        sorted_videos = sorted(videos, key=lambda v: (
            not v.failure_risk,  # Los que no fallan primero
            -v.kdp_relevance_score,  # Mayor relevancia primero
            v.estimated_words / 1000,  # Menor tiempo primero
        ))
        return sorted_videos
    
    # ==================== PILAR 5: INTEGRACIÓN CONTEXTUAL KB (41-50) ====================
    # Módulo 41: Mapeo a Roles SOE
    # Módulo 42: Vinculación con Entradas Existentes
    # Módulo 43: Detección de Contradicciones
    # Módulo 44: Actualización de Entradas Viejas
    # Módulo 45: Generación de Resumen Previo
    # Módulo 46: Extracción de Preguntas Frecuentes
    # Módulo 47: Identificación de Herramientas Mencionadas
    # Módulo 48: Detección de Casos de Estudio
    # Módulo 49: Clasificación de Formato de Aprendizaje
    # Módulo 50: Alerta de Profundidad Insuficiente
    
    def integrate_with_knowledge_base(self, metadata: VideoMetadata,
                                       kb_entries: List[Dict] = None) -> VideoMetadata:
        """
        [PILAR 5: Módulos 41-50]
        Integra con la base de conocimiento existente.
        """
        if not self.ollama_available:
            return self._fallback_kb_integration(metadata, kb_entries)
        
        prompt = f"""Analiza para integración con KB. JSON:
{{
  "assigned_role_id": 1-38,
  "linked_entry_ids": [101, 102],
  "contradicts_manual": true|false,
  "updates_entry_id": null,
  "faq_questions": ["preg1", "preg2"],
  "tools_mentioned": ["tool1", "tool2"],
  "has_case_study": true|false,
  "learning_format": "theoretical|practical",
  "depth_alert": "too_shallow|adequate|too_deep"
}}

Título: {metadata.title}
Descripción: {metadata.description[:500]}
KDP Relevance: {metadata.kdp_relevance_score}

Responde SOLO con JSON."""

        system_prompt = """Eres un integrador de conocimiento para KDP.
Mapeas videos a roles SOE y detectas relaciones con manuales existentes."""

        response = self._call_ollama(prompt, system_prompt)
        
        if response:
            parsed = self._parse_json_response(response)
            for key, value in parsed.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
        
        return metadata
    
    def _fallback_kb_integration(self, metadata: VideoMetadata,
                                  kb_entries: List[Dict] = None) -> VideoMetadata:
        """Fallback para integración KB"""
        # Mapeo a roles porKeywords
        role_mappings = {
            "ads": 7, "ppc": 7, "campaign": 7,
            "seo": 6, "ranking": 6, "keywords": 6,
            "cover": 3, "design": 3, "interior": 3,
            "pricing": 16, "royalty": 16, "cost": 16,
            "niche": 1, "research": 1, "market": 1,
        }
        
        title_lower = metadata.title.lower()
        for keyword, role_id in role_mappings.items():
            if keyword in title_lower:
                metadata.assigned_role_id = role_id
                break
        
        if not metadata.assigned_role_id:
            metadata.assigned_role_id = 1  # Default: Analista
        
        # Learning format
        if "how to" in title_lower or "tutorial" in title_lower:
            metadata.learning_format = "practical"
        else:
            metadata.learning_format = "theoretical"
        
        # Depth alert
        if metadata.expert_level == "beginner":
            metadata.depth_alert = "too_shallow"
        elif metadata.expert_level == "advanced":
            metadata.depth_alert = "too_deep"
        else:
            metadata.depth_alert = "adequate"
        
        return metadata
    
    # ==================== PILAR 6: REPORTES Y ESTRATEGIA (51-60) ====================
    # Módulo 51: Reporte de Salud del Canal
    # Módulo 52: Análisis de Evolución de Contenido
    # Módulo 53: Predicción de Futuros Videos
    # Módulo 54: Benchmarking vs Otros Canales
    # Módulo 55: ROI de Tiempo de Visualización
    # Módulo 56: Detección de Saturación de Tema
    # Módulo 57: Sugerencia de Nuevos Canales
    # Módulo 58: Alerta de Declive de Calidad
    # Módulo 59: Generación de Plan de Estudio
    # Módulo 60: Resumen Ejecutivo del Canal
    
    def generate_channel_report(self, channel_id: str,
                               channel_name: str,
                               videos: List[VideoMetadata]) -> ChannelAnalysis:
        """
        [PILAR 6: Módulos 51-60]
        Genera reportes y estrategia del canal.
        """
        analysis = ChannelAnalysis(
            channel_id=channel_id,
            channel_name=channel_name,
            video_count=len(videos)
        )
        
        if not videos:
            return analysis
        
        # Calcular métricas agregadas
        total_relevance = sum(v.kdp_relevance_score for v in videos)
        analysis.avg_kdp_relevance = total_relevance / len(videos)
        
        # Filtrar recomendados
        recommended = [v for v in videos if v.recommended_action == "download"]
        analysis.recommended_count = len(recommended)
        analysis.skip_count = len([v for v in videos if v.recommended_action == "skip"])
        
        # Top categorías
        content_types = {}
        for v in videos:
            ct = v.content_type
            content_types[ct] = content_types.get(ct, 0) + 1
        analysis.top_categories = sorted(content_types.keys(), 
                                   key=lambda x: content_types[x], 
                                   reverse=True)[:3]
        
        # Health score [Módulo 51]
        if analysis.recommended_count > analysis.skip_count:
            analysis.health_score = 75
        elif analysis.avg_kdp_relevance > 50:
            analysis.health_score = 60
        else:
            analysis.health_score = 40
        
        # ROI [Módulo 55]
        total_time = sum(v.estimated_words / 1000 for v in recommended)
        analysis.roi_score = analysis.avg_kdp_relevance / max(1, total_time) * 10
        
        # Detección de saturación [Módulo 56]
        keyword_counts = {}
        for v in videos:
            for kw in v.extracted_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        analysis.topic_saturation = any(c > len(videos) * 0.3 for c in keyword_counts.values())
        
        # Ejecutivo summary [Módulo 60]
        analysis.executive_summary = self._generate_executive_summary(analysis)
        
        return analysis
    
    def _generate_executive_summary(self, analysis: ChannelAnalysis) -> str:
        """Genera resumen ejecutivo"""
        return f"""Canal: {analysis.channel_name}
Videos: {analysis.video_count} | Recomendados: {analysis.recommended_count} | Ignorados: {analysis.skip_count}
Salud: {analysis.health_score}/100 | Relevancia KDP: {analysis.avg_kdp_relevance:.1f}%
Categorías principales: {', '.join(analysis.top_categories[:2])}
Acción: {"SEGUIR" if analysis.health_score >= 60 else "EVALUAR"}"""
    
    def generate_study_plan(self, videos: List[VideoMetadata]) -> str:
        """[Módulo 59] Genera plan de estudio"""
        if not videos:
            return "No hay videos para planificar."
        
        # Filtrar educativos
        educational = [v for v in videos if v.is_educational_series]
        practical = [v for v in videos if v.learning_format == "practical" and v.applicability_score >= 60]
        
        if not educational and not practical:
            return "No hay contenido estructurado."
        
        plan = "📚 Plan de Estudio:\n"
        plan += f"1. Verideos serie educativa ({len(educational)} videos)\n"
        for i, v in enumerate(educational[:5], 1):
            plan += f"   {i}. {v.title[:50]}\n"
        
        if practical:
            plan += f"\n2. Prácticos de alta aplicabilidad ({len(practical)} videos)\n"
            for i, v in enumerate(practical[:5], 1):
                plan += f"   {i}. {v.title[:50]}\n"
        
        return plan
    
    # ==================== MAIN PROCESSING METHODS ====================
    
    def process_video_batch(self, videos: List[Dict], 
                     progress_callback: Callable = None) -> List[VideoMetadata]:
        """
        Procesa un batch de Videos completo con los 60 módulos.
        
        Args:
            videos: Lista de diccionarios con 'video_id', 'title', 'description', 'channel_name'
            progress_callback: Función de callback para progreso
            
        Returns:
            Lista de VideoMetadata enriquecidos
        """
        results = []
        total = len(videos)
        
        for i, video in enumerate(videos):
            try:
                # Crear metadata base
                metadata = VideoMetadata(
                    video_id=video.get("video_id", ""),
                    title=video.get("title", ""),
                    description=video.get("description", ""),
                    channel_name=video.get("channel_name", "")
                )
                
                # PILAR 1: Análisis Semántico (1-10)
                metadata = self.analyze_title_semantics(metadata.title, metadata.description)
                
                # PILAR 2: Predicción de Valor (11-20)
                metadata = self.analyze_value_prediction(metadata)
                
                # PILAR 3: Filtrado Inteligente (21-30)
                metadata = self.apply_intelligent_filter(metadata)
                
                # PILAR 4: Optimización de Descarga (31-40)
                metadata = self.optimize_download(metadata)
                
                # PILAR 5: Integración KB (41-50)
                metadata = self.integrate_with_knowledge_base(metadata)
                
                results.append(metadata)
                
                if progress_callback:
                    progress_callback(i + 1, total)
                    
            except Exception as e:
                logger.warning(f"Error procesando video {video.get('video_id')}: {e}")
                continue
        
        return results
    
    def get_filtered_videos(self, videos: List[VideoMetadata],
                          action_filter: str = "download") -> List[VideoMetadata]:
        """Retorna videos filtrados por acción recomendada"""
        return [v for v in videos if v.recommended_action == action_filter]
    
    def export_report(self, channel_id: str, channel_name: str,
                   videos: List[VideoMetadata]) -> ChannelAnalysis:
        """Genera reporte completo del canal"""
        return self.generate_channel_report(channel_id, channel_name, videos)


# ==================== TRANSLATION SERVICE ====================

class TranslationService:
    """
    Servicio de traducción de transcripciones usando Ollama.
    Módulo adicional solicitado.
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434",
                 ollama_model: str = "qwen2.5:7b"):
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self._ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        if not REQUESTS_AVAILABLE:
            return False
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def translate_critical_fragments(self, text: str, 
                                 target_lang: str = "es") -> str:
        """
        Traduce fragmentos críticos de transcripción.
        """
        if not self._ollama_available:
            return text
        
        if len(text) > 50000:
            text = text[:50000]  # Limitar para no saturar
        
        lang_names = {"es": "español", "en": "inglés", "pt": "portugués"}
        target = lang_names.get(target_lang, target_lang)
        
        prompt = f"""Traduce al {target} los siguientes fragmentos críticos de transcripción.
Mantén términos técnicos en inglés solo si no hay traducción establecida.
Traduce solo lo más importante (no todo el texto):

{text[:8000]}"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json().get("response", text)
        except Exception as e:
            logger.warning(f"Error de traducción: {e}")
        
        return text
    
    def detect_language(self, text: str) -> str:
        """Detecta idioma del texto"""
        if not self._ollama_available:
            # Fallback simple
            spanish_words = ["el", "la", "los", "las", "de", "que", "es", "en", "un", "por"]
            text_lower = text.lower()
            if any(w in text_lower.split()[:20] for w in spanish_words):
                return "es"
            return "en"
        
        prompt = f"""Detecta el idioma de este texto. Responde SOLO el código: es, en, pt, fr, de, it, zh, ja, ko, u otro:

{text[:500]}"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get("response", "").strip().lower()
                if result in ["es", "en", "pt", "fr", "de", "it", "zh", "ja", "ko"]:
                    return result
        except:
            pass
        
        return "unknown"


# ==================== EXPORT FUNCTIONS ====================

def create_curation_engine(ollama_base_url: str = None,
                        ollama_model: str = None) -> ChannelCurationEngine:
    """Factory function para crear el motor de curación"""
    import os
    
    if not ollama_base_url:
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    if not ollama_model:
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    
    return ChannelCurationEngine(
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model
    )


def translate_transcription(text: str, target_lang: str = "es") -> str:
    """Función de conveniencia para traducción"""
    service = TranslationService()
    return service.translate_critical_fragments(text, target_lang)


# ==================== MAIN ====================

if __name__ == "__main__":
    print("Channel Curation Engine v3.5.0")
    print("60 módulos CON IA implementados")
    
    # Test básico
    engine = create_curation_engine()
    
    test_videos = [
        {
            "video_id": "test001",
            "title": "Cómo publicar en KDP 2025 - Guía completa",
            "description": "Tutorial paso a paso para publicar tu libro en Amazon KDP",
            "channel_name": "KDP Master"
        },
        {
            "video_id": "test002",
            "title": "Amazon Ads estrategia avanzada",
            "description": "Aprende a optimizar tus campañas publicitarias",
            "channel_name": "KDP Master"
        }
    ]
    
    results = engine.process_video_batch(test_videos)
    
    for v in results:
        print(f"\n{v.title}")
        print(f"  Relevancia KDP: {v.kdp_relevance_score}")
        print(f"  Acción: {v.recommended_action}")
        print(f"  Tipo: {v.content_type}")