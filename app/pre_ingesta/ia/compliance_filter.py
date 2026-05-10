"""
KDP MASTER - Compliance Filter (Módulo 20)
===================================
Filtro de compliance de contenido KDP.
"""

import re
from typing import Dict, Any, List, Tuple


class ComplianceFilter:
    """Módulo 20: Filtro de compliance."""
    
    FORBIDDEN_KEYWORDS = [
        'spam', 'scam', 'fraude', 'estafa', 'pirámide', 'ponzi',
        'ilícito', 'ilegal', 'prohibido', 'nsfw', 'adult',
        'odio', 'violence', 'hate', 'terrorismo', 'terrorism'
    ]
    
    TOS_RISK_KEYWORDS = [
        'giveaway', 'sorteo', 'gratis', 'gratuito', 'win free',
        'click here', 'buy now', 'limited offer', 'urgente',
        'garantizado', 'guaranteed', 'make money fast',
        'trabajo desde casa', 'easy money'
    ]
    
    FINANCIAL_DISCLAIMER = [
        'no garantiza', 'no asegur', 'riesgo', 'past performance',
        'no es asesoramiento', 'consult a professional'
    ]
    
    def __init__(self):
        self.forbidden_threshold = 0
        self.tos_risk_threshold = 2
    
    def check_compliance(self, title: str, description: str = "",
                    channel: str = "") -> Dict[str, Any]:
        """
        Verifica compliance.
        """
        text = f"{title} {description} {channel}".lower()
        
        forbidden_found = []
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword.lower() in text:
                forbidden_found.append(keyword)
        
        tos_risk_found = []
        for keyword in self.TOS_RISK_KEYWORDS:
            if keyword.lower() in text:
                tos_risk_found.append(keyword)
        
        has_disclaimer = any(
            keyword.lower() in text 
            for keyword in self.FINANCIAL_DISCLAIMER
        )
        
        status = "approved"
        reasons = []
        
        if len(forbidden_found) > self.forbidden_threshold:
            status = "blocked"
            reasons.append(f"Contenido prohibido: {forbidden_found}")
        
        if len(tos_risk_found) >= self.tos_risk_threshold:
            if status == "approved":
                status = "warning"
            reasons.append(f"Riesgo TOS: {tos_risk_found}")
        
        if not has_disclaimer and any(word in text for word in ['inversión', 'invertir', 'rendimiento', 'rentabilidad']):
            if status == "approved":
                status = "warning"
            reasons.append("Falta disclaimer financiero")
        
        return {
            'status': status,
            'reasons': reasons,
            'forbidden_found': forbidden_found,
            'tos_risk_found': tos_risk_found,
            'has_disclaimer': has_disclaimer
        }
    
    def scan_for_prohibited(self, content: str) -> Tuple[bool, List[str]]:
        """
        Escanea contenido en busca de términos prohibidos.
        Returns: (is_prohibited, found_keywords)
        """
        content_lower = content.lower()
        
        found = []
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword.lower() in content_lower:
                found.append(keyword)
        
        return len(found) > 0, found
    
    def suggest_disclaimer(self, content_type: str = "general") -> str:
        """Sugiere disclaimer apropiado."""
        if content_type == "inversion":
            return "El contenido es meramente informativo y educativo. Nada garantiza rendimientos pasados ni futuros. Todo inversión conlleva riesgos. Consulta con un profesional."
        elif content_type == "cripto":
            return "Las criptomonedas son activos volátiles. Este contenido es educativo, no asesoramiento financiero. Investiga antes de invertir."
        else:
            return "Contenido informativo. No constituye asesoramiento financiero. Consulta fuentes oficiales y profesionales."
    
    def filter_batch(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Filtra batch completo."""
        approved = []
        warning = []
        blocked = []
        
        for item in items:
            result = self.check_compliance(
                item.get('title', ''),
                item.get('description', '')
            )
            
            item['_compliance'] = result
            
            if result['status'] == 'blocked':
                blocked.append(item)
            elif result['status'] == 'warning':
                warning.append(item)
            else:
                approved.append(item)
        
        return {
            'approved': approved,
            'warning': warning,
            'blocked': blocked
        }


def create_compliance_filter() -> ComplianceFilter:
    """Factory function."""
    return ComplianceFilter()