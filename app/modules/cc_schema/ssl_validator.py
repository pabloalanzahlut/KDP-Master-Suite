"""
SSL Certificate Validator - Módulo 6 de URL Intelligence
=======================================================
Verifica que el certificado SSL sea válido y no esté expirado.
Previene ataques MITM en redes públicas.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import ssl
import socket
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class SSLStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class SSLValidationResult:
    status: SSLStatus
    domain: str
    issuer: Optional[str]
    subject: Optional[str]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    days_until_expiry: Optional[int]
    is_valid: bool
    error: Optional[str]
    verification_time_ms: float


class SSLValidator:
    """
    Validador de certificados SSL.
    Verifica validez, expiración y emite warnings para certificados próximos a expirar.
    """

    DEFAULT_TIMEOUT = 5.0
    WARNING_DAYS = 30

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        warning_days: int = WARNING_DAYS,
        verify_hostname: bool = True
    ):
        self.timeout = timeout
        self.warning_days = warning_days
        self.verify_hostname = verify_hostname

    def validate(self, url: str) -> SSLValidationResult:
        """
        Valida certificado SSL de URL.

        Args:
            url: URL a validar (debe ser https://)

        Returns:
            SSLValidationResult con estado del certificado
        """
        if not url:
            return SSLValidationResult(
                status=SSLStatus.INVALID,
                domain="",
                issuer=None,
                subject=None,
                valid_from=None,
                valid_until=None,
                days_until_expiry=None,
                is_valid=False,
                error="URL vacía",
                verification_time_ms=0
            )

        if url.startswith('http://'):
            return SSLValidationResult(
                status=SSLStatus.INVALID,
                domain=url,
                issuer=None,
                subject=None,
                valid_from=None,
                valid_until=None,
                days_until_expiry=None,
                is_valid=False,
                error="URL usa HTTP, no HTTPS",
                verification_time_ms=0
            )

        domain = self._extract_domain(url)

        if not domain:
            return SSLValidationResult(
                status=SSLStatus.INVALID,
                domain=domain or url,
                issuer=None,
                subject=None,
                valid_from=None,
                valid_until=None,
                days_until_expiry=None,
                is_valid=False,
                error="Dominio no extraído",
                verification_time_ms=0
            )

        start_time = __import__('time').time()

        try:
            context = ssl.create_default_context()
            if not self.verify_hostname:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

                    if not cert:
                        return SSLValidationResult(
                            status=SSLStatus.INVALID,
                            domain=domain,
                            issuer=None,
                            subject=None,
                            valid_from=None,
                            valid_until=None,
                            days_until_expiry=None,
                            is_valid=False,
                            error="No se pudo obtener certificado",
                            verification_time_ms=(__import__('time').time() - start_time) * 1000
                        )

                    issuer = self._get_issuer(cert)
                    subject = self._get_subject(cert)
                    valid_from = self._parse_datetime(cert.get('notBefore'))
                    valid_until = self._parse_datetime(cert.get('notAfter'))

                    days_until_expiry = None
                    if valid_until:
                        days_until_expiry = (valid_until - datetime.now()).days

                    verification_time = (__import__('time').time() - start_time) * 1000

                    if valid_until and valid_until < datetime.now():
                        return SSLValidationResult(
                            status=SSLStatus.EXPIRED,
                            domain=domain,
                            issuer=issuer,
                            subject=subject,
                            valid_from=valid_from,
                            valid_until=valid_until,
                            days_until_expiry=days_until_expiry,
                            is_valid=False,
                            error=f"Certificado expiró el {valid_until.strftime('%Y-%m-%d')}",
                            verification_time_ms=verification_time
                        )

                    if valid_until and days_until_expiry <= self.warning_days:
                        return SSLValidationResult(
                            status=SSLStatus.VALID,
                            domain=domain,
                            issuer=issuer,
                            subject=subject,
                            valid_from=valid_from,
                            valid_until=valid_until,
                            days_until_expiry=days_until_expiry,
                            is_valid=True,
                            error=f"Advertencia: certificado expira en {days_until_expiry} días",
                            verification_time_ms=verification_time
                        )

                    return SSLValidationResult(
                        status=SSLStatus.VALID,
                        domain=domain,
                        issuer=issuer,
                        subject=subject,
                        valid_from=valid_from,
                        valid_until=valid_until,
                        days_until_expiry=days_until_expiry,
                        is_valid=True,
                        error=None,
                        verification_time_ms=verification_time
                    )

        except ssl.SSLCertVerificationError as e:
            verification_time = (__import__('time').time() - start_time) * 1000
            return SSLValidationResult(
                status=SSLStatus.INVALID,
                domain=domain,
                issuer=None,
                subject=None,
                valid_from=None,
                valid_until=None,
                days_until_expiry=None,
                is_valid=False,
                error=f"Verificación SSL fallida: {str(e)}",
                verification_time_ms=verification_time
            )

        except socket.timeout:
            verification_time = (__import__('time').time() - start_time) * 1000
            return SSLValidationResult(
                status=SSLStatus.ERROR,
                domain=domain,
                issuer=None,
                subject=None,
                valid_from=None,
                valid_until=None,
                days_until_expiry=None,
                is_valid=False,
                error=f"Timeout después de {self.timeout}s",
                verification_time_ms=verification_time
            )

        except Exception as e:
            verification_time = (__import__('time').time() - start_time) * 1000
            logger.error(f"Error validando SSL de {domain}: {e}")
            return SSLValidationResult(
                status=SSLStatus.ERROR,
                domain=domain,
                issuer=None,
                subject=None,
                valid_from=None,
                valid_until=None,
                days_until_expiry=None,
                is_valid=False,
                error=str(e),
                verification_time_ms=verification_time
            )

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extrae dominio de URL."""
        if not url.startswith('https://'):
            url = url.replace('http://', 'https://', 1)

        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.split(':')[0] if parsed.netloc else None
        except Exception:
            return None

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parsea fecha de certificado."""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, '%b %d %H:%M:%S %Y %Z')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y%m%d%H%M%SZ')
            except ValueError:
                return None

    def _get_issuer(self, cert: dict) -> Optional[str]:
        """Extrae emisor del certificado."""
        issuer = cert.get('issuer', [])
        for item in issuer:
            if isinstance(item, tuple) and item[0] == 'organizationName':
                return item[1]
        return None

    def _get_subject(self, cert: dict) -> Optional[str]:
        """Extrae sujeto del certificado."""
        subject = cert.get('subject', [])
        for item in subject:
            if isinstance(item, tuple) and item[0] == 'commonName':
                return item[1]
        return None

    def is_valid(self, url: str) -> bool:
        """Verifica si SSL es válido."""
        result = self.validate(url)
        return result.is_valid and result.status == SSLStatus.VALID


def create_ssl_validator(
    timeout: float = 5.0,
    warning_days: int = 30
) -> SSLValidator:
    """Factory function."""
    return SSLValidator(timeout=timeout, warning_days=warning_days)