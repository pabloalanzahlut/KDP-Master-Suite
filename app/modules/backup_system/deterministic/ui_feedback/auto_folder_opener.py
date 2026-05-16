"""
Auto Folder Opener
==================
Abre automáticamente la carpeta de backup al completar.
"""

import os
import sys
import subprocess
import threading
from typing import Optional
from pathlib import Path


class AutoFolderOpener:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def open_folder(self, folder_path: str) -> bool:
        if not self.enabled:
            return False
        try:
            path = Path(folder_path)
            if not path.exists():
                path = path.parent
            if not path.exists():
                return False

            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception:
            return False

    def open_async(self, folder_path: str):
        def _open():
            self.open_folder(folder_path)
        thread = threading.Thread(target=_open, daemon=True)
        thread.start()

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def is_enabled(self) -> bool:
        return self.enabled


_global_opener = None


def get_auto_folder_opener(enabled: bool = True) -> AutoFolderOpener:
    global _global_opener
    if _global_opener is None:
        _global_opener = AutoFolderOpener(enabled)
    return _global_opener