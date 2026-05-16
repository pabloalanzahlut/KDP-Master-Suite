"""
Theme Manager
=============
Gestiona temas de la UI.
"""

from typing import Dict


class ThemeManager:
    def __init__(self):
        self.current_theme = "dark"

    def set_theme(self, theme: str):
        self.current_theme = theme

    def get_theme(self) -> Dict:
        return {"theme": self.current_theme, "colors": {"primary": "#1a1a2e", "accent": "#e94560"}}


def get_theme_manager():
    return ThemeManager()