"""
Módulo 4: Pre-Verificador de Espacio para Texto
Calcula KB estimados del texto extraído (no GB de video) y bloquea si hay riesgo de saturación.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import shutil
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MIN_FREE_SPACE_MB = 100
MAX_TEXT_SIZE_MB = 50
KB_PER_SUBTITLE = 50


@dataclass
class SpaceCheckResult:
    can_proceed: bool
    free_space_mb: float
    estimated_size_kb: int
    text_file_count: int
    warning: Optional[str] = None
    error: Optional[str] = None


class SpaceValidator:
    """
    Pre-verificador de Espacio para Texto
    Calcula KB estimados del texto extraído y bloquea si hay riesgo.
    """

    def __init__(self, min_free_mb: int = MIN_FREE_SPACE_MB, max_text_mb: int = MAX_TEXT_SIZE_MB):
        self.min_free_mb = min_free_mb
        self.max_text_mb = max_text_mb

    def check_available_space(self, target_dir: str) -> SpaceCheckResult:
        """
        Verifica espacio disponible en disco.

        Args:
            target_dir: Directorio objetivo

        Returns:
            SpaceCheckResult con estado de espacio
        """
        try:
            if not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    return SpaceCheckResult(
                        can_proceed=True,
                        free_space_mb=0,
                        estimated_size_kb=0,
                        text_file_count=0,
                        warning="Directory created"
                    )
                except Exception as e:
                    return SpaceCheckResult(
                        can_proceed=False,
                        free_space_mb=0,
                        estimated_size_kb=0,
                        text_file_count=0,
                        error=f"Cannot create directory: {e}"
                    )

            total, _, free = shutil.disk_usage(target_dir)
            free_mb = free / (1024 * 1024)

            if free_mb < self.min_free_mb:
                return SpaceCheckResult(
                    can_proceed=False,
                    free_space_mb=free_mb,
                    estimated_size_kb=0,
                    text_file_count=0,
                    error=f"Insufficient space: {free_mb:.1f}MB < {self.min_free_mb}MB minimum"
                )

            return SpaceCheckResult(
                can_proceed=True,
                free_space_mb=free_mb,
                estimated_size_kb=0,
                text_file_count=0,
                warning=f"Free space: {free_mb:.1f}MB" if free_mb < 500 else None
            )

        except Exception as e:
            logger.error(f"Space check failed: {e}")
            return SpaceCheckResult(
                can_proceed=False,
                free_space_mb=0,
                estimated_size_kb=0,
                text_file_count=0,
                error=str(e)
            )

    def estimate_text_size(self, subtitle_count: int, avg_words_per_sub: int = 50) -> int:
        """
        Estima el tamaño en KB del texto a extraer.

        Args:
            subtitle_count: Número de subtítulos
            avg_words_per_sub: Promedio de palabras por subtítulo

        Returns:
            Tamaño estimado en KB
        """
        total_words = subtitle_count * avg_words_per_sub
        estimated_kb = (total_words * 2) // 1024
        return max(estimated_kb, KB_PER_SUBTITLE)

    def check_batch_size(self, target_dir: str, batch_size: int) -> SpaceCheckResult:
        """
        Verifica si hay espacio suficiente para un batch de N videos.

        Args:
            target_dir: Directorio objetivo
            batch_size: Número de videos en el batch

        Returns:
            SpaceCheckResult
        """
        base_check = self.check_available_space(target_dir)
        if not base_check.can_proceed:
            return base_check

        estimated_kb = self.estimate_text_size(batch_size * 100)
        estimated_mb = estimated_kb / 1024

        if base_check.free_space_mb < estimated_mb + self.min_free_mb:
            return SpaceCheckResult(
                can_proceed=False,
                free_space_mb=base_check.free_space_mb,
                estimated_size_kb=estimated_kb,
                text_file_count=batch_size,
                error=f"Batch too large: needs {estimated_mb:.1f}MB, only {base_check.free_space_mb:.1f}MB free"
            )

        return SpaceCheckResult(
            can_proceed=True,
            free_space_mb=base_check.free_space_mb,
            estimated_size_kb=estimated_kb,
            text_file_count=batch_size,
            warning=f"Estimated batch size: {estimated_kb}KB" if estimated_kb > 5000 else None
        )

    def can_store_file(self, target_dir: str, content: str) -> bool:
        """
        Verifica si se puede almacenar el contenido dado.

        Args:
            target_dir: Directorio objetivo
            content: Contenido a almacenar

        Returns:
            True si hay espacio suficiente
        """
        content_size_kb = len(content.encode('utf-8')) // 1024

        try:
            _, _, free = shutil.disk_usage(target_dir)
            free_mb = free / (1024 * 1024)

            return free_mb > (content_size_kb / 1024) + self.min_free_mb
        except Exception:
            return True


def create_validator(min_free_mb: int = MIN_FREE_SPACE_MB) -> SpaceValidator:
    """
    Factory function para crear el validador de espacio.
    """
    return SpaceValidator(min_free_mb=min_free_mb)