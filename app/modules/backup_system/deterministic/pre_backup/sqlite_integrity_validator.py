"""
SQLite Integrity Validator
==========================
Validador de consistencia de Base de Datos SQLite.
Ejecuta PRAGMA integrity_check antes de copiar.
"""

import os
import logging
import sqlite3
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)


class SQLiteIntegrityValidator:
    """Validador de integridad de bases de datos SQLite."""

    def __init__(self):
        self.checked_databases = []

    def validate_database(self, db_path: str) -> Tuple[bool, str, List[str]]:
        if not os.path.exists(db_path):
            return False, f"Base de datos no existe: {db_path}", []

        errors = []

        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if result[0] != "ok":
                errors.append(f"Integrity check: {result[0]}")

            cursor.execute("PRAGMA quick_check")
            quick_result = cursor.fetchone()

            if quick_result[0] != "ok":
                errors.append(f"Quick check: {quick_result[0]}")

            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            db_size_mb = (page_count * page_size) / (1024 * 1024)

            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]

            cursor.execute("PRAGMA synchronous")
            sync_mode = cursor.fetchone()[0]

            self.checked_databases.append({
                "path": db_path,
                "size_mb": round(db_size_mb, 2),
                "journal": journal_mode,
                "sync": sync_mode
            })

            conn.close()

            if errors:
                return False, f"Errores encontrados: {len(errors)}", errors

            return True, (
                f"DB OK: {round(db_size_mb, 2)}MB, "
                f"journal={journal_mode}, sync={sync_mode}"
            ), []

        except sqlite3.DatabaseError as e:
            logger.error(f"Database error for {db_path}: {e}")
            return False, f"Error de base de datos: {str(e)}", [str(e)]
        except Exception as e:
            logger.error(f"Error validating {db_path}: {e}")
            return False, f"Error: {str(e)}", [str(e)]

    def validate_multiple_databases(self, db_paths: List[str]) -> Tuple[bool, dict]:
        results = {}
        all_valid = True

        for db_path in db_paths:
            is_valid, message, errors = self.validate_database(db_path)
            results[db_path] = {
                "valid": is_valid,
                "message": message,
                "errors": errors
            }
            if not is_valid:
                all_valid = False

        return all_valid, results

    def get_database_info(self, db_path: str) -> Optional[dict]:
        if not os.path.exists(db_path):
            return None

        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()

            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            cursor.execute("PRAGMA database_list")
            tables = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            conn.close()

            return {
                "path": db_path,
                "size_mb": round((page_count * page_size) / (1024 * 1024), 2),
                "table_count": table_count,
                "pages": page_count
            }
        except Exception as e:
            logger.error(f"Error getting DB info: {e}")
            return None


def validate_sqlite(db_path: str) -> Tuple[bool, str, List[str]]:
    validator = SQLiteIntegrityValidator()
    return validator.validate_database(db_path)


def validate_multiple_db(db_paths: List[str]) -> Tuple[bool, dict]:
    validator = SQLiteIntegrityValidator()
    return validator.validate_multiple_databases(db_paths)


def get_db_info(db_path: str) -> Optional[dict]:
    validator = SQLiteIntegrityValidator()
    return validator.get_database_info(db_path)