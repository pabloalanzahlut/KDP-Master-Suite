"""
KDP Master Suite - Clasificador de Contenido
Implementación de Clasificación Automática (Sección 6.1)
"""

from typing import List

class ContentClassifier:
    # --- INICIO FUNCIONALIDAD CLASIFICACIÓN ---
    CATEGORIES = [
        "Tecnología", 
        "Educación", 
        "Negocios", 
        "Salud", 
        "Entretenimiento", 
        "Noticias"
    ]

    @classmethod
    def classify(cls, text: str) -> str:
        """
        Clasifica el texto basado en keywords (Lógica algorítmica básica).
        En versiones 'Elite', esto se reemplazaría por un modelo de NLP.
        """
        if not text:
            return cls.CATEGORIES[1]  # Educación por defecto

        text = text.lower()
        
        # Diccionario de mapeo simple para demostración de lógica
        mapping = {
            "Tecnología": ["python", "software", "api", "hardware", "ia", "tech"],
            "Educación": ["curso", "tutorial", "aprender", "clase", "guía"],
            "Negocios": ["dinero", "inversión", "marketing", "empresa", "ventas"],
            "Salud": ["dieta", "ejercicio", "médico", "bienestar", "nutrición"],
            "Entretenimiento": ["cine", "música", "juegos", "vlog", "humor"],
            "Noticias": ["actualidad", "noticia", "mundo", "urgente", "informe"]
        }

        for category, keywords in mapping.items():
            if any(key in text for key in keywords):
                return category
        
        return "Educación"  # Fallback
    # --- FIN FUNCIONALIDAD CLASIFICACIÓN ---