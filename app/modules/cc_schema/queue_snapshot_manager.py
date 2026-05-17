"""
Queue Snapshot Manager - Módulo 45
===================================
Gestiona la creación de instantáneas (snapshots) de la cola antes de vaciarla.

¿Para qué sirve esto?
=====================
Imagina que vas a hacer limpieza profunda en tu casa. Antes de tirar cosas,
sacas fotos de todo para poder "volver atrás" si te arrepientes.

Este módulo hace exactamente eso: guardas un "foto" (JSON) de tu cola
antes de vaciarla. Si después te das cuenta de que borraste algo importante,
tienes el snapshot para restaurar.

Caso de uso real:
================
Tu abuela dice: "Voy a tirar toda la ropa vieja del trastero."
Pero antes, hace fotos de cada prenda por si decide recuperar algo.
Después de tirar, se da cuenta que tiró un suéter que le gustaba.
Tiene las fotos y puede buscar uno igual en la tienda.

Aquí es igual: haces snapshot antes de vaciar, luego puedes restaurar lo que sea.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class QueueSnapshotManager:
    """
    Gestor de instantáneas de cola.
    
    Proporciona funcionalidad de "snapshot" (foto) antes de vaciar la cola.
    Permite restauración completa en caso de error humano.
    """

    def __init__(self, snapshot_dir: Optional[Path] = None):
        """
        Inicializa el gestor de snapshots.
        
        Args:
            snapshot_dir: Directorio donde se guardan los snapshots.
                         Si es None, usa el directorio por defecto.
        """
        if snapshot_dir is None:
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent.parent.parent.parent
            snapshot_dir = base_dir / "data" / "queue_snapshots"
        
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        self._max_snapshots = 100
        logger.info(f"QueueSnapshotManager inicializado: {self.snapshot_dir}")

    def create_snapshot(
        self,
        items: List[Any],
        cleared_items: List[Any],
        strategy: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Crea una instantánea de la cola antes del vaciado.
        
        Args:
            items: Lista completa de items en la cola.
            cleared_items: Lista de items que se van a borrar.
            strategy: Estrategia de vaciado usada.
            metadata: Metadatos adicionales (usuario, razón, etc.).

        Returns:
            Ruta al archivo de snapshot o None si falló.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_id = f"{timestamp}_{len(items)}items"
            
            snapshot_data = {
                "snapshot_id": snapshot_id,
                "created_at": datetime.now().isoformat(),
                "strategy": strategy,
                "metadata": metadata or {},
                "total_items": len(items),
                "cleared_count": len(cleared_items),
                "items": [self._item_to_dict(item) for item in items],
                "cleared_items": [self._item_to_dict(item) for item in cleared_items]
            }
            
            filename = f"snapshot_{snapshot_id}.json"
            filepath = self.snapshot_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Snapshot creado: {filepath}")
            
            self._cleanup_old_snapshots()
            
            return str(filepath)

        except Exception as e:
            logger.error(f"Error creando snapshot: {e}")
            return None

    def _item_to_dict(self, item: Any) -> Dict[str, Any]:
        """Convierte un item a diccionario."""
        if hasattr(item, 'to_dict'):
            return item.to_dict()
        elif hasattr(item, '__dict__'):
            return vars(item)
        else:
            return {"url": str(item)}

    def load_snapshot(self, snapshot_path: str) -> Optional[Dict[str, Any]]:
        """
        Carga un snapshot desde archivo.
        
        Args:
            snapshot_path: Ruta al archivo de snapshot.

        Returns:
            Datos del snapshot o None si falló.
        """
        try:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando snapshot: {e}")
            return None

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        Lista todos los snapshots disponibles.
        
        Returns:
            Lista de información de snapshots.
        """
        snapshots = []
        
        for filepath in self.snapshot_dir.glob("snapshot_*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    snapshots.append({
                        "path": str(filepath),
                        "id": data.get("snapshot_id", filepath.stem),
                        "created_at": data.get("created_at", ""),
                        "total_items": data.get("total_items", 0),
                        "cleared_count": data.get("cleared_count", 0),
                        "strategy": data.get("strategy", "unknown")
                    })
            except Exception as e:
                logger.warning(f"Error leyendo snapshot {filepath}: {e}")
        
        return sorted(snapshots, key=lambda x: x.get("created_at", ""), reverse=True)

    def restore_snapshot(self, snapshot_path: str) -> Optional[List[Any]]:
        """
        Restaura los items desde un snapshot.
        
        Args:
            snapshot_path: Ruta al archivo de snapshot.

        Returns:
            Lista de items restaurados o None si falló.
        """
        snapshot = self.load_snapshot(snapshot_path)
        
        if not snapshot:
            return None
        
        from app.services.queue_intelligence import QueueItem
        
        items = []
        for item_data in snapshot.get("items", []):
            try:
                items.append(QueueItem.from_dict(item_data))
            except Exception as e:
                logger.warning(f"Error restaurando item: {e}")
        
        return items

    def delete_snapshot(self, snapshot_path: str) -> bool:
        """
        Elimina un snapshot específico.
        
        Args:
            snapshot_path: Ruta al archivo de snapshot.

        Returns:
            True si se eliminó correctamente.
        """
        try:
            Path(snapshot_path).unlink()
            logger.info(f"Snapshot eliminado: {snapshot_path}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando snapshot: {e}")
            return False

    def _cleanup_old_snapshots(self):
        """Elimina snapshots antiguos si hay demasiados."""
        try:
            snapshots = sorted(
                self.snapshot_dir.glob("snapshot_*.json"),
                key=lambda f: f.stat().st_mtime
            )
            
            if len(snapshots) > self._max_snapshots:
                for old_snapshot in snapshots[:-self._max_snapshots]:
                    old_snapshot.unlink()
                    logger.debug(f"Snapshot antiguo eliminado: {old_snapshot.name}")
        except Exception as e:
            logger.warning(f"Error en cleanup de snapshots: {e}")


def create_snapshot_manager(snapshot_dir: Optional[Path] = None) -> QueueSnapshotManager:
    """
    Factory function para crear una instancia de QueueSnapshotManager.
    """
    return QueueSnapshotManager(snapshot_dir=snapshot_dir)