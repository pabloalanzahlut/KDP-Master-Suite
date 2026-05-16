"""
Módulos P2: Validación de Integridad de Contenido
- P2-11: Check de Hash en DB Local
- P2-12: Validación de Estado "Procesado"
"""
import hashlib
import logging
from typing import Optional, Dict, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ContentHash:
    """Hash de contenido de un video."""
    video_id: str
    content_hash: str
    algorithm: str
    calculated_at: str
    file_size: int


class ContentHasher:
    """Gestor de hashes de contenido para deduplicación."""

    DEFAULT_HASH_DIR = "data/hashes"
    SUPPORTED_ALGORITHMS = ['md5', 'sha256', 'sha1']

    def __init__(self, storage_dir: Optional[str] = None, algorithm: str = 'md5'):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(self.DEFAULT_HASH_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.algorithm = algorithm
        self._hash_cache: Dict[str, str] = {}

    def calculate_hash(self, content: str) -> str:
        """Calcula hash de contenido de texto."""
        if self.algorithm == 'md5':
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        elif self.algorithm == 'sha256':
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        elif self.algorithm == 'sha1':
            return hashlib.sha1(content.encode('utf-8')).hexdigest()
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calcula hash de archivo."""
        try:
            if self.algorithm == 'md5':
                return hashlib.md5(file_path.read_bytes()).hexdigest()
            elif self.algorithm == 'sha256':
                return hashlib.sha256(file_path.read_bytes()).hexdigest()
            return hashlib.md5(file_path.read_bytes()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculando hash de {file_path}: {e}")
            return None

    def check_hash_exists(self, content: str) -> bool:
        """
        P2-11: Verifica si el hash ya existe en cache.
        Args:
            content: Contenido a verificar
        Returns:
            True si el hash ya existe
        """
        content_hash = self.calculate_hash(content)
        return content_hash in self._hash_cache

    def register_hash(self, video_id: str, content: str, file_size: int = 0) -> ContentHash:
        """Registra un nuevo hash."""
        content_hash = self.calculate_hash(content)
        now = datetime.now().isoformat()

        self._hash_cache[content_hash] = video_id

        return ContentHash(
            video_id=video_id,
            content_hash=content_hash,
            algorithm=self.algorithm,
            calculated_at=now,
            file_size=file_size
        )

    def find_duplicate(self, content: str) -> Optional[str]:
        """Encuentra video duplicado por hash."""
        content_hash = self.calculate_hash(content)
        return self._hash_cache.get(content_hash)

    def remove_hash(self, content_hash: str):
        """Remueve un hash del cache."""
        if content_hash in self._hash_cache:
            del self._hash_cache[content_hash]

    def get_cache_size(self) -> int:
        """Retorna cantidad de hashes en cache."""
        return len(self._hash_cache)

    def clear_cache(self):
        """Limpia el cache de hashes."""
        self._hash_cache.clear()
        logger.info("Cache de hashes limpiado")


def create_content_hasher(algorithm: str = 'md5') -> ContentHasher:
    """Crea una instancia del gestor de hashes."""
    return ContentHasher(algorithm=algorithm)


_global_hasher: Optional[ContentHasher] = None


def get_content_hasher() -> ContentHasher:
    """Obtiene la instancia global del gestor de hashes."""
    global _global_hasher
    if _global_hasher is None:
        _global_hasher = create_content_hasher()
    return _global_hasher