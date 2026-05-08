"""
UI Mixins Package
Proporciona mixins para segmentar la clase TranscriptionProcessorApp.
"""

from app.ui.mixins.download_mixin import DownloadMixin
from app.ui.mixins.processing_mixin import ProcessingMixin
from app.ui.mixins.monitor_mixin import MonitorMixin
from app.ui.mixins.search_mixin import SearchMixin
from app.ui.mixins.config_mixin import ConfigMixin
from app.ui.mixins.dashboard_mixin import DashboardMixin

__all__ = [
    'DownloadMixin',
    'ProcessingMixin', 
    'MonitorMixin',
    'SearchMixin',
    'ConfigMixin',
    'DashboardMixin',
]