"""
Módulos P4-39: Procesamiento de Solo Audio Predictivo
Sugiere descargar solo audio para podcasts/conferencias.
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FormatRecommendation:
    """Recomendación de formato de descarga."""
    recommended_format: str
    confidence: float
    reason: str
    estimated_size_mb: float
    estimated_time_savings_percent: float


class AudioOnlyPredictor:
    """Predictor de modo solo audio."""

    AUDIO_INDICATORS = {
        'podcast': ['podcast', 'entrevista', 'interview', 'conferencia', 'conference', 'talk', 'charla'],
        'music': ['music', 'música', 'song', 'canción', 'album', 'playlist'],
        'audiobook': ['audiobook', 'audiolibro', 'audio book'],
        'educational': ['lecture', 'clase', 'seminario', 'webinar', 'workshop']
    }

    VIDEO_INDICATORS = ['tutorial', 'demo', 'gameplay', 'review', 'unboxing', 'vs']

    def __init__(self):
        self._prediction_count = 0

    def predict_audio_only(
        self,
        video: Dict
    ) -> FormatRecommendation:
        """
        P4-39: Predice si el video debe descargarse solo en audio.
        Args:
            video: Datos del video
        Returns:
            FormatRecommendation con análisis
        """
        self._prediction_count += 1

        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        duration = video.get('duration_seconds', 0)
        duration_minutes = duration / 60

        audio_score = 0.0
        audio_type = 'general'

        for atype, keywords in self.AUDIO_INDICATORS.items():
            if any(kw in title or kw in description for kw in keywords):
                audio_score += 0.3
                audio_type = atype

        has_video_indicators = any(kw in title for kw in self.VIDEO_INDICATORS)
        if has_video_indicators:
            audio_score -= 0.4

        if duration_minutes > 60:
            audio_score += 0.15
        elif duration_minutes < 10:
            audio_score -= 0.1

        audio_score = max(-0.5, min(audio_score, 1.0))

        if audio_score > 0.5:
            recommended_format = 'audio_only'
            reason = f"Contenido de audio detectado ({audio_type})"
            estimated_size = duration / 1024 * 0.1
            time_savings = 85
        elif audio_score > 0.2:
            recommended_format = 'video_preferred'
            reason = "Contenido mixto - video preferido"
            estimated_size = duration / 1024 * 0.5
            time_savings = 0
        else:
            recommended_format = 'video_only'
            reason = "Contenido principalmente visual"
            estimated_size = duration / 1024 * 0.5
            time_savings = 0

        return FormatRecommendation(
            recommended_format=recommended_format,
            confidence=round(abs(audio_score), 2),
            reason=reason,
            estimated_size_mb=round(estimated_size, 1),
            estimated_time_savings_percent=time_savings
        )

    def batch_predict(self, videos: List[Dict]) -> List[FormatRecommendation]:
        """Predice formato para lista de videos."""
        return [self.predict_audio_only(v) for v in videos]

    def get_audio_only_candidates(
        self,
        videos: List[Dict],
        threshold: float = 0.5
    ) -> List[Dict]:
        """Filtra videos que deberían descargarse en audio."""
        predictions = self.batch_predict(videos)
        return [
            {**v, '_audio_recommendation': p.__dict__}
            for v, p in zip(videos, predictions)
            if p.recommended_format == 'audio_only' and p.confidence >= threshold
        ]

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del predictor."""
        return {
            "total_predicted": self._prediction_count,
            "model": "AudioOnlyPredictor v1.0"
        }


def create_audio_only_predictor() -> AudioOnlyPredictor:
    """Crea una instancia del predictor."""
    return AudioOnlyPredictor()


_global_predictor: Optional[AudioOnlyPredictor] = None


def get_audio_only_predictor() -> AudioOnlyPredictor:
    """Obtiene la instancia global."""
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = create_audio_only_predictor()
    return _global_predictor