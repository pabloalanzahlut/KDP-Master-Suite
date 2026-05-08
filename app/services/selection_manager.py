"""
Selection Manager - Temporary Multi-Selection System
====================================================
Sistema de selección temporal en memoria para validar UX sin cambios en BD.
"""

from typing import Set, List, Dict, Optional
from datetime import datetime


class SelectionManager:
    """
    Gestor de selección temporal para videos, canales y playlists.
    Mantiene el estado de selección en memoria (no persiste en BD).
    """
    
    def __init__(self):
        """Inicializa el gestor de selección."""
        # Sets para diferentes tipos de selección
        self.selected_videos: Set[int] = set()
        self.selected_channels: Set[int] = set()
        self.selected_files: Set[str] = set()
        
        # Metadata de selección
        self.selection_metadata: Dict[str, any] = {
            'last_selection_time': None,
            'selection_count': 0
        }
    
    # ==================== VIDEOS ====================
    
    def toggle_video(self, video_id: int) -> bool:
        """
        Marca/desmarca un video.
        
        Args:
            video_id: ID del video
        
        Returns:
            True si ahora está seleccionado, False si fue desmarcado
        """
        if video_id in self.selected_videos:
            self.selected_videos.remove(video_id)
            self._update_metadata()
            return False
        else:
            self.selected_videos.add(video_id)
            self._update_metadata()
            return True
    
    def select_video(self, video_id: int):
        """Marca un video como seleccionado."""
        self.selected_videos.add(video_id)
        self._update_metadata()
    
    def deselect_video(self, video_id: int):
        """Desmarca un video."""
        self.selected_videos.discard(video_id)
        self._update_metadata()
    
    def is_video_selected(self, video_id: int) -> bool:
        """Verifica si un video está seleccionado."""
        return video_id in self.selected_videos
    
    def get_selected_videos(self) -> List[int]:
        """Retorna lista de IDs de videos seleccionados."""
        return list(self.selected_videos)
    
    def select_all_videos(self, video_ids: List[int]):
        """Selecciona todos los videos de la lista."""
        self.selected_videos.update(video_ids)
        self._update_metadata()
    
    def deselect_all_videos(self):
        """Desmarca todos los videos."""
        self.selected_videos.clear()
        self._update_metadata()
    
    def get_video_selection_count(self) -> int:
        """Retorna el número de videos seleccionados."""
        return len(self.selected_videos)
    
    # ==================== CANALES ====================
    
    def toggle_channel(self, channel_id: int) -> bool:
        """
        Marca/desmarca un canal.
        
        Args:
            channel_id: ID del canal
        
        Returns:
            True si ahora está seleccionado, False si fue desmarcado
        """
        if channel_id in self.selected_channels:
            self.selected_channels.remove(channel_id)
            self._update_metadata()
            return False
        else:
            self.selected_channels.add(channel_id)
            self._update_metadata()
            return True
    
    def select_channel(self, channel_id: int):
        """Marca un canal como seleccionado."""
        self.selected_channels.add(channel_id)
        self._update_metadata()
    
    def deselect_channel(self, channel_id: int):
        """Desmarca un canal."""
        self.selected_channels.discard(channel_id)
        self._update_metadata()
    
    def is_channel_selected(self, channel_id: int) -> bool:
        """Verifica si un canal está seleccionado."""
        return channel_id in self.selected_channels
    
    def get_selected_channels(self) -> List[int]:
        """Retorna lista de IDs de canales seleccionados."""
        return list(self.selected_channels)
    
    def select_all_channels(self, channel_ids: List[int]):
        """Selecciona todos los canales de la lista."""
        self.selected_channels.update(channel_ids)
        self._update_metadata()
    
    def deselect_all_channels(self):
        """Desmarca todos los canales."""
        self.selected_channels.clear()
        self._update_metadata()
    
    def get_channel_selection_count(self) -> int:
        """Retorna el número de canales seleccionados."""
        return len(self.selected_channels)
    
    # ==================== ARCHIVOS ====================
    
    def toggle_file(self, filename: str) -> bool:
        """
        Marca/desmarca un archivo.
        
        Args:
            filename: Nombre del archivo
        
        Returns:
            True si ahora está seleccionado, False si fue desmarcado
        """
        if filename in self.selected_files:
            self.selected_files.remove(filename)
            self._update_metadata()
            return False
        else:
            self.selected_files.add(filename)
            self._update_metadata()
            return True
    
    def select_file(self, filename: str):
        """Marca un archivo como seleccionado."""
        self.selected_files.add(filename)
        self._update_metadata()
    
    def deselect_file(self, filename: str):
        """Desmarca un archivo."""
        self.selected_files.discard(filename)
        self._update_metadata()
    
    def is_file_selected(self, filename: str) -> bool:
        """Verifica si un archivo está seleccionado."""
        return filename in self.selected_files
    
    def get_selected_files(self) -> List[str]:
        """Retorna lista de archivos seleccionados."""
        return list(self.selected_files)
    
    def select_all_files(self, filenames: List[str]):
        """Selecciona todos los archivos de la lista."""
        self.selected_files.update(filenames)
        self._update_metadata()
    
    def deselect_all_files(self):
        """Desmarca todos los archivos."""
        self.selected_files.clear()
        self._update_metadata()
    
    def get_file_selection_count(self) -> int:
        """Retorna el número de archivos seleccionados."""
        return len(self.selected_files)
    
    # ==================== OPERACIONES GLOBALES ====================
    
    def clear_all_selections(self):
        """Limpia todas las selecciones (videos, canales, archivos)."""
        self.selected_videos.clear()
        self.selected_channels.clear()
        self.selected_files.clear()
        self._update_metadata()
    
    def get_total_selection_count(self) -> int:
        """Retorna el total de items seleccionados."""
        return (len(self.selected_videos) + 
                len(self.selected_channels) + 
                len(self.selected_files))
    
    def has_selections(self) -> bool:
        """Verifica si hay algún item seleccionado."""
        return self.get_total_selection_count() > 0
    
    def get_selection_summary(self) -> Dict[str, int]:
        """Retorna un resumen de las selecciones actuales."""
        return {
            'videos': len(self.selected_videos),
            'channels': len(self.selected_channels),
            'files': len(self.selected_files),
            'total': self.get_total_selection_count()
        }
    
    # ==================== OPERACIONES POR LOTES ====================
    
    def select_videos_by_channel(self, channel_id: int, video_ids: List[int]):
        """Selecciona todos los videos de un canal específico."""
        self.selected_videos.update(video_ids)
        self._update_metadata()
    
    def deselect_videos_by_channel(self, video_ids: List[int]):
        """Desmarca todos los videos de un canal específico."""
        for video_id in video_ids:
            self.selected_videos.discard(video_id)
        self._update_metadata()
    
    def invert_video_selection(self, all_video_ids: List[int]):
        """Invierte la selección de videos."""
        current = set(self.selected_videos)
        all_set = set(all_video_ids)
        self.selected_videos = all_set - current
        self._update_metadata()
    
    def invert_channel_selection(self, all_channel_ids: List[int]):
        """Invierte la selección de canales."""
        current = set(self.selected_channels)
        all_set = set(all_channel_ids)
        self.selected_channels = all_set - current
        self._update_metadata()
    
    def invert_file_selection(self, all_filenames: List[str]):
        """Invierte la selección de archivos."""
        current = set(self.selected_files)
        all_set = set(all_filenames)
        self.selected_files = all_set - current
        self._update_metadata()
    
    # ==================== FILTROS ====================
    
    def filter_selected_by_status(self, videos_with_status: List[Dict], 
                                  status: str) -> List[int]:
        """
        Filtra videos seleccionados por estado.
        
        Args:
            videos_with_status: Lista de videos con campo 'status'
            status: Estado a filtrar ('pending', 'completed', etc.)
        
        Returns:
            Lista de IDs de videos seleccionados con ese estado
        """
        return [
            v['id'] for v in videos_with_status 
            if v['id'] in self.selected_videos and v.get('status') == status
        ]
    
    # ==================== METADATA ====================
    
    def _update_metadata(self):
        """Actualiza metadata de selección."""
        self.selection_metadata['last_selection_time'] = datetime.now()
        self.selection_metadata['selection_count'] = self.get_total_selection_count()
    
    def get_metadata(self) -> Dict[str, any]:
        """Retorna metadata de selección."""
        return {
            **self.selection_metadata,
            'summary': self.get_selection_summary()
        }
    
    # ==================== EXPORT/IMPORT ====================
    
    def export_selection(self) -> Dict[str, List]:
        """
        Exporta la selección actual a un diccionario.
        Útil para guardar temporalmente o compartir entre componentes.
        """
        return {
            'videos': list(self.selected_videos),
            'channels': list(self.selected_channels),
            'files': list(self.selected_files),
            'timestamp': datetime.now().isoformat()
        }
    
    def import_selection(self, selection_data: Dict[str, List]):
        """
        Importa una selección desde un diccionario.
        
        Args:
            selection_data: Diccionario con formato de export_selection()
        """
        self.selected_videos = set(selection_data.get('videos', []))
        self.selected_channels = set(selection_data.get('channels', []))
        self.selected_files = set(selection_data.get('files', []))
        self._update_metadata()
    
    # ==================== UTILIDADES ====================
    
    def __repr__(self) -> str:
        """Representación string del gestor."""
        summary = self.get_selection_summary()
        return (f"SelectionManager(videos={summary['videos']}, "
                f"channels={summary['channels']}, "
                f"files={summary['files']})")
    
    def __len__(self) -> int:
        """Retorna el total de items seleccionados."""
        return self.get_total_selection_count()
    
    def __bool__(self) -> bool:
        """Retorna True si hay selecciones."""
        return self.has_selections()


# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    # Crear gestor
    manager = SelectionManager()
    
    # Seleccionar videos
    manager.select_video(1)
    manager.select_video(2)
    manager.toggle_video(3)  # Selecciona
    
    print(f"Videos seleccionados: {manager.get_selected_videos()}")
    print(f"Total: {manager.get_video_selection_count()}")
    
    # Seleccionar canales
    manager.select_channel(10)
    manager.select_channel(20)
    
    # Resumen
    print(f"\nResumen: {manager.get_selection_summary()}")
    print(f"Tiene selecciones: {manager.has_selections()}")
    
    # Exportar
    exported = manager.export_selection()
    print(f"\nExportado: {exported}")
    
    # Limpiar y reimportar
    manager.clear_all_selections()
    print(f"Después de limpiar: {manager.get_selection_summary()}")
    
    manager.import_selection(exported)
    print(f"Después de importar: {manager.get_selection_summary()}")
