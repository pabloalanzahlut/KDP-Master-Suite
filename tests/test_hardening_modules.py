"""
Test Suite para Hardening Modules - Módulos 41-44
================================================
Tests para validar:
- Módulo 41: RateLimitEnforcer
- Módulo 42: CircuitBreaker
- Módulo 43: HealthChecker
- Módulo 44: ConfigValidator

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import sys
import unittest
import time
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRateLimitEnforcer(unittest.TestCase):
    """Tests para Módulo 41: RateLimitEnforcer"""

    def test_limiter_creation(self):
        """Test de creación del limitador."""
        from app.modules.cc_schema import RateLimitEnforcer, RateLimitConfig
        config = RateLimitConfig(calls_per_second=10, burst_size=5)
        limiter = RateLimitEnforcer("test_module", config)
        self.assertIsNotNone(limiter)
        self.assertTrue(limiter.config.enabled)

    def test_allow_calls(self):
        """Test de allow de llamadas."""
        from app.modules.cc_schema import RateLimitEnforcer, RateLimitConfig
        limiter = RateLimitEnforcer("test", RateLimitConfig(burst_size=3, calls_per_second=3))
        self.assertTrue(limiter.allow())
        self.assertTrue(limiter.allow())
        self.assertTrue(limiter.allow())

    def test_reject_after_burst(self):
        """Test de rechazo después de burst."""
        from app.modules.cc_schema import RateLimitEnforcer, RateLimitConfig
        limiter = RateLimitEnforcer("test", RateLimitConfig(burst_size=2, calls_per_second=2))
        limiter.allow()
        limiter.allow()
        result = limiter.allow()
        self.assertFalse(result)

    def test_metrics_tracking(self):
        """Test de tracking de métricas."""
        from app.modules.cc_schema import RateLimitEnforcer
        limiter = RateLimitEnforcer("test")
        limiter.allow()
        limiter.allow()
        metrics = limiter.get_metrics()
        self.assertEqual(metrics['allowed_calls'], 2)
        self.assertEqual(metrics['total_calls'], 2)

    def test_reset(self):
        """Test de reset del limitador."""
        from app.modules.cc_schema import RateLimitEnforcer
        limiter = RateLimitEnforcer("test")
        limiter.allow()
        limiter.allow()
        limiter.reset()
        metrics = limiter.get_metrics()
        self.assertEqual(metrics['total_calls'], 0)


class TestCircuitBreaker(unittest.TestCase):
    """Tests para Módulo 42: CircuitBreaker"""

    def test_breaker_creation(self):
        """Test de creación del breaker."""
        from app.modules.cc_schema import CircuitBreaker, CircuitConfig
        config = CircuitConfig(failure_threshold=3)
        breaker = CircuitBreaker("test_service", config)
        self.assertIsNotNone(breaker)
        self.assertEqual(breaker.name, "test_service")

    def test_initial_state_closed(self):
        """Test de estado inicial cerrado."""
        from app.modules.cc_schema import CircuitBreaker, CircuitState
        breaker = CircuitBreaker("test")
        self.assertEqual(breaker.get_state(), CircuitState.CLOSED)

    def test_call_succeeds_when_closed(self):
        """Test de llamada exitosa cuando está cerrado."""
        from app.modules.cc_schema import CircuitBreaker
        breaker = CircuitBreaker("test")
        breaker.set_callable(lambda: "success")
        result = breaker.call()
        self.assertEqual(result, "success")

    def test_opens_after_threshold(self):
        """Test de apertura después del umbral."""
        from app.modules.cc_schema import CircuitBreaker, CircuitConfig, CircuitState, CircuitOpenError
        config = CircuitConfig(failure_threshold=2)
        breaker = CircuitBreaker("test", config)

        def fail():
            raise Exception("fail")

        breaker.set_callable(fail)

        for _ in range(2):
            try:
                breaker.call()
            except:
                pass

        self.assertEqual(breaker.get_state(), CircuitState.OPEN)

    def test_raises_when_open(self):
        """Test de excepción cuando está abierto."""
        from app.modules.cc_schema import CircuitBreaker, CircuitConfig, CircuitOpenError
        config = CircuitConfig(failure_threshold=1)
        breaker = CircuitBreaker("test", config)

        def fail():
            raise Exception("fail")

        breaker.set_callable(fail)
        try:
            breaker.call()
        except:
            pass

        with self.assertRaises(CircuitOpenError):
            breaker.call()

    def test_metrics(self):
        """Test de métricas."""
        from app.modules.cc_schema import CircuitBreaker
        breaker = CircuitBreaker("test")
        breaker.set_callable(lambda: "ok")
        breaker.call()
        metrics = breaker.get_metrics()
        self.assertEqual(metrics['successes'], 1)


class TestHealthChecker(unittest.TestCase):
    """Tests para Módulo 43: HealthChecker"""

    def test_checker_creation(self):
        """Test de creación del checker."""
        from app.modules.cc_schema.health_checker import HealthChecker
        checker = HealthChecker()
        self.assertIsNotNone(checker)

    def test_register_module(self):
        """Test de registro de módulo."""
        from app.modules.cc_schema.health_checker import HealthChecker
        checker = HealthChecker()
        checker.register_module("test_module", lambda: {'status': 'healthy', 'details': {}})
        self.assertEqual(len(checker._modules), 1)

    def test_check_healthy_module(self):
        """Test de verificación de módulo saludable."""
        from app.modules.cc_schema.health_checker import HealthChecker, HealthStatus
        checker = HealthChecker()
        checker.register_module("healthy_mod", lambda: {'status': 'healthy', 'details': {}})

        result = checker.check_module("healthy_mod")
        self.assertEqual(result.status, HealthStatus.HEALTHY)

    def test_check_unhealthy_module(self):
        """Test de verificación de módulo no saludable."""
        from app.modules.cc_schema.health_checker import HealthChecker, HealthStatus
        checker = HealthChecker()
        checker.register_module("sick_mod", lambda: (_ for _ in ()).throw(Exception("fail")))

        result = checker.check_module("sick_mod")
        self.assertEqual(result.status, HealthStatus.UNHEALTHY)

    def test_check_unknown_module(self):
        """Test de verificación de módulo desconocido."""
        from app.modules.cc_schema.health_checker import HealthChecker, HealthStatus
        checker = HealthChecker()

        result = checker.check_module("unknown_mod")
        self.assertEqual(result.status, HealthStatus.UNKNOWN)

    def test_check_all(self):
        """Test de verificación de todos."""
        from app.modules.cc_schema.health_checker import HealthChecker, HealthStatus
        checker = HealthChecker()
        checker.register_module("mod1", lambda: {'status': 'healthy'})
        checker.register_module("mod2", lambda: {'status': 'healthy'})

        result = checker.check_all()
        self.assertEqual(result.total_modules, 2)
        self.assertEqual(result.overall_status, HealthStatus.HEALTHY)


class TestConfigValidator(unittest.TestCase):
    """Tests para Módulo 44: ConfigValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.cc_schema.config_validator import ConfigValidator, ValidationLevel
        validator = ConfigValidator(ValidationLevel.NORMAL)
        self.assertIsNotNone(validator)
        self.assertEqual(validator.level, ValidationLevel.NORMAL)

    def test_register_schema(self):
        """Test de registro de schema."""
        from app.modules.cc_schema.config_validator import ConfigValidator
        validator = ConfigValidator()
        schema = {
            'timeout': {'type': 'int', 'required': True, 'min': 1},
            'enabled': {'type': 'bool'}
        }
        validator.register_schema("test_module", schema)
        self.assertIn("test_module", validator._schema_registry)

    def test_validate_valid_config(self):
        """Test de validación de config válida."""
        from app.modules.cc_schema.config_validator import ConfigValidator
        validator = ConfigValidator()
        validator.register_schema("test_mod", {
            'timeout': {'type': 'int', 'min': 1, 'max': 60},
            'enabled': {'type': 'bool', 'required': True}
        })

        result = validator.validate("test_mod", {'timeout': 30, 'enabled': True})
        self.assertTrue(result.valid)

    def test_validate_missing_required(self):
        """Test de validación con campo requerido faltante."""
        from app.modules.cc_schema.config_validator import ConfigValidator
        validator = ConfigValidator()
        validator.register_schema("test_mod", {
            'timeout': {'type': 'int', 'required': True}
        })

        result = validator.validate("test_mod", {'timeout': None})
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors), 0)

    def test_validate_invalid_type(self):
        """Test de validación de tipo inválido."""
        from app.modules.cc_schema.config_validator import ConfigValidator
        validator = ConfigValidator()
        validator.register_schema("test_mod", {
            'count': {'type': 'int'}
        })

        result = validator.validate("test_mod", {'count': 'not_an_int'})
        self.assertFalse(result.valid)

    def test_validate_out_of_range(self):
        """Test de validación de valor fuera de rango."""
        from app.modules.cc_schema.config_validator import ConfigValidator
        validator = ConfigValidator()
        validator.register_schema("test_mod", {
            'timeout': {'type': 'int', 'min': 1, 'max': 60}
        })

        result = validator.validate("test_mod", {'timeout': 100})
        self.assertFalse(result.valid)

    def test_validate_with_warnings(self):
        """Test de validación con warnings."""
        from app.modules.cc_schema.config_validator import ConfigValidator
        validator = ConfigValidator()
        validator.register_schema("test_mod", {'timeout': {'type': 'int'}})

        result = validator.validate("test_mod", {'timeout': 10, 'unknown_field': True})
        self.assertTrue(result.valid)
        self.assertGreater(len(result.warnings), 0)


if __name__ == '__main__':
    unittest.main()