"""
Test Suite para Backup System - FASE B3 (Encryption Modules)
============================================================
Tests para validar:
- Módulo 21: AESEncryptor
- Módulo 22: KeyDerivation
- Módulo 23: SecureKeyring
- Módulo 24: LogMasker
- Módulo 25: EncryptionValidator
- Módulo 26: SecureWiper
- Módulo 27: DigitalSigner
- Módulo 28: SignatureValidator
- Módulo 29: RansomwareDetector
- Módulo 30: SandboxIsolator

Autor: KDP_MASTER AI Team
Fecha: 2026-05-13
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAESEncryptor(unittest.TestCase):
    """Tests para Módulo 21: AESEncryptor"""

    def test_encryptor_creation(self):
        from app.modules.backup_system.deterministic.encryption import aes_encryptor
        enc = aes_encryptor.AESEncryptor()
        self.assertIsNotNone(enc)

    def test_encrypt_decrypt_file(self):
        from app.modules.backup_system.deterministic.encryption import aes_encryptor
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            enc = aes_encryptor.AESEncryptor()
            success, msg = enc.encrypt_file(tmp_path)
            self.assertTrue(success)

            enc2 = aes_encryptor.AESEncryptor(enc.get_key())
            success2, msg2 = enc2.decrypt_file(tmp_path + ".enc", tmp_path + ".dec")
            self.assertTrue(success2)

            with open(tmp_path + ".dec", 'rb') as f:
                self.assertEqual(f.read(), b"test content")

            if os.path.exists(tmp_path + ".enc"):
                os.unlink(tmp_path + ".enc")
            if os.path.exists(tmp_path + ".dec"):
                os.unlink(tmp_path + ".dec")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_derive_key_from_password(self):
        from app.modules.backup_system.deterministic.encryption import aes_encryptor
        salt = os.urandom(16)
        key = aes_encryptor.AESEncryptor.derive_key_from_password("test123", salt)
        self.assertEqual(len(key), 32)


class TestKeyDerivation(unittest.TestCase):
    """Tests para Módulo 22: KeyDerivation"""

    def test_manager_creation(self):
        from app.modules.backup_system.deterministic.encryption import key_derivation
        kd = key_derivation.KeyDerivation()
        self.assertIsNotNone(kd)

    def test_generate_salt(self):
        from app.modules.backup_system.deterministic.encryption import key_derivation
        kd = key_derivation.KeyDerivation()
        salt = kd.generate_salt()
        self.assertEqual(len(salt), 32)

    def test_derive_key(self):
        from app.modules.backup_system.deterministic.encryption import key_derivation
        kd = key_derivation.KeyDerivation()
        salt = kd.generate_salt()
        key = kd.derive_key("password", salt)
        self.assertEqual(len(key), 32)


class TestSecureKeyring(unittest.TestCase):
    """Tests para Módulo 23: SecureKeyring"""

    def test_keyring_creation(self):
        from app.modules.backup_system.deterministic.encryption import secure_keyring
        kr = secure_keyring.SecureKeyring()
        self.assertIsNotNone(kr)

    def test_store_retrieve_key(self):
        from app.modules.backup_system.deterministic.encryption import secure_keyring
        kr = secure_keyring.SecureKeyring()
        kr.store_key("test_service", "test_key_123")
        retrieved = kr.retrieve_key("test_service")
        self.assertEqual(retrieved, "test_key_123")
        kr.delete_key("test_service")


class TestLogMasker(unittest.TestCase):
    """Tests para Módulo 24: LogMasker"""

    def test_masker_creation(self):
        from app.modules.backup_system.deterministic.encryption import log_masker
        masker = log_masker.LogMasker()
        self.assertIsNotNone(masker)

    def test_mask_sensitive_data(self):
        from app.modules.backup_system.deterministic.encryption import log_masker
        masker = log_masker.LogMasker()
        text = 'api_key = "sk_live_abc123def456ghi789"'
        masked = masker.mask_sensitive_data(text)
        self.assertNotIn("sk_live", masked)

    def test_scan_for_sensitive(self):
        from app.modules.backup_system.deterministic.encryption import log_masker
        masker = log_masker.LogMasker()
        findings = masker.scan_for_sensitive('password = "secretpass123"')
        self.assertGreater(len(findings), 0)


class TestEncryptionValidator(unittest.TestCase):
    """Tests para Módulo 25: EncryptionValidator"""

    def test_validator_creation(self):
        from app.modules.backup_system.deterministic.encryption import encryption_validator
        val = encryption_validator.EncryptionValidator()
        self.assertIsNotNone(val)


class TestSecureWiper(unittest.TestCase):
    """Tests para Módulo 26: SecureWiper"""

    def test_wiper_creation(self):
        from app.modules.backup_system.deterministic.encryption import secure_wiper
        wip = secure_wiper.SecureWiper()
        self.assertIsNotNone(wip)

    def test_secure_delete(self):
        from app.modules.backup_system.deterministic.encryption import secure_wiper
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        wip = secure_wiper.SecureWiper()
        success, msg = wip.secure_delete(tmp_path)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(tmp_path))


class TestDigitalSigner(unittest.TestCase):
    """Tests para Módulo 27: DigitalSigner"""

    def test_signer_creation(self):
        from app.modules.backup_system.deterministic.encryption import digital_signer
        signer = digital_signer.DigitalSigner()
        self.assertIsNotNone(signer)

    def test_sign_manifest(self):
        from app.modules.backup_system.deterministic.encryption import digital_signer
        signer = digital_signer.DigitalSigner()
        manifest = {"files": ["a.txt", "b.txt"]}
        signed = signer.sign_manifest(manifest)
        self.assertIn("signature", signed)


class TestSignatureValidator(unittest.TestCase):
    """Tests para Módulo 28: SignatureValidator"""

    def test_validator_creation(self):
        from app.modules.backup_system.deterministic.encryption import signature_validator
        val = signature_validator.SignatureValidator()
        self.assertIsNotNone(val)


class TestRansomwareDetector(unittest.TestCase):
    """Tests para Módulo 29: RansomwareDetector"""

    def test_detector_creation(self):
        from app.modules.backup_system.deterministic.encryption import ransomware_detector
        det = ransomware_detector.RansomwareDetector()
        self.assertIsNotNone(det)

    def test_is_safe_for_backup(self):
        from app.modules.backup_system.deterministic.encryption import ransomware_detector
        det = ransomware_detector.RansomwareDetector()
        is_safe = det.is_safe_for_backup(os.getcwd())
        self.assertTrue(is_safe)


class TestSandboxIsolator(unittest.TestCase):
    """Tests para Módulo 30: SandboxIsolator"""

    def test_isolator_creation(self):
        from app.modules.backup_system.deterministic.encryption import sandbox_isolator
        iso = sandbox_isolator.SandboxIsolator()
        self.assertIsNotNone(iso)

    def test_create_sandbox(self):
        from app.modules.backup_system.deterministic.encryption import sandbox_isolator
        iso = sandbox_isolator.SandboxIsolator()
        success, path = iso.create_sandbox()
        self.assertTrue(success)
        iso.cleanup_sandbox()


class TestEncryptionIntegration(unittest.TestCase):
    """Tests de integración para FASE B3"""

    def test_all_modules_importable(self):
        from app.modules.backup_system.deterministic import encryption
        self.assertIn("aes_encryptor", encryption.__all__)
        self.assertIn("key_derivation", encryption.__all__)
        self.assertIn("secure_keyring", encryption.__all__)
        self.assertIn("log_masker", encryption.__all__)
        self.assertIn("encryption_validator", encryption.__all__)
        self.assertIn("secure_wiper", encryption.__all__)
        self.assertIn("digital_signer", encryption.__all__)
        self.assertIn("signature_validator", encryption.__all__)
        self.assertIn("ransomware_detector", encryption.__all__)
        self.assertIn("sandbox_isolator", encryption.__all__)


if __name__ == "__main__":
    unittest.main()