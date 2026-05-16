"""
P1-5: Detección de Contenido Obsoleto
Identifica fechas o versiones antiguas.
"""
import re
from datetime import datetime


class ObsolescenceDetector:
    YEAR_PATTERNS = [r'\b(20\d{2})\b']

    def detect(self, title: str, upload_date: str = None) -> dict:
        year_detected = None
        for pattern in self.YEAR_PATTERNS:
            match = re.search(pattern, title.lower())
            if match:
                year_detected = int(match.group(1))

        if year_detected:
            age = datetime.now().year - year_detected
            return {'is_obsolete': age >= 2, 'age_years': age}
        return {'is_obsolete': False, 'age_years': 0}


def get_obsolescence_detector():
    return ObsolescenceDetector()