import sqlite3
from pathlib import Path

class ReviewQueueManager:
    """Gestiona las métricas de aprobación y validación de Fase 2."""
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.threshold = 0.75

    def get_stats(self):
        """Calcula estadísticas basadas en la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Entradas en KB vs Entradas en Cola
            cursor.execute("SELECT COUNT(*) FROM review_queue")
            pending = cursor.fetchone()[0]
            
            # Para simplificar, usaremos una tabla de métricas o audit_logs en el futuro
            # Por ahora, simulamos el contador basado en el historial de distribución
            conn.close()
            return pending
        except:
            return 0

    def evaluate_confidence(self, confidence: float) -> str:
        """Determina si una entrada se auto-aprueba o va a revisión."""
        if confidence >= self.threshold:
            return "AUTO_APPROVED"
        return "FLAGGED_FOR_REVIEW"

    def calculate_approval_rate(self, auto_count, total_count) -> float:
        """Calcula la tasa de éxito de la IA."""
        if total_count == 0: return 1.0
        rate = auto_count / total_count
        return rate

    def is_quality_low(self, rate: float) -> bool:
        """Verifica si estamos por debajo del umbral del 75%."""
        return rate < 0.75