# --- INICIO FUNCIONALIDAD US-031: SCHEMA HISTORIAL AGENTES ---
import sqlite3

def create_agent_history_table(db_path: str):
    """
    Crea la tabla necesaria para almacenar el historial de prompts y respuestas.
    Sigue el principio de integridad referencial.
    """
    query = """
    CREATE TABLE IF NOT EXISTS agent_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        prompt TEXT NOT NULL,
        response TEXT,
        model_used TEXT,
        tokens_estimated INTEGER,
        execution_time_ms INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(query)
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB ERROR] Error al crear tabla de historial: {e}")

# --- FIN FUNCIONALIDAD US-031 ---