"""
Retention Compliance
====================
Verifica retención de datos.
"""

from typing import Dict
from datetime import datetime, timedelta


class RetentionCompliance:
    def check(self, created: str, retention_days: int = 365) -> Dict:
        try:
            created_dt = datetime.fromisoformat(created)
            age = (datetime.now() - created_dt).days
            return {"over_retention": age > retention_days, "age_days": age}
        except:
            return {"over_retention": False, "age_days": 0}


def get_retention_compliance():
    return RetentionCompliance()