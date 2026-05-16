"""
Log Masker
==========
Enmascarado de datos sensibles en logs de backup.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

SENSITIVE_PATTERNS = {
    "api_key": r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
    "password": r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']{8,})',
    "token": r'(token|auth[_-]?token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
    "secret": r'(secret|client[_-]?secret)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
    "path": r'(C:|D:|/home/|/Users/)[^\s"\'<>]+'
}


class LogMasker:
    """Enmascarador de datos sensibles en logs."""

    def __init__(self, mask_char: str = "*"):
        self.mask_char = mask_char

    def mask_sensitive_data(self, text: str) -> str:
        masked = text
        for pattern_name, pattern in SENSITIVE_PATTERNS.items():
            masked = re.sub(pattern, self._mask_match, masked, flags=re.IGNORECASE)
        return masked

    def _mask_match(self, match: re.Match) -> str:
        if len(match.groups()) >= 2:
            return f'{match.group(1)}: "{self.mask_char * 12}"'
        return f'"{self.mask_char * 12}"'

    def mask_file_content(self, input_file: str, output_file: str = None) -> bool:
        try:
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            masked = self.mask_sensitive_data(content)

            if output_file is None:
                output_file = input_file

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(masked)

            return True
        except Exception as e:
            logger.error(f"Error masking file: {e}")
            return False

    def scan_for_sensitive(self, text: str) -> List[Dict]:
        findings = []
        for pattern_name, pattern in SENSITIVE_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": pattern_name,
                    "match": match.group(0)[:50] + "...",
                    "position": match.start()
                })
        return findings


def mask_log_content(text: str) -> str:
    masker = LogMasker()
    return masker.mask_sensitive_data(text)