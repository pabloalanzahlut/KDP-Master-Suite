import os
import logging
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger("KDP_MASTER")

class SecurityManager:
    """Módulo de seguridad Enterprise para encriptación AES-256 GCM."""
    
    def __init__(self, key_file=None):
        if key_file is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            key_file = str(base_dir / ".master.key")
        self.key_file = os.path.abspath(key_file)
        self.master_key = self._load_or_create_key()

    def _load_or_create_key(self):
        """Carga la llave maestra o crea una nueva si no existe."""
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "rb") as f:
                    key = f.read()
                if len(key) == 32:
                    return key
                logger.warning("Key file corrupt (tamaño inválido), generando nueva")
            except Exception as e:
                logger.warning(f"No se pudo leer key file, generando nueva: {e}")
        
        new_key = os.urandom(32)
        try:
            key_dir = os.path.dirname(self.key_file)
            os.makedirs(key_dir, exist_ok=True)
            with open(self.key_file, "wb") as f:
                f.write(new_key)
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(self.key_file, 0x02)
            logger.info(f"Master key creada en {self.key_file}")
        except Exception as e:
            logger.error(f"No se pudo crear key file: {e}")
        return new_key

    def encrypt(self, plaintext):
        """Encripta un texto usando AES-256 GCM."""
        if not plaintext:
            return ""
        
        try:
            iv = os.urandom(12)
            encryptor = Cipher(
                algorithms.AES(self.master_key),
                modes.GCM(iv),
                backend=default_backend()
            ).encryptor()
            
            ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
            encrypted_data = iv + encryptor.tag + ciphertext
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encriptando: {e}")
            raise

    def decrypt(self, encrypted_base64):
        """Desencripta un texto encriptado en base64."""
        if not encrypted_base64:
            return ""
            
        try:
            data = base64.b64decode(encrypted_base64)
            if len(data) < 28:
                raise ValueError("Datos encriptados demasiado cortos o corruptos")
                
            iv = data[:12]
            tag = data[12:28]
            ciphertext = data[28:]
            
            decryptor = Cipher(
                algorithms.AES(self.master_key),
                modes.GCM(iv, tag),
                backend=default_backend()
            ).decryptor()
            
            decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
            return decrypted_data.decode()
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error desencriptando: {e}")
            raise
