"""
Módulos IA P3: Filtrado Inteligente y Personalización
- P3-21: Filtro Semántico Personalizado
- P3-22: Aprendizaje de Preferencias
- P3-25: Alerta de Gap de Conocimiento
- P3-27: Detección de Cambio de Nicho del Canal
"""
import logging
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class UserPreference:
    """Preferencia aprendida del usuario."""
    preference_type: str
    preference_value: str
    weight: float
    last_confirmed: str
    source: str


@dataclass
class KnowledgeGap:
    """Gap de conocimiento identificado."""
    gap_id: str
    topic: str
    priority: str
    description: str
    related_videos: List[str]
    suggested_action: str


@dataclass
class NicheChange:
    """Cambio de nicho detectado en un canal."""
    channel_id: str
    previous_niche: str
    current_niche: str
    confidence: float
    detected_at: str
    evidence: List[str]


class SemanticFilter:
    """Filtro semántico con aprendizaje de preferencias."""

    DEFAULT_PREFERENCES_FILE = "data/user_preferences.json"

    def __init__(self, preferences_file: Optional[str] = None):
        self.preferences_file = Path(preferences_file) if preferences_file else Path(self.DEFAULT_PREFERENCES_FILE)
        self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
        self._preferences: Dict[str, UserPreference] = {}
        self._load_preferences()

    def _load_preferences(self):
        """Carga las preferencias desde archivo."""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, val in data.items():
                        self._preferences[key] = UserPreference(**val)
                logger.info(f"Cargadas {len(self._preferences)} preferencias")
            except Exception as e:
                logger.error(f"Error cargando preferencias: {e}")

    def _save_preferences(self):
        """Guarda las preferencias a archivo."""
        try:
            data = {k: v.__dict__ for k, v in self._preferences.items()}
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando preferencias: {e}")

    def add_preference(
        self,
        preference_type: str,
        preference_value: str,
        weight: float = 1.0,
        source: str = "manual"
    ):
        """Agrega o actualiza una preferencia."""
        key = f"{preference_type}:{preference_value}"

        if key in self._preferences:
            existing = self._preferences[key]
            existing.weight = min(10.0, existing.weight + weight * 0.1)
            existing.last_confirmed = datetime.now().isoformat()
            existing.source = source if weight > existing.weight else existing.source
        else:
            self._preferences[key] = UserPreference(
                preference_type=preference_type,
                preference_value=preference_value,
                weight=weight,
                last_confirmed=datetime.now().isoformat(),
                source=source
            )

        self._save_preferences()
        logger.info(f"Preferencia agregada/actualizada: {key}")

    def filter_by_semantic_query(
        self,
        videos: List[Dict],
        query: str,
        min_relevance: float = 0.3
    ) -> List[Tuple[Dict, float]]:
        """
        P3-21: Filtra videos por consulta semántica natural.
        Args:
            videos: Lista de videos a filtrar
            query: Consulta en lenguaje natural
            min_relevance: Score mínimo de relevancia
        Returns:
            Lista de (video, relevance_score) ordenados por relevancia
        """
        query_lower = query.lower()
        query_terms = query_lower.split()

        results = []

        for video in videos:
            title = video.get('title', '').lower()
            description = video.get('description', '').lower()
            tags = video.get('tags', [])

            score = 0.0

            for term in query_terms:
                if term in title:
                    score += 3.0
                if term in description:
                    score += 1.0
                if any(term in str(tag).lower() for tag in tags):
                    score += 2.0

            if score > 0:
                title_words = len(title.split())
                description_words = len(description.split())
                density = (score / (title_words + description_words + 1)) * 10
                score += density

            normalized_score = min(score / 10.0, 1.0)

            if normalized_score >= min_relevance:
                results.append((video, normalized_score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def learn_from_user_action(
        self,
        video: Dict,
        action: str,
        category: Optional[str] = None
    ):
        """
        P3-22: Aprende de las acciones del usuario para mejorar recomendaciones.
        Args:
            video: Video sobre el que se actuó
            action: Acción realizada (downloaded, ignored, skipped, bookmarked)
            category: Categoría si se clasificó manualmente
        """
        title = video.get('title', '')
        tags = video.get('tags', [])

        if action in ['downloaded', 'bookmarked']:
            weight = 1.5
            for tag in tags:
                if isinstance(tag, str):
                    self.add_preference('tag', tag, weight, 'learned')

            if category:
                self.add_preference('category', category, weight * 2, 'learned')

            keywords = title.split()[:3]
            for kw in keywords:
                if len(kw) > 3:
                    self.add_preference('keyword', kw.lower(), weight * 0.5, 'learned')

        elif action in ['ignored', 'skipped']:
            weight = -0.5
            for tag in tags:
                if isinstance(tag, str):
                    self.add_preference('tag', tag, weight, 'learned')

    def detect_knowledge_gaps(
        self,
        user_topics: List[str],
        available_videos: List[Dict]
    ) -> List[KnowledgeGap]:
        """
        P3-25: Detecta gaps de conocimiento basándose en topics del usuario.
        Args:
            user_topics: Topics en los que el usuario está interesado
            available_videos: Videos disponibles en la KB
        Returns:
            Lista de KnowledgeGap detectados
        """
        gaps = []

        user_topics_set = set(t.lower() for t in user_topics)
        available_topics = set()

        for video in available_videos:
            title = video.get('title', '').lower()
            tags = video.get('tags', [])
            all_text = f"{title} {' '.join(str(t) for t in tags)}"

            for user_topic in user_topics_set:
                if user_topic in all_text:
                    available_topics.add(user_topic)

        missing_topics = user_topics_set - available_topics

        for topic in missing_topics:
            gap = KnowledgeGap(
                gap_id=hashlib.md5(topic.encode()).hexdigest()[:8],
                topic=topic,
                priority="high" if len(available_topics) < 5 else "medium",
                description=f"No hay videos disponibles sobre '{topic}'",
                related_videos=[],
                suggested_action=f"Buscar videos sobre '{topic}' o buscar nuevos canales"
            )
            gaps.append(gap)

        return gaps

    def detect_niche_change(
        self,
        channel_id: str,
        recent_video_titles: List[str],
        previous_niche: Optional[str] = None
    ) -> Optional[NicheChange]:
        """
        P3-27: Detecta cambio de nicho en un canal.
        Args:
            channel_id: ID del canal
            recent_video_titles: Títulos de videos recientes
            previous_niche: Nicho anteriormente registrado
        Returns:
            NicheChange si se detecta cambio, None si no
        """
        topics = {
            'kdp': ['kdp', 'amazon', 'ebook', 'publicar', 'self-publishing', 'autoedición'],
            'marketing': ['marketing', 'publicidad', 'promoción', 'ventas', 'digital'],
            'tutorial': ['tutorial', 'cómo', 'guía', 'aprender', 'curso'],
            'tech': ['python', 'programación', 'código', 'desarrollo', 'software'],
            'finanzas': ['dinero', 'inversión', 'renta', 'impuestos', 'crypto'],
            'legal': ['legal', 'ley', 'derecho', 'jurídico', 'contrato']
        }

        topic_counts = {topic: 0 for topic in topics}

        for title in recent_video_titles:
            title_lower = title.lower()
            for topic, keywords in topics.items():
                if any(kw in title_lower for kw in keywords):
                    topic_counts[topic] += 1

        dominant_topic = max(topic_counts, key=topic_counts.get)
        confidence = topic_counts[dominant_topic] / len(recent_video_titles) if recent_video_titles else 0

        if previous_niche and previous_niche != dominant_topic and confidence > 0.5:
            change = NicheChange(
                channel_id=channel_id,
                previous_niche=previous_niche,
                current_niche=dominant_topic,
                confidence=confidence,
                detected_at=datetime.now().isoformat(),
                evidence=[f"{topic}: {count}" for topic, count in topic_counts.items() if count > 0]
            )
            logger.warning(f"Cambio de nicho detectado en canal {channel_id}: {previous_niche} -> {dominant_topic}")
            return change

        return None

    def get_recommendations(self, user_history: List[Dict], limit: int = 10) -> List[Dict]:
        """Genera recomendaciones basadas en preferencias aprendidas."""
        if not user_history:
            return []

        positive_prefs = [(k, v) for k, v in self._preferences.items() if v.weight > 0]
        if not positive_prefs:
            return user_history[:limit]

        scored_videos = []
        for video in user_history:
            score = 0
            title = video.get('title', '').lower()
            tags = video.get('tags', [])

            for _, pref in positive_prefs:
                if pref.preference_type == 'tag' and any(pref.preference_value in str(t).lower() for t in tags):
                    score += pref.weight
                elif pref.preference_type == 'keyword' and pref.preference_value in title:
                    score += pref.weight * 0.5
                elif pref.preference_type == 'category' and pref.preference_value in (video.get('category', '') or '').lower():
                    score += pref.weight * 2

            scored_videos.append((video, score))

        scored_videos.sort(key=lambda x: x[1], reverse=True)
        return [v[0] for v in scored_videos[:limit]]


_global_filter: Optional[SemanticFilter] = None


def get_semantic_filter() -> SemanticFilter:
    """Obtiene la instancia global del filtro semántico."""
    global _global_filter
    if _global_filter is None:
        _global_filter = SemanticFilter()
    return _global_filter