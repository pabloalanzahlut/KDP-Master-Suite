"""
Módulos P6: Integración con Pipeline KDP
- P6-56: Enlace a Manual Existente
- P6-57: Alerta de Actualización de TOS (Terms of Service)
- P6-58: Detección de Series/Capítulos
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SeriesInfo:
    """Información de una serie detectada."""
    series_id: str
    series_name: str
    part_number: int
    total_parts: Optional[int]
    videos: List[str]
    is_complete: bool


@dataclass
class ManualSuggestion:
    """Sugerencia de manual relacionado."""
    manual_title: str
    manual_id: str
    relevance_score: float
    match_type: str
    reason: str


class ContentIntegrator:
    """Integrador de contenido con manuales y series."""

    SERIES_PATTERNS = [
        r'(parte|part|episode|episodio)\s*(\d+)',
        r'(volumen|volume|vol)\s*(\d+)',
        r'(cap[ií]tulo|chapter)\s*(\d+)',
        r'serie\s*(\d+)',
        r'tutorial\s*(\d+)',
        r'clase\s*(\d+)',
        r'lección|lesson\s*(\d+)',
        r'\((\d+)/(\d+)\)',
        r'(\d+)\s*de\s*(\d+)',
        r'#(\d+)'
    ]

    TOS_KEYWORDS = [
        'terms of service', 'tos', 'terms of use',
        'política de privacidad', 'privacy policy',
        'actualización de términos', 'new terms',
        'cambios en los términos', 'changes to terms',
        'actualizado', 'updated', 'modificado'
    ]

    MANUAL_KEYWORDS = {
        'legalidad': ['legal', 'ley', 'jurídico', 'derecho', 'compliance'],
        'kdp': ['kdp', 'amazon', 'publicación', 'ebook', 'self-publishing'],
        'marketing': ['marketing', 'promoción', 'publicidad', 'ventas'],
        'seo': ['seo', 'buscador', 'google', 'posicionamiento'],
        'escritura': ['escribir', 'escritura', 'autor', 'novela'],
        'finanzas': ['dinero', 'impuesto', 'ingreso', 'renta', 'impuestos']
    }

    def __init__(self):
        self._detected_series: Dict[str, SeriesInfo] = {}
        self._manual_index: Dict[str, List[str]] = {}

    def detect_series(self, video_title: str, video_id: str) -> Optional[SeriesInfo]:
        """
        P6-58: Detecta si un video es parte de una serie numerada.
        Args:
            video_title: Título del video
            video_id: ID único del video
        Returns:
            SeriesInfo si es parte de una serie, None si no
        """
        title_lower = video_title.lower()

        for pattern in self.SERIES_PATTERNS:
            match = re.search(pattern, title_lower, re.IGNORECASE)
            if match:
                groups = match.groups()

                if len(groups) >= 1 and groups[0]:
                    part_str = groups[0] if not groups[1] else groups[1]
                    try:
                        part_number = int(part_str if not groups[1] else groups[1])
                    except (ValueError, IndexError):
                        continue

                elif len(groups) >= 2:
                    try:
                        part_number = int(groups[0])
                        if groups[1]:
                            total = int(groups[1])
                    except (ValueError, IndexError):
                        continue

                base_name = title_lower[:match.start()].strip()
                series_name = self._clean_series_name(base_name)

                series_id = self._generate_series_id(series_name)

                if series_id in self._detected_series:
                    series = self._detected_series[series_id]
                    if video_id not in series.videos:
                        series.videos.append(video_id)
                        if part_number > series.part_number:
                            series.part_number = part_number
                else:
                    series = SeriesInfo(
                        series_id=series_id,
                        series_name=series_name,
                        part_number=part_number,
                        total_parts=None,
                        videos=[video_id],
                        is_complete=False
                    )
                    self._detected_series[series_id] = series

                logger.info(f"Serie detectada: {series_name} - Parte {part_number}")
                return series

        return None

    def _clean_series_name(self, name: str) -> str:
        """Limpia el nombre de una serie."""
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())
        return name[:50]

    def _generate_series_id(self, series_name: str) -> str:
        """Genera un ID único para la serie."""
        return series_name.lower().replace(' ', '_')[:30]

    def get_series_info(self, series_id: str) -> Optional[SeriesInfo]:
        """Obtiene información de una serie específica."""
        return self._detected_series.get(series_id)

    def get_all_series(self) -> List[SeriesInfo]:
        """Retorna todas las series detectadas."""
        return list(self._detected_series.values())

    def suggest_manual(self, video_metadata: Dict) -> List[ManualSuggestion]:
        """
        P6-56: Sugiere un manual existente relacionado con el video.
        Args:
            video_metadata: Metadatos del video (título, descripción, tags, categoría)
        Returns:
            Lista de ManualSuggestion ordenadas por relevancia
        """
        suggestions = []

        title = video_metadata.get('title', '').lower()
        description = video_metadata.get('description', '').lower()
        tags = video_metadata.get('tags', [])
        category = video_metadata.get('category', '').lower()

        content_text = f"{title} {' '.join(tags)} {description} {category}"

        for manual_category, keywords in self.MANUAL_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in content_text)
            if matches > 0:
                relevance = min(matches / len(keywords), 1.0)
                suggestions.append(ManualSuggestion(
                    manual_title=f"Manual de {manual_category.title()}",
                    manual_id=manual_category,
                    relevance_score=relevance,
                    match_type="keyword",
                    reason=f"Coincide con {matches} palabras clave de {manual_category}"
                ))

        suggestions.sort(key=lambda s: s.relevance_score, reverse=True)
        return suggestions[:5]

    def check_tos_update(self, video_title: str, video_description: str) -> bool:
        """
        P6-57: Detecta si el video trata sobre actualizaciones de Términos de Servicio.
        Args:
            video_title: Título del video
            video_description: Descripción del video
        Returns:
            True si se detecta tema de TOS
        """
        content = f"{video_title.lower()} {video_description.lower()}"

        tos_count = sum(1 for kw in self.TOS_KEYWORDS if kw in content)

        if tos_count >= 2:
            logger.warning(f"⚠️ Posible video sobre TOS detectado: {video_title[:50]}")
            return True

        return False

    def analyze_content_structure(
        self,
        video_titles: List[str],
        video_ids: List[str]
    ) -> Dict:
        """
        Analiza estructura de contenido de una lista de videos.
        Args:
            video_titles: Lista de títulos de videos
            video_ids: Lista de IDs de videos
        Returns:
            Diccionario con análisis de estructura
        """
        series_count = 0
        standalone_count = 0
        series_info = []

        for title, vid in zip(video_titles, video_ids):
            series = self.detect_series(title, vid)
            if series:
                series_count += 1
                series_info.append(series)
            else:
                standalone_count += 1

        return {
            "total_videos": len(video_titles),
            "series_count": series_count,
            "standalone_count": standalone_count,
            "series_info": [s.series_name for s in set(series_info)],
            "completion_status": {
                "complete": len([s for s in self._detected_series.values() if s.is_complete]),
                "in_progress": len([s for s in self._detected_series.values() if not s.is_complete])
            }
        }

    def set_manual_index(self, manual_category: str, manual_ids: List[str]):
        """Establece el índice de manuales disponibles para sugerencias."""
        self._manual_index[manual_category] = manual_ids

    def get_completion_order(self, series_id: str) -> List[str]:
        """Retorna los IDs de video de una serie en orden de parte."""
        series = self._detected_series.get(series_id)
        if not series:
            return []
        return series.videos


_global_integrator: Optional[ContentIntegrator] = None


def get_content_integrator() -> ContentIntegrator:
    """Obtiene la instancia global del integrador de contenido."""
    global _global_integrator
    if _global_integrator is None:
        _global_integrator = ContentIntegrator()
    return _global_integrator