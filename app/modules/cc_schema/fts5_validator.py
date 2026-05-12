"""
CC Schema Monitor - Módulo 18: Validador de Compatibilidad con FTS5
==================================================================
Verifica que el texto cumpla requisitos de tokenización y longitud
para indexación inmediata en SQLite FTS5.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 1000000
MIN_WORD_COUNT = 3


@dataclass
class FTS5ValidationResult:
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    word_count: int
    char_count: int
    token_count: int
    estimated_index_size: int


class FTS5Validator:
    """
    Validador de Compatibilidad con FTS5
    Verifica requisitos de tokenización y longitud para SQLite FTS5.
    """

    FTS5_RESERVED_CHARS = ['"', "'", '*', '?', '-', '+', '(', ')', ':', '^', '~']
    FTS5_MAX_TOKEN_LENGTH = 1000

    def __init__(self):
        self._stats = {
            'total_validated': 0,
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
        }

    def validate(self, text: str) -> FTS5ValidationResult:
        """
        Valida texto para indexación FTS5.

        Args:
            text: Texto a validar

        Returns:
            FTS5ValidationResult con resultado de validación
        """
        self._stats['total_validated'] += 1

        issues = []
        warnings = []

        char_count = len(text)
        if char_count < MIN_TEXT_LENGTH:
            issues.append(f"Text too short: {char_count} < {MIN_TEXT_LENGTH} chars")

        if char_count > MAX_TEXT_LENGTH:
            issues.append(f"Text too long: {char_count} > {MAX_TEXT_LENGTH} chars")

        words = self._extract_words(text)
        word_count = len(words)

        if word_count < MIN_WORD_COUNT:
            issues.append(f"Word count too low: {word_count} < {MIN_WORD_COUNT}")

        tokens = self._tokenize_for_fts5(text)
        token_count = len(tokens)

        reserved_issues = self._check_reserved_chars(text)
        issues.extend(reserved_issues)

        if reserved_issues:
            warnings.append("Reserved FTS5 characters found - will be escaped")

        long_tokens = [t for t in tokens if len(t) > self.FTS5_MAX_TOKEN_LENGTH]
        if long_tokens:
            issues.append(f"Tokens too long: {len(long_tokens)} tokens exceed {self.FTS5_MAX_TOKEN_LENGTH} chars")

        estimated_size = self._estimate_index_size(text, token_count)

        is_valid = len(issues) == 0

        if is_valid:
            self._stats['valid'] += 1
        else:
            self._stats['invalid'] += 1

        if warnings and not issues:
            self._stats['warnings'] += 1

        return FTS5ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            word_count=word_count,
            char_count=char_count,
            token_count=token_count,
            estimated_index_size=estimated_size
        )

    def _extract_words(self, text: str) -> List[str]:
        """Extrae palabras del texto."""
        pattern = r'\b\w+\b'
        return re.findall(pattern, text)

    def _tokenize_for_fts5(self, text: str) -> List[str]:
        """Tokeniza texto simulando FTS5."""
        cleaned = text.lower()
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        tokens = cleaned.split()
        tokens = [t.strip() for t in tokens if t.strip() and len(t) <= self.FTS5_MAX_TOKEN_LENGTH]
        return tokens

    def _check_reserved_chars(self, text: str) -> List[str]:
        """Verifica caracteres reservados de FTS5."""
        issues = []
        for char in self.FTS5_RESERVED_CHARS:
            if char in text:
                count = text.count(char)
                issues.append(f"Reserved char '{char}' found {count} time(s)")
        return issues

    def _estimate_index_size(self, text: str, token_count: int) -> int:
        """Estima tamaño del índice en bytes."""
        average_token_size = 8
        index_overhead = 1.5
        estimated = int(token_count * average_token_size * index_overhead)
        return estimated

    def prepare_for_fts5(self, text: str) -> str:
        """
        Prepara texto para indexación FTS5 escapando caracteres reservados.

        Args:
            text: Texto a preparar

        Returns:
            Texto preparado para FTS5
        """
        prepared = text

        for char in self.FTS5_RESERVED_CHARS:
            prepared = prepared.replace(char, ' ')

        prepared = re.sub(r'\s+', ' ', prepared)
        prepared = prepared.strip()

        return prepared

    def split_for_indexing(
        self,
        text: str,
        max_length: int = 500000
    ) -> List[str]:
        """
        Divide texto en chunks para indexación.

        Args:
            text: Texto a dividir
            max_length: Longitud máxima por chunk

        Returns:
            Lista de chunks
        """
        chunks = []
        paragraphs = text.split('\n\n')

        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size > max_length and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(para)
            current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [text]

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_validated': 0,
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
        }


def create_validator() -> FTS5Validator:
    """
    Factory function para crear el validador.
    """
    return FTS5Validator()


def quick_validate(text: str) -> Tuple[bool, List[str]]:
    """
    Función de conveniencia para validación rápida.
    Retorna (is_valid, issues)
    """
    validator = FTS5Validator()
    result = validator.validate(text)
    return result.is_valid, result.issues