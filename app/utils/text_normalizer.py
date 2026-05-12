"""
CC Schema Monitor con Auto-Adaptación de Parser
================================================
Módulo 3: Normalizador de Encoding On-The-Fly
Convierte automáticamente a UTF-8 limpio eliminando BOM y caracteres corruptos.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import os
import codecs
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

BOM_SEQUENCES = [
    ('utf-8-sig', codecs.BOM_UTF8),
    ('utf-16-le', codecs.BOM_UTF16_LE),
    ('utf-16-be', codecs.BOM_UTF16_BE),
    ('utf-32-le', codecs.BOM_UTF32_LE),
    ('utf-32-be', codecs.BOM_UTF32_BE),
]

CONTROL_CHARS_PATTERN = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')

MULTIPLE_SPACES = re.compile(r'\s{2,}')
MULTIPLE_NEWLINES = re.compile(r'\n{3,}')
PROBLEMATIC_UNICODE = re.compile(r'[\u200B-\u200F\u2028-\u202F\uFEFF]')


@dataclass
class NormalizationResult:
    success: bool
    content: str
    original_encoding: Optional[str]
    detected_encoding: Optional[str]
    bom_removed: bool
    control_chars_removed: int
    normalization_stats: dict
    error: Optional[str] = None


class TextNormalizer:
    """
    Normalizador de Encoding On-The-Fly
    Convierte a UTF-8 limpio eliminando BOM y caracteres corruptos.
    """

    DEFAULT_ENCODINGS = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']

    def __init__(self, aggressive_cleaning: bool = False):
        self.aggressive_cleaning = aggressive_cleaning
        self._stats = {
            'total_processed': 0,
            'bom_removed': 0,
            'control_chars_removed': 0,
            'encoding_fixes': 0,
            'invalid_sequences_cleaned': 0
        }

    def normalize_file(self, file_path: str) -> NormalizationResult:
        """
        Normaliza un archivo completo.

        Args:
            file_path: Ruta al archivo a normalizar

        Returns:
            NormalizationResult con contenido limpio
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()

            return self.normalize_bytes(raw_data)

        except Exception as e:
            logger.error(f"File normalization failed: {e}")
            return NormalizationResult(
                success=False,
                content="",
                original_encoding=None,
                detected_encoding=None,
                bom_removed=False,
                control_chars_removed=0,
                normalization_stats={},
                error=str(e)
            )

    def normalize_bytes(self, raw_data: bytes) -> NormalizationResult:
        """
        Normaliza bytes crudos.

        Args:
            raw_data: Datos binarios a normalizar

        Returns:
            NormalizationResult con contenido limpio
        """
        self._stats['total_processed'] += 1

        bom_removed = False
        detected_encoding = None
        content = raw_data.decode('utf-8', errors='ignore')

        for enc_name, bom_seq in BOM_SEQUENCES:
            if raw_data.startswith(bom_seq):
                content = content.lstrip('\ufeff')
                bom_removed = True
                self._stats['bom_removed'] += 1
                detected_encoding = enc_name
                break

        if not detected_encoding:
            detected_encoding = self._detect_encoding(raw_data)

        original_content = content
        control_chars_removed = self._remove_control_characters(content)
        content = self._clean_whitespace(content)
        content = self._remove_problematic_unicode(content)

        self._stats['control_chars_removed'] += control_chars_removed

        if self.aggressive_cleaning:
            content = self._aggressive_cleanup(content)

        return NormalizationResult(
            success=True,
            content=content,
            original_encoding=detected_encoding,
            detected_encoding='utf-8',
            bom_removed=bom_removed,
            control_chars_removed=control_chars_removed,
            normalization_stats={
                'original_length': len(original_content),
                'final_length': len(content),
                'removed_ratio': (len(original_content) - len(content)) / max(len(original_content), 1)
            }
        )

    def normalize_string(self, text: str, encoding: str = 'utf-8') -> NormalizationResult:
        """
        Normaliza un string directamente.

        Args:
            text: Texto a normalizar
            encoding: Encoding original (si se conoce)

        Returns:
            NormalizationResult con contenido limpio
        """
        content = text

        content = content.lstrip('\ufeff')

        control_chars_removed = self._remove_control_characters(content)
        content = self._clean_whitespace(content)
        content = self._remove_problematic_unicode(content)

        if self.aggressive_cleaning:
            content = self._aggressive_cleanup(content)

        return NormalizationResult(
            success=True,
            content=content,
            original_encoding=encoding,
            detected_encoding='utf-8',
            bom_removed='\ufeff' in text,
            control_chars_removed=control_chars_removed,
            normalization_stats={
                'original_length': len(text),
                'final_length': len(content),
                'removed_ratio': (len(text) - len(content)) / max(len(text), 1)
            }
        )

    def _detect_encoding(self, raw_data: bytes) -> str:
        """
        Detecta el encoding del contenido.
        """
        if raw_data.startswith(codecs.BOM_UTF8):
            return 'utf-8-sig'
        if raw_data.startswith(codecs.BOM_UTF16_LE):
            return 'utf-16-le'
        if raw_data.startswith(codecs.BOM_UTF16_BE):
            return 'utf-16-be'

        try:
            raw_data.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass

        for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                raw_data.decode(enc)
                return enc
            except UnicodeDecodeError:
                continue

        return 'unknown'

    def _remove_control_characters(self, text: str) -> int:
        """
        Elimina caracteres de control inválidos.
        Retorna el conteo de caracteres removidos.
        """
        original = text
        text = CONTROL_CHARS_PATTERN.sub('', text)
        return len(original) - len(text)

    def _clean_whitespace(self, text: str) -> str:
        """
        Limpia espacios y newlines múltiples.
        """
        text = MULTIPLE_SPACES.sub(' ', text)
        text = MULTIPLE_NEWLINES.sub('\n\n', text)
        text = text.strip()
        return text

    def _remove_problematic_unicode(self, text: str) -> str:
        """
        Elimina caracteres Unicode problemáticos (zero-width, etc).
        """
        return PROBLEMATIC_UNICODE.sub('', text)

    def _aggressive_cleanup(self, text: str) -> str:
        """
        Limpieza agresiva para contenido muy corrupto.
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def validate_utf8_compliance(self, text: str) -> Tuple[bool, List[int]]:
        """
        Valida que el texto sea UTF-8 válido.
        Retorna (is_valid, list_of_invalid_positions)
        """
        invalid_positions = []
        for i, char in enumerate(text):
            try:
                char.encode('utf-8')
            except UnicodeEncodeError:
                invalid_positions.append(i)

        return len(invalid_positions) == 0, invalid_positions

    def get_stats(self) -> dict:
        """Retorna estadísticas de normalización."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea las estadísticas."""
        self._stats = {
            'total_processed': 0,
            'bom_removed': 0,
            'control_chars_removed': 0,
            'encoding_fixes': 0,
            'invalid_sequences_cleaned': 0
        }


class VTTNormalizer(TextNormalizer):
    """
    Normalizador específico para archivos VTT.
    Maneja timestamps, tags de WEBVTT, y structure del formato.
    """

    WEBVTT_TAG = re.compile(r'^WEBVTT', re.MULTILINE)
    NOTE_TAG = re.compile(r'^NOTE\b', re.MULTILINE)
    STYLE_TAG = re.compile(r'^STYLE\b', re.MULTILINE)
    REGION_TAG = re.compile(r'^REGION:', re.MULTILINE)
    TIMESTAMP_PATTERN = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}')
    TIMESTAMP_LINE = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->')

    def normalize_vtt(self, content: str) -> str:
        """
        Normaliza contenido VTT específicamente.
        """
        result = self.normalize_string(content)
        text = result.content

        text = self.WEBVTT_TAG.sub('', text)
        text = self.NOTE_TAG.sub('', text)
        text = self.STYLE_TAG.sub('', text)
        text = self.REGION_TAG.sub('', text)

        lines = text.split('\n')
        cleaned = []

        for line in lines:
            line = line.strip()

            if self.TIMESTAMP_LINE.match(line):
                cleaned.append('')
                cleaned.append(line)
            elif line and not line.startswith('<'):
                cleaned.append(line)

        text = '\n'.join(cleaned)
        text = self._clean_whitespace(text)

        return text


class SRTNormalizer(TextNormalizer):
    """
    Normalizador específico para archivos SRT.
    """

    INDEX_PATTERN = re.compile(r'^\d+$')
    TIMESTAMP_SRT = re.compile(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}')

    def normalize_srt(self, content: str) -> str:
        """
        Normaliza contenido SRT específicamente.
        """
        result = self.normalize_string(content)
        text = result.content

        lines = text.split('\n')
        cleaned = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if self.INDEX_PATTERN.match(line) and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if self.TIMESTAMP_SRT.match(next_line):
                    cleaned.append('')
                    cleaned.append(next_line)
                    i += 2
                    while i < len(lines):
                        sub_line = lines[i].strip()
                        if sub_line and not self.INDEX_PATTERN.match(sub_line) and not self.TIMESTAMP_SRT.match(sub_line):
                            if not sub_line.startswith('<'):
                                cleaned.append(sub_line)
                            i += 1
                        else:
                            break
                    continue

            if line:
                cleaned.append(line)

            i += 1

        return '\n'.join(cleaned)


def create_normalizer(aggressive: bool = False) -> TextNormalizer:
    """
    Factory function para crear un normalizador.
    """
    return TextNormalizer(aggressive_cleaning=aggressive)


def normalize_vtt_content(content: str) -> str:
    """
    Función de conveniencia para normalizar VTT.
    """
    normalizer = VTTNormalizer(aggressive_cleaning=False)
    return normalizer.normalize_vtt(content)


def normalize_srt_content(content: str) -> str:
    """
    Función de conveniencia para normalizar SRT.
    """
    normalizer = SRTNormalizer(aggressive_cleaning=False)
    return normalizer.normalize_srt(content)


def normalize_file_auto(file_path: str, aggressive: bool = False) -> NormalizationResult:
    """
    Normaliza automáticamente detectando el tipo de archivo.
    """
    normalizer = TextNormalizer(aggressive_cleaning=aggressive)
    result = normalizer.normalize_file(file_path)

    if result.success:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.vtt':
            vtt_norm = VTTNormalizer()
            result.content = vtt_norm.normalize_vtt(result.content)
        elif ext == '.srt':
            srt_norm = SRTNormalizer()
            result.content = srt_norm.normalize_srt(result.content)

    return result