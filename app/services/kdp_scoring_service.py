"""
KDP MASTER - Video Scoring Service (Módulo IA)
==============================================
Servicio de scoring de relevancia KDP usando IA (Ollama/OpenAI/Gemini).
Se integra en el flujo de descarga para priorizar contenido de alto valor.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RelevanceLevel(Enum):
    """Niveles de relevancia KDP."""
    CRITICAL = "critical"      # 90-100: Contenido KDP esencial
    HIGH = "high"              # 70-89: Muy relevante
    MEDIUM = "medium"          # 50-69: Relevante
    LOW = "low"                # 30-49: Poco relevante
    TRIVIAL = "trivial"        # 0-29: Ruido/banal


@dataclass
class VideoScore:
    """Resultado del scoring de un video."""
    video_id: str
    title: str
    kdp_relevance_score: int  # 0-100
    relevance_level: RelevanceLevel
    detected_keywords: List[str]
    detected_topics: List[str]
    is_clickbait: bool
    estimated_words: int
    recommended_action: str  # "download", "skip", "review", "watch_later"
    reasoning: str
    confidence: float  # 0.0-1.0
    metadata: Dict  # metadata adicional del análisis


class KDPScoringService:
    """
    Servicio de scoring de relevancia KDP usando IA.
    
    Usa Ollama local por defecto, con fallback a reglas locales.
    """
    
    # Keywords de alta prioridad KDP
    HIGH_PRIORITY_KEYWORDS = {
        'amazon kdp': 15,
        'kdp print': 15,
        'amazon self publishing': 15,
        'print on demand': 12,
        'book publishing': 12,
        'ebook creation': 10,
        'amazon ads': 10,
        'kdp ads': 10,
        'book marketing': 10,
        'book sales': 10,
        'royalty calculation': 10,
        'book cover design': 8,
        'interior design': 8,
        'book formatting': 8,
        'keywords book': 8,
        'niche research': 8,
        'category research': 8,
        'book description': 8,
        'bestseller': 7,
        'side hustle': 7,
        'passive income': 7,
    }
    
    # Keywords negativas (posible clickbait o irrelevante)
    NEGATIVE_KEYWORDS = {
        'shorts': -20,
        'live': -10,
        'subscribe': -15,
        'like and share': -15,
        'notification bell': -15,
        'patreon': -10,
        'sponsored': -5,
        'outdated': -10,
    }
    
    # Clickbait patterns
    CLICKBAIT_PATTERNS = [
        r'\b(espero|espera)\b.*\b(mínimo|mucho|super)\b',
        r'\b(mejor|peor)\b.*\b(jamás|todo)\b',
        r'\b(secret|secreto|hidden)\b',
        r'\b(esto|eso)\b.*\b(cambió|cambiará)\b',
        r'\b(pierde|gana)\b.*\b(miles|dinero)\b',
        r'!{2,}',
        r'\?{3,}',
        r'\b(gana|diner)\b.*\b(dormir|sleep)\b',
        r'\b(\$|€|dólares)\b.*\b(month|mes|año|year)\b',
    ]
    
    def __init__(self, ai_provider: str = "ollama", model: str = None):
        """
        Inicializa el servicio de scoring.
        
        Args:
            ai_provider: Proveedor IA ("ollama", "openai", "gemini")
            model: Modelo específico a usar
        """
        self.ai_provider = ai_provider
        self.model = model or self._get_default_model()
        self._ollama_pool = None
        self._use_ai = False
        self._init_ai()
    
    def _get_default_model(self) -> str:
        """Obtiene el modelo por defecto según el proveedor."""
        defaults = {
            "ollama": "llama3.2:latest",
            "openai": "gpt-4",
            "gemini": "gemini-pro"
        }
        return defaults.get(self.ai_provider, "llama3.2:latest")
    
    def _init_ai(self):
        """Inicializa la conexión con el servicio IA."""
        if self.ai_provider == "ollama":
            try:
                from app.core.ollama_pool import OllamaPool
                self._ollama_pool = OllamaPool()
                self._use_ai = True
                logger.info("KDPScoringService: IA Ollama habilitada")
            except ImportError:
                logger.warning("OllamaPool no disponible, usando scoring por reglas")
                self._use_ai = False
            except Exception as e:
                logger.warning(f"Error inicializando Ollama: {e}")
                self._use_ai = False
    
    def score_video(self, title: str, description: str = "",
                   channel_name: str = "", video_id: str = None) -> VideoScore:
        """
        Calcula el score de relevancia KDP de un video.
        
        Args:
            title: Título del video
            description: Descripción del video
            channel_name: Nombre del canal
            video_id: ID del video (opcional)
            
        Returns:
            VideoScore con el análisis completo
        """
        if not video_id:
            import hashlib
            video_id = hashlib.md5(title.encode()).hexdigest()[:11]
        
        # Scoring base (reglas locales)
        kdp_score, keywords, topics = self._rule_based_score(title, description, channel_name)
        
        # Detectar clickbait
        is_clickbait = self._detect_clickbait(title, description)
        if is_clickbait:
            kdp_score = max(0, kdp_score - 15)
        
        # Estimar palabras de transcripción
        estimated_words = self._estimate_transcription_length(title)
        
        #掉整 por fecha en título (contenido obsoleto)
        if self._is_outdated(title):
            kdp_score = max(0, kdp_score - 20)
        
        # Nivel de relevancia
        relevance_level = self._get_relevance_level(kdp_score)
        
        # Acción recomendada
        action = self._get_recommended_action(kdp_score, is_clickbait)
        
        # Confianza del scoring
        confidence = min(1.0, len(keywords) / 5.0 + 0.3)
        
        # Reasoning
        reasoning = self._generate_reasoning(kdp_score, keywords, is_clickbait)
        
        return VideoScore(
            video_id=video_id,
            title=title,
            kdp_relevance_score=kdp_score,
            relevance_level=relevance_level,
            detected_keywords=keywords,
            detected_topics=topics,
            is_clickbait=is_clickbait,
            estimated_words=estimated_words,
            recommended_action=action,
            reasoning=reasoning,
            confidence=confidence,
            metadata={
                "channel": channel_name,
                "provider": self.ai_provider,
                "model": self.model
            }
        )
    
    def _rule_based_score(self, title: str, description: str, channel_name: str) -> Tuple[int, List[str], List[str]]:
        """Scoring basado en reglas locales."""
        text = f"{title} {description} {channel_name}".lower()
        score = 50  # Score base neutral
        detected_keywords = []
        detected_topics = []
        
        # Alta prioridad keywords
        for keyword, points in self.HIGH_PRIORITY_KEYWORDS.items():
            if keyword in text:
                score += points
                detected_keywords.append(keyword)
        
        # Keywords negativas
        for keyword, penalty in self.NEGATIVE_KEYWORDS.items():
            if keyword in text:
                score += penalty
                detected_keywords.append(f"⚠️{keyword}")
        
        # Detectar topics KDP específicos
        kdp_topics = {
            "publicación libros": ["publicar", "publishing", "publicación"],
            "marketing libros": ["marketing", "promoción", "ads", "publicidad"],
            "diseño": ["cover", "portada", "interior", "diseño", "format"],
            "investigación": ["niche", "category", "keywords", "investigación"],
            "finanzas": ["royalty", "income", "money", "ganancias", "venta"],
            "formatos": ["paperback", "hardcover", "ebook", "pdf", "formato"],
        }
        
        for topic, topic_keywords in kdp_topics.items():
            if any(kw in text for kw in topic_keywords):
                detected_topics.append(topic)
        
        return max(0, min(100, score)), detected_keywords[:10], detected_topics[:5]
    
    def _detect_clickbait(self, title: str, description: str) -> bool:
        """Detecta si el título es clickbait."""
        import re
        text = title.lower()
        
        for pattern in self.CLICKBAIT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Exceso de mayúsculas
        caps_ratio = sum(1 for c in title if c.isupper()) / max(len(title), 1)
        if caps_ratio > 0.3:
            return True
        
        return False
    
    def _estimate_transcription_length(self, title: str) -> int:
        """Estima la cantidad de palabras en la transcripción."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['full', 'complete', 'tutorial completo', 'guía completa']):
            return 15000
        elif any(word in title_lower for word in ['short', 'quick', 'resumen', 'summary']):
            return 3000
        elif any(word in title_lower for word in ['1 hour', '1h', '60 min', 'una hora']):
            return 8000
        elif any(word in title_lower for word in ['2 hour', '2h', '120 min', 'dos horas']):
            return 12000
        else:
            return 8000  #默认值
    
    def _is_outdated(self, title: str) -> bool:
        """Detecta si el contenido parece obsoleto."""
        import re
        title_lower = title.lower()
        
        # Buscar años antiguos
        old_years = re.findall(r'\b(20[0-1][0-9]|2019|2020|2021)\b', title)
        current_year = 2026
        
        for year_str in old_years:
            try:
                year = int(year_str)
                if year < current_year - 2:
                    return True
            except:
                pass
        
        # Palabras que sugieren contenido obsoleto
        outdated_words = ['old version', 'versión antigua', 'deprecated', 'outdated', '2020', '2021', '2022']
        return any(word in title_lower for word in outdated_words)
    
    def _get_relevance_level(self, score: int) -> RelevanceLevel:
        """Obtiene el nivel de relevancia según el score."""
        if score >= 90:
            return RelevanceLevel.CRITICAL
        elif score >= 70:
            return RelevanceLevel.HIGH
        elif score >= 50:
            return RelevanceLevel.MEDIUM
        elif score >= 30:
            return RelevanceLevel.LOW
        else:
            return RelevanceLevel.TRIVIAL
    
    def _get_recommended_action(self, score: int, is_clickbait: bool) -> str:
        """Determina la acción recomendada según el score."""
        if is_clickbait:
            return "skip"
        elif score >= 70:
            return "download"
        elif score >= 50:
            return "review"
        elif score >= 30:
            return "watch_later"
        else:
            return "skip"
    
    def _generate_reasoning(self, score: int, keywords: List[str], is_clickbait: bool) -> str:
        """Genera una explicación del scoring."""
        parts = []
        
        if score >= 70:
            parts.append(f"Alta relevancia KDP (score: {score})")
        elif score >= 50:
            parts.append(f"Relevancia moderada (score: {score})")
        else:
            parts.append(f"Baja relevancia (score: {score})")
        
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords[:5])}")
        
        if is_clickbait:
            parts.append("⚠️ Posible clickbait detectado")
        
        return " | ".join(parts)
    
    def score_batch(self, videos: List[Dict], 
                    progress_callback: Callable = None) -> List[VideoScore]:
        """
        Calcula el score para un batch de videos.
        
        Args:
            videos: Lista de diccionarios con 'title', 'description', 'video_id'
            progress_callback: Callback opcional de progreso
            
        Returns:
            Lista de VideoScore
        """
        results = []
        total = len(videos)
        
        for i, video in enumerate(videos):
            score = self.score_video(
                title=video.get('title', ''),
                description=video.get('description', ''),
                channel_name=video.get('channel', ''),
                video_id=video.get('video_id') or video.get('id')
            )
            results.append(score)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
    
    def get_filtered_videos(self, videos: List[VideoScore], 
                           min_score: int = 50,
                           exclude_clickbait: bool = True) -> List[VideoScore]:
        """
        Filtra videos según criterios de scoring.
        
        Args:
            videos: Lista de VideoScore
            min_score: Score mínimo para incluir
            exclude_clickbait: Excluir videos detectados como clickbait
            
        Returns:
            Videos filtrados y ordenados por score
        """
        filtered = []
        
        for video in videos:
            if video.kdp_relevance_score < min_score:
                continue
            if exclude_clickbait and video.is_clickbait:
                continue
            filtered.append(video)
        
        # Ordenar por score descendente
        filtered.sort(key=lambda v: v.kdp_relevance_score, reverse=True)
        
        return filtered
    
    def get_optimal_queue_order(self, videos: List[VideoScore]) -> List[VideoScore]:
        """
        Ordena videos para descarga óptima.
        
        Prioriza:
        1. Score alto (alta relevancia)
        2. Videos sin clickbait
        3. Videos completos (estimación alta de palabras)
        """
        def queue_priority(video: VideoScore) -> tuple:
            # Prioridad: score alto, sin clickbait, más palabras
            return (
                -video.kdp_relevance_score,  # Negativo para orden ascendente
                video.is_clickbait,  # False antes que True
                -video.estimated_words  # Más palabras primero
            )
        
        return sorted(videos, key=queue_priority)


def create_scoring_service(ai_provider: str = "ollama", model: str = None) -> KDPScoringService:
    """Factory function para crear el servicio de scoring."""
    return KDPScoringService(ai_provider=ai_provider, model=model)