"""
Test Suite para CC Schema Monitor - FASE 4 (Módulos 16-20)
==========================================================
Tests para:
- Módulo 16: NoiseCleaner
- Módulo 17: RetryHandler
- Módulo 18: FTS5Validator
- Módulo 19: ManifestGenerator
- Módulo 20: AtomicPersistenceManager

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import sys
import unittest
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNoiseCleaner(unittest.TestCase):
    """Tests para Módulo 16: NoiseCleaner"""

    def setUp(self):
        from app.modules.cc_schema.noise_cleaner import NoiseCleaner
        self.cleaner = NoiseCleaner(aggressive=False)

    def test_cleaner_creation(self):
        """Test de creación del cleaner."""
        self.assertIsNotNone(self.cleaner)
        self.assertFalse(self.cleaner.aggressive)

    def test_clean_timestamps(self):
        """Test de limpieza de timestamps."""
        content = "00:00:00.000 --> 00:00:05.000\nHello World"
        cleaned = self.cleaner.clean(content)
        self.assertNotIn('00:00:00', cleaned)

    def test_clean_speaker_tags(self):
        """Test de limpieza de speaker tags."""
        content = "[Speaker 1] Hello [Speaker 2] World"
        cleaned = self.cleaner.clean(content)
        self.assertNotIn('[Speaker', cleaned)

    def test_clean_promotional(self):
        """Test de limpieza de texto promocional."""
        content = "Don't forget to subscribe to my channel!"
        cleaned = self.cleaner.clean(content)
        self.assertNotIn('subscribe', cleaned.lower())

    def test_clean_whitespace(self):
        """Test de limpieza de whitespace."""
        content = "Hello    World\n\n\n\nTest"
        cleaned = self.cleaner.clean(content)
        self.assertNotIn('    ', cleaned)
        self.assertNotIn('\n\n\n', cleaned)

    def test_clean_detailed(self):
        """Test de limpieza detallada."""
        content = "00:00:00 --> 00:00:05\nHello [Speaker] World"
        result = self.cleaner.clean_detailed(content)
        self.assertIsNotNone(result)
        self.assertGreater(result.removed_count, 0)

    def test_stats(self):
        """Test de estadísticas."""
        self.cleaner.clean("Test content")
        stats = self.cleaner.get_stats()
        self.assertIn('total_cleaned', stats)


class TestRetryHandler(unittest.TestCase):
    """Tests para Módulo 17: RetryHandler"""

    def setUp(self):
        from app.modules.cc_schema.retry_handler import RetryHandler, RetryConfig
        self.handler = RetryHandler(RetryConfig(max_attempts=3, base_delay=0.1))

    def test_handler_creation(self):
        """Test de creación del handler."""
        self.assertIsNotNone(self.handler)
        self.assertEqual(self.handler.config.max_attempts, 3)

    def test_retry_config(self):
        """Test de configuración de retry."""
        from app.modules.cc_schema.retry_handler import RetryConfig, RetryStrategy
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            strategy=RetryStrategy.EXPONENTIAL
        )
        self.assertEqual(config.max_attempts, 5)
        self.assertEqual(config.strategy, RetryStrategy.EXPONENTIAL)

    def test_execute_success(self):
        """Test de ejecución exitosa."""
        def success_func():
            return "success"

        result, retry_result = self.handler.execute(success_func)
        self.assertEqual(result, "success")
        self.assertTrue(retry_result.success)
        self.assertEqual(retry_result.attempts, 1)

    def test_execute_failure(self):
        """Test de ejecución con fallo."""
        attempt_count = [0]

        def fail_func():
            attempt_count[0] += 1
            raise Exception("Test error")

        result, retry_result = self.handler.execute(fail_func)
        self.assertIsNone(result)
        self.assertFalse(retry_result.success)
        self.assertGreaterEqual(retry_result.attempts, 1)

    def test_execute_eventual_success(self):
        """Test de éxito eventual después de reintentos."""
        attempt_count = [0]

        def eventually_success():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                return (False, "Retry needed")
            return (True, "success after retry")

        result, retry_result = self.handler.execute(eventually_success)
        self.assertIsNotNone(result)

    def test_stats(self):
        """Test de estadísticas."""
        stats = self.handler.get_stats()
        self.assertIn('total_attempts', stats)


class TestFTS5Validator(unittest.TestCase):
    """Tests para Módulo 18: FTS5Validator"""

    def setUp(self):
        from app.modules.cc_schema.fts5_validator import FTS5Validator
        self.validator = FTS5Validator()

    def test_validator_creation(self):
        """Test de creación del validador."""
        self.assertIsNotNone(self.validator)

    def test_validate_good_content(self):
        """Test de validación de contenido válido."""
        content = "This is a sample text with enough content to pass FTS5 validation."
        result = self.validator.validate(content)
        self.assertIsNotNone(result)
        self.assertGreater(result.word_count, 0)

    def test_validate_short_content(self):
        """Test de validación de contenido corto."""
        content = "Short"
        result = self.validator.validate(content)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.issues), 0)

    def test_validate_with_reserved_chars(self):
        """Test de validación con caracteres reservados."""
        content = "Hello \"world\" and *test*"
        result = self.validator.validate(content)
        self.assertIsNotNone(result)
        self.assertGreater(len(result.issues), 0)

    def test_prepare_for_fts5(self):
        """Test de preparación para FTS5."""
        content = "Hello \"world\" *test*"
        prepared = self.validator.prepare_for_fts5(content)
        self.assertNotIn('"', prepared)
        self.assertNotIn('*', prepared)

    def test_split_for_indexing(self):
        """Test de división para indexación."""
        content = "Paragraph 1\n\n" * 100
        chunks = self.validator.split_for_indexing(content, max_length=500)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)


class TestManifestGenerator(unittest.TestCase):
    """Tests para Módulo 19: ManifestGenerator"""

    def setUp(self):
        from app.modules.cc_schema.manifest_generator import ManifestGenerator
        self.test_dir = tempfile.mkdtemp()
        self.generator = ManifestGenerator(output_dir=self.test_dir)

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_generator_creation(self):
        """Test de creación del generador."""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.output_dir, self.test_dir)

    def test_generate_metadata(self):
        """Test de generación de metadatos."""
        metadata = self.generator.generate(
            source_url="https://youtube.com/watch?v=test",
            video_id="test123",
            title="Test Video",
            content="Sample transcription content here",
            language="en",
            format="vtt"
        )

        self.assertEqual(metadata.video_id, "test123")
        self.assertEqual(metadata.language, "en")
        self.assertGreater(len(metadata.content_hash), 0)

    def test_to_dict(self):
        """Test de conversión a diccionario."""
        metadata = self.generator.generate(
            source_url="https://youtube.com/watch?v=test",
            video_id="test123",
            title="Test Video",
            content="Sample content"
        )

        data = self.generator.to_dict(metadata)
        self.assertIn('version', data)
        self.assertIn('metadata', data)
        self.assertIn('checksum', data)

    def test_save_manifest(self):
        """Test de guardado de manifest."""
        metadata = self.generator.generate(
            source_url="https://youtube.com/watch?v=test",
            video_id="test123",
            title="Test Video",
            content="Sample content"
        )

        path = self.generator.save(metadata)
        self.assertTrue(os.path.exists(path))

    def test_load_manifest(self):
        """Test de carga de manifest."""
        metadata = self.generator.generate(
            source_url="https://youtube.com/watch?v=test",
            video_id="test456",
            title="Test Video",
            content="Sample content for loading"
        )

        path = self.generator.save(metadata)
        loaded = self.generator.load(path)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.video_id, "test456")


class TestAtomicPersistenceManager(unittest.TestCase):
    """Tests para Módulo 20: AtomicPersistenceManager"""

    def setUp(self):
        from app.modules.cc_schema.atomic_persistence import AtomicPersistenceManager
        self.test_db = tempfile.mktemp(suffix='.db')
        self.manager = AtomicPersistenceManager(db_path=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_manager_creation(self):
        """Test de creación del manager."""
        self.assertIsNotNone(self.manager)
        self.assertTrue(os.path.exists(self.test_db))

    def test_save_transcription(self):
        """Test de guardado de transcripción."""
        success, msg = self.manager.save(
            content="Sample transcription content",
            video_id="test123",
            source_url="https://youtube.com/watch?v=test123"
        )
        self.assertTrue(success)
        self.assertIn("Saved", msg or "already exists" in msg)

    def test_get_transcription(self):
        """Test de obtención de transcripción."""
        self.manager.save(
            content="Sample content for get test",
            video_id="test_get",
            source_url="https://youtube.com/watch?v=get"
        )

        result = self.manager.get("test_get")
        self.assertIsNotNone(result)
        self.assertEqual(result.video_id, "test_get")

    def test_save_batch(self):
        """Test de guardado en lote."""
        transcriptions = [
            {
                'content': f'Content {i}',
                'video_id': f'batch_{i}',
                'source_url': f'https://youtube.com/watch?v=batch{i}'
            }
            for i in range(3)
        ]

        stats = self.manager.save_batch(transcriptions)
        self.assertIn('total', stats)
        self.assertIn('saved', stats)

    def test_statistics(self):
        """Test de estadísticas."""
        self.manager.save(
            content="Test content for stats",
            video_id="stats_test",
            source_url="https://youtube.com/watch?v=stats"
        )

        stats = self.manager.get_statistics()
        self.assertIn('total_transcriptions', stats)
        self.assertGreater(stats['total_transcriptions'], 0)

    def test_transaction_context(self):
        """Test de context manager de transacción."""
        with self.manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transcriptions")
            count = cursor.fetchone()[0]
            self.assertIsInstance(count, int)


class TestIntegrationPhase4(unittest.TestCase):
    """Tests de integración FASE 4."""

    def test_all_modules_import(self):
        """Test de importación de todos los módulos."""
        try:
            from app.modules.cc_schema import (
                NoiseCleaner,
                RetryHandler,
                FTS5Validator,
                ManifestGenerator,
                AtomicPersistenceManager
            )
            all_ok = True
        except ImportError as e:
            all_ok = False
            self.fail(f"Module import failed: {e}")

        self.assertTrue(all_ok)

    def test_full_pipeline_simulation(self):
        """Test de simulación de pipeline completo."""
        from app.modules.cc_schema.noise_cleaner import NoiseCleaner
        from app.modules.cc_schema.retry_handler import RetryHandler, RetryConfig
        from app.modules.cc_schema.fts5_validator import FTS5Validator
        from app.modules.cc_schema.manifest_generator import ManifestGenerator

        raw_content = "00:00:00 --> 00:00:05\nHello [Speaker] World\nSubscribe to my channel!"
        raw_content += "\n" * 50 + "This is a longer content with more text to ensure validation passes."

        cleaner = NoiseCleaner()
        cleaned = cleaner.clean(raw_content)
        self.assertNotIn('00:00:00', cleaned)

        validator = FTS5Validator()
        result = validator.validate(cleaned)
        self.assertIsNotNone(result)

        generator = ManifestGenerator()
        metadata = generator.generate(
            source_url="https://youtube.com/watch?v=pipeline_test",
            video_id="pipeline_test",
            title="Pipeline Test",
            content=cleaned,
            language="en"
        )
        self.assertEqual(metadata.video_id, "pipeline_test")


if __name__ == '__main__':
    unittest.main(verbosity=2)