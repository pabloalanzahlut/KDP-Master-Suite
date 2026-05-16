"""
Shortcut Manager
================
Gestiona atajos de teclado.
"""

from typing import Dict


class ShortcutManager:
    def __init__(self):
        self.shortcuts = {"Ctrl+B": "backup", "Ctrl+R": "restore", "Ctrl+P": "panic"}

    def get_all(self) -> Dict:
        return self.shortcuts


def get_shortcut_manager():
    return ShortcutManager()