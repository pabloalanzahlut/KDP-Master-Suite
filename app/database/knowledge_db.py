"""
KDP MASTER - Knowledge Base Database Manager
=============================================
Gestiona la persistencia de entradas de conocimiento en knowledge_base.db.
Soporta dual-write: archivos markdown + SQLite.
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class KnowledgeDBManager:
    """Gestor de base de datos SQLite para la base de conocimiento."""

    def __init__(self, db_path: str = None):
        """
        Inicializa el gestor de base de datos de conocimiento.

        Args:
            db_path: Ruta a la base de datos. Si es None, usa la ruta por defecto.
        """
        if db_path is None:
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent.parent.parent
            kb_dir = base_dir / "knowledge"
            kb_dir.mkdir(parents=True, exist_ok=True)
            db_path = kb_dir / "knowledge_base.db"

        self.db_path = str(db_path)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Crea y retorna una conexi&oacute;n a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Crea la tabla de conocimiento si no existe."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    source TEXT,
                    content TEXT NOT NULL UNIQUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_entries(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_source ON knowledge_entries(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_content ON knowledge_entries(content)")
            conn.commit()
            logger.info("Knowledge base database initialized at %s", self.db_path)
        except Exception as e:
            logger.error("Error inicializando knowledge base DB: %s", e)
            conn.rollback()
            raise
        finally:
            conn.close()

    def insert_entry(self, category: str, source: str, content: str, timestamp: str = None, auto_export: bool = True) -> Tuple[bool, str]:
        """
        Inserta una nueva entrada de conocimiento.

        Args:
            category: Categor&iacute;a del conocimiento
            source: Fuente del conocimiento
            content: Contenido del conocimiento
            timestamp: Timestamp opcional (default: ahora)
            auto_export: Si True, regenera exports HTML despu&eacute;s de insertar

        Returns:
            Tuple (success, message)
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO knowledge_entries (category, source, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (category, source, content.strip(), timestamp))
            conn.commit()
            entry_id = cursor.lastrowid
            logger.debug("Knowledge entry inserted: %s from %s (ID: %d)", category, source, entry_id)
            
            # Regeneraci&oacute;n autom&aacute;tica de exports si est&aacute; habilitado
            if auto_export:
                self._trigger_auto_export()
            
            return True, f"Entry inserted (ID: {entry_id})"
        except sqlite3.IntegrityError:
            logger.debug("Duplicate knowledge entry skipped: %s from %s", category, source)
            return False, "Duplicate entry (content already exists)"
        except Exception as e:
            logger.error("Error inserting knowledge entry: %s", e)
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def _trigger_auto_export(self):
        """Dispara regeneraci&oacute;n autom&aacute;tica de exports."""
        try:
            import subprocess
            export_script = Path(__file__).parent.parent.parent / "export_kb.py"
            if export_script.exists():
                logger.info("Triggering auto-export of KB...")
                subprocess.Popen(
                    ["python", str(export_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                logger.info("Auto-export triggered successfully")
        except Exception as e:
            logger.warning("Auto-export failed: %s", e)

    def search_entries(self, query: str) -> List[Dict]:
        """
        Busca entradas que coincidan con la consulta.

        Args:
            query: T&eacute;rmino de b&uacute;squeda

        Returns:
            Lista de diccionarios con las entradas encontradas
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, category, source, content, timestamp
                FROM knowledge_entries
                WHERE content LIKE ?
                ORDER BY timestamp DESC
            """, (f'%{query}%',))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Error searching knowledge entries: %s", e)
            return []
        finally:
            conn.close()

    def get_all_entries(self, limit: int = None, category: str = None) -> List[Dict]:
        """
        Obtiene todas las entradas de conocimiento.

        Args:
            limit: N&uacute;mero m&aacute;ximo de entradas
            category: Filtrar por categor&iacute;a

        Returns:
            Lista de diccionarios con las entradas
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT id, category, source, content, timestamp FROM knowledge_entries"
            params = []
            conditions = []

            if category:
                conditions.append("category = ?")
                params.append(category)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Error getting all entries: %s", e)
            return []
        finally:
            conn.close()

    def get_entry_count(self, category: str = None) -> int:
        """
        Obtiene el n&uacute;mero total de entradas.

        Args:
            category: Filtrar por categor&iacute;a

        Returns:
            N&uacute;mero de entradas
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if category:
                cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE category = ?", (category,))
            else:
                cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error("Error getting entry count: %s", e)
            return 0
        finally:
            conn.close()

    def get_categories(self) -> List[str]:
        """Obtiene todas las categor&iacute;as &uacute;nicas presentes en la DB."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT category FROM knowledge_entries ORDER BY category")
            return [row['category'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error getting categories: %s", e)
            return []
        finally:
            conn.close()

    def get_category_stats(self) -> Dict[str, int]:
        """Obtiene conteo de entradas por categor&iacute;a."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT category, COUNT(*) as count FROM knowledge_entries GROUP BY category ORDER BY count DESC")
            return {row['category']: row['count'] for row in cursor.fetchall()}
        except Exception as e:
            logger.error("Error getting category stats: %s", e)
            return {}
        finally:
            conn.close()

    def delete_entry(self, entry_id: int) -> bool:
        """Elimina una entrada por su ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error("Error deleting entry: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def clear_all_entries(self) -> int:
        """Elimina todas las entradas. Retorna el n&uacute;mero eliminado."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM knowledge_entries")
            conn.commit()
            logger.info("Cleared %d knowledge entries", count)
            return count
        except Exception as e:
            logger.error("Error clearing entries: %s", e)
            conn.rollback()
            return 0
        finally:
            conn.close()

    # ============================================================
    # MÓDULO 3: VALIDACIÓN EN POPULATE
    # Evita duplicados al poblar desde archivos markdown
    # ============================================================
    def populate_from_markdown_files(self, kb_dir: str = None, force: bool = False) -> int:
        """
        Población inicial: lee archivos markdown existentes y los inserta en la DB.
        
        Args:
            kb_dir: Directorio con archivos markdown. Si es None, usa knowledge/manuals/
            force: Si True, re-procesa todos los archivos sin importar estado previo
            
        Fundamentos de programación:
        - Idempotencia: seguro ejecutar múltiples veces
        - Validación: verifica existencia antes de insertar
        - Trazabilidad: cuenta insertados vs omitidos
        """
        import hashlib
        
        if kb_dir is None:
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent.parent.parent
            kb_dir = base_dir / "knowledge" / "manuals"

        kb_path = Path(kb_dir)
        if not kb_path.exists():
            logger.warning("Knowledge directory does not exist: %s", kb_path)
            return 0

        inserted = 0
        skipped = 0
        file_map = {
            "MANUAL_LEGALIDAD.md": "Legalidad y Compliance",
            "MATRIZ_MAESTRA.md": "Matriz de Roles (GEM)",
            "MANUAL de FÓRMULAS.MD": "Fórmulas y Métricas",
            "MASTER_KB.txt": "Conocimiento General KDP"
        }

        existing_hashes = set()
        if not force:
            existing = self.get_all_entries()
            existing_hashes = {hashlib.sha256(e['content'].encode()).hexdigest()[:16] for e in existing}
            logger.info(f"DB ya tiene {len(existing_hashes)} hashes únicos")

        for filename, default_category in file_map.items():
            filepath = kb_path / filename
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
                entries = content.split("## 🟢 MÓDULO:")
                for entry in entries:
                    entry = entry.strip()
                    if not entry:
                        continue

                    lines = entry.split("\n", 4)
                    source = "Manual Migration"
                    timestamp = None
                    body = entry

                    for line in lines[:3]:
                        line_lower = line.strip().lower()
                        if line_lower.startswith("- **fuente:**"):
                            source = line.split(":", 1)[1].strip() if ":" in line else "Manual Migration"
                        elif line_lower.startswith("- **fecha:**"):
                            timestamp = line.split(":", 1)[1].strip() if ":" in line else None

                    if len(lines) > 3:
                        body = "\n".join(lines[3:]).strip()
                    elif len(lines) > 1:
                        body = "\n".join(lines[1:]).strip()

                    if not body or len(body) < 20:
                        continue

                    entry_hash = hashlib.sha256(body.encode()).hexdigest()[:16]
                    if entry_hash in existing_hashes and not force:
                        skipped += 1
                        continue

                    success, _ = self.insert_entry(default_category, source, body, timestamp)
                    if success:
                        inserted += 1
                        existing_hashes.add(entry_hash)

                logger.info("Populated %d entries from %s (skipped: %d)", inserted, filename, skipped)
            except Exception as e:
                logger.error("Error reading %s: %s", filename, e)

        logger.info("Total knowledge entries populated from markdown: %d (inserted: %d, skipped: %d)", 
                    inserted + skipped, inserted, skipped)
        return inserted

    # -----------------------------------------------------------
    # FIN MÓDULO 3
    # -----------------------------------------------------------

    def close(self):
        """Cierra conexiones activas (no necesario con SQLite por conexi&oacute;n ef&iacute;mera, pero por consistencia de API)."""
        pass
