"""
CAPTCHA Detector - Módulo 15 de URL Intelligence
===============================================
Analiza respuesta HTML para detectar presencia de CAPTCHA.
Alertar al usuario que necesita resolver CAPTCHA manualmente.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import re
import requests
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CaptchaStatus(Enum):
    NOT_DETECTED = "not_detected"
    DETECTED = "detected"
    LIKELY = "likely"
    ERROR = "error"


@dataclass
class CaptchaResult:
    status: CaptchaStatus
    detected_type: List[str]
    is_blocked: bool
    action_required: str
    error: Optional[str]


class CaptchaDetector:
    """
    Detector de CAPTCHA en páginas web.
    Analiza HTML para identificar sistemas de CAPTCHA.
    """

    CAPTCHA_PATTERNS = [
        (r'g-recaptcha', 'Google reCAPTCHA'),
        (r'recaptcha', 'Google reCAPTCHA'),
        (r'hcaptcha', 'hCaptcha'),
        (r'cloudflare', 'Cloudflare Challenge'),
        (r'cf-challenge', 'Cloudflare Challenge'),
        (r'__cf_bm', 'Cloudflare Bot Detection'),
        (r'turnstile', 'Cloudflare Turnstile'),
        (r'arkose', 'Arkose Labs'),
        (r'funcaptcha', 'Arkose Labs'),
        (r'geetest', 'GeeTest'),
        (r'mtcaptcha', 'MTCaptcha'),
    ]

    CAPTCHAS_HTML = [
        '<iframe src="/captcha',
        '<div class="captcha"',
        '<form action="/verify',
    ]

    def __init__(self):
        self._session = requests.Session()

    def detect(self, url: str) -> CaptchaResult:
        """
        Detecta CAPTCHA en URL.

        Args:
            url: URL a analizar

        Returns:
            CaptchaResult con detección
        """
        detected = []

        try:
            response = self._session.get(url, timeout=10)
            html = response.text.lower()

            for pattern, name in self.CAPTCHA_PATTERNS:
                if re.search(pattern, html, re.IGNORECASE):
                    detected.append(name)

            for html_pattern in self.CAPTCHAS_HTML:
                if html_pattern.lower() in html:
                    detected.append("Captcha detected in HTML")

            if detected:
                return CaptchaResult(
                    status=CaptchaStatus.DETECTED,
                    detected_type=list(set(detected)),
                    is_blocked=True,
                    action_required="Resolver CAPTCHA manualmente en navegador",
                    error=None
                )

            if response.status_code == 403:
                return CaptchaResult(
                    status=CaptchaStatus.LIKELY,
                    detected_type=["403 Forbidden - probable CAPTCHA"],
                    is_blocked=True,
                    action_required="Verificar manualmente en navegador",
                    error=None
                )

            return CaptchaResult(
                status=CaptchaStatus.NOT_DETECTED,
                detected_type=[],
                is_blocked=False,
                action_required="Ninguna acción requerida",
                error=None
            )

        except Exception as e:
            return CaptchaResult(
                status=CaptchaStatus.ERROR,
                detected_type=[],
                is_blocked=False,
                action_required="Error al analizar",
                error=str(e)
            )

    def is_blocked(self, url: str) -> bool:
        """Verifica si URL está bloqueada por CAPTCHA."""
        result = self.detect(url)
        return result.is_blocked


def create_captcha_detector() -> CaptchaDetector:
    """Factory function."""
    return CaptchaDetector()