"""
Sandbox Isolator
================
Aislamiento de backup en sandbox.
"""

import os
import logging
import tempfile
import shutil
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SandboxIsolator:
    """Aislador de operaciones de backup en sandbox."""

    def __init__(self):
        self.sandbox_dir = None

    def create_sandbox(self, base_path: str = None) -> Tuple[bool, str]:
        try:
            self.sandbox_dir = tempfile.mkdtemp(prefix="backup_sandbox_")
            logger.info(f"Sandbox created: {self.sandbox_dir}")
            return True, self.sandbox_dir
        except Exception as e:
            logger.error(f"Error creating sandbox: {e}")
            return False, str(e)

    def execute_in_sandbox(self, func, *args, **kwargs):
        if self.sandbox_dir is None:
            self.create_sandbox()

        old_cwd = os.getcwd()
        try:
            os.chdir(self.sandbox_dir)
            result = func(*args, **kwargs)
            return result
        finally:
            os.chdir(old_cwd)

    def cleanup_sandbox(self) -> bool:
        if self.sandbox_dir and os.path.exists(self.sandbox_dir):
            try:
                shutil.rmtree(self.sandbox_dir)
                self.sandbox_dir = None
                logger.info("Sandbox cleaned up")
                return True
            except Exception as e:
                logger.error(f"Error cleaning sandbox: {e}")
                return False
        return True

    def __enter__(self):
        self.create_sandbox()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_sandbox()


def create_sandbox() -> Tuple[bool, str]:
    isolator = SandboxIsolator()
    return isolator.create_sandbox()