"""
KDP MASTER - Channel Curation Metrics Service
==============================================
Servicio de métricas y estadísticas para curación de canales.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class CurationMetricsService:
    """
    Servicio de métricas para el motor de curación de canales.
    Proporciona estadísticas y análisis de videos clasificados.
    """

    def __init__(self, db_manager=None):
        self.db = db_manager
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos

    def get_channel_health_score(self, channel_id: int = None, channel_url: str = None) -> Dict:
        """
        Calcula el score de salud de un canal o del sistema completo.

        Returns:
            Dict con:
            - health_score: 0-100
            - total_videos: cantidad total
            - avg_relevance: promedio de relevance score
            - last_scan: última fecha de scan
            - recommendations: lista de recomendaciones
        """
        try:
            if not self.db:
                from app.database.db_manager import DatabaseManager
                self.db = DatabaseManager()

            # Obtener videos
            if channel_id:
                videos = self.db.get_videos_by_channel(channel_id)
            else:
                videos = self._get_all_videos()

            if not videos:
                return {
                    "health_score": 0,
                    "total_videos": 0,
                    "avg_relevance": 0,
                    "last_scan": None,
                    "recommendations": ["No hay videos para analizar"]
                }

            # Calcular métricas
            total = len(videos)
            scores = []

            for v in videos:
                # Intentar obtener score del metadata
                metadata = v.get('metadata_json', '{}')
                if isinstance(metadata, str):
                    try:
                        import json
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}

                score = metadata.get('kdp_relevance_score', 50)  # Default 50
                scores.append(score)

            avg_score = sum(scores) / len(scores) if scores else 0

            # Calcular health score
            health_score = self._calculate_health_score(avg_score, total)

            # Generar recomendaciones
            recommendations = self._generate_recommendations(avg_score, total, scores)

            # Última fecha de scan
            last_scan = self._get_last_scan_date(channel_id)

            return {
                "health_score": health_score,
                "total_videos": total,
                "avg_relevance": round(avg_score, 1),
                "last_scan": last_scan,
                "recommendations": recommendations,
                "quality_distribution": self._get_quality_distribution(scores)
            }

        except Exception as e:
            logger.error(f"Error calculando health score: {e}")
            return {
                "health_score": 0,
                "total_videos": 0,
                "avg_relevance": 0,
                "error": str(e)
            }

    def _calculate_health_score(self, avg_relevance: float, total_videos: int) -> int:
        """Calcula el score de salud (0-100)."""
        # Base score from avg relevance (70% del peso)
        relevance_component = avg_relevance * 0.7

        # Volume component (30% del peso, capped at 30)
        volume_component = min(30, (total_videos / 10) * 3)

        return int(relevance_component + volume_component)

    def _get_quality_distribution(self, scores: List[int]) -> Dict:
        """Obtiene distribución de calidad."""
        distribution = {
            "critical": 0,   # 90-100
            "high": 0,      # 70-89
            "medium": 0,    # 50-69
            "low": 0,      # 30-49
            "trivial": 0   # 0-29
        }

        for score in scores:
            if score >= 90:
                distribution["critical"] += 1
            elif score >= 70:
                distribution["high"] += 1
            elif score >= 50:
                distribution["medium"] += 1
            elif score >= 30:
                distribution["low"] += 1
            else:
                distribution["trivial"] += 1

        return distribution

    def _generate_recommendations(self, avg_score: float, total: int, scores: List[int]) -> List[str]:
        """Genera recomendaciones basadas en métricas."""
        recommendations = []

        if total == 0:
            recommendations.append("Agrega canales para comenzar el análisis")
        elif total < 10:
            recommendations.append(f"Solo {total} videos. Considera agregar más contenido")
        elif total > 100:
            recommendations.append(f"Tienes {total} videos. Excelente volumen")

        if avg_score < 40:
            recommendations.append("El contenido tiene baja relevancia KDP. Revisa los filtros de palabras clave")
        elif avg_score < 60:
            recommendations.append("Contenido de relevancia moderada. Ajusta los criterios de clasificación")
        elif avg_score >= 70:
            recommendations.append("Contenido de alta relevancia. ¡Excelente selección!")

        # Detectar si hay mucho contenido trivial
        trivial_count = sum(1 for s in scores if s < 30)
        if trivial_count > total * 0.3:
            recommendations.append(f"{trivial_count} videos son triviales. Considera excluirlos")

        return recommendations

    def _get_all_videos(self) -> List[Dict]:
        """Obtiene todos los videos."""
        try:
            conn = self.db.get_connection()
            conn.row_factory = None
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos")
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    def _get_last_scan_date(self, channel_id: int = None) -> Optional[str]:
        """Obtiene la última fecha de scan."""
        try:
            if not self.db:
                return None

            history = self.db.get_scan_history(limit=1, channel_id=channel_id)
            if history:
                return history[0].get('scan_time')
            return None
        except:
            return None

    def get_top_rated_videos(self, limit: int = 10, min_score: int = 50) -> List[Dict]:
        """Obtiene los videos mejor valorados."""
        try:
            if not self.db:
                return []

            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Query para obtener videos ordenados
            # Nota: Esto requiere que los videos tengan metadata con score
            cursor.execute("""
                SELECT v.id, v.title, v.video_url, v.channel_id,
                       v.published_at, v.duration_seconds
                FROM videos v
                ORDER BY v.id DESC
                LIMIT ?
            """, (limit * 2,))

            videos = []
            for row in cursor.fetchall():
                videos.append(dict(row))

            conn.close()
            return videos[:limit]

        except Exception as e:
            logger.error(f"Error obteniendo top videos: {e}")
            return []

    def get_batch_statistics(self) -> Dict:
        """Obtiene estadísticas del batch actual."""
        return {
            "total_processed": len(self._cache.get('processed_ids', [])),
            "total_skipped": self._cache.get('skipped_count', 0),
            "avg_score": self._cache.get('avg_score', 0),
            "cache_age": self._cache.get('timestamp', None)
        }


def create_curation_metrics_service(db_manager=None) -> CurationMetricsService:
    """Factory function."""
    return CurationMetricsService(db_manager=db_manager)