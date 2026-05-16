"""
Módulo P1-4: Cache de Miniaturas en Disco
Guarda thumbnails localmente para evitar re-descargarlas.
"""
import os
import hashlib
import urllib.request
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ThumbnailCache:
    """Cache de miniaturas en disco para evitar re-descargas."""

    DEFAULT_CACHE_DIR = Path("cache/thumbnails")
    DEFAULT_MAX_AGE_DAYS = 30
    DEFAULT_MAX_SIZE_MB = 500

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS,
        max_size_mb: int = DEFAULT_MAX_SIZE_MB
    ):
        self.cache_dir = Path(cache_dir) if cache_dir else self.DEFAULT_CACHE_DIR
        self.max_age_days = max_age_days
        self.max_size_mb = max_size_mb
        self._init_cache_dir()

    def _init_cache_dir(self):
        """Inicializa el directorio de cache."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache de miniaturas inicializado en: {self.cache_dir}")
        except Exception as e:
            logger.error(f"Error al crear directorio de cache: {e}")
            self.cache_dir = Path(tempfile.gettempdir()) / "kdp_thumbnails"
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, video_id: str, resolution: str = "default") -> str:
        """Genera una clave única para el cache basada en video_id y resolución."""
        raw = f"{video_id}_{resolution}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_cache_path(self, video_id: str, resolution: str = "default") -> Path:
        """Obtiene la ruta del archivo cache para un video."""
        cache_key = self._get_cache_key(video_id, resolution)
        extension = "jpg"
        return self.cache_dir / f"{cache_key}.{extension}"

    def get(self, video_id: str, resolution: str = "default") -> Optional[str]:
        """
        Recupera una miniatura del cache si existe y no ha expirado.
        Returns: Ruta local de la miniatura o None si no existe/expiró.
        """
        cache_path = self._get_cache_path(video_id, resolution)

        if not cache_path.exists():
            return None

        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if file_age > timedelta(days=self.max_age_days):
            try:
                cache_path.unlink()
                logger.debug(f"Miniatura expirada eliminada: {video_id}")
            except Exception:
                pass
            return None

        return str(cache_path)

    def set(self, video_id: str, thumbnail_url: str, resolution: str = "default") -> Optional[str]:
        """
        Descarga y guarda una miniatura en cache.
        Returns: Ruta local de la miniatura guardada o None si falló.
        """
        cache_path = self._get_cache_path(video_id, resolution)

        if cache_path.exists():
            return str(cache_path)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            request = urllib.request.Request(thumbnail_url, headers=headers)
            with urllib.request.urlopen(request, timeout=10) as response:
                image_data = response.read()
                with open(cache_path, 'wb') as f:
                    f.write(image_data)
                logger.debug(f"Minatura cacheada: {video_id}")
                return str(cache_path)
        except Exception as e:
            logger.warning(f"Error cacheando miniatura {video_id}: {e}")
            return None

    def clear_expired(self) -> int:
        """Elimina miniaturas expiradas. Returns: Cantidad eliminada."""
        removed = 0
        try:
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    file_age = datetime.now() - datetime.fromtimestamp(file.stat().st_mtime)
                    if file_age > timedelta(days=self.max_age_days):
                        try:
                            file.unlink()
                            removed += 1
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Error limpiando cache expirado: {e}")
        return removed

    def get_cache_size(self) -> Tuple[int, int]:
        """
        Retorna el tamaño actual del cache en bytes y cantidad de archivos.
        """
        total_size = 0
        file_count = 0
        try:
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    total_size += file.stat().st_size
                    file_count += 1
        except Exception:
            pass
        return total_size, file_count

    def clear_all(self) -> int:
        """Limpia todo el cache. Returns: Cantidad de archivos eliminados."""
        removed = 0
        try:
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                        removed += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Error limpiando cache: {e}")
        return removed

    def enforce_size_limit(self) -> int:
        """
        Elimina las miniaturas más antiguas si se supera el límite de tamaño.
        Returns: Cantidad de archivos eliminados.
        """
        current_size_bytes, file_count = self.get_cache_size()
        max_bytes = self.max_size_mb * 1024 * 1024

        if current_size_bytes <= max_bytes:
            return 0

        removed = 0
        files_with_age = []
        try:
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    files_with_age.append((file, file.stat().st_mtime))

            files_with_age.sort(key=lambda x: x[1])

            for file, _ in files_with_age:
                if current_size_bytes <= max_bytes:
                    break
                try:
                    size = file.stat().st_size
                    file.unlink()
                    current_size_bytes -= size
                    removed += 1
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error aplicando límite de tamaño: {e}")
        return removed


_global_cache: Optional[ThumbnailCache] = None


def get_thumbnail_cache(
    cache_dir: Optional[str] = None,
    max_age_days: int = 30,
    max_size_mb: int = 500
) -> ThumbnailCache:
    """Obtiene la instancia global del cache de miniaturas."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ThumbnailCache(cache_dir, max_age_days, max_size_mb)
    return _global_cache