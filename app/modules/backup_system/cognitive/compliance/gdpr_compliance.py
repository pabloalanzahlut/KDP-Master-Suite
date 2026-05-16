"""
GDPR Compliance
===============
Verifica cumplimiento GDPR.
"""

from typing import Dict


class GDPRCompliance:
    def check(self, data: Dict) -> Dict:
        personal_data = ["name", "email", "phone", "address"]
        has_personal = any(f in str(data).lower() for f in personal_data)
        return {"compliant": not has_personal, "gdpr_required": has_personal}


def get_gdpr_compliance():
    return GDPRCompliance()