"""
Test Suite para CC Schema Monitor - Módulos 1-5
================================================
Tests para validar:
- Módulo 1: CCAvailabilityValidator
- Módulo 2: ParallelSubtitleFetcher
- Módulo 3: TextNormalizer
- Módulo 4: SpaceValidator
- Módulo 5: ContentDeduplicator

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCCAvailabilityValidator(unittest.TestCase):
    """Tests para Módulo 1: CCAvailabilityValidator"""

    def setUp(self):
        self.test_db = tempfile.mktemp(suffix='.db')
        from app.modules.cc_schema import CCAvailabilityValidator
        self.validator = CCAvailabilityValidator(db_path=self.test_db, cache_enabled=True)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_validator_creation(self):
        """Test de creación del validador."""
        self.assertIsNotNone(self.validator)
        self.assertTrue(self.validator.cache_enabled)

    def test_format_enum_values(self):
        """Test de valores del enum CCFormat."""
        from app.modules.cc_schema import CCFormat
        self.assertEqual(CCFormat.VTT.value, "vtt")
        self.assertEqual(CCFormat.SRT.value, "srt")
        self.assertEqual(CCFormat.JSON.value, "json")
        self.assertEqual(CCFormat.TXT.value, "txt")

    def test_result_dataclass_fields(self):
        """Test de campos del CCCheckResult."""
        from app.modules.cc_schema.cc_availability_validator import CCCheckResult
        result = CCCheckResult(
            available=True,
            formats=[],
            language="en",
            auto_generated=False,
            duration_seconds=120,
            subtitle_count=50,
            confidence_score=0.85
        )
        self.assertTrue(result.available)
        self.assertEqual(result.language, "en")
        self.assertEqual(result.confidence_score, 0.85)

    def test_quality_threshold_validation(self):
        """Test de validación de umbral de calidad."""
        from app.modules.cc_schema.cc_availability_validator import CCCheckResult
        good_result = CCCheckResult(
            available=True,
            formats=[],
            language="en",
            auto_generated=False,
            duration_seconds=120,
            subtitle_count=50,
            confidence_score=0.75
        )
        bad_result = CCCheckResult(
            available=False,
            formats=[],
            language=None,
            auto_generated=False,
            duration_seconds=None,
            subtitle_count=None,
            confidence_score=0.0
        )
        self.assertTrue(self.validator.validate_quality_threshold(good_result, 0.6))
        self.assertFalse(self.validator.validate_quality_threshold(bad_result, 0.6))

    def test_preferred_format_selection(self):
        """Test de selección de formato preferido."""
        from app.modules.cc_schema.cc_availability_validator import CCCheckResult
        from app.modules.cc_schema import CCFormat
        result = CCCheckResult(
            available=True,
            formats=[CCFormat.SRT, CCFormat.VTT],
            language="en",
            auto_generated=False,
            duration_seconds=120,
            subtitle_count=50,
            confidence_score=0.85
        )
        preferred = self.validator.get_preferred_format(result)
        self.assertEqual(preferred, CCFormat.VTT)

    def test_preferred_format_empty(self):
        """Test con formatos vacíos."""
        from app.modules.cc_schema.cc_availability_validator import CCCheckResult
        result = CCCheckResult(
            available=False,
            formats=[],
            language=None,
            auto_generated=False,
            duration_seconds=None,
            subtitle_count=0,
            confidence_score=0.0
        )
        preferred = self.validator.get_preferred_format(result)
        self.assertIsNone(preferred)


class TestParallelSubtitleFetcher(unittest.TestCase):
    """Tests para Módulo 2: ParallelSubtitleFetcher"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        from app.modules.cc_schema import ParallelSubtitleFetcher, ParallelFetchConfig
        config = ParallelFetchConfig(max_workers=2, timeout_seconds=5)
        self.fetcher = ParallelSubtitleFetcher(config=config)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_fetcher_creation(self):
        """Test de creación del fetcher."""
        self.assertIsNotNone(self.fetcher)
        self.assertEqual(self.fetcher.config.max_workers, 2)

    def test_format_enum_values(self):
        """Test de valores del enum SubtitleFormat."""
        from app.modules.cc_schema import SubtitleFormat
        self.assertEqual(SubtitleFormat.VTT.value, "vtt")
        self.assertEqual(SubtitleFormat.SRT.value, "srt")

    def test_result_dataclass(self):
        """Test de SubtitleDownloadResult."""
        from app.modules.cc_schema import SubtitleDownloadResult, SubtitleFormat
        result = SubtitleDownloadResult(
            format=SubtitleFormat.VTT,
            success=True,
            file_path="/test/path.vtt",
            content="WEBVTT\n00:00:00.000 --> 00:00:05.000\nTest",
            error=None,
            download_time=1.5,
            file_size=1024
        )
        self.assertTrue(result.success)
        self.assertEqual(result.format, SubtitleFormat.VTT)
        self.assertEqual(result.file_size, 1024)

    def test_cleanup_temp_files(self):
        """Test de limpieza de archivos temporales."""
        test_file = os.path.join(self.test_dir, "test_video.vtt")
        with open(test_file, 'w') as f:
            f.write("test content")

        self.fetcher.cleanup_temp_files(self.test_dir, "test_video")
        self.assertFalse(os.path.exists(test_file))

    def test_get_active_count(self):
        """Test de conteo de requests activos."""
        count = self.fetcher.get_active_count()
        self.assertEqual(count, 0)


class TestTextNormalizer(unittest.TestCase):
    """Tests para Módulo 3: TextNormalizer"""

    def setUp(self):
        from app.utils.text_normalizer import TextNormalizer
        self.normalizer = TextNormalizer(aggressive_cleaning=False)

    def test_normalizer_creation(self):
        """Test de creación del normalizador."""
        self.assertIsNotNone(self.normalizer)
        self.assertFalse(self.normalizer.aggressive_cleaning)

    def test_normalize_string_basic(self):
        """Test de normalización básica de string."""
        result = self.normalizer.normalize_string("  Hello   World  ")
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Hello World")

    def test_remove_control_chars(self):
        """Test de remoción de caracteres de control."""
        text_with_controls = "Hello\x00World\x1FTest"
        count = self.normalizer._remove_control_characters(text_with_controls)
        self.assertGreater(count, 0)

    def test_clean_whitespace(self):
        """Test de limpieza de whitespace."""
        dirty = "Hello\n\n\n\n\nWorld"
        cleaned = self.normalizer._clean_whitespace(dirty)
        self.assertNotIn('\n\n\n', cleaned)

    def test_remove_problematic_unicode(self):
        """Test de remoción de Unicode problemático."""
        text = "Hello\u200BWorld\uFEFFTest"
        cleaned = self.normalizer._remove_problematic_unicode(text)
        self.assertNotIn('\u200B', cleaned)
        self.assertNotIn('\uFEFF', cleaned)

    def test_detect_utf8_encoding(self):
        """Test de detección de encoding UTF-8."""
        raw = "Hello World".encode('utf-8')
        detected = self.normalizer._detect_encoding(raw)
        self.assertEqual(detected, 'utf-8')

    def test_detect_latin1_encoding(self):
        """Test de detección de encoding Latin-1."""
        raw = "Caf\xe9".encode('latin-1')
        detected = self.normalizer._detect_encoding(raw)
        self.assertEqual(detected, 'latin-1')

    def test_validate_utf8_compliance(self):
        """Test de validación de compliance UTF-8."""
        valid_text = "Hello World 日本語"
        is_valid, invalid_positions = self.normalizer.validate_utf8_compliance(valid_text)
        self.assertTrue(is_valid)
        self.assertEqual(len(invalid_positions), 0)

    def test_get_stats(self):
        """Test de estadísticas del normalizador."""
        stats = self.normalizer.get_stats()
        self.assertIn('total_processed', stats)
        self.assertIn('bom_removed', stats)


class TestVTTNormalizer(unittest.TestCase):
    """Tests para VTTNormalizer específico."""

    def setUp(self):
        from app.utils.text_normalizer import VTTNormalizer
        self.vtt_normalizer = VTTNormalizer()

    def test_normalize_vtt_basic(self):
        """Test de normalización VTT básica."""
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello World

00:00:05.000 --> 00:00:10.000
Second subtitle
"""
        result = self.vtt_normalizer.normalize_vtt(vtt_content)
        self.assertIn("Hello World", result)


class TestSRTNormalizer(unittest.TestCase):
    """Tests para SRTNormalizer específico."""

    def setUp(self):
        from app.utils.text_normalizer import SRTNormalizer
        self.srt_normalizer = SRTNormalizer()

    def test_normalize_srt_basic(self):
        """Test de normalización SRT básica."""
        srt_content = """1
00:00:00,000 --> 00:00:05,000
Hello World

2
00:00:05,000 --> 00:00:10,000
Second subtitle
"""
        result = self.srt_normalizer.normalize_srt(srt_content)
        self.assertIn("Hello World", result)


class TestSpaceValidator(unittest.TestCase):
    """Tests para Módulo 4: SpaceValidator"""

    def setUp(self):
        from app.modules.cc_schema import SpaceValidator
        self.validator = SpaceValidator(min_free_mb=10)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_validator_creation(self):
        """Test de creación del validador."""
        self.assertIsNotNone(self.validator)
        self.assertEqual(self.validator.min_free_mb, 10)

    def test_estimate_text_size(self):
        """Test de estimación de tamaño de texto."""
        estimated = self.validator.estimate_text_size(subtitle_count=100)
        self.assertGreater(estimated, 0)
        self.assertLess(estimated, 10000)

    def test_check_available_space(self):
        """Test de verificación de espacio disponible."""
        result = self.validator.check_available_space(self.test_dir)
        self.assertTrue(result.can_proceed)
        self.assertGreater(result.free_space_mb, 0)

    def test_check_batch_size(self):
        """Test de verificación de tamaño de batch."""
        result = self.validator.check_batch_size(self.test_dir, batch_size=10)
        self.assertTrue(result.can_proceed)
        self.assertEqual(result.text_file_count, 10)

    def test_can_store_file(self):
        """Test de verificación de almacenamiento de archivo."""
        content = "test content" * 100
        can_store = self.validator.can_store_file(self.test_dir, content)
        self.assertTrue(can_store)


class TestContentDeduplicator(unittest.TestCase):
    """Tests para Módulo 5: ContentDeduplicator"""

    def setUp(self):
        self.test_db = tempfile.mktemp(suffix='.db')
        from app.modules.cc_schema import ContentDeduplicator
        self.deduplicator = ContentDeduplicator(db_path=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_deduplicator_creation(self):
        """Test de creación del deduplicador."""
        self.assertIsNotNone(self.deduplicator)
        self.assertTrue(os.path.exists(self.test_db))

    def test_compute_hash(self):
        """Test de computación de hash."""
        from app.modules.cc_schema import ContentHasher
        content = "Hello World"
        hash1 = ContentHasher.compute_hash(content)
        hash2 = ContentHasher.compute_hash(content)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_hash_consistency(self):
        """Test de consistencia de hash."""
        from app.modules.cc_schema import ContentHasher
        content = "Hello World"
        hash1 = ContentHasher.compute_hash(content)
        hash2 = ContentHasher.compute_hash("  Hello   World  ")
        self.assertEqual(hash1, hash2)

    def test_partial_hash(self):
        """Test de hash parcial."""
        from app.modules.cc_schema import ContentHasher
        content = "A" * 1000
        partial = ContentHasher.compute_partial_hash(content, length=100)
        self.assertEqual(len(partial), 64)

    def test_check_duplicate_new_content(self):
        """Test de verificación de contenido nuevo (no duplicado)."""
        result = self.deduplicator.check_duplicate("Hello World", video_id="test123")
        self.assertFalse(result.is_duplicate)
        self.assertEqual(len(result.hash), 64)

    def test_register_content(self):
        """Test de registro de contenido."""
        content = "Hello World Test"
        result = self.deduplicator.register_content(
            content=content,
            video_id="test456",
            source_url="https://youtube.com/watch?v=test",
            title="Test Video"
        )
        self.assertTrue(result)

    def test_get_duplicate_count(self):
        """Test de conteo de duplicados."""
        count = self.deduplicator.get_duplicate_count()
        self.assertGreaterEqual(count, 0)

    def test_find_similar_content_empty(self):
        """Test de búsqueda de contenido similar (vacío)."""
        results = self.deduplicator.find_similar_content("Hello World")
        self.assertIsInstance(results, list)


class TestNormalizeFileAuto(unittest.TestCase):
    """Tests para función de conveniencia normalize_file_auto."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_normalize_vtt_file(self):
        """Test de normalización de archivo VTT."""
        from app.utils.text_normalizer import normalize_file_auto
        vtt_file = os.path.join(self.test_dir, "test.vtt")
        with open(vtt_file, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nHello")

        result = normalize_file_auto(vtt_file)
        self.assertTrue(result.success)


class TestIntegration(unittest.TestCase):
    """Tests de integración para flujo completo."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_kb.db")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_normalizer_validator_integration(self):
        """Test de integración normalizador + validador."""
        from app.utils.text_normalizer import TextNormalizer
        from app.modules.cc_schema import ContentHasher

        normalizer = TextNormalizer()
        raw_content = "  Hello   World  \n\n\n\n\nTest"
        normalized = normalizer.normalize_string(raw_content)
        self.assertTrue(normalized.success)

        content_hash = ContentHasher.compute_hash(normalized.content)
        self.assertEqual(len(content_hash), 64)

    def test_space_and_deduplicator_integration(self):
        """Test de integración espacio + deduplicador."""
        from app.modules.cc_schema import SpaceValidator, ContentDeduplicator

        validator = SpaceValidator()
        space_result = validator.check_available_space(self.test_dir)
        self.assertTrue(space_result.can_proceed)

        deduplicator = ContentDeduplicator(db_path=self.test_db)
        count = deduplicator.get_duplicate_count()
        self.assertGreaterEqual(count, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)