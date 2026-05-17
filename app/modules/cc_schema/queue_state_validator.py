"""
Queue State Validator - Módulo 46
==================================
Valida y clasifica los items de la cola según su estado.

¿Para qué sirve esto?
=====================
Cuando vas a limpiar tu casa, no tratas toda la ropa igual.
- La ropa sucia va a la lavadora (failed)
- La ropa limpia va al armario (completed)
- La ropa por arreglar va al taller (pending)

Este módulo hace lo mismo con tus videos en cola:
- Videos que fallaron = "fallidos" (posible reintentar o descartar)
- Videos completados = "hechos" (ya se procesaron)
- Videos pendientes = "por hacer" (esperando su turno)

Caso de uso real:
================
Tu organizador dice: "Voy a hacer limpieza."
Pero antes, clasifica:
- Documentos vencidos → papelera
- Documentos vigentes → archivo
- Documentos por firmar → pendientes

Aquí es igual: clasificar antes de actuar.

为什么 esto importa?
===================
Porque NO puedes tratar todos los videos igual. Un video que falló
por error de red (404) probablemente quieres reintentarlo, no borrarlo.
Un video que ya está completado ya no ocupa espacio en la cola.

Este validador te dice QUÉ tiene cada item para que.decidas QUÉ hacer con él.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ItemState(Enum):
    """Estados posibles de un item en la cola."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FailureType(Enum):
    """Tipos de fallos posibles."""
    NETWORK_ERROR = "network_error"
    VIDEO_UNAVAILABLE = "video_unavailable"
    AUTH_REQUIRED = "auth_required"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Resultado de la validación de un item."""
    is_valid: bool
    state: ItemState
    failure_type: Optional[FailureType] = None
    error_message: str = ""
    can_retry: bool = False
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class QueueStateValidator:
    """
    Validador de estados de cola.
    
    Analiza cada item y determina:
    - Su estado actual
    - Si es recuperable
    - Qué hacer con él
    """

    KNOWN_ERROR_PATTERNS = {
        "404": (FailureType.VIDEO_UNAVAILABLE, False, "Video no disponible"),
        "403": (FailureType.AUTH_REQUIRED, False, "Se requiere autenticación"),
        "429": (FailureType.RATE_LIMITED, True, "Rate limit - esperar y reintentar"),
        "timeout": (FailureType.NETWORK_ERROR, True, "Timeout de red"),
        "connection": (FailureType.NETWORK_ERROR, True, "Error de conexión"),
        "unavailable": (FailureType.VIDEO_UNAVAILABLE, False, "Video no disponible"),
        "private": (FailureType.AUTH_REQUIRED, False, "Video privado"),
        "deleted": (FailureType.VIDEO_UNAVAILABLE, False, "Video eliminado")
    }

    def __init__(self):
        logger.info("QueueStateValidator inicializado")

    def validate_item(self, item: Any) -> ValidationResult:
        """
        Valida un solo item.
        
        Args:
            item: Item a validar (puede ser dict o objeto con atributos).

        Returns:
            ValidationResult con el análisis.
        """
        try:
            state = self._extract_state(item)
            error_msg = self._extract_error(item)
            
            if state == ItemState.FAILED:
                failure_type, can_retry, error_desc = self._analyze_failure(error_msg)
                return ValidationResult(
                    is_valid=True,
                    state=state,
                    failure_type=failure_type,
                    error_message=error_desc,
                    can_retry=can_retry,
                    recommendations=self._get_recommendations(failure_type, can_retry)
                )
            
            return ValidationResult(
                is_valid=True,
                state=state,
                recommendations=self._get_recommendations_by_state(state)
            )

        except Exception as e:
            logger.error(f"Error validando item: {e}")
            return ValidationResult(
                is_valid=False,
                state=ItemState.UNKNOWN if hasattr(ItemState, 'UNKNOWN') else ItemState.PENDING,
                error_message=str(e)
            )

    def validate_batch(self, items: List[Any]) -> Dict[str, Any]:
        """
        Valida una lista completa de items.
        
        Args:
            items: Lista de items a validar.

        Returns:
            Diccionario con estadísticas y items clasificados.
        """
        results = {
            "total": len(items),
            "by_state": {},
            "failed_retryable": 0,
            "failed_non_retryable": 0,
            "items": []
        }

        for item in items:
            validation = self.validate_item(item)
            
            state_key = validation.state.value
            results["by_state"][state_key] = results["by_state"].get(state_key, 0) + 1
            
            if validation.state == ItemState.FAILED:
                if validation.can_retry:
                    results["failed_retryable"] += 1
                else:
                    results["failed_non_retryable"] += 1
            
            results["items"].append({
                "url": self._extract_url(item),
                "state": validation.state.value,
                "failure_type": validation.failure_type.value if validation.failure_type else None,
                "can_retry": validation.can_retry,
                "error": validation.error_message,
                "recommendations": validation.recommendations
            })

        return results

    def _extract_state(self, item: Any) -> ItemState:
        """Extrae el estado de un item."""
        if isinstance(item, dict):
            state_str = item.get("status", "pending").lower()
        elif hasattr(item, "status"):
            state_str = str(item.status).lower()
        else:
            state_str = "pending"

        for state in ItemState:
            if state.value == state_str:
                return state
        
        return ItemState.PENDING

    def _extract_error(self, item: Any) -> str:
        """Extrae el mensaje de error de un item."""
        if isinstance(item, dict):
            return item.get("last_error", item.get("error", ""))
        elif hasattr(item, "last_error"):
            return item.last_error
        return ""

    def _extract_url(self, item: Any) -> str:
        """Extrae la URL de un item."""
        if isinstance(item, dict):
            return item.get("url", "")
        elif hasattr(item, "url"):
            return item.url
        return ""

    def _analyze_failure(self, error_msg: str) -> Tuple[FailureType, bool, str]:
        """Analiza el tipo de fallo."""
        error_lower = error_msg.lower()
        
        for pattern, (failure_type, can_retry, description) in self.KNOWN_ERROR_PATTERNS.items():
            if pattern in error_lower:
                return failure_type, can_retry, description
        
        return FailureType.UNKNOWN, True, f"Error desconocido: {error_msg[:50]}"

    def _get_recommendations(self, failure_type: FailureType, can_retry: bool) -> List[str]:
        """Genera recomendaciones basadas en el tipo de fallo."""
        recommendations = []
        
        if failure_type == FailureType.VIDEO_UNAVAILABLE:
            recommendations.append("El video ya no está disponible")
            recommendations.append("Considerar eliminar de la cola")
        
        elif failure_type == FailureType.AUTH_REQUIRED:
            recommendations.append("Se requiere acceso al video")
            recommendations.append("Verificar si el canal es público")
        
        elif failure_type == FailureType.RATE_LIMITED:
            recommendations.append("YouTube detecto muchas solicitudes")
            recommendations.append("Esperar unos minutos antes de reintentar")
        
        elif failure_type == FailureType.NETWORK_ERROR:
            if can_retry:
                recommendations.append("Error de red temporal")
                recommendations.append("Reintentar automáticamente")
            else:
                recommendations.append("Problema de red persistente")
        
        return recommendations

    def _get_recommendations_by_state(self, state: ItemState) -> List[str]:
        """Genera recomendaciones basadas en el estado."""
        if state == ItemState.COMPLETED:
            return ["Ya procesado", "Considerar mover a archivo"]
        
        elif state == ItemState.PENDING:
            return ["Esperando procesamiento", "No requiere acción"]
        
        elif state == ItemState.DOWNLOADING:
            return ["En progreso", "No cancelar"]
        
        elif state == ItemState.CANCELLED:
            return ["Cancelado por usuario", "Considerar eliminar"]
        
        return []

    def get_filter_summary(self, items: List[Any]) -> Dict[str, int]:
        """
        Obtiene un resumen de cuántos items hay en cada estado.
        
        Es como hacer inventario antes de limpar.
        
        Returns:
            Diccionario con conteo por estado.
        """
        summary = {
            "failed_retryable": 0,
            "failed_non_retryable": 0,
            "completed": 0,
            "pending": 0,
            "downloading": 0,
            "cancelled": 0
        }
        
        for item in items:
            validation = self.validate_item(item)
            
            if validation.state == ItemState.FAILED:
                if validation.can_retry:
                    summary["failed_retryable"] += 1
                else:
                    summary["failed_non_retryable"] += 1
            elif validation.state == ItemState.COMPLETED:
                summary["completed"] += 1
            elif validation.state == ItemState.PENDING:
                summary["pending"] += 1
            elif validation.state == ItemState.DOWNLOADING:
                summary["downloading"] += 1
            elif validation.state == ItemState.CANCELLED:
                summary["cancelled"] += 1
        
        return summary


def create_state_validator() -> QueueStateValidator:
    """Factory function."""
    return QueueStateValidator()