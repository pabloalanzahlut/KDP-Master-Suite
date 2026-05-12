"""
Transaction Manager
===================
Gestor de transacciones de copia (All-or-Nothing).
Si falla la copia del archivo N, elimina los anteriores y revierte.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)


class TransactionManager:
    """Gestor de transacciones para operaciones de backup."""

    def __init__(self, transaction_dir: str = None):
        self.transaction_dir = transaction_dir or os.path.join(os.getcwd(), ".backup_transactions")
        self.active_transaction = None
        self.staged_files = []

    def begin_transaction(self, transaction_id: str = None) -> str:
        if transaction_id is None:
            from datetime import datetime
            transaction_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.active_transaction = transaction_id
        self.staged_files = []
        self.transaction_path = os.path.join(self.transaction_dir, transaction_id)

        try:
            os.makedirs(self.transaction_path, exist_ok=True)
            logger.info(f"Transaction started: {transaction_id}")
        except Exception as e:
            logger.error(f"Error starting transaction: {e}")

        return transaction_id

    def stage_file(self, source: str, dest: str) -> bool:
        if not self.active_transaction:
            logger.warning("No active transaction")
            return False

        self.staged_files.append({
            "source": source,
            "dest": dest,
            "staged_at": len(self.staged_files) + 1
        })
        return True

    def commit(self) -> Tuple[bool, str, List[str]]:
        if not self.active_transaction:
            return False, "No active transaction", []

        copied_files = []
        failed_at_index = None

        for i, file_info in enumerate(self.staged_files):
            try:
                dest_path = Path(file_info["dest"])
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(file_info["source"], file_info["dest"])
                copied_files.append(file_info["dest"])
                logger.info(f"Committed: {file_info['dest']}")

            except Exception as e:
                logger.error(f"Failed at file {i + 1}: {e}")
                failed_at_index = i
                break

        if failed_at_index is not None:
            self._rollback(copied_files)
            return False, f"Failed at file {failed_at_index + 1}, rolled back {len(copied_files)} files", copied_files

        self._cleanup()
        return True, f"Transaction committed: {len(copied_files)} files", copied_files

    def _rollback(self, copied_files: List[str]) -> None:
        logger.warning(f"Rolling back {len(copied_files)} files")
        for file_path in copied_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Rolled back: {file_path}")
            except Exception as e:
                logger.error(f"Error rolling back {file_path}: {e}")

    def _cleanup(self) -> None:
        if self.active_transaction and os.path.exists(self.transaction_path):
            try:
                shutil.rmtree(self.transaction_path)
            except Exception as e:
                logger.warning(f"Could not cleanup transaction dir: {e}")

    def abort(self) -> None:
        if self.active_transaction:
            logger.info(f"Transaction aborted: {self.active_transaction}")
            self._cleanup()
            self.active_transaction = None
            self.staged_files = []

    def get_staged_count(self) -> int:
        return len(self.staged_files)


def execute_backup_transaction(files: List[Tuple[str, str]]) -> Tuple[bool, str, List[str]]:
    tm = TransactionManager()
    tid = tm.begin_transaction()

    for source, dest in files:
        tm.stage_file(source, dest)

    return tm.commit()


def begin_backup_transaction(transaction_id: str = None) -> str:
    tm = TransactionManager()
    return tm.begin_transaction(transaction_id)


def commit_transaction() -> Tuple[bool, str, List[str]]:
    tm = TransactionManager()
    return tm.commit()