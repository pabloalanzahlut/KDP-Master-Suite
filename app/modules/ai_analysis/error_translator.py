"""
AI Analysis - Error Translator
==============================
Módulo 34: Traduce errores de extracción a soluciones accionables.
Usa Ollama para diagnóstico inteligente.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    EXTRACTION = "extraction"
    FORMAT = "format"
    NETWORK = "network"
    PARSING = "parsing"
    VALIDATION = "validation"
    CONTENT = "content"
    UNKNOWN = "unknown"


class ActionType(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    FIX = "fix"
    NOTIFY = "notify"
    IGNORE = "ignore"


@dataclass
class ErrorTranslation:
    original_error: str
    category: ErrorCategory
    severity: float
    solution: str
    action: ActionType
    troubleshooting_steps: List[str]
    prevention_tips: List[str]


class ErrorTranslator:
    """
    Traductor de errores de extracción a soluciones.
    Proporciona diagnóstico y acciones reparables.
    """

    ERROR_PATTERNS = {
        ErrorCategory.EXTRACTION: [
            (r'failed\s+to\s+extract', 'extracción', 0.7),
            (r'no\s+content\s+found', 'contenido vacío', 0.6),
            (r'empty\s+response', 'respuesta vacía', 0.6),
            (r'cannot\s+parse\s+response', 'parsing fallido', 0.5),
        ],
        ErrorCategory.FORMAT: [
            (r'invalid\s+format', 'formato inválido', 0.6),
            (r'malformed\s+json', 'JSON malformado', 0.7),
            (r'encoding\s+error', 'error de codificación', 0.5),
            (r'unsupported\s+charset', 'charset no soportado', 0.4),
        ],
        ErrorCategory.NETWORK: [
            (r'timeout', 'timeout de red', 0.6),
            (r'connection\s+refused', 'conexión rechazada', 0.7),
            (r'dns\s+fail', 'fallo DNS', 0.8),
            (r'ssl\s+error', 'error SSL', 0.7),
            (r'connection\s+reset', 'conexión reiniciada', 0.5),
        ],
        ErrorCategory.PARSING: [
            (r'parse\s+error', 'error de parsing', 0.5),
            (r'html\s+parser', 'HTML no parseable', 0.6),
            (r'regex\s+fail', 'regex fallido', 0.4),
            (r'xml\s+error', 'error XML', 0.5),
        ],
        ErrorCategory.VALIDATION: [
            (r'validation\s+failed', 'validación fallida', 0.5),
            (r'invalid\s+schema', 'schema inválido', 0.6),
            (r'missing\s+field', 'campo faltante', 0.4),
            (r'duplicate\s+entry', 'entrada duplicada', 0.3),
        ],
        ErrorCategory.CONTENT: [
            (r'no\s+text\s+found', 'sin texto extraíble', 0.6),
            (r'video\s+only', 'solo video sin texto', 0.5),
            (r'blocked\s+content', 'contenido bloqueado', 0.7),
            (r'paywall', 'paywall detectado', 0.8),
        ]
    }

    SOLUTIONS = {
        ErrorCategory.EXTRACTION: {
            ActionType.RETRY: "Reintentar con delay exponencial (1s, 2s, 4s)",
            ActionType.FALLBACK: "Usar fuente alternativa o backup",
            ActionType.FIX: "Revisar selectors CSS/XPath del extractor"
        },
        ErrorCategory.FORMAT: {
            ActionType.FIX: "Aplicar normalización de encoding UTF-8",
            ActionType.FALLBACK: "Intentar parsing con lenient mode"
        },
        ErrorCategory.NETWORK: {
            ActionType.RETRY: "Reintentar con backoff exponencial",
            ActionType.NOTIFY: "Alertar si más de 3 retries fallan"
        },
        ErrorCategory.PARSING: {
            ActionType.FIX: "Ajustar expresiones regulares",
            ActionType.FALLBACK: "Usar parser más flexible"
        },
        ErrorCategory.VALIDATION: {
            ActionType.FIX: "Aplicar schema por defecto",
            ActionType.IGNORE: "Omitir validación opcional"
        },
        ErrorCategory.CONTENT: {
            ActionType.FALLBACK: "Buscar fuente alternativa",
            ActionType.SKIP: "Marcar como no procesable y continuar"
        },
        ErrorCategory.UNKNOWN: {
            ActionType.NOTIFY: "Revisar logs para más detalle",
            ActionType.RETRY: "Reintentar operación"
        }
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def translate(self, error: str, context: Optional[Dict] = None) -> ErrorTranslation:
        """
        Traduce error a solución accionable.

        Args:
            error: Mensaje de error
            context: Contexto adicional (opcional)

        Returns:
            ErrorTranslation con diagnóstico y solución
        """
        if self.ai_client and self.ai_client.is_available():
            return self._translate_with_ai(error, context)
        return self._translate_fallback(error, context)

    def _translate_with_ai(self, error: str, context: Optional[Dict]) -> ErrorTranslation:
        """Traduce usando Ollama."""
        try:
            result = self.ai_client.analyze(error, "error")
            if result.success:
                parsed = result.metadata
                category = ErrorCategory(parsed.get('category', 'unknown'))
                action = ActionType(parsed.get('action', 'retry'))

                return ErrorTranslation(
                    original_error=error,
                    category=category,
                    severity=parsed.get('severity', 0.5),
                    solution=parsed.get('solution', 'Revisar manualmente'),
                    action=action,
                    troubleshooting_steps=parsed.get('steps', []),
                    prevention_tips=parsed.get('prevention', [])
                )
        except Exception as e:
            logger.warning(f"AI error translation failed: {e}")
        return self._translate_fallback(error, context)

    def _translate_fallback(self, error: str, context: Optional[Dict]) -> ErrorTranslation:
        """Traduce usando patrones."""
        error_lower = error.lower()
        matched_category = ErrorCategory.UNKNOWN
        severity = 0.5

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern, _, sev in patterns:
                if re.search(pattern, error_lower):
                    matched_category = category
                    severity = sev
                    break
            if matched_category != ErrorCategory.UNKNOWN:
                break

        solutions = self.SOLUTIONS.get(matched_category, self.SOLUTIONS[ErrorCategory.UNKNOWN])
        default_action = ActionType.RETRY if matched_category != ErrorCategory.UNKNOWN else ActionType.NOTIFY
        solution = solutions.get(default_action, "Revisar logs para más detalle")

        troubleshooting = self._get_troubleshooting_steps(matched_category)
        prevention = self._get_prevention_tips(matched_category)

        return ErrorTranslation(
            original_error=error,
            category=matched_category,
            severity=severity,
            solution=solution,
            action=default_action,
            troubleshooting_steps=troubleshooting,
            prevention_tips=prevention
        )

    def _get_troubleshooting_steps(self, category: ErrorCategory) -> List[str]:
        """Obtiene pasos de troubleshooting por categoría."""
        steps_map = {
            ErrorCategory.EXTRACTION: [
                "1. Verificar que la URL es accesible",
                "2. Revisar logs de red",
                "3. Probar con User-Agent alternativo"
            ],
            ErrorCategory.NETWORK: [
                "1. Verificar conexión a internet",
                "2. Revisar firewall/proxy",
                "3. Probar ping a host"
            ],
            ErrorCategory.FORMAT: [
                "1. Verificar encoding del archivo",
                "2. Intentar conversión a UTF-8",
                "3. Revisar estructura del JSON"
            ],
            ErrorCategory.CONTENT: [
                "1. Buscar espejo/archive del contenido",
                "2. Verificar si requiere autenticación",
                "3. Intentar con diferente crawler"
            ]
        }
        return steps_map.get(category, ["Revisar logs detallados", "Consultar documentación"])

    def _get_prevention_tips(self, category: ErrorCategory) -> List[str]:
        """Obtiene tips de prevención por categoría."""
        tips_map = {
            ErrorCategory.NETWORK: [
                "Implementar retry con exponential backoff",
                "Usar circuit breaker para APIs externas"
            ],
            ErrorCategory.EXTRACTION: [
                "Mantener selectores actualizados",
                "Verificar periódicamente fuentes"
            ],
            ErrorCategory.FORMAT: [
                "Validar schemas antes de parsing",
                "Estandarizar formatos de entrada"
            ]
        }
        return tips_map.get(category, ["Monitorear logs regularmente"])

    def batch_translate(self, errors: List[str]) -> List[ErrorTranslation]:
        """Traduce múltiples errores."""
        return [self.translate(e) for e in errors]

    def get_action_summary(self, translations: List[ErrorTranslation]) -> Dict[ActionType, int]:
        """Resume acciones recomendadas."""
        summary = {}
        for t in translations:
            action = t.action.value
            summary[action] = summary.get(action, 0) + 1
        return summary