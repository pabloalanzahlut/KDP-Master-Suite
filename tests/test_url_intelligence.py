"""
Test Suite para URL Intelligence Modules - Módulos 1-10
=========================================================
Tests para validar:
- Módulo 1: URLSyntaxValidator
- Módulo 2: VideoIDExtractor
- Módulo 3: DomainWhitelist
- Módulo 4: DNSResolver
- Módulo 5: HTTPHeadValidator
- Módulo 6: SSLValidator
- Módulo 7: HTTPStatusInterpreter
- Módulo 8: RedirectChain
- Módulo 9: UserAgentRotator
- Módulo 10: ConnectionPool

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import os
import sys
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestURLSyntaxValidator(unittest.TestCase):
    """Tests para Módulo 1: URLSyntaxValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.cc_schema import URLSyntaxValidator
        validator = URLSyntaxValidator()
        self.assertIsNotNone(validator)

    def test_valid_https_url(self):
        """Test de URL HTTPS válida."""
        from app.modules.cc_schema import URLSyntaxValidator
        validator = URLSyntaxValidator()
        result = validator.validate("https://www.youtube.com/watch?v=abc123")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.scheme, "https")

    def test_valid_http_url(self):
        """Test de URL HTTP válida."""
        from app.modules.cc_schema import URLSyntaxValidator
        validator = URLSyntaxValidator()
        result = validator.validate("http://example.com/video")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.scheme, "http")

    def test_invalid_missing_scheme(self):
        """Test de URL sin esquema."""
        from app.modules.cc_schema import URLSyntaxValidator
        validator = URLSyntaxValidator()
        result = validator.validate("www.youtube.com/watch?v=abc")
        self.assertFalse(result.is_valid)
        self.assertIn("esquema", result.errors[0].lower())

    def test_invalid_unsupported_scheme(self):
        """Test de esquema no soportado."""
        from app.modules.cc_schema import URLSyntaxValidator
        validator = URLSyntaxValidator()
        result = validator.validate("ftp://example.com/file")
        self.assertFalse(result.is_valid)

    def test_normalize_url(self):
        """Test de normalización de URL."""
        from app.modules.cc_schema import URLSyntaxValidator
        validator = URLSyntaxValidator()
        normalized = validator.normalize("HTTPS://WWW.YOUTUBE.COM/WATCH?V=ABC123")
        self.assertIn("youtube.com", normalized.lower())
        self.assertTrue(normalized.startswith("https://"))


class TestVideoIDExtractor(unittest.TestCase):
    """Tests para Módulo 2: VideoIDExtractor"""

    def test_extractor_creation(self):
        """Test de creación del extractor."""
        from app.modules.cc_schema import VideoIDExtractor
        extractor = VideoIDExtractor()
        self.assertIsNotNone(extractor)

    def test_extract_standard_youtube(self):
        """Test de extracción de YouTube estándar."""
        from app.modules.cc_schema import VideoIDExtractor
        extractor = VideoIDExtractor()
        result = extractor.extract("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.video_id, "dQw4w9WgXcQ")
        self.assertEqual(result.platform.value, "youtube")

    def test_extract_youtu_be(self):
        """Test de extracción de youtu.be."""
        from app.modules.cc_schema import VideoIDExtractor
        extractor = VideoIDExtractor()
        result = extractor.extract("https://youtu.be/dQw4w9WgXcQ")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.video_id, "dQw4w9WgXcQ")

    def test_extract_vimeo(self):
        """Test de extracción de Vimeo."""
        from app.modules.cc_schema import VideoIDExtractor
        extractor = VideoIDExtractor()
        result = extractor.extract("https://vimeo.com/123456789")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.platform.value, "vimeo")

    def test_extract_invalid_url(self):
        """Test de URL inválida."""
        from app.modules.cc_schema import VideoIDExtractor
        extractor = VideoIDExtractor()
        result = extractor.extract("not-a-valid-url")
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.video_id)

    def test_is_video_url(self):
        """Test de verificación de URL de video."""
        from app.modules.cc_schema import VideoIDExtractor
        extractor = VideoIDExtractor()
        self.assertTrue(extractor.is_video_url("https://www.youtube.com/watch?v=abc123"))
        self.assertFalse(extractor.is_video_url("https://example.com"))


class TestDomainWhitelist(unittest.TestCase):
    """Tests para Módulo 3: DomainWhitelist"""

    def test_whitelist_creation(self):
        """Test de creación del validador."""
        from app.modules.cc_schema import DomainWhitelist
        wl = DomainWhitelist()
        self.assertIsNotNone(wl)

    def test_allow_youtube(self):
        """Test de YouTube en whitelist."""
        from app.modules.cc_schema import DomainWhitelist
        wl = DomainWhitelist()
        result = wl.validate("https://www.youtube.com/watch?v=abc")
        self.assertTrue(result.is_allowed)
        self.assertEqual(result.status.value, "allowed")

    def test_allow_youtu_be(self):
        """Test de youtu.be en whitelist."""
        from app.modules.cc_schema import DomainWhitelist
        wl = DomainWhitelist()
        result = wl.validate("https://youtu.be/abc123")
        self.assertTrue(result.is_allowed)

    def test_allow_vimeo(self):
        """Test de Vimeo en whitelist."""
        from app.modules.cc_schema import DomainWhitelist
        wl = DomainWhitelist()
        result = wl.validate("https://vimeo.com/123456")
        self.assertTrue(result.is_allowed)

    def test_block_unknown_domain(self):
        """Test de dominio desconocido."""
        from app.modules.cc_schema import DomainWhitelist
        wl = DomainWhitelist()
        result = wl.validate("https://unknown-domain.xyz/video")
        self.assertFalse(result.is_allowed)
        self.assertEqual(result.status.value, "blocked")

    def test_custom_whitelist(self):
        """Test de whitelist personalizada."""
        from app.modules.cc_schema import DomainWhitelist
        wl = DomainWhitelist(whitelist={'example.com'})
        result = wl.validate("https://example.com/video")
        self.assertTrue(result.is_allowed)


class TestDNSResolver(unittest.TestCase):
    """Tests para Módulo 4: DNSResolver"""

    def test_resolver_creation(self):
        """Test de creación del resolvedor."""
        from app.modules.cc_schema import DNSResolver
        resolver = DNSResolver()
        self.assertIsNotNone(resolver)

    def test_resolve_google(self):
        """Test de resolución de google.com."""
        from app.modules.cc_schema import DNSResolver
        resolver = DNSResolver(timeout=5)
        result = resolver.resolve("google.com")
        self.assertEqual(result.status.value, "resolved")
        self.assertTrue(len(result.ip_addresses) > 0)

    def test_resolve_youtube(self):
        """Test de resolución de youtube.com."""
        from app.modules.cc_schema import DNSResolver
        resolver = DNSResolver()
        result = resolver.resolve("youtube.com")
        self.assertEqual(result.status.value, "resolved")

    def test_resolve_invalid_domain(self):
        """Test de dominio inválido."""
        from app.modules.cc_schema import DNSResolver
        resolver = DNSResolver()
        result = resolver.resolve("this-domain-does-not-exist-12345.com")
        self.assertEqual(result.status.value, "nxdomain")

    def test_is_resolvable(self):
        """Test de verificación de resolubilidad."""
        from app.modules.cc_schema import DNSResolver
        resolver = DNSResolver()
        self.assertTrue(resolver.is_resolvable("google.com"))
        self.assertFalse(resolver.is_resolvable("nonexistent-xyz-12345.com"))

    def test_clear_cache(self):
        """Test de limpieza de cache."""
        from app.modules.cc_schema import DNSResolver
        resolver = DNSResolver()
        resolver.resolve("google.com")
        resolver.clear_cache()
        self.assertEqual(len(resolver._cache), 0)


class TestHTTPHeadValidator(unittest.TestCase):
    """Tests para Módulo 5: HTTPHeadValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.cc_schema import HTTPHeadValidator
        validator = HTTPHeadValidator()
        self.assertIsNotNone(validator)

    def test_validate_google(self):
        """Test de validación de google.com."""
        from app.modules.cc_schema import HTTPHeadValidator
        validator = HTTPHeadValidator()
        result = validator.validate("https://www.google.com")
        self.assertIn(result.status.value, ["available", "unavailable"])

    def test_validate_nonexistent(self):
        """Test de URL inexistente."""
        from app.modules.cc_schema import HTTPHeadValidator
        validator = HTTPHeadValidator(timeout=5)
        result = validator.validate("https://this-domain-does-not-exist-xyz.com")
        self.assertEqual(result.status.value, "error")

    def test_is_available(self):
        """Test de verificación de disponibilidad."""
        from app.modules.cc_schema import HTTPHeadValidator
        validator = HTTPHeadValidator()
        is_available = validator.is_available("https://www.google.com")
        self.assertIsInstance(is_available, bool)

    def test_response_time_recorded(self):
        """Test de que response time es registrado."""
        from app.modules.cc_schema import HTTPHeadValidator
        validator = HTTPHeadValidator(timeout=10)
        result = validator.validate("https://www.google.com")
        self.assertGreater(result.response_time_ms, 0)

    def test_close_session(self):
        """Test de cierre de sesión."""
        from app.modules.cc_schema import HTTPHeadValidator
        validator = HTTPHeadValidator()
        validator.close()


class TestSSLValidator(unittest.TestCase):
    """Tests para Módulo 6: SSLValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.cc_schema import SSLValidator
        validator = SSLValidator()
        self.assertIsNotNone(validator)

    def test_validate_google_ssl(self):
        """Test de validación SSL de google.com."""
        from app.modules.cc_schema import SSLValidator
        validator = SSLValidator()
        result = validator.validate("https://www.google.com")
        self.assertIn(result.status.value, ["valid", "invalid", "error"])

    def test_validate_youtube_ssl(self):
        """Test de validación SSL de youtube.com."""
        from app.modules.cc_schema import SSLValidator
        validator = SSLValidator()
        result = validator.validate("https://www.youtube.com")
        self.assertIn(result.status.value, ["valid", "invalid"])

    def test_validate_http_fails(self):
        """Test de que HTTP falla para SSL."""
        from app.modules.cc_schema import SSLValidator
        validator = SSLValidator()
        result = validator.validate("http://www.example.com")
        self.assertEqual(result.status.value, "invalid")

    def test_is_valid_method(self):
        """Test del método is_valid."""
        from app.modules.cc_schema import SSLValidator
        validator = SSLValidator()
        is_valid = validator.is_valid("https://www.google.com")
        self.assertIsInstance(is_valid, bool)

    def test_extract_domain(self):
        """Test de extracción de dominio."""
        from app.modules.cc_schema import SSLValidator
        validator = SSLValidator()
        domain = validator._extract_domain("https://www.youtube.com/watch?v=abc")
        self.assertEqual(domain, "www.youtube.com")


class TestHTTPStatusInterpreter(unittest.TestCase):
    """Tests para Módulo 7: HTTPStatusInterpreter"""

    def test_interpreter_creation(self):
        """Test de creación del intérprete."""
        from app.modules.cc_schema import HTTPStatusInterpreter
        interpreter = HTTPStatusInterpreter()
        self.assertIsNotNone(interpreter)

    def test_interpret_200(self):
        """Test de código 200."""
        from app.modules.cc_schema import HTTPStatusInterpreter
        interpreter = HTTPStatusInterpreter()
        result = interpreter.interpret(200)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.category.value, "success")

    def test_interpret_404(self):
        """Test de código 404."""
        from app.modules.cc_schema import HTTPStatusInterpreter
        interpreter = HTTPStatusInterpreter()
        result = interpreter.interpret(404)
        self.assertEqual(result.status_code, 404)
        self.assertTrue(result.is_blocking)

    def test_interpret_403(self):
        """Test de código 403."""
        from app.modules.cc_schema import HTTPStatusInterpreter
        interpreter = HTTPStatusInterpreter()
        result = interpreter.interpret(403)
        self.assertEqual(result.status_code, 403)
        self.assertTrue(result.is_blocking)

    def test_interpret_429(self):
        """Test de código 429 (rate limit)."""
        from app.modules.cc_schema import HTTPStatusInterpreter
        interpreter = HTTPStatusInterpreter()
        result = interpreter.interpret(429)
        self.assertEqual(result.status_code, 429)

    def test_should_proceed(self):
        """Test de should_proceed."""
        from app.modules.cc_schema import HTTPStatusInterpreter
        interpreter = HTTPStatusInterpreter()
        self.assertTrue(interpreter.should_proceed(200))
        self.assertFalse(interpreter.should_proceed(404))

    def test_is_blocking(self):
        """Test de is_blocking."""
        from app.modules.cc_schema import HTTPStatusInterpreter
        interpreter = HTTPStatusInterpreter()
        self.assertFalse(interpreter.is_blocking(200))
        self.assertTrue(interpreter.is_blocking(404))
        self.assertTrue(interpreter.is_blocking(500))


class TestRedirectChain(unittest.TestCase):
    """Tests para Módulo 8: RedirectChain"""

    def test_chain_creation(self):
        """Test de creación del follower."""
        from app.modules.cc_schema import RedirectChain
        chain = RedirectChain()
        self.assertIsNotNone(chain)

    def test_no_redirect_google(self):
        """Test de URL sin redirect."""
        from app.modules.cc_schema import RedirectChain
        chain = RedirectChain()
        result = chain.follow("https://www.google.com")
        self.assertEqual(result.total_hops, 1)
        self.assertFalse(result.is_circular)

    def test_follow_youtu_be(self):
        """Test de seguimiento de youtu.be."""
        from app.modules.cc_schema import RedirectChain
        chain = RedirectChain(max_hops=5)
        result = chain.follow("https://youtu.be/dQw4w9WgXcQ")
        self.assertIsNotNone(result)

    def test_has_redirect(self):
        """Test de detección de redirects."""
        from app.modules.cc_schema import RedirectChain
        chain = RedirectChain()
        has_redirect = chain.has_redirect("https://youtu.be/abc123")
        self.assertIsInstance(has_redirect, bool)

    def test_resolve_short_url(self):
        """Test de resolución de URL corta."""
        from app.modules.cc_schema import RedirectChain
        chain = RedirectChain()
        result = chain.resolve_short_url("https://youtu.be/abc123")
        self.assertIsNotNone(result)

    def test_close(self):
        """Test de cierre."""
        from app.modules.cc_schema import RedirectChain
        chain = RedirectChain()
        chain.close()


class TestUserAgentRotator(unittest.TestCase):
    """Tests para Módulo 9: UserAgentRotator"""

    def test_rotator_creation(self):
        """Test de creación del rotator."""
        from app.modules.cc_schema import UserAgentRotator
        rotator = UserAgentRotator()
        self.assertIsNotNone(rotator)

    def test_get_user_agent(self):
        """Test de obtención de User-Agent."""
        from app.modules.cc_schema import UserAgentRotator
        rotator = UserAgentRotator()
        ua = rotator.get()
        self.assertIsInstance(ua, str)
        self.assertTrue(len(ua) > 0)

    def test_get_desktop(self):
        """Test de obtención de User-Agent de escritorio."""
        from app.modules.cc_schema import UserAgentRotator
        rotator = UserAgentRotator()
        ua = rotator.get_desktop()
        self.assertIn("Mozilla", ua)

    def test_get_mobile(self):
        """Test de obtención de User-Agent móvil."""
        from app.modules.cc_schema import UserAgentRotator
        rotator = UserAgentRotator()
        ua = rotator.get_mobile()
        self.assertIn("Mobile", ua)

    def test_get_info(self):
        """Test de extracción de información."""
        from app.modules.cc_schema import UserAgentRotator
        rotator = UserAgentRotator()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"
        info = rotator.get_info(ua)
        self.assertEqual(info.browser, "Chrome")
        self.assertEqual(info.os, "Windows")
        self.assertFalse(info.is_mobile)

    def test_history(self):
        """Test de historial."""
        from app.modules.cc_schema import UserAgentRotator
        rotator = UserAgentRotator()
        rotator.get()
        rotator.get()
        history = rotator.get_history()
        self.assertEqual(len(history), 2)

    def test_clear_history(self):
        """Test de limpieza de historial."""
        from app.modules.cc_schema import UserAgentRotator
        rotator = UserAgentRotator()
        rotator.get()
        rotator.clear_history()
        self.assertEqual(len(rotator.get_history()), 0)


class TestConnectionPool(unittest.TestCase):
    """Tests para Módulo 10: ConnectionPool"""

    def test_pool_creation(self):
        """Test de creación del pool."""
        from app.modules.cc_schema import ConnectionPool
        pool = ConnectionPool()
        self.assertIsNotNone(pool)

    def test_get_session(self):
        """Test de obtención de sesión."""
        from app.modules.cc_schema import ConnectionPool
        pool = ConnectionPool()
        session = pool.get_session()
        self.assertIsNotNone(session)

    def test_session_reuse(self):
        """Test de reutilización de sesión."""
        from app.modules.cc_schema import ConnectionPool
        pool = ConnectionPool()
        session1 = pool.get_session()
        session2 = pool.get_session()
        self.assertEqual(id(session1), id(session2))

    def test_get_stats(self):
        """Test de obtención de estadísticas."""
        from app.modules.cc_schema import ConnectionPool
        pool = ConnectionPool()
        pool.get_session()
        stats = pool.get_stats()
        self.assertEqual(stats.total_connections, 10)
        self.assertGreater(stats.connections_created, 0)

    def test_context_manager(self):
        """Test de uso como context manager."""
        from app.modules.cc_schema import ConnectionPool
        with ConnectionPool() as pool:
            session = pool.get_session()
            self.assertIsNotNone(session)

    def test_close(self):
        """Test de cierre del pool."""
        from app.modules.cc_schema import ConnectionPool
        pool = ConnectionPool()
        pool.get_session()
        pool.close()


if __name__ == '__main__':
    unittest.main()