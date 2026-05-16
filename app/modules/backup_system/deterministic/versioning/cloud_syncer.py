"""
Cloud Syncer
============
Sincronizador con nube privada (Nextcloud/S3).
"""

import os
import logging
import subprocess
from typing import Dict, Optional


class CloudSyncer:
    """Sincronizador con nube."""

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def sync_to_nextcloud(self, local_path: str, remote_path: str) -> bool:
        try:
            rclone_cmd = self.config.get("rclone_cmd", "rclone")
            result = subprocess.run(
                [rclone_cmd, "copy", local_path, f"nextcloud:{remote_path}"],
                capture_output=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error syncing to Nextcloud: {e}")
            return False

    def sync_to_s3(self, local_path: str, bucket: str) -> bool:
        try:
            aws_cmd = self.config.get("aws_cmd", "aws")
            result = subprocess.run(
                [aws_cmd, "s3", "cp", local_path, f"s3://{bucket}/", "--recursive"],
                capture_output=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error syncing to S3: {e}")
            return False

    def sync_backup(self, backup_path: str, target: str) -> bool:
        if target.startswith("s3://"):
            return self.sync_to_s3(backup_path, target.replace("s3://", ""))
        else:
            return self.sync_to_nextcloud(backup_path, target)


def sync_to_cloud(backup_path: str, target: str, config: Dict = None) -> bool:
    syncer = CloudSyncer(config)
    return syncer.sync_backup(backup_path, target)