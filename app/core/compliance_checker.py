import re

class ComplianceChecker:
    """Escaneo proactivo de TOS y Red Flags antes de integrar a la KB."""
    
    RED_FLAGS = [
        (r"trademark infringement", "Legal: Posible infracción de marca"),
        (r"bypass amazon security", "TOS: Intento de evasión de seguridad"),
        (r"fake reviews", "TOS: Manipulación de reseñas"),
        (r"account suspension workaround", "Legal: Evasión de suspensión")
    ]

    def scan_text(self, text: str) -> dict:
        """
        Analiza el texto buscando violaciones de cumplimiento.
        Retorna: {"safe": bool, "flags": list}
        """
        found_flags = []
        text_lower = text.lower()
        
        for pattern, reason in self.RED_FLAGS:
            if re.search(pattern, text_lower):
                found_flags.append(reason)
        
        return {
            "safe": len(found_flags) == 0,
            "flags": found_flags,
            "severity": "high" if found_flags else "none"
        }