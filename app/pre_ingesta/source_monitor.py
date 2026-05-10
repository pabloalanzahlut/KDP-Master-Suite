"""
KDP MASTER - Source Monitor (Módulo 7)
===================================
Monitor de disponibilidad de fuente.
"""

import socket
import urllib.request
import urllib.error
from typing import Tuple, Optional
from datetime import datetime


class SourceMonitor:
    """Módulo 7: Monitor de disponibilidad de fuente."""
    
    TIMEOUT_SECONDS = 10
    
    def __init__(self):
        self.ping_results = {}
    
    def check_availability(self, url: str) -> Tuple[bool, str]:
        """
        Realiza ping técnico al servidor de origen.
        Returns: (is_available, status_message)
        """
        try:
            if 'youtube.com' in url:
                return self._check_youtube_source(url)
            
            return True, "Fuente no reconocida, omitiendo verificación"
        
        except Exception as e:
            return False, f"Error verificando: {str(e)}"
    
    def _check_youtube_source(self, url: str) -> Tuple[bool, str]:
        """Verifica fuente YouTube."""
        try:
            test_url = "https://www.youtube.com"
            
            req = urllib.request.Request(
                test_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECONDS) as response:
                if response.status == 200:
                    return True, f"Fuente disponible (HTTP {response.status})"
            
            return False, f"Respuesta inesperada: {response.status}"
        
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.timeout):
                return False, "Timeout de conexión"
            return False, f"Error de conexión: {str(e.reason)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_multiple(self, urls: list) -> dict:
        """Verifica múltiples URLs."""
        results = {}
        
        for url in urls:
            is_available, message = self.check_availability(url)
            results[url] = {
                'available': is_available,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        
        return results
    
    def is_private_or_blocked(self, video_info: dict) -> Tuple[bool, str]:
        """Detecta si video es privado o bloqueado."""
        if not video_info:
            return True, "Sin información del video"
        
        if video_info.get('availability') != 'public':
            return True, f"Video no público: {video_info.get('availability')}"
        
        if video_info.get('age_limit', 0) > 18:
            return True, "Video con restricción de edad"
        
        return False, "Video público disponible"


def create_source_monitor() -> SourceMonitor:
    """Factory function."""
    return SourceMonitor()