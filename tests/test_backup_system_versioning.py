"""
Test Suite para Backup System - FASE B4 (Versioning Modules)
============================================================
Tests para validar:
- Módulo 31: VersionTagger
- Módulo 32: RetentionPolicy
- Módulo 33: DeltaDetector
- Módulo 34: LogCompressor
- Módulo 35: ArchiveArchiver
- Módulo 36: MaxAgeValidator
- Módulo 37: QuotaManager
- Módulo 38: CloudSyncer
- Módulo 39: IntegrityVerifier
- Módulo 40: StatusReporter

Autor: KDP_MASTER AI Team
Fecha: 2026-05-13
"""

import os
import sys
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVersionTagger(unittest.TestCase):
    def test_tagger_creation(self):
        from app.modules.backup_system.deterministic.versioning import version_tagger
        tagger = version_tagger.VersionTagger()
        self.assertIsNotNone(tagger)


class TestRetentionPolicy(unittest.TestCase):
    def test_policy_creation(self):
        from app.modules.backup_system.deterministic.versioning import retention_policy
        policy = retention_policy.RetentionPolicy()
        self.assertIsNotNone(policy)

    def test_analyze_backups(self):
        from app.modules.backup_system.deterministic.versioning import retention_policy
        policy = retention_policy.RetentionPolicy()
        result = policy.analyze_backups(os.getcwd())
        self.assertIn("daily", result)


class TestDeltaDetector(unittest.TestCase):
    def test_detector_creation(self):
        from app.modules.backup_system.deterministic.versioning import delta_detector
        det = delta_detector.DeltaDetector()
        self.assertIsNotNone(det)


class TestLogCompressor(unittest.TestCase):
    def test_compressor_creation(self):
        from app.modules.backup_system.deterministic.versioning import log_compressor
        comp = log_compressor.LogCompressor()
        self.assertIsNotNone(comp)


class TestArchiveArchiver(unittest.TestCase):
    def test_archiver_creation(self):
        from app.modules.backup_system.deterministic.versioning import archive_archiver
        arch = archive_archiver.ArchiveArchiver()
        self.assertIsNotNone(arch)


class TestMaxAgeValidator(unittest.TestCase):
    def test_validator_creation(self):
        from app.modules.backup_system.deterministic.versioning import max_age_validator
        val = max_age_validator.MaxAgeValidator()
        self.assertIsNotNone(val)

    def test_check_backup_age(self):
        from app.modules.backup_system.deterministic.versioning import max_age_validator
        val = max_age_validator.MaxAgeValidator()
        result = val.check_backup_age(__file__)
        self.assertIn("exists", result)


class TestQuotaManager(unittest.TestCase):
    def test_manager_creation(self):
        from app.modules.backup_system.deterministic.versioning import quota_manager
        mgr = quota_manager.QuotaManager()
        self.assertIsNotNone(mgr)

    def test_set_quota(self):
        from app.modules.backup_system.deterministic.versioning import quota_manager
        mgr = quota_manager.QuotaManager()
        mgr.set_quota("test", 1000)
        self.assertEqual(mgr.quotas.get("test"), 1000)


class TestCloudSyncer(unittest.TestCase):
    def test_syncer_creation(self):
        from app.modules.backup_system.deterministic.versioning import cloud_syncer
        syncer = cloud_syncer.CloudSyncer()
        self.assertIsNotNone(syncer)


class TestIntegrityVerifier(unittest.TestCase):
    def test_verifier_creation(self):
        from app.modules.backup_system.deterministic.versioning import integrity_verifier
        val = integrity_verifier.IntegrityVerifier()
        self.assertIsNotNone(val)

    def test_calculate_hash(self):
        from app.modules.backup_system.deterministic.versioning import integrity_verifier
        val = integrity_verifier.IntegrityVerifier()
        h = val.calculate_file_hash(__file__)
        self.assertEqual(len(h), 64)


class TestStatusReporter(unittest.TestCase):
    def test_reporter_creation(self):
        from app.modules.backup_system.deterministic.versioning import status_reporter
        rep = status_reporter.StatusReporter()
        self.assertIsNotNone(rep)

    def test_generate_status(self):
        from app.modules.backup_system.deterministic.versioning import status_reporter
        rep = status_reporter.StatusReporter()
        status = rep.generate_backup_status(os.getcwd())
        self.assertIn("backup_count", status)


class TestVersioningIntegration(unittest.TestCase):
    def test_all_modules_importable(self):
        from app.modules.backup_system.deterministic import versioning
        self.assertIn("version_tagger", versioning.__all__)
        self.assertIn("retention_policy", versioning.__all__)


if __name__ == "__main__":
    unittest.main()