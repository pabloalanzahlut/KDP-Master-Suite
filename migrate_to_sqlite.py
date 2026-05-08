import sqlite3
import os
import re
from pathlib import Path
from datetime import datetime

def migrate():
    """
    Migra el contenido de los archivos Markdown a una base de datos SQLite.
    """
    base_dir = Path(os.getcwd())
    if base_dir.name == "dist":
        base_dir = base_dir.parent
    
    kb_dir = base_dir / "knowledge" / "manuals"
    db_path = base_dir / "knowledge" / "knowledge_base.db"
    
    if not kb_dir.exists():
        print("❌ No se encontró la carpeta de manuales para migrar.")
        return

    print(f"🚀 Iniciando migración a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear tabla si no existe, con una restricción ÚNICA en el contenido
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        source TEXT,
        content TEXT NOT NULL UNIQUE,
        timestamp DATETIME
    );
    """)
    conn.commit()

    # Regex para parsear los bloques de los manuales
    block_pattern = re.compile(
        r"## 🟢 MÓDULO: (.*?)\n- \*\*FUENTE:\*\* (.*?)\n- \*\*FECHA:\*\* (.*?)\n\n(.*?)\n\n---",
        re.DOTALL
    )

    migrated_count = 0
    try:
        for md_file in kb_dir.glob("*.md"):
            print(f"   Procesando archivo: {md_file.name}")
            content = md_file.read_text(encoding='utf-8')
            
            for match in block_pattern.finditer(content):
                category, source, date_str, block_content = match.groups()
                
                block_content = block_content.strip()
                
                try:
                    timestamp = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
                except ValueError:
                    timestamp = datetime.now()

                try:
                    cursor.execute(
                        "INSERT INTO knowledge_entries (category, source, content, timestamp) VALUES (?, ?, ?, ?)",
                        (category.strip(), source.strip(), block_content, timestamp)
                    )
                    migrated_count += 1
                except sqlite3.IntegrityError:
                    # El contenido ya existe, lo ignoramos
                    pass
        
        conn.commit()
        print(f"\n✅ Migración completada. Se han añadido {migrated_count} nuevas entradas a la base de datos.")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error durante la migración: {e}. Se han revertido los cambios.")
    finally:
        conn.close()