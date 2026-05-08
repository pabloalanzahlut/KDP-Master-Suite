import ssl
import socket
from typing import Tuple

class SSLValidator:
    """Módulo 50: Validación de SSL del Canal."""
    
    @staticmethod
    def check_ssl_certificate(hostname: str, port: int = 443) -> Tuple[bool, str]:
        """
        Verifica el certificado SSL de un host.
        
        Returns:
            (is_valid, message) tuple
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    subject = dict(x[0] for x in cert.get('subject', [{}])[0])
                    return True, f"Certificado válido: {subject.get('commonName', 'N/A')}"
        except ssl.SSLError as e:
            return False, f"Error SSL: {e}"
        except Exception as e:
            return False, f"Error de conexión: {e}"
    
    @staticmethod
    def validate_channel_ssl(channel_url: str) -> Tuple[bool, str]:
        """Valida el SSL de una URL de canal."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(channel_url)
            hostname = parsed.hostname
            if not hostname:
                return False, "URL inválida"
            return SSLValidator.check_ssl_certificate(hostname)
        except Exception as e:
            return False, f"Error: {e}"
