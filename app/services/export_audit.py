"""
KDP MASTER - Export Audit Logger
===========================
Registro ligero de exportaciones para compliance.
Tabla: export_audit (append-only)
"""

import sqlite3
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class ExportAuditLogger:
    """Logger de auditoría de exportaciones."""
    
    def __init__(self, db_path: str = None):
        """Inicializa el logger."""
        if db_path is None:
            db_path = self._get_default_db_path()
            
        self.db_path = db_path
        self.init_table()
    
    def _get_default_db_path(self) -> str:
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "knowledge" / "knowledge_base.db")
    
    def get_connection(self) -> sqlite3.Connection:
        """Crea conexión a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_table(self):
        """Crea la tabla de auditoría si no existe."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS export_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    format TEXT NOT NULL,
                    categories TEXT,
                    entries_count INTEGER,
                    file_size_bytes INTEGER,
                    content_hash TEXT,
                    output_path TEXT,
                    user_session TEXT,
                    warnings TEXT
                )
            """)
            conn.commit()
        except Exception as e:
            logger.error(f"Error creating audit table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def log_export(self, 
                   format: str,
                   categories: List[str],
                   entries_count: int,
                   file_size_bytes: int,
                   content_hash: str,
                   output_path: str,
                   warnings: List[str] = None,
                   user_session: str = None) -> bool:
        """
        Registra una exportación.
        
        Returns:
            True si se registró correctamente.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            categories_str = ','.join(categories) if categories else ''
            warnings_str = ';'.join(warnings) if warnings else ''
            
            cursor.execute("""
                INSERT INTO export_audit 
                (timestamp, format, categories, entries_count, file_size_bytes, 
                 content_hash, output_path, user_session, warnings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                format,
                categories_str,
                entries_count,
                file_size_bytes,
                content_hash,
                output_path,
                user_session or 'default',
                warnings_str
            ))
            conn.commit()
            
            logger.info(f"Exported logged: {format} - {entries_count} entries - {file_size_bytes} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error logging export: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_recent_exports(self, limit: int = 10) -> List[Dict]:
        """Obtiene las exportaciones más recientes."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, timestamp, format, categories, entries_count, 
                       file_size_bytes, content_hash, output_path
                FROM export_audit
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error fetching exports: {e}")
            return []
        finally:
            conn.close()
    
    def get_export_stats(self) -> Dict:
        """Obtiene estadísticas de exportaciones."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) as total FROM export_audit")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT SUM(file_size_bytes) as total_size FROM export_audit")
            total_size = cursor.fetchone()['total_size'] or 0
            
            cursor.execute("""
                SELECT format, COUNT(*) as count 
                FROM export_audit 
                GROUP BY format
            """)
            by_format = {row['format']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_exports': total,
                'total_size_bytes': total_size,
                'by_format': by_format
            }
            
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return {'total_exports': 0, 'total_size_bytes': 0, 'by_format': {}}
        finally:
            conn.close()
    
    def clear_old_logs(self, days: int = 90) -> int:
        """Elimina logs mayores a X días. Returns count deleted."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM export_audit 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleared {deleted} old export logs")
            return deleted
            
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()


def log_export_result(result, categories: List[str] = None) -> bool:
    """Función de conveniencia para registrar resultado."""
    try:
        from kb_exporter import ExportResult
        
        if not result.success:
            return False
            
        logger_instance = ExportAuditLogger()
        
        return logger_instance.log_export(
            format=result.format,
            categories=categories or [],
            entries_count=result.entries_count,
            file_size_bytes=result.file_size_bytes,
            content_hash=result.content_hash or '',
            output_path=result.output_path or '',
            warnings=result.warnings
        )
        
    except Exception as e:
        logger.error(f"Failed to log export: {e}")
        return False


if __name__ == "__main__":
    logger = ExportAuditLogger()
    
    stats = logger.get_export_stats()
    print(f"Total exports: {stats['total_exports']}")
    print(f"Total size: {stats['total_size_bytes'] / 1024:.1f} KB")
    print(f"By format: {stats['by_format']}")