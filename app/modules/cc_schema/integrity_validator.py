"""
CC Schema Monitor - Módulo 8: Validador de Integridad Post-Extracción
======================================================================
Verifica que el texto extraído tenga >100 palabras, estructura de párrafos
coherente y sin artefactos de parsing.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntegrityStatus(Enum):
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    CORRUPTED = "corrupted"


@dataclass
class IntegrityIssue:
    severity: str
    code: str
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class IntegrityValidationResult:
    is_valid: bool
    status: IntegrityStatus
    word_count: int
    paragraph_count: int
    issues: List[IntegrityIssue]
    score: float
    summary: str


class PostExtractionValidator:
    """
    Validador de Integridad Post-Extracción
    Verifica calidad y estructura del texto extraído.
    """

    MIN_WORDS = 100
    MIN_PARAGRAPHS = 3
    MAX_EMPTY_LINES_RATIO = 0.5
    MAX_SINGLE_WORD_PARAGRAPHS = 0.3

    PARSING_ARTIFACTS = [
        r'<\s*/?\s*(?:c|s|p|span|b|i|u)\s*>',
        r'&lt;\s*/?\s*(?:c|s|p|span|b|i|u)\s*&gt;',
        r'\{[a-zA-Z_]+\}',
        r'\[[a-zA-Z_]+\]',
        r'\x00',
        r'\x1a',
        r'\r\n\r\n\r\n',
    ]

    WORD_COUNT_PATTERN = re.compile(r'\b\w+\b')

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._stats = {
            'total_validated': 0,
            'valid': 0,
            'warnings': 0,
            'invalid': 0,
            'corrupted': 0
        }

    def validate(self, content: str, metadata: Optional[Dict] = None) -> IntegrityValidationResult:
        """
        Valida la integridad del contenido extraído.

        Args:
            content: Texto a validar
            metadata: Metadatos opcionales (video_id, url, etc.)

        Returns:
            IntegrityValidationResult con resultado de validación
        """
        self._stats['total_validated'] += 1

        issues = []
        word_count = self._count_words(content)
        paragraph_count = self._count_paragraphs(content)

        if word_count < self.MIN_WORDS:
            issues.append(IntegrityIssue(
                severity="error" if self.strict_mode else "warning",
                code="LOW_WORD_COUNT",
                description=f"Word count ({word_count}) below minimum ({self.MIN_WORDS})",
                suggestion="Verify if video has enough spoken content"
            ))

        if paragraph_count < self.MIN_PARAGRAPHS:
            issues.append(IntegrityIssue(
                severity="error" if self.strict_mode else "warning",
                code="LOW_PARAGRAPH_COUNT",
                description=f"Paragraph count ({paragraph_count}) below minimum ({self.MIN_PARAGRAPHS})",
                suggestion="Check if extraction captured full content"
            ))

        artifact_issues = self._check_parsing_artifacts(content)
        issues.extend(artifact_issues)

        corruption_issues = self._check_corruption(content)
        issues.extend(corruption_issues)

        structure_issues = self._check_structure(content)
        issues.extend(structure_issues)

        single_word_count = self._count_single_word_paragraphs(content)
        single_word_ratio = single_word_count / max(paragraph_count, 1)
        if single_word_ratio > self.MAX_SINGLE_WORD_PARAGRAPHS:
            issues.append(IntegrityIssue(
                severity="warning",
                code="EXCESSIVE_SINGLE_WORD_PARAS",
                description=f"Single-word paragraph ratio ({single_word_ratio:.1%}) too high",
                suggestion="Check timestamp alignment issues"
            ))

        critical_issues = [i for i in issues if i.severity == "error"]
        warning_issues = [i for i in issues if i.severity == "warning"]

        score = self._calculate_score(word_count, paragraph_count, len(artifact_issues), len(corruption_issues))

        if len(corruption_issues) > 2:
            status = IntegrityStatus.CORRUPTED
            is_valid = False
            self._stats['corrupted'] += 1
        elif critical_issues:
            status = IntegrityStatus.INVALID
            is_valid = False
            self._stats['invalid'] += 1
        elif warning_issues:
            status = IntegrityStatus.WARNING
            is_valid = not self.strict_mode
            self._stats['warnings'] += 1
        else:
            status = IntegrityStatus.VALID
            is_valid = True
            self._stats['valid'] += 1

        summary_parts = []
        if is_valid:
            summary_parts.append("VALID")
        elif status == IntegrityStatus.CORRUPTED:
            summary_parts.append("CORRUPTED")
        else:
            summary_parts.append("INVALID")
        summary_parts.append(f"Words: {word_count}, Paragraphs: {paragraph_count}")
        if issues:
            summary_parts.append(f"Issues: {len(issues)}")

        return IntegrityValidationResult(
            is_valid=is_valid,
            status=status,
            word_count=word_count,
            paragraph_count=paragraph_count,
            issues=issues,
            score=score,
            summary=" | ".join(summary_parts)
        )

    def _count_words(self, content: str) -> int:
        """Cuenta palabras en el contenido."""
        return len(self.WORD_COUNT_PATTERN.findall(content))

    def _count_paragraphs(self, content: str) -> int:
        """Cuenta párrafos (bloques de texto separados por líneas vacías)."""
        paragraphs = re.split(r'\n\s*\n', content)
        return len([p for p in paragraphs if p.strip()])

    def _check_parsing_artifacts(self, content: str) -> List[IntegrityIssue]:
        """Detecta artefactos de parsing."""
        issues = []
        for pattern in self.PARSING_ARTIFACTS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues.append(IntegrityIssue(
                    severity="warning",
                    code="PARSING_ARTIFACT",
                    description=f"Found {len(matches)} parsing artifact(s): {pattern[:30]}",
                    suggestion="Run content through normalizer"
                ))
        return issues

    def _check_corruption(self, content: str) -> List[IntegrityIssue]:
        """Detecta caracteres corruptos."""
        issues = []

        null_count = content.count('\x00')
        if null_count > 0:
            issues.append(IntegrityIssue(
                severity="error",
                code="NULL_CHARS",
                description=f"Found {null_count} null character(s)",
                suggestion="Remove null bytes from content"
            ))

        if '\x1a' in content:
            issues.append(IntegrityIssue(
                severity="error",
                code="SUB_CHAR",
                description="Found SUB (0x1A) character - possible encoding corruption",
                suggestion="Verify source encoding and re-encode as UTF-8"
            ))

        try:
            content.encode('utf-8')
        except UnicodeEncodeError as e:
            issues.append(IntegrityIssue(
                severity="error",
                code="UTF8_CORRUPTION",
                description=f"UTF-8 encoding error: {e}",
                suggestion="Re-encode content as UTF-8"
            ))

        return issues

    def _check_structure(self, content: str) -> List[IntegrityIssue]:
        """Verifica estructura del contenido."""
        issues = []

        empty_lines = content.count('\n\n\n')
        total_lines = content.count('\n')
        empty_ratio = empty_lines / max(total_lines, 1)
        if empty_ratio > self.MAX_EMPTY_LINES_RATIO:
            issues.append(IntegrityIssue(
                severity="warning",
                code="EXCESSIVE_EMPTY_LINES",
                description=f"Empty line ratio ({empty_ratio:.1%}) too high",
                suggestion="Clean up excessive newlines"
            ))

        lines = content.split('\n')
        very_short_lines = sum(1 for l in lines if len(l.strip()) > 0 and len(l.strip()) < 3)
        short_ratio = very_short_lines / max(len([l for l in lines if l.strip()]), 1)
        if short_ratio > 0.5:
            issues.append(IntegrityIssue(
                severity="warning",
                code="EXCESSIVE_SHORT_LINES",
                description=f"Too many very short lines ({short_ratio:.1%})",
                suggestion="Check for broken timestamps or extraction errors"
            ))

        return issues

    def _count_single_word_paragraphs(self, content: str) -> int:
        """Cuenta párrafos que son solo una palabra."""
        paragraphs = re.split(r'\n\s*\n', content)
        count = 0
        for para in paragraphs:
            words = [w for w in para.split() if w.strip()]
            if len(words) == 1:
                count += 1
        return count

    def _calculate_score(
        self,
        word_count: int,
        paragraph_count: int,
        artifact_count: int,
        corruption_count: int
    ) -> float:
        """Calcula score de integridad (0.0-1.0)."""
        base = 1.0

        if word_count < self.MIN_WORDS:
            base -= 0.3
        elif word_count < self.MIN_WORDS * 2:
            base -= 0.1

        if paragraph_count < self.MIN_PARAGRAPHS:
            base -= 0.2

        base -= artifact_count * 0.05
        base -= corruption_count * 0.2

        return max(0.0, min(1.0, base))

    def validate_file(self, file_path: str, metadata: Optional[Dict] = None) -> IntegrityValidationResult:
        """
        Valida un archivo directamente.

        Args:
            file_path: Ruta al archivo
            metadata: Metadatos opcionales

        Returns:
            IntegrityValidationResult
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.validate(content, metadata)
        except Exception as e:
            logger.error(f"Failed to validate file {file_path}: {e}")
            return IntegrityValidationResult(
                is_valid=False,
                status=IntegrityStatus.INVALID,
                word_count=0,
                paragraph_count=0,
                issues=[IntegrityIssue(
                    severity="error",
                    code="FILE_READ_ERROR",
                    description=f"Cannot read file: {e}",
                    suggestion="Check file permissions and encoding"
                )],
                score=0.0,
                summary=f"ERROR: Cannot read file - {e}"
            )

    def get_stats(self) -> dict:
        """Retorna estadísticas de validación."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_validated': 0,
            'valid': 0,
            'warnings': 0,
            'invalid': 0,
            'corrupted': 0
        }


def create_validator(strict: bool = False) -> PostExtractionValidator:
    """
    Factory function para crear el validador.
    """
    return PostExtractionValidator(strict_mode=strict)


def quick_integrity_check(content: str) -> Tuple[bool, float, str]:
    """
    Función de conveniencia para check rápido.
    Retorna (is_valid, score, summary)
    """
    validator = PostExtractionValidator()
    result = validator.validate(content)
    return result.is_valid, result.score, result.summary