"""
KDP_MASTER - Push Notification Module
======================================
Sistema de notificaciones push configurables con umbrales de alerta.
"""

import time
import threading
from typing import Optional

try:
    from app.ui.components.notifications import ToastNotification
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False


class PushNotification:
    """
    Sistema de notificaciones push con umbrales configurables.
    Solo envía notificaciones cuando se supera el umbral de videos nuevos
    en una ventana de tiempo específica.
    """
    
    DEFAULT_THRESHOLD_VIDEOS = 5
    DEFAULT_WINDOW_MINUTES = 30
    
    def __init__(self):
        self._lock = threading.Lock()
        self._video_counts = []
        self._last_notification = 0
        self._threshold_videos = self.DEFAULT_THRESHOLD_VIDEOS
        self._window_minutes = self.DEFAULT_WINDOW_MINUTES
        self._enabled = True
    
    def configure(self, threshold_videos: int = None, window_minutes: int = None, enabled: bool = True):
        """Configura los parámetros del sistema de notificaciones."""
        with self._lock:
            if threshold_videos is not None:
                self._threshold_videos = max(1, min(50, threshold_videos))
            if window_minutes is not None:
                self._window_minutes = max(1, min(1440, window_minutes))
            self._enabled = enabled
    
    def should_notify(self, new_videos_count: int) -> bool:
        """
        Determina si se debe enviar una notificación basándose en el umbral.
        
        Args:
            new_videos_count: Número de videos nuevos detectados
            
        Returns:
            True si se debe notificar
        """
        if not self._enabled:
            return False
        
        if new_videos_count <= 0:
            return False
        
        with self._lock:
            current_time = time.time()
            window_seconds = self._window_minutes * 60
            
            self._video_counts = [
                (count, timestamp) for count, timestamp in self._video_counts
                if current_time - timestamp < window_seconds
            ]
            
            self._video_counts.append((new_videos_count, current_time))
            
            total_in_window = sum(count for count, _ in self._video_counts)
            
            if total_in_window >= self._threshold_videos:
                if current_time - self._last_notification >= window_seconds:
                    self._last_notification = current_time
                    self._video_counts = []
                    return True
            
            return False
    
    def send(self, title: str, message: str, parent=None):
        """Envía una notificación toast."""
        if not TOAST_AVAILABLE:
            return
        
        try:
            if parent is None:
                class MockParent:
                    def winfo_screenwidth(self):
                        return 1920
                parent = MockParent()
            
            ToastNotification.show(parent, message, type="info", duration=5000)
        except Exception:
            pass
    
    def get_config(self) -> dict:
        """Obtiene la configuración actual."""
        with self._lock:
            return {
                "threshold_videos": self._threshold_videos,
                "window_minutes": self._window_minutes,
                "enabled": self._enabled
            }
    
    def reset(self):
        """Resetea el contador de notificaciones."""
        with self._lock:
            self._video_counts = []
            self._last_notification = 0


push_notifier = PushNotification()