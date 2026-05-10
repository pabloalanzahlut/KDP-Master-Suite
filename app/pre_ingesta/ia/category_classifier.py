"""
KDP MASTER - Category Classifier (Módulo 15)
===========================================
Clasificador automático por categorías KDP.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


class CategoryClassifier:
    """Módulo 15: Clasificador por categorías KDP."""
    
    KDP_CATEGORIES = {
        "finanzas_personales": {
            "keywords": ["finanzas personales", "gestión del dinero", "presupuesto", "ahorro", "control gastos"],
            "subcategories": ["ahorro", "presupuesto", "deuda", "emergency fund"]
        },
        "inversiones": {
            "keywords": ["inversión", "invertir", "rentabilidad", "cartera", "portfolio", "activos"],
            "subcategories": ["bolsa", "fondos", "bienes raíces", "alternativas"]
        },
        "criptomonedas": {
            "keywords": ["criptomoneda", "bitcoin", "ethereum", "crypto", "blockchain", "token", "defi"],
            "subcategories": ["bitcoin", "altcoins", "nft", "defi", "trading"]
        },
        "fiscalidad": {
            "keywords": ["fiscalidad", "impuestos", "tax", "ría", "declaración", "modelo"],
            "subcategories": ["irpf", "iva", "impuesto sociedades", "deducciones"]
        },
        "jubilación": {
            "keywords": ["jubilación", "pensiones", "retiro", "pensión", "plan de pensiones"],
            "subcategories": ["plan de pensiones", "ahorro jubil', "semanas cotizadas"]
        },
        "emprendimiento": {
            "keywords": ["emprendedor", "emprendimiento", "startup", "negcio propio", "autónomo"],
            "subcategories": ["freelance", "autónomo", "sae", "innovación"]
        },
        "marketing": {
            "keywords": ["marketing", "seo", "publicidad", "marketing digital", "social media"],
            "subcategories": ["seo", "content marketing", "email marketing", "ads"]
        },
        "productividad": {
            "keywords": ["productividad", "eficiencia", "organización", "gestión tiempo"],
            "subcategories": ["time management", "habitos", "rutas", "focus"]
        },
        "tecnología": {
            "keywords": ["tecnología", "tech", "software", "ia", "inteligencia artificial"],
            "subcategories": ["desarrollo", "ia", "machine learning", "automation"]
        },
        "bienes_raíces": {
            "keywords": ["bienes raíces", "inmueble", "propiedad", "alquiler", "hipoteca"],
            "subcategories": ["comprar", "alquilar", "reforma", "hipoteca"]
        },
        "educación_financiera": {
            "keywords": ["educación financiera", "aprender", "curso", "formación", "tutorial"],
            "subcategories": ["básico", "intermedio", "avanzado", "práctico"]
        },
        "psicología_financiera": {
            "keywords": ["psicología", "mentalidad", "mindset", "comportamiento", " sesgos"],
            "subcategories": ["comportamiento", "decisiones", "emociones", " hábitos"]
        }
    }
    
    def __init__(self):
        self.default_category = "finanzas_personales"
    
    def set_default_category(self, category: str):
        """Configura categoría por defecto."""
        if category in self.KDP_CATEGORIES:
            self.default_category = category
    
    def classify(self, title: str, description: str = "",
               tags: List[str] = None) -> Tuple[str, float, List[str]]:
        """
        Clasifica video en categoría KDP.
        Returns: (category, confidence, subcategories)
        """
        text = f"{title} {description}".lower()
        
        if tags:
            text += " " + " ".join(tags).lower()
        
        scores = {}
        
        for category, data in self.KDP_CATEGORIES.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword.lower() in text:
                    score += 1
            
            if score > 0:
                scores[category] = score
        
        if not scores:
            return self.default_category, 0.0, []
        
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        confidence = min(max_score / 5.0, 1.0)
        
        subcategories = self._detect_subcategories(
            title, description, self.KDP_CATEGORIES[best_category].get("subcategories", [])
        )
        
        return best_category, confidence, subcategories
    
    def _detect_subcategories(self, title: str, description: str,
                         possible: List[str]) -> List[str]:
        """Detecta subcategorías."""
        text = f"{title} {description}".lower()
        
        detected = []
        for sub in possible:
            if sub.lower() in text:
                detected.append(sub)
        
        return detected[:3]
    
    def get_available_categories(self) -> List[str]:
        """Obtiene categorías disponibles."""
        return list(self.KDP_CATEGORIES.keys())
    
    def get_category_info(self, category: str) -> Optional[Dict[str, Any]]:
        """Obtiene info de categoría."""
        return self.KDP_CATEGORIES.get(category)
    
    def classify_batch(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clasifica batch de videos."""
        results = []
        
        for video in videos:
            title = video.get('title', '')
            description = video.get('description', '')
            tags = video.get('tags', [])
            
            category, confidence, subcategories = self.classify(title, description, tags)
            
            results.append({
                'video_id': video.get('id'),
                'category': category,
                'confidence': confidence,
                'subcategories': subcategories
            })
        
        return results


def create_category_classifier() -> CategoryClassifier:
    """Factory function."""
    return CategoryClassifier()