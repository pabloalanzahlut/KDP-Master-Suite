"""
KDP Master Suite - Gestión de Errores Centralizada
Implementación del Glosario de Errores (Sección 7)
"""

from typing import Dict

class KDPError(Exception):
    """Base para excepciones del sistema con código de error."""
    def __init__(self, code: str, message: str, solution: str):
        self.code = code
        self.message = message
        self.solution = solution
        super().__init__(f"[{self.code}] {self.message}")

class ErrorRegistry:
    """Registro maestro de errores según el glosario del proyecto."""
    
    GLOSSARY: Dict[str, Dict[str, str]] = {
        "E001": {
            "description": "URL de YouTube no válida",
            "solution": "Verifique el formato de la URL"
        },
        "E002": {
            "description": "Error de conexión",
            "solution": "Compruebe su conexión a internet"
        },
        "E003": {
            "description": "API Key inválida",
            "solution": "Revise la clave en la configuración"
        },
        "E004": {
            "description": "Archivo corrupto",
            "solution": "Elimine y vuelva a descargar"
        },
        "E005": {
            "description": "Límite de cuota excedido",
            "solution": "Espere y reintente más tarde"
        }
    }

    @classmethod
    def get_error(cls, code: str) -> KDPError:
        """Retorna una instancia de KDPError basada en el código."""
        data = cls.GLOSSARY.get(code, {"description": "Error desconocido", "solution": "Consulte soporte"})
        return KDPError(code, data["description"], data["solution"])