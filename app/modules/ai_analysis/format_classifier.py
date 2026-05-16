"""
P1-7: Identificación de Formato (Live vs Editado)
"""
from typing import Dict


class FormatClassifier:
    LIVE_INDICATORS = ['live', 'directo', 'en vivo', 'streaming']

    def classify(self, title: str, description: str = "") -> Dict:
        content = f"{title.lower()} {description.lower()}"
        is_live = any(ind in content for ind in self.LIVE_INDICATORS)
        return {'format': 'live' if is_live else 'edited', 'confidence': 0.8}


def get_format_classifier():
    return FormatClassifier()