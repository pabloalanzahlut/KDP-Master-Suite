"""
ConfigValidator - Módulo 44
============================
Valida configs de módulos antes de ejecutar.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, fields
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    validated_config: Dict[str, Any]

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ConfigValidator:
    """
    Validador de configuraciones de módulos.
    Verifica tipos, rangos y dependencias.
    """

    TYPE_VALIDATORS = {
        'int': lambda v: isinstance(v, int),
        'float': lambda v: isinstance(v, (int, float)),
        'str': lambda v: isinstance(v, str),
        'bool': lambda v: isinstance(v, bool),
        'list': lambda v: isinstance(v, list),
        'dict': lambda v: isinstance(v, dict)
    }

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self._schema_registry: Dict[str, Dict[str, Any]] = {}

    def register_schema(self, module_name: str, schema: Dict[str, Any]):
        """
        Registra schema de validación para un módulo.

        Args:
            module_name: Nombre del módulo
            schema: Dict con {field_name: {type, required, min, max, values}}
        """
        self._schema_registry[module_name] = schema
        logger.info(f"ConfigValidator: Schema registrado para '{module_name}'")

    def validate(self, module_name: str, config: Dict[str, Any]) -> ValidationResult:
        """
        Valida configuración contra schema.

        Args:
            module_name: Nombre del módulo
            config: Configuración a validar

        Returns:
            ValidationResult con errores y warnings
        """
        errors = []
        warnings = []
        validated = {}

        schema = self._schema_registry.get(module_name)
        if not schema:
            if self.level == ValidationLevel.STRICT:
                errors.append(f"No schema registrado para '{module_name}'")
            warnings.append(f"Sin schema para '{module_name}', validación básica")
            return ValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                validated_config=config
            )

        for field_name, field_spec in schema.items():
            value = config.get(field_name)
            field_errors, field_warnings = self._validate_field(
                field_name, value, field_spec
            )
            errors.extend(field_errors)
            warnings.extend(field_warnings)

            if value is not None or field_spec.get('required', False):
                validated[field_name] = value

        for field_name in config:
            if field_name not in schema:
                warnings.append(f"Campo '{field_name}' no en schema")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_config=validated
        )

    def _validate_field(self, name: str, value: Any, spec: Dict[str, Any]) -> tuple:
        """Valida un campo individual."""
        errors = []
        warnings = []

        required = spec.get('required', False)
        if value is None:
            if required:
                errors.append(f"Campo requerido '{name}' es None")
            return errors, warnings

        expected_type = spec.get('type')
        if expected_type:
            validator = self.TYPE_VALIDATORS.get(expected_type)
            if validator and not validator(value):
                errors.append(f"'{name}': tipo inválido, esperado {expected_type}")

        if 'min' in spec and isinstance(value, (int, float)):
            if value < spec['min']:
                errors.append(f"'{name}': valor {value} menor que mínimo {spec['min']}")

        if 'max' in spec and isinstance(value, (int, float)):
            if value > spec['max']:
                errors.append(f"'{name}': valor {value} mayor que máximo {spec['max']}")

        if 'values' in spec and isinstance(spec['values'], list):
            if value not in spec['values']:
                errors.append(f"'{name}': valor '{value}' no en lista permitida")

        if 'min_length' in spec and isinstance(value, (str, list)):
            if len(value) < spec['min_length']:
                errors.append(f"'{name}': longitud {len(value)} menor que mínimo {spec['min_length']}")

        if 'max_length' in spec and isinstance(value, (str, list)):
            if len(value) > spec['max_length']:
                errors.append(f"'{name}': longitud {len(value)} mayor que máximo {spec['max_length']}")

        return errors, warnings

    def validate_module_configs(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, ValidationResult]:
        """Valida múltiples configs de módulos."""
        results = {}
        for module_name, config in configs.items():
            results[module_name] = self.validate(module_name, config)
        return results


config_validator_instance = ConfigValidator()


def create_config_validator(level: ValidationLevel = ValidationLevel.NORMAL) -> ConfigValidator:
    """Factory function."""
    return ConfigValidator(level)