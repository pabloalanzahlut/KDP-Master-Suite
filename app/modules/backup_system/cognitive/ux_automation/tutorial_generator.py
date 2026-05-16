"""
Tutorial Generator
==================
Genera tutoriales de uso.
"""

from typing import Dict, List


class TutorialGenerator:
    def generate(self, topic: str) -> Dict:
        steps = [{"step": 1, "action": "Abre la app"}, {"step": 2, "action": "Usa el botón de pánico"}]
        return {"topic": topic, "steps": steps, "duration_minutes": 2}


def get_tutorial_generator():
    return TutorialGenerator()