# --- INICIO FUNCIONALIDAD US-009: BATCH DB TRANSACTIONS ---
import sqlite3
from typing import List, Any, Iterable, Tuple

class BatchDatabaseEngine:
    """
    Provee métodos para operaciones masivas en DB garantizando 
    atomicidad y alto rendimiento (US-009).
    """
    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_bulk_insert(self, query: str, data: Iterable[Tuple[Any, ...]]) -> bool:
        """
        Ejecuta una inserción masiva en una única transacción.
        Ideal para el Monitor de Canales o importación de metadatos.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(query, data)
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"[DATABASE BATCH ERROR] Fallo en transacción masiva: {e}")
            return False

    def execute_atomic_batch(self, operations: List[Tuple[str, Tuple[Any, ...]]]) -> bool:
        """
        Ejecuta múltiples sentencias SQL diferentes en un solo bloque atómico.
        Si una falla, ninguna se aplica (Rollback automático por context manager).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for query, params in operations:
                    cursor.execute(query, params)
                conn.commit()
                return True
        except sqlite3.Error as e:
            # El context manager de sqlite3 hace rollback automáticamente si hay error
            print(f"[DATABASE ATOMIC ERROR] Error en bloque transaccional: {e}")
            return False

# --- FIN FUNCIONALIDAD US-009 ---