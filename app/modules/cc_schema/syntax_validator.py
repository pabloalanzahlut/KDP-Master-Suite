"""
URL Syntax Validator - Módulo 1 de URL Intelligence
===================================================
Valida que la URL cumpla con RFC 3986 antes de cualquier petición.
Detecta URLs malformadas como "youtube.com/watch" sin ID de video.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class URLSyntaxStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"


@dataclass
class SyntaxValidationResult:
    is_valid: bool
    status: URLSyntaxStatus
    scheme: Optional[str]
    netloc: Optional[str]
    path: Optional[str]
    query: Optional[str]
    fragment: Optional[str]
    errors: List[str]
    warnings: List[str]


class URLSyntaxValidator:
    """
    Validador de sintaxis de URL según RFC 3986.
    Detecta URLs malformadas, caracteres inválidos y estructuras sospechosas.
    """

    VALID_SCHEMES = {'http', 'https'}

    SUSPICIOUS_PATTERNS = [
        r'\.\./',
        r'\.\.%2f',
        r'%00',
        r'\x00',
        r'[\r\n]',
    ]

    INVALID_CHARS = frozenset('<>"{`}|\\^[]`')

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def validate(self, url: str) -> SyntaxValidationResult:
        """
        Valida sintaxis de URL.

        Args:
            url: URL a validar

        Returns:
            SyntaxValidationResult con estado y componentes parseados
        """
        errors = []
        warnings = []

        if not url or not isinstance(url, str):
            return SyntaxValidationResult(
                is_valid=False,
                status=URLSyntaxStatus.INVALID,
                scheme=None,
                netloc=None,
                path=None,
                query=None,
                fragment=None,
                errors=["URL está vacía o no es string"],
                warnings=[]
            )

        url = url.strip()

        scheme = self._extract_scheme(url)
        if not scheme:
            errors.append("Falta esquema (http/https)")
            return SyntaxValidationResult(
                is_valid=False,
                status=URLSyntaxStatus.INVALID,
                scheme=None,
                netloc=None,
                path=None,
                query=None,
                fragment=None,
                errors=errors,
                warnings=[]
            )

        if scheme.lower() not in self.VALID_SCHEMES:
            errors.append(f"Esquema '{scheme}' no soportado")
            return SyntaxValidationResult(
                is_valid=False,
                status=URLSyntaxStatus.INVALID,
                scheme=scheme,
                netloc=None,
                path=None,
                query=None,
                fragment=None,
                errors=errors,
                warnings=[]
            )

        if '://' not in url:
            errors.append("Falta separador '://'")
            return SyntaxValidationResult(
                is_valid=False,
                status=URLSyntaxStatus.INVALID,
                scheme=scheme,
                netloc=None,
                path=None,
                query=None,
                fragment=None,
                errors=errors,
                warnings=[]
            )

        rest = url[len(scheme) + 3:]

        if not rest:
            errors.append("Falta dominio después de '://'")
            return SyntaxValidationResult(
                is_valid=False,
                status=URLSyntaxStatus.INVALID,
                scheme=scheme,
                netloc=None,
                path=None,
                query=None,
                fragment=None,
                errors=errors,
                warnings=[]
            )

        netloc, path, query, fragment = self._parse_authority(rest)

        if not netloc:
            errors.append("Falta dominio (netloc)")
            return SyntaxValidationResult(
                is_valid=False,
                status=URLSyntaxStatus.INVALID,
                scheme=scheme,
                netloc=None,
                path=path,
                query=query,
                fragment=fragment,
                errors=errors,
                warnings=[]
            )

        if self._contains_invalid_chars(url):
            errors.append("Contiene caracteres inválidos")

        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                errors.append(f"Patrón sospechoso detectado: {pattern}")

        if netloc.startswith('localhost') and self.strict_mode:
            warnings.append("Usando localhost - posible entorno de desarrollo")

        if len(url) > 2048:
            warnings.append(f"URL muy larga ({len(url)} chars) - puede ser rechazada por algunos servidores")

        is_valid = len(errors) == 0

        status = URLSyntaxStatus.VALID if is_valid else URLSyntaxStatus.INVALID

        if is_valid and warnings and self.strict_mode:
            status = URLSyntaxStatus.SUSPICIOUS

        return SyntaxValidationResult(
            is_valid=is_valid,
            status=status,
            scheme=scheme,
            netloc=netloc,
            path=path,
            query=query,
            fragment=fragment,
            errors=errors,
            warnings=warnings
        )

    def _extract_scheme(self, url: str) -> Optional[str]:
        """Extrae el esquema de la URL."""
        match = re.match(r'^([a-zA-Z][a-zA-Z0-9+.-]*):', url)
        return match.group(1) if match else None

    def _parse_authority(self, rest: str) -> tuple:
        """Parsea authority (netloc), path, query y fragment."""
        netloc = rest
        path = ""
        query = ""
        fragment = ""

        fragment_idx = rest.find('#')
        if fragment_idx != -1:
            netloc = rest[:fragment_idx]
            fragment = rest[fragment_idx + 1:]

        query_idx = netloc.find('?')
        if query_idx != -1:
            path_or_netloc = netloc[:query_idx]
            query = netloc[query_idx + 1:]
            if '/' in path_or_netloc:
                last_slash = path_or_netloc.rfind('/')
                netloc = path_or_netloc[:last_slash]
                path = path_or_netloc[last_slash:]
            else:
                netloc = path_or_netloc
        else:
            if '/' in netloc:
                last_slash = netloc.rfind('/')
                netloc = netloc[:last_slash]
                path = netloc[last_slash:]

        return netloc, path, query, fragment

    def _contains_invalid_chars(self, url: str) -> bool:
        """Detecta caracteres inválidos en URL."""
        for char in self.INVALID_CHARS:
            if char in url:
                return True
        return False

    def normalize(self, url: str) -> Optional[str]:
        """
        Normaliza URL a formato canónico.

        Args:
            url: URL a normalizar

        Returns:
            URL normalizada o None si es inválida
        """
        result = self.validate(url)
        if not result.is_valid:
            return None

        normalized = url.strip().rstrip('/')

        if result.scheme and result.scheme.isupper():
            scheme_len = len(result.scheme)
            rest = normalized[scheme_len + 3:]
            normalized = result.scheme.lower() + '://' + rest

        if result.netloc and result.netloc.isupper():
            scheme = 'https' if normalized.startswith('https://') else 'http' if normalized.startswith('http://') else ''
            if '://' in normalized:
                after_scheme = normalized.split('://', 1)[1]
                if '/' in after_scheme:
                    domain = after_scheme.split('/')[0]
                    path = '/' + '/'.join(after_scheme.split('/')[1:])
                    normalized = scheme + '://' + domain.lower() + path
                else:
                    normalized = scheme + '://' + after_scheme.lower()

        return normalized


def create_syntax_validator(strict: bool = False) -> URLSyntaxValidator:
    """Factory function."""
    return URLSyntaxValidator(strict_mode=strict)