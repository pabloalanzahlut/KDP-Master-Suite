"""
User-Agent Rotator - Módulo 9 de URL Intelligence
===============================================
Rota User-Agents para evitar detección como bot.
Simula navegador Chrome/Firefox legítimo.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-17
"""

import logging
import random
from typing import List, Optional, Dict
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class UserAgentInfo:
    ua_string: str
    browser: str
    os: str
    is_mobile: bool


class UserAgentRotator:
    """
    Rotador de User-Agent para evitar detección de bots.
    Mantiene historial y alterna entre navegadores populares.
    """

    CHROME_DESKTOP = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]

    FIREFOX_DESKTOP = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    ]

    SAFARI_DESKTOP = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4; rv:124.0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    ]

    CHROME_MOBILE = [
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.0.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    ]

    EDGE = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    ]

    def __init__(
        self,
        rotation_strategy: str = "random",
        mobile_weight: float = 0.1,
        history_size: int = 50
    ):
        self.rotation_strategy = rotation_strategy
        self.mobile_weight = mobile_weight
        self.history_size = history_size

        self._all_agents = (
            self.CHROME_DESKTOP +
            self.FIREFOX_DESKTOP +
            self.SAFARI_DESKTOP +
            self.CHROME_MOBILE +
            self.EDGE
        )

        self._history: deque = deque(maxlen=history_size)
        self._current_index = 0

    def get(self) -> str:
        """
        Obtiene下一个 User-Agent según estrategia.

        Returns:
            User-Agent string
        """
        if self.rotation_strategy == "random":
            return self._get_random()
        elif self.rotation_strategy == "sequential":
            return self._get_sequential()
        elif self.rotation_strategy == "round_robin":
            return self._get_round_robin()
        else:
            return random.choice(self._all_agents)

    def _get_random(self) -> str:
        """Obtiene User-Agent aleatorio."""
        candidates = self._get_candidates()
        ua = random.choice(candidates)
        self._add_to_history(ua)
        return ua

    def _get_sequential(self) -> str:
        """Obtiene User-Agent secuencial."""
        ua = self._all_agents[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._all_agents)
        self._add_to_history(ua)
        return ua

    def _get_round_robin(self) -> str:
        """Obtiene User-Agent rotando navegadores."""
        recent = set(self._history)

        candidates = [ua for ua in self._all_agents if ua not in recent]

        if not candidates:
            candidates = self._all_agents

        ua = random.choice(candidates)
        self._add_to_history(ua)
        return ua

    def _get_candidates(self) -> List[str]:
        """Obtiene candidatos según peso de móvil."""
        if random.random() < self.mobile_weight:
            return self.CHROME_MOBILE
        else:
            return (
                self.CHROME_DESKTOP +
                self.FIREFOX_DESKTOP +
                self.SAFARI_DESKTOP +
                self.EDGE
            )

    def _add_to_history(self, ua: str):
        """Agrega User-Agent al historial."""
        self._history.append(ua)

    def get_info(self, ua: str) -> UserAgentInfo:
        """Extrae información de User-Agent."""
        ua_lower = ua.lower()

        is_chrome = 'chrome' in ua_lower and 'edg' not in ua_lower
        is_firefox = 'firefox' in ua_lower
        is_safari = 'safari' in ua_lower and 'chrome' not in ua_lower
        is_edge = 'edg' in ua_lower

        if is_chrome:
            browser = "Chrome"
        elif is_firefox:
            browser = "Firefox"
        elif is_edge:
            browser = "Edge"
        elif is_safari:
            browser = "Safari"
        else:
            browser = "Unknown"

        is_windows = 'windows' in ua_lower
        is_mac = 'mac os x' in ua_lower or 'macintosh' in ua_lower
        is_linux = 'linux' in ua_lower
        is_android = 'android' in ua_lower
        is_ios = 'iphone' in ua_lower or 'ipad' in ua_lower

        if is_android or is_ios:
            os = "Mobile"
            is_mobile = True
        elif is_windows:
            os = "Windows"
            is_mobile = False
        elif is_mac:
            os = "macOS"
            is_mobile = False
        elif is_linux:
            os = "Linux"
            is_mobile = False
        else:
            os = "Unknown"
            is_mobile = False

        return UserAgentInfo(
            ua_string=ua,
            browser=browser,
            os=os,
            is_mobile=is_mobile
        )

    def get_desktop(self) -> str:
        """Obtiene User-Agent de escritorio."""
        candidates = (
            self.CHROME_DESKTOP +
            self.FIREFOX_DESKTOP +
            self.SAFARI_DESKTOP +
            self.EDGE
        )
        ua = random.choice(candidates)
        self._add_to_history(ua)
        return ua

    def get_mobile(self) -> str:
        """Obtiene User-Agent móvil."""
        ua = random.choice(self.CHROME_MOBILE)
        self._add_to_history(ua)
        return ua

    def get_history(self) -> List[str]:
        """Retorna historial de User-Agents."""
        return list(self._history)

    def clear_history(self):
        """Limpia historial de User-Agents."""
        self._history.clear()


def create_user_agent_rotator(
    mobile_weight: float = 0.1,
    rotation_strategy: str = "round_robin"
) -> UserAgentRotator:
    """Factory function."""
    return UserAgentRotator(
        mobile_weight=mobile_weight,
        rotation_strategy=rotation_strategy
    )