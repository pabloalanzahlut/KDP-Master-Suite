"""
Módulos IA P5-47: Identificación de Herramientas Mencionadas
Lista software/herramientas citadas en el contenido.
"""
import logging
from typing import List, Dict, Set
from collections import Counter

logger = logging.getLogger(__name__)


class ToolsDetector:
    """Detector de herramientas mencionadas en videos."""

    TOOL_DATABASE = {
        'amazon': ['kdp', 'kindle', 'amazon', 'createspace'],
        'writing': ['word', 'scrivener', 'google docs', 'notion', 'evernote'],
        'design': ['canva', 'photoshop', 'illustrator', 'affinity', 'figma'],
        'video': ['camtasia', 'obs', 'premiere', 'final cut', 'davinci'],
        'audio': ['audacity', 'descript', 'otter', 'rev'],
        'seo': ['ahrefs', 'semrush', 'moz', 'google console'],
        'marketing': ['mailchimp', 'convertkit', 'hubspot', 'buffer'],
        'productivity': ['notion', 'trello', 'asana', 'monday', 'airtable'],
        'ai': ['chatgpt', 'claude', 'midjourney', 'dall-e', 'copy.ai', 'jasper'],
        'finance': ['quickbooks', 'xero', 'excel', 'google sheets']
    }

    def __init__(self):
        self._detection_count = 0

    def detect_tools(
        self,
        title: str,
        description: str = "",
        transcript: str = ""
    ) -> List[Dict]:
        """
        P5-47: Detecta herramientas mencionadas.
        Args:
            title: Título del video
            description: Descripción del video
            transcript: Transcripción (opcional)
        Returns:
            Lista de herramientas detectadas
        """
        self._detection_count += 1

        content = f"{title.lower()} {description.lower()} {transcript.lower()}"

        detected = []

        for category, tools in self.TOOL_DATABASE.items():
            for tool in tools:
                if tool in content:
                    position = content.find(tool)

                    is_in_title = tool in title.lower()
                    is_in_description = tool in description.lower()
                    is_in_transcript = tool in transcript.lower()

                    detected.append({
                        'tool': tool,
                        'category': category,
                        'context': 'title' if is_in_title else ('description' if is_in_description else 'transcript'),
                        'confidence': 1.0 if is_in_title else (0.8 if is_in_description else 0.5)
                    })

        return detected

    def get_tool_list(
        self,
        videos: List[Dict]
    ) -> Dict[str, int]:
        """Obtiene lista de herramientas y su frecuencia."""
        tool_counter = Counter()

        for video in videos:
            tools = self.detect_tools(
                video.get('title', ''),
                video.get('description', ''),
                video.get('transcript', '')
            )
            for tool in tools:
                tool_counter[tool['tool']] += 1

        return dict(tool_counter.most_common(20))

    def categorize_tools(
        self,
        videos: List[Dict]
    ) -> Dict[str, List[str]]:
        """Categoriza herramientas por tipo."""
        categories = {}

        for video in videos:
            tools = self.detect_tools(
                video.get('title', ''),
                video.get('description', ''),
                video.get('transcript', '')
            )

            for tool in tools:
                cat = tool['category']
                if cat not in categories:
                    categories[cat] = []
                if tool['tool'] not in categories[cat]:
                    categories[cat].append(tool['tool'])

        return categories

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del detector."""
        return {
            "total_detected": self._detection_count,
            "model": "ToolsDetector v1.0"
        }


def create_tools_detector() -> ToolsDetector:
    """Crea una instancia del detector."""
    return ToolsDetector()


_global_detector: Optional[ToolsDetector] = None


def get_tools_detector() -> ToolsDetector:
    """Obtiene la instancia global."""
    global _global_detector
    if _global_detector is None:
        _global_detector = create_tools_detector()
    return _global_detector