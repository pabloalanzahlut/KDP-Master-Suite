"""
Módulos IA P4-37: Predicción de Fallos de Descarga
Predice videos propensos a error durante la descarga.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FailurePrediction:
    """Predicción de fallo para un video."""
    video_id: str
    failure_probability: float
    risk_factors: List[str]
    recommended_action: str


class FailurePredictor:
    """Predictor de fallos de descarga."""

    RISK_INDICATORS = {
        'live_stream': ['live', 'estreno', 'directo'],
        'unavailable': ['privado', 'eliminado', 'not available'],
        'geo_blocked': ['geo', 'region', 'bloqueado'],
        'too_long': 7200,
        'too_short': 30,
        'low_quality': ['audio only', 'sin video'],
        'age_limit': ['age', 'restringido', 'adult']
    }

    def __init__(self):
        self._prediction_count = 0
        self._failure_history: List[Dict] = []

    def predict_failure_risk(
        self,
        video: Dict,
        historical_data: Optional[List[Dict]] = None
    ) -> FailurePrediction:
        """
        P4-37: Predice la probabilidad de fallo de descarga.
        Args:
            video: Datos del video
            historical_data: Historial de descargas anteriores
        Returns:
            FailurePrediction con análisis
        """
        self._prediction_count += 1

        video_id = video.get('id', '')
        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        duration = video.get('duration_seconds', 0)

        risk_factors = []
        failure_probability = 0.1

        for indicator, keywords in self.RISK_INDICATORS.items():
            if isinstance(keywords, list):
                if any(kw in title or kw in description for kw in keywords):
                    risk_factors.append(indicator)
                    failure_probability += 0.2
            else:
                if duration > keywords:
                    risk_factors.append('too_long')
                    failure_probability += 0.15

        if duration < 30:
            risk_factors.append('too_short')
            failure_probability += 0.1

        if video.get('availability') in ['private', 'deleted', 'unavailable']:
            risk_factors.append('availability_issue')
            failure_probability += 0.4

        if video.get('region_restriction'):
            risk_factors.append('geo_restricted')
            failure_probability += 0.25

        failure_probability = min(failure_probability, 1.0)

        if failure_probability > 0.7:
            recommended_action = "skip"
            action_text = "Alto riesgo - considerar omitir"
        elif failure_probability > 0.4:
            recommended_action = "retry"
            action_text = "Riesgo medio - preparar reintento"
        else:
            recommended_action = "proceed"
            action_text = "Bajo riesgo - proceder normalmente"

        return FailurePrediction(
            video_id=video_id,
            failure_probability=round(failure_probability, 2),
            risk_factors=risk_factors,
            recommended_action=action_text
        )

    def batch_predict(
        self,
        videos: List[Dict]
    ) -> List[FailurePrediction]:
        """Predice riesgo de fallo para una lista de videos."""
        return [self.predict_failure_risk(v) for v in videos]

    def filter_high_risk(
        self,
        videos: List[Dict],
        threshold: float = 0.5
    ) -> List[Dict]:
        """Filtra videos con alto riesgo de fallo."""
        predictions = self.batch_predict(videos)
        high_risk_ids = {p.video_id for p in predictions if p.failure_probability > threshold}
        return [v for v in videos if v.get('id') in high_risk_ids]

    def record_failure(self, video_id: str, error_type: str):
        """Registra un fallo para mejorar predicciones."""
        self._failure_history.append({
            'video_id': video_id,
            'error_type': error_type,
            'timestamp': datetime.now().isoformat()
        })

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del predictor."""
        return {
            "total_predicted": self._prediction_count,
            "failure_history_count": len(self._failure_history),
            "model": "FailurePredictor v1.0"
        }


def create_failure_predictor() -> FailurePredictor:
    """Crea una instancia del predictor de fallos."""
    return FailurePredictor()


_global_predictor: Optional[FailurePredictor] = None


def get_failure_predictor() -> FailurePredictor:
    """Obtiene la instancia global del predictor."""
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = create_failure_predictor()
    return _global_predictor