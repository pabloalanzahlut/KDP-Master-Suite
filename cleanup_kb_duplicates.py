"""
LIMPIEZA - Elimina duplicados de la Base de Conocimiento
=========================================================
Ejecutar una sola vez para limpiar duplicados existentes.
python cleanup_kb_duplicates.py
"""

import sqlite3
import hashlib
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def cleanup_knowledge_base(db_path: str) -> dict:
    """Elimina duplicados de la tabla knowledge_entries."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
    total_before = cursor.fetchone()[0]
    logger.info(f"Entradas totales antes: {total_before}")
    
    cursor.execute("""
        SELECT MIN(id) as keep_id, SUBSTR(content, 1, 100) as content_prefix
        FROM knowledge_entries
        GROUP BY SUBSTR(content, 1, 100)
    """)
    ids_to_keep = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("""
        DELETE FROM knowledge_entries
        WHERE id NOT IN ({})
    """.format(','.join('?' * len(ids_to_keep))), list(ids_to_keep))
    
    deleted = cursor.rowcount
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
    total_after = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"Duplicados eliminados: {deleted}")
    logger.info(f"Entradas despues: {total_after}")
    
    return {
        "total_before": total_before,
        "total_after": total_after,
        "deleted": deleted
    }


def main():
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent
    
    db_path = base_dir / "knowledge" / "knowledge_base.db"
    
    if not db_path.exists():
        logger.error(f"DB no encontrada: {db_path}")
        return 1
    
    logger.info(f"Limpiando: {db_path}")
    result = cleanup_knowledge_base(str(db_path))
    
    print("\n" + "=" * 40)
    print("LIMPIEZA COMPLETADA")
    print("=" * 40)
    print(f"  Antes: {result['total_before']}")
    print(f"  Despues: {result['total_after']}")
    print(f"  Eliminados: {result['deleted']}")
    print("=" * 40)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())