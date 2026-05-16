"""
Compliance Report
=================
Genera reportes de cumplimiento.
"""

from typing import Dict


class ComplianceReport:
    def generate(self, checks: Dict) -> Dict:
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        return {"passed": passed, "total": total, "percentage": round(passed/total*100, 1)}


def get_compliance_report():
    return ComplianceReport()