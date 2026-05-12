"""
Test Suite para Backup System - FASE B2 (Execution Modules)
============================================================
Tests para validar:
- Módulo 11: AtomicCloner
- Módulo 12: TransactionManager
- Módulo 13: QueueSnapshotManager
- Módulo 14: ConfigBackupManager
- Módulo 15: FileSizeValidator
- Módulo 16: SHA256Hasher
- Módulo 17: ZSTDCompressor
- Módulo 18: ArchiveSegmenter
- Módulo 19: DirectoryStructureValidator
- Módulo 20: HiddenFileCollector

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import sys
import unittest
import tempfile
import shutil
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAtomicCloner(unittest.TestCase):
    """Tests para Módulo 11: AtomicCloner"""

    def setUp(self):
        from app.modules.backup_system.deterministic.execution import atomic_cloner
        self.cloner = atomic_cloner.AtomicCloner()

    def test_cloner_creation(self):
        """Test de creación del cloner."""
        self.assertIsNotNone(self.cloner)

    def test_clone_single_file(self):
        """Test de clonación de archivo único."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        dest_path = tmp_path + ".copy"
        try:
            success, msg = self.cloner.clone_file(tmp_path, dest_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(dest_path))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(dest_path):
                os.unlink(dest_path)

    def test_clone_directory(self):
        """Test de clonación de directorio."""
        test_dir = tempfile.mkdtemp()
        dest_dir = tempfile.mkdtemp()

        try:
            for i in range(3):
                with open(os.path.join(test_dir, f"file{i}.txt"), 'w') as f:
                    f.write(f"content {i}")

            success, results = self.cloner.clone_directory(test_dir, dest_dir)
            self.assertTrue(success)
            self.assertEqual(len(results["success"]), 3)
        finally:
            shutil.rmtree(test_dir)
            shutil.rmtree(dest_dir)


class TestTransactionManager(unittest.TestCase):
    """Tests para Módulo 12: TransactionManager"""

    def test_manager_creation(self):
        """Test de creación del manager."""
        from app.modules.backup_system.deterministic.execution import transaction_manager
        tm = transaction_manager.TransactionManager()
        self.assertIsNotNone(tm)

    def test_begin_commit_transaction(self):
        """Test de transacción básica."""
        from app.modules.backup_system.deterministic.execution import transaction_manager
        tm = transaction_manager.TransactionManager()
        tid = tm.begin_transaction("test_tx")
        self.assertIsNotNone(tid)

        tm.stage_file(__file__, "/tmp/test_backup_file.txt")
        success, msg, files = tm.commit()
        self.assertTrue(success)


class TestQueueSnapshotManager(unittest.TestCase):
    """Tests para Módulo 13: QueueSnapshotManager"""

    def test_manager_creation(self):
        """Test de creación del manager."""
        from app.modules.backup_system.deterministic.execution import queue_snapshot_manager
        manager = queue_snapshot_manager.QueueSnapshotManager()
        self.assertIsNotNone(manager)

    def test_capture_snapshot(self):
        """Test de captura de instantánea."""
        from app.modules.backup_system.deterministic.execution import queue_snapshot_manager
        manager = queue_snapshot_manager.QueueSnapshotManager()
        success, msg = manager.capture_queue_state({"test": "data"})
        self.assertTrue(success)

    def test_load_snapshot(self):
        """Test de carga de instantánea."""
        from app.modules.backup_system.deterministic.execution import queue_snapshot_manager
        manager = queue_snapshot_manager.QueueSnapshotManager()
        manager.capture_queue_state({"test": "data"})
        snapshot = manager.load_queue_snapshot()
        self.assertIsNotNone(snapshot)


class TestConfigBackupManager(unittest.TestCase):
    """Tests para Módulo 14: ConfigBackupManager"""

    def test_manager_creation(self):
        """Test de creación del manager."""
        from app.modules.backup_system.deterministic.execution import config_backup_manager
        manager = config_backup_manager.ConfigBackupManager()
        self.assertIsNotNone(manager)

    def test_find_configs(self):
        """Test de búsqueda de configs."""
        from app.modules.backup_system.deterministic.execution import config_backup_manager
        manager = config_backup_manager.ConfigBackupManager()
        configs = manager.find_config_files(os.getcwd())
        self.assertIsInstance(configs, list)


class TestFileSizeValidator(unittest.TestCase):
    """Tests para Módulo 15: FileSizeValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.backup_system.deterministic.execution import file_size_validator
        validator = file_size_validator.FileSizeValidator()
        self.assertIsNotNone(validator)

    def test_validate_same_file(self):
        """Test de validación de archivo idéntico."""
        from app.modules.backup_system.deterministic.execution import file_size_validator
        validator = file_size_validator.FileSizeValidator()
        success, msg = validator.validate_file(__file__, __file__)
        self.assertTrue(success)

    def test_validation_summary(self):
        """Test de resumen de validación."""
        from app.modules.backup_system.deterministic.execution import file_size_validator
        validator = file_size_validator.FileSizeValidator()
        validator.validate_file(__file__, __file__)
        summary = validator.get_validation_summary()
        self.assertIn("total", summary)


class TestSHA256Hasher(unittest.TestCase):
    """Tests para Módulo 16: SHA256Hasher"""

    def test_hasher_creation(self):
        """Test de creación del hasher."""
        from app.modules.backup_system.deterministic.execution import sha256_hasher
        hasher = sha256_hasher.SHA256Hasher()
        self.assertIsNotNone(hasher)

    def test_compute_hash(self):
        """Test de cálculo de hash."""
        from app.modules.backup_system.deterministic.execution import sha256_hasher
        hasher = sha256_hasher.SHA256Hasher()
        success, hash_value, _ = hasher.compute_file_hash(__file__)
        self.assertTrue(success)
        self.assertIsNotNone(hash_value)
        self.assertEqual(len(hash_value), 64)

    def test_verify_hash(self):
        """Test de verificación de hash."""
        from app.modules.backup_system.deterministic.execution import sha256_hasher
        hasher = sha256_hasher.SHA256Hasher()
        success, hash_value, _ = hasher.compute_file_hash(__file__)
        is_valid, msg = hasher.verify_file_hash(__file__, hash_value)
        self.assertTrue(is_valid)


class TestZSTDCompressor(unittest.TestCase):
    """Tests para Módulo 17: ZSTDCompressor"""

    def test_compressor_creation(self):
        """Test de creación del compresor."""
        from app.modules.backup_system.deterministic.execution import zstd_compressor
        comp = zstd_compressor.ZSTDCompressor()
        self.assertIsNotNone(comp)

    def test_compression_stats(self):
        """Test de estadísticas de compresión."""
        from app.modules.backup_system.deterministic.execution import zstd_compressor
        comp = zstd_compressor.ZSTDCompressor()
        stats = comp.get_compression_stats()
        self.assertIn("total", stats)


class TestArchiveSegmenter(unittest.TestCase):
    """Tests para Módulo 18: ArchiveSegmenter"""

    def test_segmenter_creation(self):
        """Test de creación del segmentador."""
        from app.modules.backup_system.deterministic.execution import archive_segmenter
        seg = archive_segmenter.ArchiveSegmenter()
        self.assertIsNotNone(seg)

    def test_create_single_archive(self):
        """Test de creación de archivo único."""
        from app.modules.backup_system.deterministic.execution import archive_segmenter
        seg = archive_segmenter.ArchiveSegmenter()
        success, segments, msg = seg.create_segmented_archive([__file__], "/tmp/test_archive")
        self.assertTrue(success)

    def test_get_segment_info(self):
        """Test de información de segmentos."""
        from app.modules.backup_system.deterministic.execution import archive_segmenter
        seg = archive_segmenter.ArchiveSegmenter()
        info = seg.get_segment_info(["test.part001.zip"])
        self.assertIn("segment_count", info)


class TestDirectoryStructureValidator(unittest.TestCase):
    """Tests para Módulo 19: DirectoryStructureValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.backup_system.deterministic.execution import directory_structure_validator
        validator = directory_structure_validator.DirectoryStructureValidator()
        self.assertIsNotNone(validator)

    def test_map_directory(self):
        """Test de mapeo de directorio."""
        from app.modules.backup_system.deterministic.execution import directory_structure_validator
        validator = directory_structure_validator.DirectoryStructureValidator()
        structure = validator.map_directory_structure(os.getcwd())
        self.assertIn("root", structure)

    def test_flatten_files(self):
        """Test de aplanado de archivos."""
        from app.modules.backup_system.deterministic.execution import directory_structure_validator
        validator = directory_structure_validator.DirectoryStructureValidator()
        structure = {"type": "file", "name": "test.txt"}
        files = validator._flatten_files(structure)
        self.assertIn("test.txt", files)


class TestHiddenFileCollector(unittest.TestCase):
    """Tests para Módulo 20: HiddenFileCollector"""

    def test_collector_creation(self):
        """Test de creación del colector."""
        from app.modules.backup_system.deterministic.execution import hidden_file_collector
        collector = hidden_file_collector.HiddenFileCollector()
        self.assertIsNotNone(collector)

    def test_find_hidden_files(self):
        """Test de búsqueda de archivos ocultos."""
        from app.modules.backup_system.deterministic.execution import hidden_file_collector
        collector = hidden_file_collector.HiddenFileCollector()
        hidden = collector.find_hidden_files(os.getcwd())
        self.assertIsInstance(hidden, list)

    def test_collect_system_files(self):
        """Test de recolección de archivos de sistema."""
        from app.modules.backup_system.deterministic.execution import hidden_file_collector
        collector = hidden_file_collector.HiddenFileCollector()
        system = collector.collect_system_files(os.getcwd())
        self.assertIsInstance(system, list)


class TestExecutionIntegration(unittest.TestCase):
    """Tests de integración para FASE B2"""

    def test_all_modules_importable(self):
        """Test de importación de todos los módulos."""
        from app.modules.backup_system.deterministic import execution
        self.assertIn("atomic_cloner", execution.__all__)
        self.assertIn("transaction_manager", execution.__all__)
        self.assertIn("queue_snapshot_manager", execution.__all__)
        self.assertIn("config_backup_manager", execution.__all__)
        self.assertIn("file_size_validator", execution.__all__)
        self.assertIn("sha256_hasher", execution.__all__)
        self.assertIn("zstd_compressor", execution.__all__)
        self.assertIn("archive_segmenter", execution.__all__)
        self.assertIn("directory_structure_validator", execution.__all__)
        self.assertIn("hidden_file_collector", execution.__all__)


if __name__ == "__main__":
    unittest.main()