"""
Version Tagger
==============
Sistema de versionado semántico de backups.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional


class VersionTagger:
    """Taggeador de versiones."""

    VERSION_FORMAT = "v{major}.{minor}.{patch}"

    def __init__(self, app_version: str = "3.4.8"):
        self.app_version = app_version

    def tag_backup(self, backup_path: str, backup_type: str = "daily") -> Dict:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag = f"{self.app_version}_{backup_type}_{timestamp}"

        metadata = {
            "version": self.app_version,
            "backup_type": backup_type,
            "tag": tag,
            "created_at": datetime.now().isoformat()
        }

        meta_file = os.path.join(backup_path, ".backup_metadata.json")
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return metadata


def tag_backup(backup_path: str, backup_type: str = "daily") -> Dict:
    tagger = VersionTagger()
    return tagger.tag_backup(backup_path, backup_type)