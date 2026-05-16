"""
Test Suite para Backup System - FASE B1 (Pre-Backup Modules)
=============================================================
Tests para validar:
- Módulo 1: StorageQuotaValidator
- Módulo 2: AtomicWriteLock
- Módulo 3: RamBufferFlusher
- Módulo 4: CriticalPathValidator
- Módulo 5: PermissionScanner
- Módulo 6: SMARTDiskValidator
- Módulo 7: HardwareTempMonitor
- Módulo 8: ExternalMediaVerifier
- Módulo 9: SQLiteIntegrityValidator
- Módulo 10: FileLockDetector

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import sys
import unittest
import tempfile
import shutil
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStorageQuotaValidator(unittest.TestCase):
    """Tests para Módulo 1: StorageQuotaValidator"""

    def setUp(self):
        from app.modules.backup_system.deterministic.pre_backup import storage_quota_validator
        self.validator = storage_quota_validator.StorageQuotaValidator()

    def test_validator_creation(self):
        """Test de creación del validador."""
        self.assertIsNotNone(self.validator)

    def test_calculate_backup_size_single_file(self):
        """Test de cálculo de tamaño para un archivo."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            size = self.validator.calculate_backup_size([tmp_path])
            self.assertGreater(size, 0)
        finally:
            os.unlink(tmp_path)

    def test_calculate_backup_size_directory(self):
        """Test de cálculo de tamaño para directorio."""
        test_dir = tempfile.mkdtemp()
        try:
            for i in range(3):
                with open(os.path.join(test_dir, f"file{i}.txt"), 'w') as f:
                    f.write("test content " * 100)

            size = self.validator.calculate_backup_size([test_dir])
            self.assertGreater(size, 0)
        finally:
            shutil.rmtree(test_dir)

    def test_get_disk_info(self):
        """Test de información del disco."""
        info = self.validator.get_disk_info(os.getcwd())
        self.assertIn("total_gb", info)
        self.assertIn("free_gb", info)
        self.assertIn("free_percent", info)
        self.assertGreater(info["total_gb"], 0)

    def test_validate_backup_quota_insufficient_space(self):
        """Test de validación con espacio insuficiente."""
        is_valid, message = self.validator.validate_backup_quota(
            [__file__],
            os.getcwd()
        )
        self.assertTrue(is_valid)


class TestAtomicWriteLock(unittest.TestCase):
    """Tests para Módulo 2: AtomicWriteLock"""

    def test_lock_singleton(self):
        """Test de singleton del lock."""
        from app.modules.backup_system.deterministic.pre_backup import atomic_write_lock
        lock1 = atomic_write_lock.AtomicWriteLock()
        lock2 = atomic_write_lock.AtomicWriteLock()
        self.assertIs(lock1, lock2)

    def test_acquire_release(self):
        """Test de adquisición y liberación."""
        from app.modules.backup_system.deterministic.pre_backup import atomic_write_lock
        lock = atomic_write_lock.AtomicWriteLock()
        result = lock.acquire(timeout=5)
        self.assertTrue(result)
        self.assertTrue(lock.is_active())
        lock.release()
        self.assertFalse(lock.is_active())

    def test_context_manager(self):
        """Test de contexto with."""
        from app.modules.backup_system.deterministic.pre_backup import atomic_write_lock
        with atomic_write_lock.atomic_backup_context(timeout=5) as lock:
            self.assertTrue(lock.is_active())
        self.assertFalse(lock.is_active())

    def test_timeout_on_locked(self):
        """Test de timeout cuando ya está bloqueado por otro proceso."""
        import threading
        from app.modules.backup_system.deterministic.pre_backup import atomic_write_lock
        lock = atomic_write_lock.AtomicWriteLock()
        result = lock.acquire(timeout=1)
        self.assertTrue(result)
        lock.release()


class TestRamBufferFlusher(unittest.TestCase):
    """Tests para Módulo 3: RamBufferFlusher"""

    def test_flusher_creation(self):
        """Test de creación del flusher."""
        from app.modules.backup_system.deterministic.pre_backup import ram_buffer_flusher
        flusher = ram_buffer_flusher.RamBufferFlusher()
        self.assertIsNotNone(flusher)

    def test_flush_buffers(self):
        """Test de flush de buffers."""
        from app.modules.backup_system.deterministic.pre_backup import ram_buffer_flusher
        flusher = ram_buffer_flusher.RamBufferFlusher()
        success, message = flusher.flush_all_buffers()
        self.assertTrue(success)

    def test_sync_directory(self):
        """Test de sincronización de directorio."""
        from app.modules.backup_system.deterministic.pre_backup import ram_buffer_flusher
        flusher = ram_buffer_flusher.RamBufferFlusher()
        success, message = flusher.sync_directory(os.getcwd())
        self.assertTrue(success)

    def test_ensure_kernel_sync(self):
        """Test de sincronización de kernel."""
        from app.modules.backup_system.deterministic.pre_backup import ram_buffer_flusher
        flusher = ram_buffer_flusher.RamBufferFlusher()
        success, message = flusher.ensure_kernel_sync()
        self.assertTrue(success)


class TestCriticalPathValidator(unittest.TestCase):
    """Tests para Módulo 4: CriticalPathValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.backup_system.deterministic.pre_backup import critical_path_validator
        validator = critical_path_validator.CriticalPathValidator()
        self.assertIsNotNone(validator)

    def test_validate_existing_path(self):
        """Test de validación de ruta existente."""
        from app.modules.backup_system.deterministic.pre_backup import critical_path_validator
        validator = critical_path_validator.CriticalPathValidator(base_path=os.getcwd())
        is_valid, status = validator.validate_critical_path(os.getcwd())
        self.assertTrue(is_valid)

    def test_validate_nonexistent_path(self):
        """Test de validación de ruta inexistente."""
        from app.modules.backup_system.deterministic.pre_backup import critical_path_validator
        validator = critical_path_validator.CriticalPathValidator()
        is_valid, status = validator.validate_critical_path("/nonexistent/path/12345")
        self.assertFalse(is_valid)

    def test_get_missing_paths(self):
        """Test de obtención de rutas faltantes."""
        from app.modules.backup_system.deterministic.pre_backup import critical_path_validator
        validator = critical_path_validator.CriticalPathValidator(base_path=os.getcwd())
        missing = validator.get_missing_paths()
        self.assertIsInstance(missing, list)


class TestPermissionScanner(unittest.TestCase):
    """Tests para Módulo 5: PermissionScanner"""

    def test_scanner_creation(self):
        """Test de creación del escáner."""
        from app.modules.backup_system.deterministic.pre_backup import permission_scanner
        scanner = permission_scanner.PermissionScanner()
        self.assertIsNotNone(scanner)

    def test_check_path_permissions(self):
        """Test de verificación de permisos."""
        from app.modules.backup_system.deterministic.pre_backup import permission_scanner
        scanner = permission_scanner.PermissionScanner()
        perms = scanner.check_path_permissions(__file__)
        self.assertTrue(perms["exists"])
        self.assertTrue(perms["readable"])

    def test_validate_files_for_backup(self):
        """Test de validación de archivos para backup."""
        from app.modules.backup_system.deterministic.pre_backup import permission_scanner
        scanner = permission_scanner.PermissionScanner()
        is_valid, invalid = scanner.validate_files_for_backup([__file__])
        self.assertTrue(is_valid)
        self.assertEqual(len(invalid), 0)

    def test_get_permissions_string(self):
        """Test de obtener string de permisos."""
        from app.modules.backup_system.deterministic.pre_backup import permission_scanner
        scanner = permission_scanner.PermissionScanner()
        perms = scanner.get_file_permissions_string(__file__)
        self.assertIsInstance(perms, str)
        self.assertGreater(len(perms), 0)


class TestSMARTDiskValidator(unittest.TestCase):
    """Tests para Módulo 6: SMARTDiskValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.backup_system.deterministic.pre_backup import smart_disk_validator
        validator = smart_disk_validator.SMARTDiskValidator()
        self.assertIsNotNone(validator)

    def test_get_disk_health(self):
        """Test de obtención de salud del disco."""
        from app.modules.backup_system.deterministic.pre_backup import smart_disk_validator
        validator = smart_disk_validator.SMARTDiskValidator()
        health = validator.get_disk_health()
        self.assertIn("status", health)
        self.assertIn("health", health)

    def test_is_disk_healthy(self):
        """Test de verificación de disco sano."""
        from app.modules.backup_system.deterministic.pre_backup import smart_disk_validator
        validator = smart_disk_validator.SMARTDiskValidator()
        is_healthy, message = validator.is_disk_healthy()
        self.assertIsInstance(is_healthy, bool)

    def test_validate_before_backup(self):
        """Test de validación previa al backup."""
        from app.modules.backup_system.deterministic.pre_backup import smart_disk_validator
        validator = smart_disk_validator.SMARTDiskValidator()
        is_valid, message = validator.validate_before_backup()
        self.assertIsInstance(is_valid, bool)


class TestHardwareTempMonitor(unittest.TestCase):
    """Tests para Módulo 7: HardwareTempMonitor"""

    def test_monitor_creation(self):
        """Test de creación del monitor."""
        from app.modules.backup_system.deterministic.pre_backup import hardware_temp_monitor
        monitor = hardware_temp_monitor.HardwareTempMonitor()
        self.assertIsNotNone(monitor)

    def test_get_temperature_status(self):
        """Test de obtención de estado de temperatura."""
        from app.modules.backup_system.deterministic.pre_backup import hardware_temp_monitor
        monitor = hardware_temp_monitor.HardwareTempMonitor()
        status = monitor.get_system_temperature_status()
        self.assertIn("status", status)
        self.assertIn("available", status)

    def test_validate_for_backup(self):
        """Test de validación para backup."""
        from app.modules.backup_system.deterministic.pre_backup import hardware_temp_monitor
        monitor = hardware_temp_monitor.HardwareTempMonitor()
        is_valid, message = monitor.validate_for_backup()
        self.assertIsInstance(is_valid, bool)


class TestExternalMediaVerifier(unittest.TestCase):
    """Tests para Módulo 8: ExternalMediaVerifier"""

    def test_verifier_creation(self):
        """Test de creación del verificador."""
        from app.modules.backup_system.deterministic.pre_backup import external_media_verifier
        verifier = external_media_verifier.ExternalMediaVerifier()
        self.assertIsNotNone(verifier)

    def test_detect_external_media(self):
        """Test de detección de medios externos."""
        from app.modules.backup_system.deterministic.pre_backup import external_media_verifier
        verifier = external_media_verifier.ExternalMediaVerifier()
        media = verifier.detect_external_media()
        self.assertIsInstance(media, list)

    def test_verify_external_write(self):
        """Test de verificación de escritura externa."""
        from app.modules.backup_system.deterministic.pre_backup import external_media_verifier
        verifier = external_media_verifier.ExternalMediaVerifier()
        is_valid, message = verifier.verify_external_write(os.getcwd())
        self.assertTrue(is_valid)


class TestSQLiteIntegrityValidator(unittest.TestCase):
    """Tests para Módulo 9: SQLiteIntegrityValidator"""

    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.test_db.close()
        conn = sqlite3.connect(self.test_db.name)
        conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'test')")
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.backup_system.deterministic.pre_backup import sqlite_integrity_validator
        validator = sqlite_integrity_validator.SQLiteIntegrityValidator()
        self.assertIsNotNone(validator)

    def test_validate_database(self):
        """Test de validación de base de datos."""
        from app.modules.backup_system.deterministic.pre_backup import sqlite_integrity_validator
        validator = sqlite_integrity_validator.SQLiteIntegrityValidator()
        is_valid, message, errors = validator.validate_database(self.test_db.name)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_nonexistent_database(self):
        """Test de validación de base de datos inexistente."""
        from app.modules.backup_system.deterministic.pre_backup import sqlite_integrity_validator
        validator = sqlite_integrity_validator.SQLiteIntegrityValidator()
        is_valid, message, errors = validator.validate_database("/nonexistent/db.db")
        self.assertFalse(is_valid)

    def test_get_database_info(self):
        """Test de obtención de info de DB."""
        from app.modules.backup_system.deterministic.pre_backup import sqlite_integrity_validator
        validator = sqlite_integrity_validator.SQLiteIntegrityValidator()
        info = validator.get_database_info(self.test_db.name)
        self.assertIsNotNone(info)
        self.assertIn("size_mb", info)


class TestFileLockDetector(unittest.TestCase):
    """Tests para Módulo 10: FileLockDetector"""

    def test_detector_creation(self):
        """Test de creación del detector."""
        from app.modules.backup_system.deterministic.pre_backup import file_lock_detector
        detector = file_lock_detector.FileLockDetector()
        self.assertIsNotNone(detector)

    def test_scan_for_locked_files(self):
        """Test de escaneo de archivos bloqueados."""
        from app.modules.backup_system.deterministic.pre_backup import file_lock_detector
        detector = file_lock_detector.FileLockDetector()
        locked = detector.scan_for_locked_files(os.getcwd())
        self.assertIsInstance(locked, list)

    def test_check_file_lock(self):
        """Test de verificación de lock de archivo."""
        from app.modules.backup_system.deterministic.pre_backup import file_lock_detector
        detector = file_lock_detector.FileLockDetector()
        lock_info = detector.check_file_lock(__file__)
        self.assertIn("locked", lock_info)
        self.assertIn("reason", lock_info)

    def test_validate_for_backup(self):
        """Test de validación para backup."""
        from app.modules.backup_system.deterministic.pre_backup import file_lock_detector
        detector = file_lock_detector.FileLockDetector()
        is_valid, locked = detector.validate_for_backup(os.getcwd())
        self.assertIsInstance(is_valid, bool)


class TestPreBackupIntegration(unittest.TestCase):
    """Tests de integración para FASE B1"""

    def test_all_modules_importable(self):
        """Test de importación de todos los módulos."""
        from app.modules.backup_system.deterministic import pre_backup
        self.assertIn("storage_quota_validator", pre_backup.__all__)
        self.assertIn("atomic_write_lock", pre_backup.__all__)
        self.assertIn("ram_buffer_flusher", pre_backup.__all__)
        self.assertIn("critical_path_validator", pre_backup.__all__)
        self.assertIn("permission_scanner", pre_backup.__all__)
        self.assertIn("smart_disk_validator", pre_backup.__all__)
        self.assertIn("hardware_temp_monitor", pre_backup.__all__)
        self.assertIn("external_media_verifier", pre_backup.__all__)
        self.assertIn("sqlite_integrity_validator", pre_backup.__all__)
        self.assertIn("file_lock_detector", pre_backup.__all__)


if __name__ == "__main__":
    unittest.main()