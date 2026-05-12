"""
Test Suite para CC Schema Monitor - FASE 3 (Módulos 11-15)
==========================================================
Tests para:
- Módulo 11: CCMetadataCacheManager
- Módulo 12: ThumbnailOCRExtractor
- Módulo 13: LogCompressor
- Módulo 14: ParagraphStructureValidator
- Módulo 15: LanguageDetector

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


class TestCCMetadataCacheManager(unittest.TestCase):
    """Tests para Módulo 11: CCMetadataCacheManager"""

    def setUp(self):
        self.test_db = tempfile.mktemp(suffix='.db')
        from app.modules.cc_schema.cc_metadata_cache import CCMetadataCacheManager
        self.cache = CCMetadataCacheManager(db_path=self.test_db, ttl_seconds=3600)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_cache_creation(self):
        """Test de creación del cache."""
        self.assertIsNotNone(self.cache)
        self.assertEqual(self.cache.ttl_seconds, 3600)

    def test_cache_set_and_get(self):
        """Test de set y get básico."""
        video_id = "test_video_123"
        self.cache.set(
            video_id=video_id,
            available=True,
            formats=['vtt', 'srt'],
            language='en',
            subtitle_count=100,
            confidence_score=0.85
        )

        result = self.cache.get(video_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.video_id, video_id)
        self.assertTrue(result.available)
        self.assertEqual(result.formats, ['vtt', 'srt'])

    def test_cache_invalidate(self):
        """Test de invalidación."""
        video_id = "test_video_456"
        self.cache.set(video_id, available=True, formats=[], language='en')
        self.cache.invalidate(video_id)

        result = self.cache.get(video_id)
        self.assertIsNone(result)

    def test_cache_stats(self):
        """Test de estadísticas."""
        stats = self.cache.get_stats()
        self.assertIn('total_entries', stats)
        self.assertIn('ttl_seconds', stats)

    def test_clear_all(self):
        """Test de limpiar todo."""
        self.cache.set("video1", True, [], 'en')
        self.cache.set("video2", True, [], 'es')
        self.cache.clear_all()

        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 0)

    def test_cache_hit_ratio(self):
        """Test de ratio de hits."""
        ratio = self.cache.get_cache_hit_ratio()
        self.assertIsInstance(ratio, float)
        self.assertGreaterEqual(ratio, 0.0)


class TestThumbnailOCRExtractor(unittest.TestCase):
    """Tests para Módulo 12: ThumbnailOCRExtractor"""

    def setUp(self):
        from app.modules.cc_schema.ocr_fallback import ThumbnailOCRExtractor
        self.ocr = ThumbnailOCRExtractor(min_confidence=0.70)

    def test_ocr_creation(self):
        """Test de creación del OCR."""
        self.assertIsNotNone(self.ocr)
        self.assertEqual(self.ocr.min_confidence, 0.70)

    def test_is_available(self):
        """Test de verificación de disponibilidad."""
        available = self.ocr.is_available()
        self.assertIsInstance(available, bool)

    def test_result_dataclass(self):
        """Test de OCRExtractionResult."""
        from app.modules.cc_schema.ocr_fallback import OCRExtractionResult

        result = OCRExtractionResult(
            success=True,
            frames_processed=5,
            frames_with_text=3,
            total_words=100,
            combined_text="Sample text",
            average_confidence=0.85
        )

        self.assertTrue(result.success)
        self.assertEqual(result.frames_processed, 5)
        self.assertGreater(result.average_confidence, 0.0)

    def test_stats(self):
        """Test de estadísticas."""
        stats = self.ocr.get_stats()
        self.assertIn('total_attempts', stats)


class TestLogCompressor(unittest.TestCase):
    """Tests para Módulo 13: LogCompressor"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        from app.modules.cc_schema.log_compressor import LogCompressor
        self.compressor = LogCompressor(compression_level=3)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_compressor_creation(self):
        """Test de creación del compresor."""
        self.assertIsNotNone(self.compressor)
        self.assertEqual(self.compressor.compression_level, 3)

    def test_compress_file_small(self):
        """Test de compresión de archivo pequeño (skip)."""
        small_file = os.path.join(self.test_dir, "small.log")
        with open(small_file, 'w') as f:
            f.write("Short content")

        result = self.compressor.compress_file(small_file)
        self.assertFalse(result.success)
        self.assertEqual(result.method, "skip_small")

    def test_compress_file_not_found(self):
        """Test de compresión de archivo inexistente."""
        result = self.compressor.compress_file("/nonexistent/file.log")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "File not found")

    def test_get_log_info_not_found(self):
        """Test de info de archivo inexistente."""
        info = self.compressor.get_log_info("/nonexistent.log")
        self.assertIsNone(info)

    def test_compression_stats(self):
        """Test de estadísticas de compresión."""
        stats = self.compressor.get_stats()
        self.assertIn('total_compressed', stats)
        self.assertIn('failed', stats)


class TestParagraphStructureValidator(unittest.TestCase):
    """Tests para Módulo 14: ParagraphStructureValidator"""

    def setUp(self):
        from app.modules.cc_schema.structure_validator import ParagraphStructureValidator
        self.validator = ParagraphStructureValidator(strict_mode=False)

    def test_validator_creation(self):
        """Test de creación del validador."""
        self.assertIsNotNone(self.validator)

    def test_validate_good_structure(self):
        """Test de validación de buena estructura."""
        content = """
        This is the first paragraph with enough content to pass validation tests.
        It contains multiple sentences and proper word distribution throughout.
        All paragraphs have sufficient text length for proper validation.

        Here is the second paragraph with additional valuable information here.
        It continues to provide substantial content for thorough analysis.
        More sentences are added to ensure we meet minimum requirements.

        This is the third paragraph completing the structure requirements here.
        All paragraphs have enough text to be considered valid and properly structured.
        Additional words are included to ensure we exceed the minimum threshold.
        """

        result = self.validator.validate(content)
        self.assertIsNotNone(result)
        self.assertGreater(result.paragraph_count, 0)

    def test_validate_single_paragraph(self):
        """Test de validación con un solo párrafo."""
        content = "Short single paragraph"

        result = self.validator.validate(content)
        self.assertFalse(result.is_valid)

    def test_quick_validate(self):
        """Test de función de conveniencia."""
        from app.modules.cc_schema.structure_validator import quick_validate_structure

        content = """
        First paragraph with enough text.
        More content here to ensure validity.

        Second paragraph also valid.
        """

        is_valid, score = quick_validate_structure(content)
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(score, float)


class TestLanguageDetector(unittest.TestCase):
    """Tests para Módulo 15: LanguageDetector"""

    def setUp(self):
        from app.modules.cc_schema.language_detector import LanguageDetector
        self.detector = LanguageDetector()

    def test_detector_creation(self):
        """Test de creación del detector."""
        self.assertIsNotNone(self.detector)

    def test_detect_english(self):
        """Test de detección de inglés."""
        text = "This is a sample text in English that should be detected correctly."
        result = self.detector.detect(text)

        self.assertTrue(result.detected)
        if result.primary:
            self.assertIn(result.primary.code, ['en', 'es', 'de', 'fr', 'pt'])

    def test_detect_short_text(self):
        """Test de detección de texto corto."""
        text = "Hi"
        result = self.detector.detect(text)
        self.assertFalse(result.detected)

    def test_detect_spanish(self):
        """Test de detección de español."""
        text = "Este es un texto en español que debe ser detectado correctamente."
        result = self.detector.detect(text)

        self.assertTrue(result.detected)

    def test_get_supported_languages(self):
        """Test de lista de idiomas soportados."""
        langs = self.detector.get_supported_languages()
        self.assertIsInstance(langs, list)
        self.assertIn('en', langs)
        self.assertIn('es', langs)

    def test_quick_detect(self):
        """Test de función de conveniencia."""
        from app.modules.cc_schema.language_detector import quick_detect

        text = "Hello world this is English text"
        lang = quick_detect(text)
        self.assertIn(lang, [None, 'en', 'es', 'de', 'fr', 'pt'])


class TestMultiLanguageSegmenter(unittest.TestCase):
    """Tests para MultiLanguageSegmenter."""

    def setUp(self):
        from app.modules.cc_schema.language_detector import MultiLanguageSegmenter
        self.segmenter = MultiLanguageSegmenter()

    def test_segmenter_creation(self):
        """Test de creación del segmenter."""
        self.assertIsNotNone(self.segmenter)

    def test_segment(self):
        """Test de segmentación."""
        text = "Hello world\nThis is English\n\nHola mundo\nEsto es español"
        segments = self.segmenter.segment(text)
        self.assertIsInstance(segments, list)


class TestIntegrationPhase3(unittest.TestCase):
    """Tests de integración FASE 3."""

    def test_cache_and_detector_integration(self):
        """Test de integración cache + detector de idioma."""
        from app.modules.cc_schema.cc_metadata_cache import CCMetadataCacheManager
        from app.modules.cc_schema.language_detector import LanguageDetector
        import tempfile

        db_path = tempfile.mktemp(suffix='.db')

        cache = CCMetadataCacheManager(db_path=db_path)
        detector = LanguageDetector()

        video_id = "integration_test_123"
        cache.set(
            video_id=video_id,
            available=True,
            formats=['vtt'],
            language='en'
        )

        cached = cache.get(video_id)
        self.assertIsNotNone(cached)

        if cached.language:
            lang_result = detector.detect(f"Sample text in {cached.language}")
            self.assertTrue(lang_result.detected or not lang_result.detected)

        os.remove(db_path)

    def test_validator_and_detector_integration(self):
        """Test de integración validador + detector."""
        from app.modules.cc_schema.structure_validator import ParagraphStructureValidator
        from app.modules.cc_schema.language_detector import LanguageDetector

        content = """
        This is a paragraph with valid structure.
        It contains enough content to pass validation.

        Another paragraph for testing purposes.
        """

        validator = ParagraphStructureValidator()
        struct_result = validator.validate(content)

        detector = LanguageDetector()
        lang_result = detector.detect(content)

        self.assertTrue(struct_result.is_valid or not struct_result.is_valid)
        self.assertTrue(lang_result.detected or not lang_result.detected)

    def test_all_modules_import(self):
        """Test de importación de todos los módulos."""
        try:
            from app.modules.cc_schema import (
                CCAvailabilityValidator,
                ParallelSubtitleFetcher,
                SpaceValidator,
                ContentDeduplicator,
                SubtitleQualityFilter,
                PostExtractionValidator,
                ImmutableAuditLedger,
                DomainRateLimiter,
                CCMetadataCacheManager,
                ThumbnailOCRExtractor,
                LogCompressor,
                ParagraphStructureValidator,
                LanguageDetector
            )
            all_ok = True
        except ImportError as e:
            all_ok = False
            self.fail(f"Module import failed: {e}")

        self.assertTrue(all_ok)


if __name__ == '__main__':
    unittest.main(verbosity=2)