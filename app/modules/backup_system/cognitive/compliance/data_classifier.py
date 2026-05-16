"""
Data Classifier
===============
Clasifica datos por sensibilidad.
"""

from typing import Dict


class DataClassifier:
    def classify(self, content: str) -> Dict:
        sensitive = ["password", "secret", "key", "token", "api_key"]
        found = [s for s in sensitive if s in content.lower()]
        level = "high" if found else "low"
        return {"level": level, "sensitive_fields": found}


def get_data_classifier():
    return DataClassifier()