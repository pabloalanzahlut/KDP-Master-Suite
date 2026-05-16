"""
Módulos P4: Selección Masiva Inteligente
- P4-37: Guardar Selección como "Grupo"
- P4-39: Confirmación de Volumen
- P4-40: Estimación de Espacio Total
"""
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class VideoSelection:
    """Representa un video seleccionado."""
    video_id: str
    title: str
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    duration_seconds: Optional[int] = None
    discovered_at: Optional[str] = None
    status: str = "pending"


@dataclass
class SelectionGroup:
    """Grupo de videos seleccionados."""
    id: str
    name: str
    description: str
    videos: List[VideoSelection]
    created_at: str
    updated_at: str
    estimated_size_mb: float = 0.0
    estimated_duration_hours: float = 0.0


class BatchGroupManager:
    """Gestor de grupos de selección masiva."""

    DEFAULT_STORAGE_DIR = Path("data/selection_groups")
    DEFAULT_AVG_SIZE_MB = 5.0
    DEFAULT_AVG_DURATION_SEC = 600

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else self.DEFAULT_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._current_group: Optional[SelectionGroup] = None

    def create_group(
        self,
        name: str,
        description: str = "",
        videos: Optional[List[Dict]] = None
    ) -> SelectionGroup:
        """Crea un nuevo grupo de selección."""
        video_list = []
        estimated_size = 0.0
        estimated_duration = 0

        if videos:
            for v in videos:
                video = VideoSelection(
                    video_id=v.get('id', str(uuid.uuid4())),
                    title=v.get('title', 'Sin título'),
                    channel_id=v.get('channel_id'),
                    channel_name=v.get('channel_name'),
                    duration_seconds=v.get('duration_seconds'),
                    discovered_at=v.get('discovered_at'),
                    status=v.get('status', 'pending')
                )
                video_list.append(video)
                size = v.get('duration_seconds', self.DEFAULT_AVG_DURATION_SEC) / 1024 * 0.5
                estimated_size += size
                estimated_duration += v.get('duration_seconds', self.DEFAULT_AVG_DURATION_SEC)

        now = datetime.now().isoformat()
        group = SelectionGroup(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            videos=video_list,
            created_at=now,
            updated_at=now,
            estimated_size_mb=round(estimated_size, 2),
            estimated_duration_hours=round(estimated_duration / 3600, 2)
        )

        self._save_group(group)
        self._current_group = group
        logger.info(f"Grupo creado: {name} con {len(video_list)} videos")
        return group

    def add_to_group(self, group_id: str, video: Dict) -> bool:
        """Agrega un video a un grupo existente."""
        group = self._load_group(group_id)
        if not group:
            return False

        video_obj = VideoSelection(
            video_id=video.get('id', str(uuid.uuid4())),
            title=video.get('title', 'Sin título'),
            channel_id=video.get('channel_id'),
            channel_name=video.get('channel_name'),
            duration_seconds=video.get('duration_seconds'),
            discovered_at=video.get('discovered_at'),
            status=video.get('status', 'pending')
        )

        if any(v.video_id == video_obj.video_id for v in group.videos):
            logger.warning(f"Video {video_obj.video_id} ya está en el grupo")
            return False

        group.videos.append(video_obj)
        group.updated_at = datetime.now().isoformat()

        group.estimated_size_mb = sum(
            (v.duration_seconds or self.DEFAULT_AVG_DURATION_SEC) / 1024 * 0.5
            for v in group.videos
        )
        group.estimated_duration_hours = sum(
            v.duration_seconds or self.DEFAULT_AVG_DURATION_SEC
            for v in group.videos
        ) / 3600

        self._save_group(group)
        return True

    def remove_from_group(self, group_id: str, video_id: str) -> bool:
        """Remueve un video de un grupo."""
        group = self._load_group(group_id)
        if not group:
            return False

        group.videos = [v for v in group.videos if v.video_id != video_id]
        group.updated_at = datetime.now().isoformat()

        group.estimated_size_mb = sum(
            (v.duration_seconds or self.DEFAULT_AVG_DURATION_SEC) / 1024 * 0.5
            for v in group.videos
        )
        group.estimated_duration_hours = sum(
            v.duration_seconds or self.DEFAULT_AVG_DURATION_SEC
            for v in group.videos
        ) / 3600

        self._save_group(group)
        return True

    def get_group(self, group_id: str) -> Optional[SelectionGroup]:
        """Obtiene un grupo por ID."""
        return self._load_group(group_id)

    def list_groups(self) -> List[SelectionGroup]:
        """Lista todos los grupos guardados."""
        groups = []
        try:
            for file in self.storage_dir.glob("*.json"):
                group = self._load_group_from_file(file)
                if group:
                    groups.append(group)
        except Exception as e:
            logger.error(f"Error listando grupos: {e}")
        return sorted(groups, key=lambda g: g.updated_at, reverse=True)

    def delete_group(self, group_id: str) -> bool:
        """Elimina un grupo."""
        file_path = self.storage_dir / f"{group_id}.json"
        if file_path.exists():
            file_path.unlink()
            if self._current_group and self._current_group.id == group_id:
                self._current_group = None
            return True
        return False

    def estimate_space(self, videos: List[Dict], include_processing: bool = True) -> Dict:
        """
        Estima el espacio total requerido para los videos.
        Returns: Diccionario con estimaciones de tamaño y duración.
        """
        total_duration_sec = 0
        total_processed_size_mb = 0
        count = len(videos)

        for v in videos:
            duration = v.get('duration_seconds', self.DEFAULT_AVG_DURATION_SEC)
            total_duration_sec += duration
            total_processed_size_mb += duration / 1024 * 0.5

        return {
            "video_count": count,
            "total_duration_seconds": total_duration_sec,
            "total_duration_hours": round(total_duration_sec / 3600, 2),
            "estimated_download_mb": round(total_duration_sec / 1024 * 0.5, 2),
            "estimated_download_gb": round(total_duration_sec / 1024 / 1024 * 0.5, 2),
            "estimated_processed_mb": round(total_processed_size_mb, 2) if include_processed else 0,
            "estimated_processed_gb": round(total_processed_size_mb / 1024, 2) if include_processed else 0,
            "avg_duration_minutes": round(total_duration_sec / count / 60, 1) if count > 0 else 0,
            "avg_size_mb": round(total_processed_size_mb / count, 2) if count > 0 else 0
        }

    def volume_confirmation(
        self,
        count: int,
        threshold: int = 100,
        action: str = "descargar"
    ) -> Tuple[bool, str]:
        """
        P4-39: Confirmación de Volumen
        Solicita confirmación si el número de videos excede el threshold.
        Returns: (confirmed: bool, message: str)
        """
        if count <= threshold:
            return True, f"Procediendo con {count} videos a {action}"

        message = (
            f"⚠️ Cantidad elevada: ¿Estás seguro de {action} {count} videos?\n\n"
            f"Esta operación puede tomar un tiempo considerable y consumir "
            f"recursos significativos del sistema.\n\n"
            f"Recomendación: Usa filtros para reducir la selección o "
            f"procesa en lotes más pequeños."
        )
        return False, message

    def _save_group(self, group: SelectionGroup):
        """Guarda un grupo en archivo JSON."""
        file_path = self.storage_dir / f"{group.id}.json"
        data = {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "videos": [asdict(v) for v in group.videos],
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "estimated_size_mb": group.estimated_size_mb,
            "estimated_duration_hours": group.estimated_duration_hours
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando grupo: {e}")

    def _load_group(self, group_id: str) -> Optional[SelectionGroup]:
        """Carga un grupo desde archivo."""
        file_path = self.storage_dir / f"{group_id}.json"
        return self._load_group_from_file(file_path)

    def _load_group_from_file(self, file_path: Path) -> Optional[SelectionGroup]:
        """Carga un grupo desde un archivo."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            videos = [VideoSelection(**v) for v in data.get('videos', [])]
            return SelectionGroup(
                id=data['id'],
                name=data['name'],
                description=data.get('description', ''),
                videos=videos,
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                estimated_size_mb=data.get('estimated_size_mb', 0),
                estimated_duration_hours=data.get('estimated_duration_hours', 0)
            )
        except Exception as e:
            logger.error(f"Error cargando grupo desde {file_path}: {e}")
            return None


_global_manager: Optional[BatchGroupManager] = None


def get_batch_group_manager() -> BatchGroupManager:
    """Obtiene la instancia global del gestor de grupos."""
    global _global_manager
    if _global_manager is None:
        _global_manager = BatchGroupManager()
    return _global_manager