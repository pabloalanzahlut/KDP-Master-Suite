"""
Test Suite para Backup System - UI Feedback y Scalability
===========================================================
Tests para validar módulos de UI Feedback (41-50) y Scalability (51-60).
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestToastNotifier(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.ui_feedback import toast_notifier
        self.notifier = toast_notifier.ToastNotifier()

    def test_notifier_creation(self):
        self.assertIsNotNone(self.notifier)

    def test_notify_success(self):
        toast = self.notifier.success("Test", "Mensaje de prueba")
        self.assertEqual(toast.level, "success")

    def test_notify_error(self):
        toast = self.notifier.error("Error", "Algo salió mal")
        self.assertEqual(toast.level, "error")

    def test_get_history(self):
        self.notifier.info("Test", "Mensaje")
        history = self.notifier.get_history(limit=5)
        self.assertGreater(len(history), 0)


class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from app.modules.backup_system.deterministic.ui_feedback import audit_logger
        self.logger = audit_logger.AuditLogger(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_creation(self):
        self.assertIsNotNone(self.logger)

    def test_log_backup_start(self):
        entry = self.logger.log_backup_start("test_backup.zip", 1024)
        self.assertEqual(entry["action"], "backup_start")

    def test_log_backup_complete(self):
        entry = self.logger.log_backup_complete("test_backup.zip", 10.5)
        self.assertEqual(entry["action"], "backup_complete")


class TestLastBackupTimestamp(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from app.modules.backup_system.deterministic.ui_feedback import last_backup_timestamp
        self.ts = last_backup_timestamp.LastBackupTimestamp(
            os.path.join(self.temp_dir, "state.json")
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_timestamp_creation(self):
        self.assertIsNotNone(self.ts)

    def test_update_backup(self):
        result = self.ts.update_backup("/path/backup.zip", 2048)
        self.assertIsNotNone(result)
        self.assertEqual(self.ts.get_backup_count(), 1)


class TestServiceReactivator(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.ui_feedback import service_reactivator
        self.reactivator = service_reactivator.ServiceReactivator()

    def test_reactivator_creation(self):
        self.assertIsNotNone(self.reactivator)

    def test_register_service(self):
        self.reactivator.register_service("test_service")
        status = self.reactivator.get_service_status("test_service")
        self.assertIsNotNone(status)


class TestPostBackupSpaceValidator(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.ui_feedback import post_backup_space_validator
        self.validator = post_backup_space_validator.PostBackupSpaceValidator()

    def test_validator_creation(self):
        self.assertIsNotNone(self.validator)

    def test_validate(self):
        result = self.validator.validate()
        self.assertIn("status", result)


class TestAutoFolderOpener(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.ui_feedback import auto_folder_opener
        self.opener = auto_folder_opener.AutoFolderOpener(enabled=False)

    def test_opener_creation(self):
        self.assertIsNotNone(self.opener)

    def test_set_enabled(self):
        self.opener.set_enabled(True)
        self.assertTrue(self.opener.is_enabled())


class TestFilePermissionValidator(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.ui_feedback import file_permission_validator
        self.validator = file_permission_validator.FilePermissionValidator()

    def test_validator_creation(self):
        self.assertIsNotNone(self.validator)

    def test_validate_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name
        try:
            result = self.validator.validate_file(tmp_path)
            self.assertEqual(result["status"], "ok")
        finally:
            os.unlink(tmp_path)


class TestGlobalHashGenerator(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.ui_feedback import global_hash_generator
        self.generator = global_hash_generator.GlobalHashGenerator()

    def test_generator_creation(self):
        self.assertIsNotNone(self.generator)

    def test_hash_string(self):
        hash_val = self.generator.hash_string("test data")
        self.assertGreater(len(hash_val), 0)


class TestMultiThreadCoordinator(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import multi_thread_coordinator
        self.coordinator = multi_thread_coordinator.MultiThreadCoordinator(max_workers=2)

    def test_coordinator_creation(self):
        self.assertIsNotNone(self.coordinator)

    def test_submit_task(self):
        def dummy_task():
            return 42
        future = self.coordinator.submit("task1", dummy_task)
        self.assertIsNotNone(future)

    def tearDown(self):
        self.coordinator.shutdown()


class TestBufferManager(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import buffer_manager
        self.manager = buffer_manager.BufferManager(max_size=10, max_memory_mb=1)

    def test_manager_creation(self):
        self.assertIsNotNone(self.manager)

    def test_put_get(self):
        self.manager.put(b"test data", 9)
        data = self.manager.get()
        self.assertEqual(data, b"test data")


class TestStreamProcessor(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import stream_processor
        self.processor = stream_processor.StreamProcessor()

    def test_processor_creation(self):
        self.assertIsNotNone(self.processor)

    def test_process_file(self):
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        results = []
        self.processor.process_file(tmp_path, lambda chunk: results.append(chunk))
        os.unlink(tmp_path)
        self.assertGreater(len(results), 0)


class TestAsyncIOHandler(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import async_io_handler
        self.handler = async_io_handler.AsyncIOHandler(max_concurrent=2)

    def test_handler_creation(self):
        self.assertIsNotNone(self.handler)

    def test_read_write(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        data = self.handler.read_file_async(tmp_path)
        self.assertEqual(data, b"test")
        os.unlink(tmp_path)

        result = self.handler.write_file_async(tmp_path + ".out", b"output")
        self.assertTrue(result)
        os.unlink(tmp_path + ".out")


class TestLoadBalancer(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import load_balancer
        self.balancer = load_balancer.LoadBalancer(["w1", "w2"])

    def test_balancer_creation(self):
        self.assertIsNotNone(self.balancer)

    def test_get_best_worker(self):
        worker = self.balancer.get_best_worker()
        self.assertIsNotNone(worker)


class TestBatchProcessor(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import batch_processor
        self.processor = batch_processor.BatchProcessor(batch_size=5)

    def test_processor_creation(self):
        self.assertIsNotNone(self.processor)

    def test_create_job(self):
        job_id = self.processor.create_job("job1", list(range(10)))
        self.assertEqual(job_id, "job1")


class TestCacheManager(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import cache_manager
        self.cache = cache_manager.CacheManager(max_entries=10)

    def test_cache_creation(self):
        self.assertIsNotNone(self.cache)

    def test_set_get(self):
        self.cache.set("key1", "value1")
        val = self.cache.get("key1")
        self.assertEqual(val, "value1")


class TestProgressAggregator(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import progress_aggregator
        self.aggregator = progress_aggregator.ProgressAggregator()

    def test_aggregator_creation(self):
        self.assertIsNotNone(self.aggregator)

    def test_register_thread(self):
        self.aggregator.register_thread("thread1", 100)
        progress = self.aggregator.get_global_progress()
        self.assertEqual(progress["total_items"], 100)


class TestResourceMonitor(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import resource_monitor
        self.monitor = resource_monitor.ResourceMonitor()

    def test_monitor_creation(self):
        self.assertIsNotNone(self.monitor)

    def test_get_current_stats(self):
        stats = self.monitor.get_current_stats()
        self.assertIn("cpu_percent", stats)


class TestHeadlessModeManager(unittest.TestCase):
    def setUp(self):
        from app.modules.backup_system.deterministic.scalability import headless_mode_manager
        self.manager = headless_mode_manager.HeadlessModeManager()

    def test_manager_creation(self):
        self.assertIsNotNone(self.manager)

    def test_set_headless(self):
        self.manager.set_headless(True)
        self.assertTrue(self.manager.is_headless())


class TestUIFeedbackIntegration(unittest.TestCase):
    def test_all_modules_importable(self):
        from app.modules.backup_system.deterministic import ui_feedback
        self.assertIsNotNone(ui_feedback)


class TestScalabilityIntegration(unittest.TestCase):
    def test_all_modules_importable(self):
        from app.modules.backup_system.deterministic import scalability
        self.assertIsNotNone(scalability)


if __name__ == "__main__":
    unittest.main()