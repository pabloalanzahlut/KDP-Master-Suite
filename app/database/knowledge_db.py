"""
KDP MASTER - Knowledge Base Database Manager
=============================================
Gestiona la persistencia de entradas de conocimiento en knowledge_base.db.
Soporta dual-write: archivos markdown + SQLite + FTS5.
"""

import sqlite3
import os
import sys
import json
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
        """Crea la tabla de conocimiento si no existe con soporte para búsqueda avanzada."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    source TEXT,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            self._migrate_schema(conn, cursor)
            self._init_fts_table(conn, cursor)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_entries(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_source ON knowledge_entries(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_timestamp ON knowledge_entries(timestamp)")
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_tipo ON knowledge_entries(tipo)")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_status ON knowledge_entries(status)")
            except sqlite3.OperationalError:
                pass
            conn.commit()
            logger.info("Knowledge base database initialized at %s", self.db_path)
        except Exception as e:
            logger.error("Error inicializando knowledge base DB: %s", e)
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _migrate_schema(self, conn, cursor):
        """Migra el schema de la base de datos de forma no destructiva."""
        try:
            cursor.execute("PRAGMA table_info(knowledge_entries)")
            columns = {row[1] for row in cursor.fetchall()}
            new_columns = {
                'tipo': 'TEXT DEFAULT "Artículo"',
                'status': 'TEXT DEFAULT "Procesado"',
                'estructura': 'TEXT',
                'formato': 'TEXT',
                'palabras': 'INTEGER DEFAULT 0',
                'confidence_score': 'REAL DEFAULT 0.0',
                'metadata_json': 'TEXT'
            }
            for col_name, col_def in new_columns.items():
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE knowledge_entries ADD COLUMN {col_name} {col_def}")
            conn.commit()
        except Exception as e:
            logger.debug("Migración schema: %s", e)
    
    def _init_fts_table(self, conn, cursor):
        """Inicializa la tabla virtual FTS5 para búsqueda full-text."""
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    content, category, tipo, source, content_rowid='id'
                )
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_entries BEGIN
                    INSERT INTO knowledge_fts(rowid, content, category, tipo, source)
                    VALUES (new.id, new.content, new.category, COALESCE(new.tipo, 'Artículo'), new.source);
                END
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge_entries BEGIN
                    DELETE FROM knowledge_fts WHERE rowid = old.id;
                END
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge_entries BEGIN
                    DELETE FROM knowledge_fts WHERE rowid = old.id;
                    INSERT INTO knowledge_fts(rowid, content, category, tipo, source)
                    VALUES (new.id, new.content, new.category, COALESCE(new.tipo, 'Artículo'), new.source);
                END
            """)
            cursor.execute("DELETE FROM knowledge_fts")
            cursor.execute("INSERT INTO knowledge_fts(rowid, content, category, tipo, source) SELECT id, content, category, COALESCE(tipo, 'Artículo'), source FROM knowledge_entries")
            conn.commit()
            logger.debug("FTS5 triggers inicializados")
        except Exception as e:
            logger.warning("FTS5 init: %s", e)

    def insert_entry(self, category: str, source: str, content: str, timestamp: str = None, 
                  auto_export: bool = True, tipo: str = "Artículo", status: str = "Procesado",
                  estructura: str = None, formato: str = None, metadata: dict = None) -> Tuple[bool, str]:
        """
        Inserta una nueva entrada de conocimiento.

        Args:
            category: Categoría del conocimiento
            source: Fuente del conocimiento
            content: Contenido del conocimiento
            timestamp: Timestamp opcional (default: ahora)
            auto_export: Si True, regenera exports HTML después de insertar
            tipo: Tipo de contenido (Tutorial, Artículo, Investigación, Lista, Legal, Fórmulas)
            status: Estado (Procesado, Pendiente, Error)
            estructura: Estructura del contenido
            formato: Formato del contenido
            metadata: Metadata adicional como dict

        Returns:
            Tuple (success, message)
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        palabras = len(content.split())
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        confidence_score = self._calculate_confidence(content, estructura, formato)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO knowledge_entries (category, source, content, timestamp, tipo, status, estructura, formato, palabras, confidence_score, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (category, source, content.strip(), timestamp, tipo, status, estructura, formato, palabras, confidence_score, metadata_json))
            conn.commit()
            entry_id = cursor.lastrowid
            logger.debug("Knowledge entry inserted: %s from %s (ID: %d)", category, source, entry_id)
            
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

    def _calculate_confidence(self, content: str, estructura: str = None, formato: str = None) -> float:
        """Calcula un score de confianza basado en la calidad del contenido."""
        score = 0.5
        if estructura:
            score += 0.1
        if formato:
            score += 0.1
        if len(content.split()) > 100:
            score += 0.1
        if any(kw in content.lower() for kw in ['procedimiento', 'instrucción', 'regla', 'protocolo']):
            score += 0.1
        return min(score, 1.0)
    
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
    
    def search_advanced(self, query: str = None, tipo: str = None, status: str = None,
                        date_from: str = None, date_to: str = None, order: str = "newest",
                        page: int = 1, page_size: int = 50) -> Dict:
        """
        Búsqueda avanzada con filtros y paginación.

        Args:
            query: Término de búsqueda
            tipo: Tipo de contenido (Tutorial, Artículo, Investigación, Lista, Legal, Fórmulas)
            status: Estado (Procesado, Pendiente, Error)
            date_from: Fecha inicio (YYYY-MM)
            date_to: Fecha fin (YYYY-MM)
            order: Orden (newest, oldest)
            page: Número de página
            page_size: Resultados por página

        Returns:
            Dict con 'results', 'total', 'page', 'pages', 'elapsed_ms'
        """
        import time
        start_time = time.time()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            conditions = []
            params = []
            
            if query and query.strip():
                conditions.append("content LIKE ?")
                params.append(f'%{query.strip()}%')
            
            if tipo and tipo != "Todos":
                conditions.append("tipo = ?")
                params.append(tipo)
            
            if status and status != "Todos":
                conditions.append("status = ?")
                params.append(status)
            
            if date_from:
                conditions.append("timestamp >= ?")
                params.append(f"{date_from}-01")
            
            if date_to:
                conditions.append("timestamp <= ?")
                params.append(f"{date_to}-31")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            order_clause = "timestamp DESC" if order == "newest" else "timestamp ASC"
            
            count_query = f"SELECT COUNT(*) FROM knowledge_entries WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            offset = (page - 1) * page_size
            data_query = f"""
                SELECT id, category, source, tipo, status, estructura, formato, 
                       palabras, confidence_score, timestamp, 
                       substr(content, 1, 200) as content_preview
                FROM knowledge_entries 
                WHERE {where_clause}
                ORDER BY {order_clause}
                LIMIT {page_size} OFFSET {offset}
            """
            cursor.execute(data_query, params)
            rows = [dict(row) for row in cursor.fetchall()]
            
            elapsed_ms = (time.time() - start_time) * 1000
            pages = (total + page_size - 1) // page_size if total > 0 else 1
            
            return {
                'results': rows,
                'total': total,
                'page': page,
                'pages': pages,
                'elapsed_ms': elapsed_ms
            }
        except Exception as e:
            logger.error("Error en búsqueda avanzada: %s", e)
            return {'results': [], 'total': 0, 'page': 1, 'pages': 1, 'elapsed_ms': 0}
        finally:
            conn.close()
    
    def search_fts(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Búsqueda full-text usando FTS5.

        Args:
            query: Término de búsqueda
            limit: Límite de resultados

        Returns:
            Lista de diccionarios con resultados
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT k.id, k.category, k.source, k.tipo, k.status, k.timestamp,
                       snippet(knowledge_fts, 0, '<mark>', '</mark>', '...', 30) as snippet
                FROM knowledge_fts f
                JOIN knowledge_entries k ON f.rowid = k.id
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error en búsqueda FTS5: %s", e)
            return []
        finally:
            conn.close()
    
    def get_tipos(self) -> List[str]:
        """Obtiene todos los tipos únicos."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT tipo FROM knowledge_entries WHERE tipo IS NOT NULL ORDER BY tipo")
            return [row['tipo'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error getting tipos: %s", e)
            return []
        finally:
            conn.close()
    
    def get_status_list(self) -> List[str]:
        """Obtiene todos los estados únicos."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT status FROM knowledge_entries WHERE status IS NOT NULL ORDER BY status")
            return [row['status'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error getting status: %s", e)
            return []
        finally:
            conn.close()
    
    def update_entry_status(self, entry_id: int, status: str) -> bool:
        """Actualiza el estado de una entrada."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE knowledge_entries SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, entry_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error("Error updating status: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def rebuild_fts_index(self) -> Tuple[int, float]:
        """Reconstruye el índice FTS5 desde la tabla principal."""
        import time
        start_time = time.time()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM knowledge_fts")
            cursor.execute("""
                INSERT INTO knowledge_fts(rowid, content, category, tipo, source)
                SELECT id, content, category, tipo, source FROM knowledge_entries
            """)
            conn.commit()
            count = cursor.rowcount
            elapsed = (time.time() - start_time) * 1000
            logger.info("FTS5 index rebuilt: %d entries in %.0fms", count, elapsed)
            return count, elapsed
        except Exception as e:
            logger.error("Error rebuilding FTS5: %s", e)
            conn.rollback()
            return 0, 0
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
        """Obtiene todas las categorías únicas."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT category FROM knowledge_entries WHERE category IS NOT NULL ORDER BY category")
            return [row['category'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error getting categories: %s", e)
            return []
        finally:
            conn.close()
    
    def search_entries(self, query: str = None, filters: dict = None, page: int = 1, 
                       page_size: int = 20, order_by: str = "timestamp DESC") -> Dict:
        """
        Alias para compatibilidad con enhanced search tab.
        
        Args:
            query: Término de búsqueda
            filters: dict con 'type', 'category', 'date_from', 'date_to'
            page: Número de página
            page_size: Resultados por página
            order_by: Orden SQL
        
        Returns:
            dict con 'entries', 'total', 'pages', 'elapsed_ms'
        """
        tipo = filters.get('type') if filters else None
        category = filters.get('category') if filters else None
        date_from = filters.get('date_from') if filters else None
        date_to = filters.get('date_to') if filters else None
        
        order = "newest" if "DESC" in order_by.upper() else "oldest"
        
        result = self.search_advanced(
            query=query,
            tipo=tipo,
            status=None,
            date_from=date_from,
            date_to=date_to,
            order=order,
            page=page,
            page_size=page_size
        )
        
        entries = []
        for row in result.get('results', []):
            entries.append({
                'id': row.get('id'),
                'source': row.get('source'),
                'category': row.get('category'),
                'type': row.get('tipo'),
                'content': row.get('content_preview', ''),
                'timestamp': row.get('timestamp'),
                'palabras': row.get('palabras', 0),
                'confidence_score': row.get('confidence_score', 0)
            })
        
        return {
            'entries': entries,
            'total': result.get('total', 0),
            'pages': result.get('pages', 1),
            'elapsed_ms': result.get('elapsed_ms', 0)
        }
    
    def get_entries_filtered(self, filters: dict = None, order_by: str = "timestamp DESC", 
                             limit: int = 1000) -> Dict:
        """
        Listar entradas con filtros sin búsqueda de texto.
        
        Args:
            filters: dict con 'type', 'category', 'date_from', 'date_to'
            order_by: Orden SQL
            limit: Máximo de resultados
        
        Returns:
            dict con 'entries', 'total'
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            conditions = []
            params = []
            
            if filters:
                if filters.get('type') and filters['type'] != "Todos":
                    conditions.append("tipo = ?")
                    params.append(filters['type'])
                if filters.get('category') and filters['category'] != "Todos":
                    conditions.append("category = ?")
                    params.append(filters['category'])
                if filters.get('date_from'):
                    conditions.append("timestamp >= ?")
                    params.append(filters['date_from'])
                if filters.get('date_to'):
                    conditions.append("timestamp <= ?")
                    params.append(filters['date_to'])
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor.execute(f"SELECT COUNT(*) FROM knowledge_entries WHERE {where_clause}", params)
            total = cursor.fetchone()[0]
            
            cursor.execute(f"""
                SELECT id, source, category, tipo, content, timestamp, palabras, confidence_score
                FROM knowledge_entries 
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ?
            """, params + [limit])
            
            entries = [dict(row) for row in cursor.fetchall()]
            
            return {'entries': entries, 'total': total}
        except Exception as e:
            logger.error("Error en get_entries_filtered: %s", e)
            return {'entries': [], 'total': 0}
        finally:
            conn.close()
    
    def query_raw(self, sql: str, params: tuple = ()) -> List:
        """Ejecuta query SQL raw y retorna resultados."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error("Error query_raw: %s", e)
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
    
    # ================================================================
    # FASE 1: INFRAESTRUCTURA CORE (Módulos 1-15)
    # ================================================================
    
    def normalize_query(self, query: str) -> str:
        """
        MÓDULO 4: Normalización Unicode (Fold Accents)
        Normaliza la búsqueda ignorando tildes y caracteres especiales.
        """
        import unicodedata
        if not query:
            return query
        normalized = unicodedata.normalize('NFD', query)
        return ''.join(c for c in normalized if not unicodedata.combining(c))
    
    def search_bm25(self, query: str, limit: int = 50, filters: dict = None) -> Dict:
        """
        MÓDULO 16: Ranking BM25
        Implementa el algoritmo BM25 para ordenar resultados por relevancia.
        """
        import time
        start_time = time.time()
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            N = cursor.fetchone()[0]
            cursor.execute("SELECT AVG(palabras) FROM knowledge_entries WHERE palabras > 0")
            avg_len = cursor.fetchone()[0] or 1000
            
            k1, b = 1.5, 0.75
            query_terms = query.split()
            
            conditions = ["content LIKE ?"]
            params = [f'%{term}%' for term in query_terms]
            
            if filters:
                if filters.get('tipo') and filters['tipo'] != "Todos":
                    conditions.append("tipo = ?")
                    params.append(filters['tipo'])
                if filters.get('category') and filters['category'] != "Todos":
                    conditions.append("category = ?")
                    params.append(filters['category'])
            
            cursor.execute(f"""
                SELECT id, category, source, tipo, content, palabras, timestamp,
                       substr(content, 1, 200) as content_preview
                FROM knowledge_entries
                WHERE {' AND '.join(conditions)}
                LIMIT ?
            """, params + [limit * 3])
            
            results = []
            for row in cursor.fetchall():
                doc_len = row[5] or avg_len
                content_lower = (row[4] or "").lower()
                
                score = 0.0
                for term in query_terms:
                    tf = content_lower.count(term.lower())
                    if tf > 0:
                        cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE content LIKE ?", (f'%{term.lower()}%',))
                        ni = cursor.fetchone()[0] or 1
                        idf = max(0, (N - ni + 0.5) / (ni + 0.5))
                        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_len)))
                        score += idf * tf_norm
                
                results.append({
                    'id': row[0], 'category': row[1], 'source': row[2], 'tipo': row[3],
                    'content_preview': row[7], 'timestamp': row[6], 'bm25_score': score
                })
            
            results.sort(key=lambda x: x['bm25_score'], reverse=True)
            return {'results': results[:limit], 'total': len(results[:limit]), 
                    'elapsed_ms': (time.time() - start_time) * 1000, 'algorithm': 'BM25'}
        except Exception as e:
            logger.error("Error BM25: %s", e)
            return {'results': [], 'total': 0, 'elapsed_ms': 0}
        finally:
            conn.close()
    
    def search_with_proximity(self, query: str, distance: int = 10, limit: int = 50) -> Dict:
        """
        MÓDULO 19: Búsqueda por Proximidad (NEAR)
        """
        import time
        start_time = time.time()
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            terms = query.split()
            if len(terms) < 2:
                return self.search_advanced(query=query, page_size=limit)
            
            conditions, params = [], []
            for i in range(len(terms) - 1):
                conditions.append("LOWER(content) LIKE ? AND LOWER(content) LIKE ?")
                params.extend([f'%{terms[i].lower()}%', f'%{terms[i+1].lower()}%'])
            
            cursor.execute(f"""
                SELECT id, category, source, tipo, content, timestamp, substr(content, 1, 200) as content_preview
                FROM knowledge_entries
                WHERE {' AND '.join(conditions)}
                LIMIT ?
            """, params + [limit])
            
            return {'results': [dict(row) for row in cursor.fetchall()], 'total': len(cursor.fetchall()),
                    'elapsed_ms': (time.time() - start_time) * 1000}
        except Exception as e:
            logger.error("Error proximidad: %s", e)
            return {'results': [], 'total': 0}
        finally:
            conn.close()
    
    def get_term_frequency(self, term: str) -> Dict:
        """
        MÓDULO 12: Contador de Frecuencia de Términos
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM knowledge_entries
                WHERE LOWER(content) LIKE LOWER(?)
            """, (f'%{term}%',))
            return {'term': term, 'documents_count': cursor.fetchone()[0]}
        finally:
            conn.close()
    
    def validate_integrity(self) -> Dict:
        """
        MÓDULO 15: Validación de Integridad SQL
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            total_entries = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM knowledge_fts")
            total_fts = cursor.fetchone()[0]
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            return {'status': 'OK' if integrity == 'ok' else 'ERROR',
                    'total_entries': total_entries, 'total_fts_index': total_fts,
                    'sqlite_integrity': integrity}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
        finally:
            conn.close()
    
    def detect_language(self, text: str) -> str:
        """
        MÓDULO 9: Detección de Idioma (ES/EN)
        """
        if not text:
            return 'unknown'
        
        spanish = ['el', 'la', 'los', 'las', 'de', 'que', 'es', 'en', 'con', 'para']
        english = ['the', 'and', 'is', 'in', 'to', 'of', 'for', 'with', 'on', 'at']
        
        words = text.lower().split()
        es = sum(1 for w in words if w in spanish)
        en = sum(1 for w in words if w in english)
        
        return 'es' if es > en else 'en' if en > es else 'unknown'
    
    def get_snippet_with_context(self, content: str, query: str, before: int = 50, after: int = 100) -> str:
        """
        MÓDULO 5: Snippets Dinámicos Configurables
        """
        if not content or not query:
            return content[:200] if content else ""
        
        pos = content.lower().find(query.lower())
        if pos == -1:
            return content[:200]
        
        start, end = max(0, pos - before), min(len(content), pos + len(query) + after)
        snippet = content[start:end]
        return ("..." + snippet + "...") if start > 0 or end < len(content) else snippet
    
    def rebuild_fts_index(self) -> Dict:
        """
        Reconstruye el índice FTS5 completo.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM knowledge_fts")
            return {'status': 'SUCCESS', 'indexed_count': cursor.fetchone()[0]}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
        finally:
            conn.close()
    
    # ================================================================
    # FASE 3: FILTROS AVANZADOS (Módulos 36-45)
    # ================================================================
    
    def collapse_similar_results(self, results: List[Dict], threshold: float = 0.95) -> List[Dict]:
        """
        MÓDULO 39: Colapso de Resultados Similares (>95%)
        """
        if not results:
            return results
        
        collapsed = []
        for result in results:
            is_duplicate = False
            for existing in collapsed:
                similarity = self._calculate_similarity(
                    result.get('content', ''), existing.get('content', '')
                )
                if similarity >= threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                collapsed.append(result)
        
        return collapsed
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similitud entre dos textos (Jaccard simple).
        """
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def detect_links_in_content(self, content: str) -> List[str]:
        """
        MÓDULO 44: Detección de Enlaces en Fragmentos
        Extrae URLs del contenido.
        """
        import re
        url_pattern = r'https?://[^\s]+|www\.[^\s]+'
        return re.findall(url_pattern, content)
    
    # ================================================================
    # FASE 4: UI/UX Y EXPORTACIÓN (Módulos 46-60)
    # ================================================================
    
    def compress_index(self) -> Dict:
        """
        MÓDULO 59: Compresión de Índice
        Optimiza el tamaño en disco de la base de datos.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("VACUUM")
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            new_size = cursor.fetchone()[0]
            return {'status': 'SUCCESS', 'new_size_bytes': new_size}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
        finally:
            conn.close()
    
    def verify_source_file(self, source: str) -> Dict:
        """
        MÓDULO 41: Verificación de Origen en Tiempo Real
        Verifica si el archivo fuente existe.
        """
        import os
        
        base_path = os.path.dirname(self.db_path)
        
        possible_paths = [
            os.path.join(base_path, "manuals", source),
            os.path.join(base_path, "transcriptions", source),
            os.path.join(base_path, source)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return {'exists': True, 'path': path, 'size': os.path.getsize(path)}
        
        return {'exists': False, 'path': None}
