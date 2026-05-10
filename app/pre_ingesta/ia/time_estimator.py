"""
KDP MASTER - Time Estimator (Módulo 16)
===================================
Estimador cognitivo de tiempo de proceso.
"""

from typing import Dict, Any, Tuple


class TimeEstimator:
    """Módulo 16: Estimador de tiempo de proceso."""
    
    BASE_DOWNLOAD_SPEED_MBPS = 5.0
    BASE_PROCESS_TIME_PER_MIN = 0.5
    
    LANGUAGE_COMPLEXITY = {
        'es': 1.0,
        'en': 1.1,
        'pt': 1.0,
        'fr': 1.1,
        'de': 1.2,
        'it': 1.0,
    }
    
    CONTENT_COMPLEXITY = {
        'tutorial': 1.2,
        'course': 1.5,
        'review': 1.0,
        'interview': 0.9,
        'podcast': 0.8,
        'explanation': 1.1,
        'news': 0.7,
        'entertainment': 0.6,
    }
    
    def __init__(self):
        self.download_speed_mbps = self.BASE_DOWNLOAD_SPEED_MBPS
        self.process_time_per_min = self.BASE_PROCESS_TIME_PER_MIN
    
    def set_download_speed(self, speed_mbps: float):
        """Configura velocidad de descarga."""
        self.download_speed_mbps = max(speed_mbps, 1.0)
    
    def estimate(self, duration_seconds: int, language: str = 'es',
               content_type: str = 'tutorial', 
               has_subtitles: bool = True) -> Dict[str, Any]:
        """
        Estima tiempo total de procesamiento.
        """
        duration_min = duration_seconds / 60
        
        estimated_size_mb = self._estimate_size(duration_min)
        download_time_min = estimated_size_mb / self.download_speed_mbps
        
        complexity = self._get_complexity(language, content_type)
        process_time_min = duration_min * self.process_time_per_min * complexity
        
        if not has_subtitles:
            process_time_min *= 1.5
        
        total_time_min = download_time_min + process_time_min
        
        return {
            'estimated_size_mb': round(estimated_size_mb, 2),
            'download_time_min': round(download_time_min, 2),
            'process_time_min': round(process_time_min, 2),
            'total_time_min': round(total_time_min, 2),
            'estimated_duration_sec': duration_seconds,
            'complexity_factor': complexity,
            'confidence': 0.8 if has_subtitles else 0.6
        }
    
    def _estimate_size(self, duration_min: float) -> float:
        """Estima tamaño en MB."""
        return duration_min * 8
    
    def _get_complexity(self, language: str, content_type: str) -> float:
        """Calcula factor de complejidad."""
        lang_factor = self.LANGUAGE_COMPLEXITY.get(language.lower(), 1.0)
        content_factor = self.CONTENT_COMPLEXITY.get(content_type.lower(), 1.0)
        
        return lang_factor * content_factor
    
    def estimate_batch(self, videos: list) -> Dict[str, Any]:
        """Estima tiempo para batch de videos."""
        total_size = 0
        total_time = 0
        
        for video in videos:
            est = self.estimate(
                video.get('duration', 0),
                video.get('language', 'es'),
                video.get('content_type', 'tutorial'),
                video.get('has_subtitles', True)
            )
            total_size += est['estimated_size_mb']
            total_time += est['total_time_min']
        
        return {
            'video_count': len(videos),
            'total_size_mb': round(total_size, 2),
            'total_time_min': round(total_time, 2),
            'estimated_hours': round(total_time / 60, 2)
        }
    
    def get_optimal_batch_size(self, available_time_min: float) -> int:
        """Calcula tamaño óptimo de batch."""
        avg_video_time = 15
        return max(1, int(available_time_min / avg_video_time))


def create_time_estimator() -> TimeEstimator:
    """Factory function."""
    return TimeEstimator()