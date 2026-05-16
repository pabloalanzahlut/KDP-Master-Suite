"""
Language Selector
=================
Selector de idioma.
"""

from typing import Dict


class LanguageSelector:
    def __init__(self):
        self.current = "es"
        self.languages = {"es": "Español", "en": "English"}

    def set_language(self, lang: str):
        if lang in self.languages:
            self.current = lang

    def get_language(self) -> str:
        return self.current


def get_language_selector():
    return LanguageSelector()