"""
CC Schema Monitor - Módulo 14: Validador de Estructura de Párrafos
==================================================================
Asegura que el texto tenga saltos de línea lógicos y jerarquía para
chunking óptimo en ventanas de contexto Ollama.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

MIN_PARAGRAPH_LENGTH = 20
MAX_PARAGRAPH_LENGTH = 500
IDEAL_PARAGRAPH_LENGTH = 150
MIN_PARAGRAPHS = 3
MAX_CONSECUTIVE_EMPTY_LINES = 2


@dataclass
class ParagraphInfo:
    index: int
    text: str
    start_line: int
    end_line: int
    word_count: int
    char_count: int
    is_valid: bool
    issues: List[str]


@dataclass
class StructureValidationResult:
    is_valid: bool
    paragraph_count: int
    valid_paragraphs: int
    invalid_paragraphs: int
    paragraphs: List[ParagraphInfo]
    overall_score: float
    suggestions: List[str]


class ParagraphStructureValidator:
    """
    Validador de Estructura de Párrafos
    Asegura texto con saltos de línea lógicos y jerarquía.
    """

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._stats = {
            'total_validated': 0,
            'valid': 0,
            'needs_fix': 0,
            'invalid': 0
        }

    def validate(self, content: str) -> StructureValidationResult:
        """
        Valida la estructura de párrafos del contenido.

        Args:
            content: Texto a validar

        Returns:
            StructureValidationResult con análisis detallado
        """
        self._stats['total_validated'] += 1

        lines = content.split('\n')
        paragraphs = self._extract_paragraphs(lines)

        paragraph_infos = []
        valid_count = 0
        invalid_count = 0

        for idx, para_text in enumerate(paragraphs):
            info = self._analyze_paragraph(idx, para_text, lines)
            paragraph_infos.append(info)

            if info.is_valid:
                valid_count += 1
            else:
                invalid_count += 1

        score = self._calculate_score(valid_count, invalid_count, paragraph_infos)
        suggestions = self._generate_suggestions(paragraph_infos)

        is_valid = valid_count >= MIN_PARAGRAPHS and (not self.strict_mode or invalid_count == 0)

        if is_valid:
            self._stats['valid'] += 1
        elif valid_count > 0:
            self._stats['needs_fix'] += 1
        else:
            self._stats['invalid'] += 1

        return StructureValidationResult(
            is_valid=is_valid,
            paragraph_count=len(paragraphs),
            valid_paragraphs=valid_count,
            invalid_paragraphs=invalid_count,
            paragraphs=paragraph_infos,
            overall_score=score,
            suggestions=suggestions
        )

    def _extract_paragraphs(self, lines: List[str]) -> List[str]:
        """Extrae párrafos del texto."""
        paragraphs = []
        current_para = []
        empty_line_count = 0

        for line in lines:
            stripped = line.strip()

            if not stripped:
                empty_line_count += 1
                if empty_line_count >= MAX_CONSECUTIVE_EMPTY_LINES:
                    if current_para:
                        paragraphs.append('\n'.join(current_para))
                        current_para = []
                continue

            empty_line_count = 0

            if stripped.startswith('#'):
                if current_para:
                    paragraphs.append('\n'.join(current_para))
                    current_para = []
                current_para.append(stripped)
            else:
                current_para.append(stripped)

        if current_para:
            paragraphs.append('\n'.join(current_para))

        return [p for p in paragraphs if p.strip()]

    def _analyze_paragraph(self, idx: int, text: str, all_lines: List[str]) -> ParagraphInfo:
        """Analiza un párrafo individual."""
        issues = []
        word_count = len(text.split())
        char_count = len(text)

        start_line = 0
        line_count = 0
        for i, line in enumerate(all_lines):
            if text.startswith(line.strip()):
                start_line = i
                break

        end_line = start_line + text.count('\n')

        if char_count < MIN_PARAGRAPH_LENGTH:
            issues.append(f"too_short:{char_count}<{MIN_PARAGRAPH_LENGTH}")
        elif char_count > MAX_PARAGRAPH_LENGTH:
            issues.append(f"too_long:{char_count}>{MAX_PARAGRAPH_LENGTH}")

        if word_count < 3:
            issues.append("insufficient_words")

        if text.count('\n') > 10:
            issues.append("excessive_line_breaks")

        if re.match(r'^[A-Z\s]+$', text):
            issues.append("all_caps")

        if re.match(r'^\d+\.\s+\S+', text.strip()):
            issues.append("numbered_list_fragment")

        has_valid_structure = len(issues) == 0 or (
            not self.strict_mode and
            len([i for i in issues if 'too_short' in i]) < 2
        )

        return ParagraphInfo(
            index=idx,
            text=text[:100] + '...' if len(text) > 100 else text,
            start_line=start_line,
            end_line=end_line,
            word_count=word_count,
            char_count=char_count,
            is_valid=has_valid_structure,
            issues=issues
        )

    def _calculate_score(
        self,
        valid_count: int,
        invalid_count: int,
        paragraphs: List[ParagraphInfo]
    ) -> float:
        """Calcula score de estructura."""
        total = valid_count + invalid_count
        if total == 0:
            return 0.0

        base_score = valid_count / total

        ideal_count = sum(1 for p in paragraphs if MIN_PARAGRAPH_LENGTH <= p.char_count <= MAX_PARAGRAPH_LENGTH)
        ideal_ratio = ideal_count / total if total > 0 else 0

        score = (base_score * 0.6) + (ideal_ratio * 0.4)
        return min(max(score, 0.0), 1.0)

    def _generate_suggestions(self, paragraphs: List[ParagraphInfo]) -> List[str]:
        """Genera sugerencias para mejorar estructura."""
        suggestions = []

        too_short = sum(1 for p in paragraphs if p.char_count < MIN_PARAGRAPH_LENGTH)
        if too_short > 0:
            suggestions.append(f"Merge {too_short} short paragraphs (<{MIN_PARAGRAPH_LENGTH} chars)")

        too_long = sum(1 for p in paragraphs if p.char_count > MAX_PARAGRAPH_LENGTH)
        if too_long > 0:
            suggestions.append(f"Split {too_long} long paragraphs (>{MAX_PARAGRAPH_LENGTH} chars)")

        avg_length = sum(p.char_count for p in paragraphs) / len(paragraphs) if paragraphs else 0
        if avg_length < IDEAL_PARAGRAPH_LENGTH * 0.5:
            suggestions.append("Paragraphs are too short on average - consider combining related content")

        return suggestions

    def optimize_for_chunks(self, content: str, chunk_size: int = 500) -> List[str]:
        """
        Optimiza el contenido para chunking en ventanas de contexto.

        Args:
            content: Texto a optimizar
            chunk_size: Tamaño objetivo por chunk

        Returns:
            Lista de chunks optimizados
        """
        result = self.validate(content)

        if not result.is_valid:
            content = self._auto_fix_structure(content)

        paragraphs = self._extract_paragraphs(content.split('\n'))
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(para)
            current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _auto_fix_structure(self, content: str) -> str:
        """Corrige automáticamente la estructura del contenido."""
        lines = content.split('\n')
        fixed_lines = []
        current_para = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if current_para:
                    merged = ' '.join(current_para)
                    fixed_lines.append(merged)
                    fixed_lines.append('')
                    current_para = []
            else:
                if len(stripped) < 20 and current_para:
                    current_para.append(stripped)
                else:
                    if current_para:
                        merged = ' '.join(current_para)
                        fixed_lines.append(merged)
                        current_para = []
                    fixed_lines.append(stripped)

        if current_para:
            merged = ' '.join(current_para)
            fixed_lines.append(merged)

        return '\n'.join(fixed_lines)

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_validated': 0,
            'valid': 0,
            'needs_fix': 0,
            'invalid': 0
        }


def create_validator(strict: bool = False) -> ParagraphStructureValidator:
    """
    Factory function para crear el validador.
    """
    return ParagraphStructureValidator(strict_mode=strict)


def quick_validate_structure(content: str) -> Tuple[bool, float]:
    """
    Función de conveniencia para validación rápida.
    Retorna (is_valid, score)
    """
    validator = ParagraphStructureValidator()
    result = validator.validate(content)
    return result.is_valid, result.overall_score