"""
KDP_MASTER - Database Manager for Channel Monitoring
====================================================
Gestiona la persistencia de canales, videos y estado de procesamiento.
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
try:
    from app.core.utils import normalize_youtube_url
except ImportError:
    def normalize_youtube_url(url): return url.strip().lower()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestor de base de datos SQLite para el sistema de monitoreo de canales."""
    
    def __init__(self, db_path: str = None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path: Ruta a la base de datos. Si es None, usa la ruta por defecto.
        """
        if db_path is None:
            # Soporte para PyInstaller (frozen app)
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "channel_monitor.db"
        
        self.db_path = str(db_path)
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Crea y retorna una conexión a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        return conn
    
    def init_database(self):
        """Crea las tablas si no existen."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Tabla de canales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_url TEXT NOT NULL UNIQUE,
                    channel_id TEXT,
                    channel_name TEXT NOT NULL,
                    priority INTEGER DEFAULT 3,
                    last_checked TIMESTAMP,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de videos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    video_id TEXT NOT NULL UNIQUE,
                    video_url TEXT NOT NULL,
                    title TEXT,
                    content_hash TEXT,
                    is_repost BOOLEAN DEFAULT 0,
                    duration_seconds INTEGER,
                    tags TEXT,
                    published_at TIMESTAMP,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
                )
            """)
            
            # Tabla de historial de procesamiento
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    processed_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            """)
            
            # Índices para mejorar rendimiento
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON processing_history(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_channels_active ON channels(active)")
            
            # Migración: Añadir columnas nuevas a tablas existentes
            try:
                cursor.execute("SELECT priority FROM channels LIMIT 1")
            except:
                cursor.execute("ALTER TABLE channels ADD COLUMN priority INTEGER DEFAULT 3")
            
            try:
                cursor.execute("SELECT content_hash FROM videos LIMIT 1")
            except:
                cursor.execute("ALTER TABLE videos ADD COLUMN content_hash TEXT")
                cursor.execute("ALTER TABLE videos ADD COLUMN is_repost BOOLEAN DEFAULT 0")
            
            # Migración v2.6: Añadir duration_seconds y tags a videos
            try:
                cursor.execute("SELECT duration_seconds FROM videos LIMIT 1")
            except:
                cursor.execute("ALTER TABLE videos ADD COLUMN duration_seconds INTEGER")
                cursor.execute("ALTER TABLE videos ADD COLUMN tags TEXT")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_duration ON videos(duration_seconds)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at)")
            
            # Índices críticos para dashboard (polling, paginación, gráficos)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_discovered_at ON videos(discovered_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON processing_history(status)")
            
            # Migración v2.7: Añadir content_hash_raw para validación de integridad VTT
            try:
                cursor.execute("SELECT content_hash_raw FROM videos LIMIT 1")
            except:
                cursor.execute("ALTER TABLE videos ADD COLUMN content_hash_raw TEXT")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_hash_raw ON videos(content_hash_raw)")
            
            # Tabla de conocimiento (knowledge_base.db integration)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    secondary_categories TEXT,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    content TEXT NOT NULL,
                    extract TEXT,
                    tags TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    value_score INTEGER DEFAULT 0,
                    is_banal BOOLEAN DEFAULT 0,
                    is_analyzed BOOLEAN DEFAULT 0,
                    rol_gem TEXT,
                    metricas TEXT,
                    raw_ai_response TEXT,
                    processed_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analyzed_at TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_entries(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_entries(source)")
            
            # Migracion: Añadir columnas de metadatos enriquecidos (v2.6.0)
            try:
                cursor.execute("SELECT metadata_json FROM knowledge_entries LIMIT 1")
            except:
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN metadata_json TEXT")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN keywords TEXT")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN duration_seconds INTEGER")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN is_short BOOLEAN DEFAULT 0")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN enriched_via_api BOOLEAN DEFAULT 0")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN upload_date TEXT")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN channel_name TEXT")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN view_count INTEGER")
                cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN like_count INTEGER")
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_duration ON knowledge_entries(duration_seconds)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_is_short ON knowledge_entries(is_short)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_upload_date ON knowledge_entries(upload_date)")
            
            # Migración v2.7: Tabla de filtros por palabras clave
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_filters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    include_keywords TEXT NOT NULL DEFAULT '[]',
                    exclude_keywords TEXT NOT NULL DEFAULT '[]',
                    mode TEXT NOT NULL DEFAULT 'OR',
                    enabled INTEGER DEFAULT 0,
                    total_ignored INTEGER DEFAULT 0,
                    ignored_today INTEGER DEFAULT 0,
                    last_reset_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ==================== MÓDULO 1: Migración video_relations ====================
            try:
                cursor.execute("SELECT COUNT(*) FROM video_relations LIMIT 1")
            except:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS video_relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video1_id TEXT NOT NULL,
                        video2_id TEXT NOT NULL,
                        relation_type TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(video1_id, video2_id)
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_relations_v1 ON video_relations(video1_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_relations_v2 ON video_relations(video2_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_relations_type ON video_relations(relation_type)")
                logger.info("Módulo 1: Tabla video_relations creada")
            # ==================== FIN MÓDULO 1 ====================
            
            # ==================== MÓDULO 3: Historial de Escaneos ====================
            try:
                cursor.execute("SELECT COUNT(*) FROM scan_history LIMIT 1")
            except:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scan_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id INTEGER NOT NULL,
                        scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        duration_seconds REAL,
                        videos_found INTEGER DEFAULT 0,
                        errors TEXT,
                        status TEXT DEFAULT 'success'
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_history_channel ON scan_history(channel_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_history_time ON scan_history(scan_time DESC)")
                logger.info("Módulo 3: Tabla scan_history creada")
            # ==================== FIN MÓDULO 3 ====================
            
            # Migración: Añadir columna ignored_by_filter a videos
            try:
                cursor.execute("SELECT ignored_by_filter FROM videos LIMIT 1")
            except:
                cursor.execute("ALTER TABLE videos ADD COLUMN ignored_by_filter INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE videos ADD COLUMN filter_reason TEXT")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_ignored ON videos(ignored_by_filter)")
            
            # Migración v2.8: Tabla de indexación de archivos
            self._init_file_index_tables(conn)
            
            # ==================== MÓDULO: Perfiles de Filtros ====================
            try:
                cursor.execute("SELECT COUNT(*) FROM filter_profiles LIMIT 1")
            except:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS filter_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        include_keywords TEXT,
                        exclude_keywords TEXT,
                        mode TEXT DEFAULT 'OR',
                        enabled INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_filter_profiles_name ON filter_profiles(name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_filter_profiles_active ON filter_profiles(is_active)")
                # Crear perfil por defecto si no existe
                cursor.execute("""
                    INSERT OR IGNORE INTO filter_profiles (name, include_keywords, exclude_keywords, mode, enabled, is_active)
                    VALUES ('Por Defecto', '[]', '[]', 'OR', 0, 1)
                """)
                logger.info("Módulo: Tabla filter_profiles creada con perfil por defecto")
            # ==================== FIN MÓDULO: Perfiles de Filtros ====================
            
            conn.commit()
            logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_file_index_tables(self, conn: sqlite3.Connection):
        """Inicializa las tablas de indexación de archivos y FTS5."""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indexed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                mtime REAL,
                content_hash TEXT,
                parent_dir TEXT,
                metadata_json TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON indexed_files(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_type ON indexed_files(file_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_mtime ON indexed_files(mtime)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_parent ON indexed_files(parent_dir)")
        
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS transcription_search USING fts5(
                file_id UNINDEXED,
                content,
                tokenize='porter unicode61'
            )
        """)
        
        logger.info("Tablas de indexación de archivos inicializadas")
    
    # ==================== OPERACIONES DE INDEXACIÓN DE ARCHIVOS ====================
    
    def file_index_exists(self, file_path: str) -> Optional[Dict]:
        """Verifica si un archivo ya está indexado."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM indexed_files WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def file_index_upsert(self, file_path: str, file_name: str, file_type: str, 
                         file_size: int, mtime: float, content_hash: str = None, 
                         parent_dir: str = None, metadata_json: str = None) -> int:
        """Inserta o actualiza un archivo en la tabla indexada."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO indexed_files (file_path, file_name, file_type, file_size, mtime, content_hash, parent_dir, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                file_name = excluded.file_name,
                file_type = excluded.file_type,
                file_size = excluded.file_size,
                mtime = excluded.mtime,
                content_hash = excluded.content_hash,
                parent_dir = excluded.parent_dir,
                metadata_json = excluded.metadata_json,
                indexed_at = CURRENT_TIMESTAMP
        """, (file_path, file_name, file_type, file_size, mtime, content_hash, parent_dir, metadata_json))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id
    
    def file_index_delete(self, file_path: str) -> bool:
        """Elimina un archivo de la tabla indexada."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM indexed_files WHERE file_path = ?", (file_path,))
        deleted = cursor.rowcount > 0
        if deleted:
            cursor.execute("DELETE FROM transcription_search WHERE file_id IN (SELECT id FROM indexed_files WHERE file_path = ?)", (file_path,))
        conn.commit()
        conn.close()
        return deleted
    
    def file_index_get_by_type(self, file_type: str) -> List[Dict]:
        """Obtiene todos los archivos de un tipo."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM indexed_files WHERE file_type = ? ORDER BY indexed_at DESC", (file_type,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                task_name TEXT,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                details TEXT,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                duration_seconds REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduler_history_task_id ON scheduler_history(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduler_history_started ON scheduler_history(started_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduler_history_status ON scheduler_history(status)")

    def file_index_get_stats(self) -> Dict:
        """Obtiene estadísticas de la indexación."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM indexed_files")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT file_type, COUNT(*) as count FROM indexed_files GROUP BY file_type")
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {"total": total, "by_type": by_type}
    
    def transcription_search(self, query: str, limit: int = 50) -> List[Dict]:
        """Busca en transcripciones usando FTS5."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.file_path, f.file_name, f.file_type, snipippet(transcription_search, 1, '<mark>', '</mark>', '...', 32) as snippet
            FROM transcription_search t
            JOIN indexed_files f ON f.id = t.file_id
            WHERE transcription_search MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def transcription_add_content(self, file_id: int, content: str):
        """Añade contenido a la tabla FTS5."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transcription_search WHERE file_id = ?", (file_id,))
        cursor.execute("INSERT INTO transcription_search (file_id, content) VALUES (?, ?)", (file_id, content))
        conn.commit()
        conn.close()
    
    def transcription_remove_content(self, file_id: int):
        """Elimina contenido de la tabla FTS5."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transcription_search WHERE file_id = ?", (file_id,))
        conn.commit()
        conn.close()
    
    def file_index_purge_missing(self, base_paths: List[str]) -> int:
        """Elimina entradas de archivos que ya no existen."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM indexed_files")
        deleted = 0
        for (path,) in cursor.fetchall():
            if not os.path.exists(path):
                cursor.execute("DELETE FROM transcription_search WHERE file_id IN (SELECT id FROM indexed_files WHERE file_path = ?)", (path,))
                cursor.execute("DELETE FROM indexed_files WHERE file_path = ?", (path,))
                deleted += 1
        conn.commit()
        conn.close()
        return deleted
    
    # ==================== OPERACIONES DE CANALES ====================
    
    def add_channel(self, channel_url: str, channel_name: str, channel_id: str = None) -> int:
        """
        Añade un nuevo canal a la base de datos.
        
        Args:
            channel_url: URL del canal de YouTube
            channel_name: Nombre descriptivo del canal
            channel_id: ID del canal (opcional)
        
        Returns:
            ID del canal insertado, o 0 si ya existía
        """
        # Normalizar URL antes de guardar
        channel_url = normalize_youtube_url(channel_url)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar si ya existe antes de intentar insertar
            cursor.execute("SELECT id, active FROM channels WHERE channel_url = ?", (channel_url,))
            existing = cursor.fetchone()
            if existing:
                # Si existe pero está inactivo, reactivarlo
                if not existing['active']:
                    cursor.execute("UPDATE channels SET active = 1, channel_name = ? WHERE id = ?", (channel_name, existing['id']))
                    conn.commit()
                    logger.info(f"Canal reactivado: {channel_name} (ID: {existing['id']})")
                return 0  # 0 indica que ya existía
            
            cursor.execute("""
                INSERT INTO channels (channel_url, channel_id, channel_name)
                VALUES (?, ?, ?)
            """, (channel_url, channel_id, channel_name))
            
            conn.commit()
            channel_db_id = cursor.lastrowid
            logger.info(f"Canal añadido: {channel_name} (ID: {channel_db_id})")
            return channel_db_id
        except Exception as e:
            logger.error(f"Error añadiendo canal: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def remove_channel(self, channel_id: int) -> bool:
        """
        Elimina un canal de la base de datos.
        
        Args:
            channel_id: ID del canal a eliminar
        
        Returns:
            True si se eliminó correctamente
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Canal eliminado: ID {channel_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error eliminando canal: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_all_channels(self, active_only: bool = True, priority_filter: int = None) -> List[Dict]:
        """
        Obtiene todos los canales.
        
        Args:
            active_only: Si True, solo retorna canales activos
            priority_filter: Si se especifica, filtra por prioridad (1-5)
        
        Returns:
            Lista de diccionarios con información de canales
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM channels"
            conditions = []
            if active_only:
                conditions.append("active = 1")
            if priority_filter is not None:
                conditions.append(f"priority = {priority_filter}")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY priority DESC, channel_name"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo canales: {e}")
            return []
        finally:
            conn.close()
    
    def get_priority_channels(self) -> List[Dict]:
        """Obtiene canales ordenados por prioridad (5=más prioritaria)."""
        return self.get_all_channels(active_only=True)
    
    def update_channel_last_checked(self, channel_id: int):
        """Actualiza la fecha de última verificación de un canal."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO video_relations (video1_id, video2_id, relation_type, confidence)
                VALUES (?, ?, ?, ?)
            """, (video1_id, video2_id, relation_type, confidence))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error añadiendo relación de videos: {e}")
            return False
        finally:
            conn.close()

    def get_recent_videos_for_comparison(self, limit: int = 50, window_days: int = 30) -> List[Dict]:
        """
        Obtiene videos recientes para comparación de similitud semántica.
        
        Args:
            limit: Máximo de videos a retornar
            window_days: Días hacia atrás a buscar
        
        Returns:
            Lista de videos con contenido para comparar
        """
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=window_days)).strftime('%Y-%m-%d')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT v.video_id, v.title, v.content_hash, v.published_at,
                       c.channel_name
                FROM videos v
                JOIN channels c ON v.channel_id = c.id
                WHERE v.published_at >= ? AND v.content_hash IS NOT NULL
                ORDER BY v.published_at DESC
                LIMIT ?
            """, (cutoff_date, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo videos recientes: {e}")
            return []
        finally:
            conn.close()

    def get_all_videos_count(self) -> int:
        """Retorna el total de videos en la base de datos."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM videos")
            return cursor.fetchone()[0]
        except Exception:
            return 0
        finally:
            conn.close()
    
    def toggle_channel_active(self, channel_id: int, active: bool) -> bool:
        """Activa o desactiva un canal."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE channels 
                SET active = ? 
                WHERE id = ?
            """, (1 if active else 0, channel_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error cambiando estado del canal: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_channel_name(self, channel_id: int, new_name: str) -> bool:
        """Actualiza el nombre de un canal (Auto-Healing)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE channels SET channel_name = ? WHERE id = ?", (new_name, channel_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error actualizando nombre de canal: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_channel(self, channel_id: int, name: str = None, url: str = None, active: bool = None, priority: int = None) -> bool:
        """Actualiza nombre, URL, prioridad y/o estado de un canal."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if name is not None:
                cursor.execute("UPDATE channels SET channel_name = ? WHERE id = ?", (name, channel_id))
            if url is not None:
                url = normalize_youtube_url(url)
                cursor.execute("UPDATE channels SET channel_url = ? WHERE id = ?", (url, channel_id))
            if active is not None:
                cursor.execute("UPDATE channels SET active = ? WHERE id = ?", (1 if active else 0, channel_id))
            if priority is not None:
                cursor.execute("UPDATE channels SET priority = ? WHERE id = ?", (priority, channel_id))
            conn.commit()
            logger.info(f"Canal actualizado: ID {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando canal: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ==================== OPERACIONES DE VIDEOS ====================
    
    def add_video(self, channel_id: int, video_id: str, video_url: str, 
                  title: str = None, published_at: str = None) -> Optional[int]:
        """
        Añade un nuevo video a la base de datos.
        
        Args:
            channel_id: ID del canal al que pertenece
            video_id: ID único del video de YouTube
            video_url: URL completa del video
            title: Título del video (opcional)
            published_at: Fecha de publicación (opcional)
         
        Returns:
            ID del video insertado o None si ya existe
        """
        conn = self.get_connection()
        cursor = conn.cursor()
         
        try:
            cursor.execute("""
                INSERT INTO videos (channel_id, video_id, video_url, title, published_at)
                VALUES (?, ?, ?, ?, ?)
            """, (channel_id, video_id, video_url, title, published_at))
         
            video_db_id = cursor.lastrowid
             
            # Crear entrada en historial de procesamiento
            cursor.execute("""
                INSERT INTO processing_history (video_id, status)
                VALUES (?, 'pending')
            """, (video_db_id,))
             
            conn.commit()
            logger.info(f"Video añadido: {title or video_id}")
            return video_db_id
        except sqlite3.IntegrityError:
            # El video ya existe
            logger.debug(f"Video ya existe: {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error añadir video: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def add_videos_batch(self, videos: List[Tuple[int, str, str, str, str]]) -> Dict[str, int]:
        """Inserta videos en lote usando executemany. Retorna {video_id: internal_id}."""
        if not videos:
            return {}

        video_ids = [v[1] for v in videos]
        placeholders = ','.join('?' * len(video_ids))

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.executemany("""
                INSERT OR IGNORE INTO videos (channel_id, video_id, video_url, title, published_at)
                VALUES (?, ?, ?, ?, ?)
            """, videos)

            cursor.execute(f"""
                SELECT id, video_id FROM videos 
                WHERE video_id IN ({placeholders})
            """, video_ids)

            id_map = {vid: iid for iid, vid in cursor.fetchall()}

            history_data = [(iid, 'pending') for iid in id_map.values()]
            if history_data:
                cursor.executemany("""
                    INSERT OR IGNORE INTO processing_history (video_id, status)
                    VALUES (?, ?)
                """, history_data)

            conn.commit()
            logger.info(f"Batch insert: {len(id_map)} videos processed")
            return id_map

        except Exception as e:
            logger.error(f"Error en batch de videos: {e}")
            conn.rollback()
            return {}
        finally:
            conn.close()

    def get_videos_by_channel(self, channel_id: int) -> List[Dict]:
        """Obtiene todos los videos de un canal."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT v.*, ph.status, ph.processed_at
                FROM videos v
                LEFT JOIN processing_history ph ON v.id = ph.video_id
                WHERE v.channel_id = ?
                ORDER BY v.discovered_at DESC
""", (channel_id,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo videos: {e}")
            return []
        finally:
            conn.close()

    def video_exists(self, video_id: str) -> bool:
        """Verifica si un video ya existe en la base de datos."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error verificando existencia de video: {e}")
            return False
        finally:
            conn.close()
    
    def update_video_content_hash(self, video_id: str, content_hash: str) -> bool:
        """Actualiza el hash de contenido de un video (post-descarga)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE videos 
                SET content_hash = ? 
                WHERE video_id = ?
            """, (content_hash, video_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error actualizando content_hash: {e}")
            return False
        finally:
            conn.close()
    
    def check_content_hash_exists(self, content_hash: str) -> bool:
        """Verifica si un hash de contenido ya existe (deduplicación)."""
        if not content_hash:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT 1 FROM videos WHERE content_hash = ?", (content_hash,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error verificando content_hash: {e}")
            return False
        finally:
            conn.close()
    
    def update_video_content_hash_raw(self, video_id: str, content_hash_raw: str) -> bool:
        """Actualiza el hash raw del archivo VTT descargado."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE videos 
                SET content_hash_raw = ? 
                WHERE video_id = ?
            """, (content_hash_raw, video_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error actualizando content_hash_raw: {e}")
            return False
        finally:
            conn.close()
    
    def check_content_hash_raw_exists(self, content_hash_raw: str) -> bool:
        """Verifica si un hash raw de VTT ya existe (deduplicación en descarga)."""
        if not content_hash_raw:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT 1 FROM videos WHERE content_hash_raw = ?", (content_hash_raw,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error verificando content_hash_raw: {e}")
            return False
        finally:
            conn.close()
    
    def get_video_hash_raw(self, video_id: str) -> str:
        """Obtiene el hash raw de un video existente."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT content_hash_raw FROM videos WHERE video_id = ?", (video_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error obteniendo content_hash_raw: {e}")
            return None
        finally:
            conn.close()
    
    def check_title_similarity(self, channel_id: int, title: str, threshold: float = 0.85) -> bool:
        """Detecta posibles reposts por similitud de título (>85%)."""
        import re
        
        def normalize_title(t: str) -> str:
            t = t.lower()
            t = re.sub(r'[^\w\s]', '', t)
            t = re.sub(r'\s+', ' ', t).strip()
            return t
        
        normalized = normalize_title(title)
        if len(normalized) < 5:
            return False
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT title FROM videos 
                WHERE channel_id = ? 
                AND title IS NOT NULL
            """, (channel_id,))
            
            for row in cursor:
                existing_title = normalize_title(row[0])
                if len(existing_title) < 5:
                    continue
                    
                # Simple Levenshtein-like comparison
                words1 = set(normalized.split())
                words2 = set(existing_title.split())
                
                if not words1 or not words2:
                    continue
                    
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                
                if union > 0:
                    similarity = intersection / union
                    if similarity >= threshold:
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error en detección de reposts: {e}")
            return False
        finally:
            conn.close()
    
    def mark_as_repost(self, video_id: str) -> bool:
        """Marca un video como posible repost."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE videos 
                SET is_repost = 1 
                WHERE video_id = ?
            """, (video_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error marcando repost: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== OPERACIONES DE PROCESAMIENTO ====================
    
    def get_pending_videos(self, limit: int = None) -> List[Dict]:
        """
        Obtiene videos pendientes de procesar.
        
        Args:
            limit: Número máximo de videos a retornar
        
        Returns:
            Lista de videos pendientes
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT v.*, ph.status, c.channel_name
                FROM videos v
                JOIN processing_history ph ON v.id = ph.video_id
                JOIN channels c ON v.channel_id = c.id
                WHERE ph.status = 'pending'
                ORDER BY v.discovered_at ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo videos pendientes: {e}")
            return []
        finally:
            conn.close()
    
    def update_video_status(self, video_db_id: int, status: str, error_message: str = None):
        """
        Actualiza el estado de procesamiento de un video.
        
        Args:
            video_db_id: ID del video en la base de datos
            status: Nuevo estado (pending/processing/completed/failed)
            error_message: Mensaje de error si aplica
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            processed_at = datetime.now().isoformat() if status in ['completed', 'failed'] else None
            
            cursor.execute("""
                UPDATE processing_history
                SET status = ?, processed_at = ?, error_message = ?
                WHERE video_id = ?
            """, (status, processed_at, error_message, video_db_id))
            
            conn.commit()
            logger.info(f"Estado actualizado para video ID {video_db_id}: {status}")
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_global_stats(self) -> Dict:
        """Obtiene estadísticas globales del sistema de monitoreo."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            stats = {}
            cursor.execute("SELECT COUNT(*) FROM channels")
            stats['total_channels'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM videos")
            stats['total_videos'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM processing_history WHERE status = 'failed'")
            stats['failed_videos'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(last_checked) FROM channels")
            stats['last_check'] = cursor.fetchone()[0] or "Nunca"
            
            return stats
        except Exception as e:
            logger.error(f"Error en estadísticas globales: {e}")
            return {}
        finally:
            conn.close()

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del sistema de monitoreo."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Total de canales activos
            cursor.execute("SELECT COUNT(*) as count FROM channels WHERE active = 1")
            stats['active_channels'] = cursor.fetchone()['count']
            
            # Total de videos
            cursor.execute("SELECT COUNT(*) as count FROM videos")
            stats['total_videos'] = cursor.fetchone()['count']
            
            # Videos por estado
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM processing_history 
                GROUP BY status
            """)
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            stats['pending'] = status_counts.get('pending', 0)
            stats['processing'] = status_counts.get('processing', 0)
            stats['completed'] = status_counts.get('completed', 0)
            stats['failed'] = status_counts.get('failed', 0)
            
            # Estadísticas de duplicados
            cursor.execute("SELECT COUNT(*) as count FROM videos WHERE is_repost = 1")
            stats['total_reposts'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM video_relations")
            stats['total_relations'] = cursor.fetchone()['count']
            
            # Calcular tasa de duplicados
            if stats['total_videos'] > 0:
                stats['duplicate_rate'] = round((stats['total_reposts'] / stats['total_videos']) * 100, 1)
            else:
                stats['duplicate_rate'] = 0
            
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
        finally:
            conn.close()

    # ==================== MÉTODOS MÓDULO 3: Historial de Escaneos ====================
    
    def log_scan(self, channel_id: int, duration_seconds: float, videos_found: int, errors: str = None, status: str = 'success') -> bool:
        """Registra un escaneo de canal en el historial."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO scan_history (channel_id, duration_seconds, videos_found, errors, status)
                VALUES (?, ?, ?, ?, ?)
            """, (channel_id, duration_seconds, videos_found, errors, status))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error registrando escaneo: {e}")
            return False
        finally:
            conn.close()
    
    def get_recent_scans(self, limit: int = 10) -> List[Dict]:
        """Obtiene los escaneos más recientes."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT sh.*, c.channel_name
                FROM scan_history sh
                JOIN channels c ON sh.channel_id = c.id
                ORDER BY sh.scan_time DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo escaneos recientes: {e}")
            return []
        finally:
            conn.close()
    
    def get_scan_stats(self) -> Dict:
        """Obtiene estadísticas de escaneos."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            stats = {}
            cursor.execute("SELECT COUNT(*) FROM scan_history")
            stats['total_scans'] = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(duration_seconds) FROM scan_history")
            stats['total_duration'] = cursor.fetchone()[0] or 0
            cursor.execute("SELECT AVG(duration_seconds) FROM scan_history")
            stats['avg_duration'] = round(cursor.fetchone()[0] or 0, 2)
            cursor.execute("SELECT SUM(videos_found) FROM scan_history")
            stats['total_videos_found'] = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM scan_history WHERE status = 'success'")
            stats['successful_scans'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM scan_history WHERE status = 'error'")
            stats['failed_scans'] = cursor.fetchone()[0]
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo stats de escaneos: {e}")
            return {}
        finally:
            conn.close()
    
    def reset_stale_processing_videos(self, hours_threshold: int = 1) -> int:
        """
        Resetea videos en estado 'processing' más antiguos que X horas.
        Esto previene que videos queden bloqueados indefinidamente si el proceso falla.
        
        Args:
            hours_threshold: Horas después de las cuales un video 'processing' se considera huérfano
        
        Returns:
            Número de videos reseteados
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Calcular timestamp threshold
            from datetime import timedelta
            threshold_time = datetime.now() - timedelta(hours=hours_threshold)
            
            cursor.execute("""
                UPDATE processing_history
                SET status = 'pending', 
                    error_message = 'Reset automático por timeout'
                WHERE status = 'processing' 
                AND created_at < ?
            """, (threshold_time.isoformat(),))
            
            conn.commit()
            reset_count = cursor.rowcount
            
            if reset_count > 0:
                logger.info(f"Reseteados {reset_count} videos huérfanos en estado 'processing'")
            
            return reset_count
        except Exception as e:
            logger.error(f"Error reseteando videos huérfanos: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    # ==================== ANALYTICS DASHBOARD ====================
    
    def get_daily_video_counts(self, days: int = 7) -> List[Dict]:
        """
        Obtiene el conteo de videos descubiertos por día.
        Útil para gráficos de actividad.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # SQLite: strftime('%Y-%m-%d', discovered_at)
            cursor.execute(f"""
                SELECT 
                    strftime('%Y-%m-%d', discovered_at) as date,
                    COUNT(*) as count
                FROM videos 
                WHERE discovered_at >= date('now', '-{days} days')
                GROUP BY date
                ORDER BY date ASC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo conteo diario: {e}")
            return []
        finally:
            conn.close()

    def get_status_distribution(self) -> Dict[str, int]:
        """
        Obtiene la distribución actual de estados de procesamiento.
        Útil para gráficos de torta/anillo.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM processing_history 
                GROUP BY status
            """)
            
            result = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for row in cursor.fetchall():
                result[row['status']] = row['count']
                
            return result
        except Exception as e:
            logger.error(f"Error obteniendo distribución de estados: {e}")
            return {}
        finally:
            conn.close()

    # ==================== IMPORT LOG ====================
    
    def log_import(self, source_file: str, total: int, new_count: int, 
                   duplicates: int, failed: int):
        """Registra una importación de canales en el historial."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_file TEXT,
                    total_channels INTEGER,
                    new_channels INTEGER,
                    duplicate_channels INTEGER,
                    failed_channels INTEGER
                )
            """)
            cursor.execute("""
                INSERT INTO import_log 
                (source_file, total_channels, new_channels, duplicate_channels, failed_channels)
                VALUES (?, ?, ?, ?, ?)
            """, (source_file, total, new_count, duplicates, failed))
            conn.commit()
            logger.info(f"Importación registrada: {new_count} nuevos de {total}")
        except Exception as e:
            logger.error(f"Error registrando importación: {e}")
            conn.rollback()
        finally:
            conn.close()

    # ==================== KNOWLEDGE BASE ====================

    def insert_entry(self, category: str, source: str, content: str, timestamp: str = None,
                      secondary_categories: str = None, source_url: str = None,
                      extract: str = None, tags: str = None, confidence_score: float = 0.0,
                      value_score: int = 0, is_banal: bool = False, is_analyzed: bool = False,
                      rol_gem: str = None, metricas: str = None, raw_ai_response: str = None,
                      processed_by: str = None) -> bool:
        """
        Inserta una entrada de conocimiento extendida en la DB.
        
        Args:
            category: Categoría principal asignada
            secondary_categories: JSON array de categorías secundarias
            source: Fuente del contenido (video, manual, etc.)
            source_url: URL de la fuente (YouTube)
            content: Contenido limpio
            extract: Resumen breve (≤200 chars)
            tags: JSON array de tags
            confidence_score: Score de confianza de la IA (0-1)
            value_score: Score de valor EVALUACION_0_10
            is_banal: TRUE si [FUERA_DE_SCOPE] o [CONTENIDO_BANAL]
            is_analyzed: TRUE si pasó análisis profundo
            rol_gem: Rol GEM asignado (ej: "#20 Especialista Compliance")
            metricas: JSON de métricas detectadas
            raw_ai_response: Respuesta completa de la IA (auditoría)
            processed_by: Modelo IA usado
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO knowledge_entries (
                    category, secondary_categories, source, source_url, content,
                    extract, tags, confidence_score, value_score, is_banal,
                    is_analyzed, rol_gem, metricas, raw_ai_response, processed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (category, secondary_categories, source, source_url, content,
                  extract, tags, confidence_score, value_score, is_banal,
                  is_analyzed, rol_gem, metricas, raw_ai_response, processed_by))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error insertando entrada de conocimiento: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def insert_entry_with_metadata(self, category: str, source: str, content: str,
                                    metadata: dict = None, keywords: list = None,
                                    timestamp: str = None, secondary_categories: str = None,
                                    source_url: str = None, extract: str = None,
                                    tags: str = None, confidence_score: float = 0.0,
                                    value_score: int = 0, is_banal: bool = False,
                                    is_analyzed: bool = False, rol_gem: str = None,
                                    metricas: str = None, raw_ai_response: str = None,
                                    processed_by: str = None) -> bool:
        """
        Inserta entrada de conocimiento con metadatos enriquecidos (v2.6.0).
        
        Args:
            category: Categoria principal
            source: Fuente del contenido
            content: Contenido limpio
            metadata: Dict de metadatos parseados (opcional)
            keywords: Lista de keywords extraidas (opcional)
            secondary_categories: JSON array de categorias secundarias
            source_url: URL de la fuente (YouTube)
            extract: Resumen breve
            tags: JSON array de tags
            confidence_score: Score de confianza de la IA
            value_score: Score de valor
            is_banal: TRUE si contenido banal
            is_analyzed: TRUE si paso analisis profundo
            rol_gem: Rol GEM asignado
            metricas: JSON de metricas
            raw_ai_response: Respuesta de la IA
            processed_by: Modelo IA usado
        """
        import json
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
            keywords_json = json.dumps(keywords, ensure_ascii=False) if keywords else None
            
            duration_seconds = metadata.get('duration_seconds') if metadata else None
            is_short = metadata.get('is_short', False) if metadata else False
            enriched_via_api = metadata.get('enriched_via_api', False) if metadata else False
            upload_date = metadata.get('upload_date') if metadata else None
            channel_name = metadata.get('channel') if metadata else None
            view_count = metadata.get('view_count') if metadata else None
            like_count = metadata.get('like_count') if metadata else None
            
            cursor.execute("""
                INSERT INTO knowledge_entries (
                    category, secondary_categories, source, source_url, content,
                    extract, tags, confidence_score, value_score, is_banal,
                    is_analyzed, rol_gem, metricas, raw_ai_response, processed_by,
                    metadata_json, keywords, duration_seconds, is_short, enriched_via_api,
                    upload_date, channel_name, view_count, like_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (category, secondary_categories, source, source_url, content,
                  extract, tags, confidence_score, value_score, is_banal,
                  is_analyzed, rol_gem, metricas, raw_ai_response, processed_by,
                  metadata_json, keywords_json, duration_seconds, is_short, enriched_via_api,
                  upload_date, channel_name, view_count, like_count))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error insertando entrada con metadatos: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def search_knowledge(self, query: str, limit: int = 50, search_keywords: bool = False) -> list:
        """Busca entradas de conocimiento por texto.
        
        Args:
            query: Texto a buscar
            limit: Número máximo de resultados
            search_keywords: Si True, busca también en el campo keywords
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            if search_keywords:
                cursor.execute("""
                    SELECT id, category, secondary_categories, source, source_url,
                           content, extract, tags, keywords, confidence_score, value_score,
                           is_banal, is_analyzed, rol_gem, metricas, processed_by, created_at
                    FROM knowledge_entries
                    WHERE content LIKE ? OR keywords LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (f'%{query}%', f'%{query}%', limit))
            else:
                cursor.execute("""
                    SELECT id, category, secondary_categories, source, source_url,
                           content, extract, tags, keywords, confidence_score, value_score,
                           is_banal, is_analyzed, rol_gem, metricas, processed_by, created_at
                    FROM knowledge_entries
                    WHERE content LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (f'%{query}%', limit))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error buscando conocimiento: {e}")
            return []
        finally:
            conn.close()
    
    def search_by_keywords(self, keywords: str, limit: int = 50) -> list:
        """Busca entradas por keywords específicas.
        
        Args:
            keywords: Keywords separadas por comas a buscar
            limit: Número máximo de resultados
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            keyword_list = [k.strip() for k in keywords.split(',')]
            conditions = ' OR '.join(['keywords LIKE ?' for _ in keyword_list])
            params = [f'%{k}%' for k in keyword_list] + [limit]
            
            cursor.execute(f"""
                SELECT id, category, secondary_categories, source, source_url,
                       content, extract, tags, keywords, confidence_score, value_score,
                       is_banal, is_analyzed, rol_gem, metricas, processed_by, created_at
                FROM knowledge_entries
                WHERE {conditions}
                ORDER BY created_at DESC
                LIMIT ?
            """, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error buscando por keywords: {e}")
            return []
        finally:
            conn.close()

    def get_knowledge_stats(self) -> dict:
        """Estadísticas de la base de conocimiento (extendidas)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries")
            total = cursor.fetchone()['count']
            
            cursor.execute("SELECT category, COUNT(*) as count FROM knowledge_entries GROUP BY category")
            by_category = {r['category']: r['count'] for r in cursor.fetchall()}
            
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries WHERE is_banal = 1")
            total_banal = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries WHERE is_analyzed = 1")
            total_analyzed = cursor.fetchone()['count']
            
            cursor.execute("SELECT processed_by, COUNT(*) as count FROM knowledge_entries WHERE processed_by IS NOT NULL GROUP BY processed_by")
            by_model = {r['processed_by']: r['count'] for r in cursor.fetchall()}
            
            return {
                'total_entries': total,
                'by_category': by_category,
                'total_banal': total_banal,
                'total_analyzed': total_analyzed,
                'by_model': by_model
            }
        except Exception as e:
            logger.error(f"Error stats conocimiento: {e}")
            return {'total_entries': 0, 'by_category': {}, 'total_banal': 0, 'total_analyzed': 0, 'by_model': {}}
        finally:
            conn.close()
    
    def get_import_history(self, limit: int = 20) -> List[Dict]:
        """Obtiene el historial de importaciones."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_file TEXT,
                    total_channels INTEGER,
                    new_channels INTEGER,
                    duplicate_channels INTEGER,
                    failed_channels INTEGER
                )
            """)
            conn.commit()
            
            cursor.execute("""
                SELECT * FROM import_log 
                ORDER BY import_date DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo historial de importaciones: {e}")
            return []
        finally:
            conn.close()

    # ==================== DETECCIÓN DE DUPLICADOS ====================

    def find_duplicates_by_duration_and_window(self, duration: int, window_days: int = 7, tolerance_seconds: int = 5) -> List[Dict]:
        """
        Busca videos duplicados por duración similar dentro de ventana de tiempo.
        
        Args:
            duration: Duración del video en segundos
            window_days: Días hacia atrás a buscar (default: 7)
            tolerance_seconds: Tolerancia de diferencia en segundos (default: 5)
        
        Returns:
            Lista de videos potenciales duplicados
        """
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=window_days)).strftime('%Y-%m-%d')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT v.id, v.video_id, v.title, v.channel_id, v.published_at, v.discovered_at,
                       c.channel_name, c.channel_url
                FROM videos v
                JOIN channels c ON v.channel_id = c.id
                WHERE v.published_at >= ?
                  AND v.duration_seconds IS NOT NULL
                  AND ABS(v.duration_seconds - ?) <= ?
                ORDER BY v.published_at DESC
            """, (cutoff_date, duration, tolerance_seconds))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error buscando duplicados por duración: {e}")
            return []
        finally:
            conn.close()

    def find_similar_titles(self, title: str, channel_id: int = None, threshold: float = 0.80, limit: int = 10) -> List[Dict]:
        """
        Busca videos con títulos similares usando Jaccard similarity.
        
        Args:
            title: Título a comparar
            channel_id: Filtrar por canal específico (None = todos)
            threshold: Umbral de similitud (0.0-1.0)
            limit: Máximo de resultados
        
        Returns:
            Lista de videos con títulos similares
        """
        import re
        
        def normalize_text(t: str) -> set:
            t = t.lower()
            t = re.sub(r'[^\w\s]', '', t)
            words = t.split()
            return set(w for w in words if len(w) > 2)
        
        title_words = normalize_text(title)
        if not title_words:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if channel_id:
                cursor.execute("""
                    SELECT v.id, v.video_id, v.title, v.channel_id, v.published_at,
                           c.channel_name, c.channel_url
                    FROM videos v
                    JOIN channels c ON v.channel_id = c.id
                    WHERE v.channel_id = ? AND v.title IS NOT NULL
                """, (channel_id,))
            else:
                cursor.execute("""
                    SELECT v.id, v.video_id, v.title, v.channel_id, v.published_at,
                           c.channel_name, c.channel_url
                    FROM videos v
                    JOIN channels c ON v.channel_id = c.id
                    WHERE v.title IS NOT NULL
                """)
            
            similar = []
            for row in cursor:
                existing_words = normalize_text(row['title'])
                if not existing_words:
                    continue
                
                intersection = len(title_words & existing_words)
                union = len(title_words | existing_words)
                
                if union > 0:
                    similarity = intersection / union
                    if similarity >= threshold:
                        similar.append({
                            **dict(row),
                            'similarity_score': round(similarity, 2)
                        })
            
            similar.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar[:limit]
        except Exception as e:
            logger.error(f"Error buscando títulos similares: {e}")
            return []
        finally:
            conn.close()

    def find_duplicates_by_tags(self, tags: List[str], min_common: int = 3, window_days: int = 30) -> List[Dict]:
        """
        Busca videos que compartan al menos min_common tags en común.
        
        Args:
            tags: Lista de tags del video
            min_common: Mínimo de tags en común (default: 3)
            window_days: Días hacia atrás a buscar (default: 30)
        
        Returns:
            Lista de videos con tags similares
        """
        from datetime import datetime, timedelta
        
        if not tags or len(tags) < min_common:
            return []
        
        cutoff_date = (datetime.now() - timedelta(days=window_days)).strftime('%Y-%m-%d')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, video_id, title, channel_id, published_at, tags
                FROM videos
                WHERE published_at >= ? AND tags IS NOT NULL AND tags != ''
            """, (cutoff_date,))
            
            similar = []
            for row in cursor:
                if not row['tags']:
                    continue
                
                existing_tags = set(t.strip().lower() for t in row['tags'].split(','))
                new_tags = set(t.strip().lower() for t in tags)
                
                common = len(existing_tags & new_tags)
                if common >= min_common:
                    similar.append({
                        **dict(row),
                        'common_tags_count': common,
                        'common_tags': list(existing_tags & new_tags)
                    })
            
            similar.sort(key=lambda x: x['common_tags_count'], reverse=True)
            return similar
        except Exception as e:
            logger.error(f"Error buscando duplicados por tags: {e}")
            return []
        finally:
            conn.close()

    def add_video_metadata(self, video_id: str, duration_seconds: int = None, tags: str = None) -> bool:
        """
        Actualiza metadatos adicionales de un video (duration, tags).
        
        Args:
            video_id: ID del video en YouTube
            duration_seconds: Duración en segundos
            tags: Tags separados por coma
        
        Returns:
            True si se actualizó correctamente
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE videos 
                SET duration_seconds = COALESCE(?, duration_seconds),
                    tags = COALESCE(?, tags)
                WHERE video_id = ?
            """, (duration_seconds, tags, video_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error actualizando metadatos de video: {e}")
            return False
        finally:
            conn.close()

    def get_duplicate_stats(self) -> Dict:
        """
        Obtiene estadísticas de duplicados detectados.
        
        Returns:
            Diccionario con estadísticas
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) as count FROM videos WHERE is_repost = 1")
            total_reposts = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM videos WHERE content_hash IS NOT NULL")
            with_hash = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM videos WHERE content_hash IS NOT NULL AND is_repost = 1")
            duplicates_by_hash = cursor.fetchone()['count']
            
            return {
                'total_reposts_detected': total_reposts,
                'videos_with_content_hash': with_hash,
                'duplicates_by_hash': duplicates_by_hash,
                'duplicate_rate': round((total_reposts / with_hash * 100), 2) if with_hash > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats de duplicados: {e}")
            return {'total_reposts_detected': 0, 'videos_with_content_hash': 0, 'duplicates_by_hash': 0, 'duplicate_rate': 0}
        finally:
            conn.close()
    
    def get_duplicate_relations(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene las relaciones de duplicados registradas.
        
        Args:
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de diccionarios con información de relaciones
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT 
                    vr.id,
                    vr.video1_id,
                    vr.video2_id,
                    vr.relation_type,
                    vr.confidence,
                    vr.created_at,
                    v1.title as video1_title,
                    v2.title as video2_title
                FROM video_relations vr
                LEFT JOIN videos v1 ON vr.video1_id = v1.video_id
                LEFT JOIN videos v2 ON vr.video2_id = v2.video_id
                ORDER BY vr.created_at DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'video1_id': row['video1_id'],
                    'video2_id': row['video2_id'],
                    'relation_type': row['relation_type'],
                    'confidence': row['confidence'],
                    'created_at': row['created_at'],
                    'video1_title': row.get('video1_title', 'Unknown'),
                    'video2_title': row.get('video2_title', 'Unknown')
                })
            return results
        except Exception as e:
            logger.error(f"Error obteniendo relaciones de duplicados: {e}")
            return []
        finally:
            conn.close()

    def mark_as_repost(self, video_id: str, duplicate_of: str = None) -> bool:
        """
        Marca un video como repost/duplicado.
        
        Args:
            video_id: ID del video a marcar
            duplicate_of: ID del video original (opcional)
        
        Returns:
            True si se marcó correctamente
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE videos 
                SET is_repost = 1
                WHERE video_id = ?
            """, (video_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error marcando repost: {e}")
            return False
        finally:
            conn.close()

    def add_video_relation(self, video1_id: str, video2_id: str, relation_type: str, confidence: float = 1.0) -> bool:
        """
        Registra una relación entre dos videos (duplicado, similar, etc.).
        
        Args:
            video1_id: ID del primer video
            video2_id: ID del segundo video
            relation_type: Tipo de relación ('exact_duplicate', 'repost', 'similar_topic')
            confidence: Nivel de confianza (0.0-1.0)
        
        Returns:
            True si se insertó correctamente
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video1_id TEXT NOT NULL,
                    video2_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(video1_id, video2_id)
                )
            """)
            conn.commit()
            
            cursor.execute("""
                INSERT OR IGNORE INTO video_relations (video1_id, video2_id, relation_type, confidence)
                VALUES (?, ?, ?, ?)
            """, (video1_id, video2_id, relation_type, confidence))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error añadiendo relación de videos: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== OPERACIONES DE FILTROS POR PALABRAS CLAVE ====================
    
    def save_keyword_filter(self, 
                           include_keywords: List[str], 
                           exclude_keywords: List[str], 
                           mode: str = "OR",
                           enabled: bool = False) -> bool:
        """Guarda la configuración del filtro de palabras clave."""
        import json
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO keyword_filters 
                (id, include_keywords, exclude_keywords, mode, enabled, updated_at)
                VALUES (1, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                json.dumps(include_keywords),
                json.dumps(exclude_keywords),
                mode,
                1 if enabled else 0
            ))
            conn.commit()
            logger.info(f"Filtro guardado: include={include_keywords}, exclude={exclude_keywords}, mode={mode}, enabled={enabled}")
            return True
        except Exception as e:
            logger.error(f"Error guardando filtro: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_keyword_filter(self) -> Optional[Dict]:
        """Obtiene la configuración del filtro de palabras clave."""
        import json
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM keyword_filters WHERE id = 1")
            row = cursor.fetchone()
            
            if row:
                return {
                    "include_keywords": json.loads(row['include_keywords']),
                    "exclude_keywords": json.loads(row['exclude_keywords']),
                    "mode": row['mode'],
                    "enabled": bool(row['enabled']),
                    "total_ignored": row['total_ignored'],
                    "ignored_today": row['ignored_today'],
                    "last_reset_date": row['last_reset_date']
                }
            return None
        except Exception as e:
            logger.error(f"Error obteniendo filtro: {e}")
            return None
        finally:
            conn.close()
    
    def increment_ignored_count(self, count: int = 1) -> bool:
        """Incrementa el contador de videos ignorados por el filtro."""
        from datetime import date
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = date.today().isoformat()
            
            cursor.execute("SELECT last_reset_date FROM keyword_filters WHERE id = 1")
            row = cursor.fetchone()
            
            if row and row['last_reset_date'] != today:
                cursor.execute("""
                    UPDATE keyword_filters 
                    SET total_ignored = total_ignored + ?,
                        ignored_today = ?,
                        last_reset_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (count, count, today))
            else:
                cursor.execute("""
                    UPDATE keyword_filters 
                    SET total_ignored = total_ignored + ?,
                        ignored_today = ignored_today + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (count, count))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error incrementando contador: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_filter_statistics(self) -> Dict:
        """Obtiene estadísticas del filtro de palabras clave."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    SUM(ignored_by_filter) as total_ignored_videos,
                    COUNT(*) as total_videos
                FROM videos
            """)
            row = cursor.fetchone()
            
            return {
                "total_ignored_videos": row['total_ignored_videos'] or 0,
                "total_videos": row['total_videos'] or 0,
                "filter_rate": round((row['total_ignored_videos'] or 0) / max(row['total_videos'], 1) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Error en estadísticas del filtro: {e}")
            return {"total_ignored_videos": 0, "total_videos": 0, "filter_rate": 0}
        finally:
            conn.close()

    def save_scheduler_history(self, task_id: str, task_name: str, task_type: str,
                               status: str, message: str, details: dict = None,
                               started_at: str = None, finished_at: str = None,
                               duration_seconds: float = 0) -> bool:
        """Guarda un resultado de ejecución de tarea en el historial"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO scheduler_history
                (task_id, task_name, task_type, status, message, details, started_at, finished_at, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, task_name, task_type, status, message,
                  json.dumps(details) if details else None,
                  started_at, finished_at, duration_seconds))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error guardando historial del scheduler: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_scheduler_history(self, limit: int = 100, task_id: str = None,
                              status: str = None) -> List[Dict]:
        """Obtiene el historial de ejecuciones del scheduler"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM scheduler_history WHERE 1=1"
            params = []

            if task_id:
                query += " AND task_id = ?"
                params.append(task_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo historial del scheduler: {e}")
            return []
        finally:
            conn.close()

    def get_scheduler_history_today(self) -> Dict:
        """Obtiene estadísticas del historial de hoy"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            today = datetime.now().strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM scheduler_history
                WHERE date(started_at) = ?
                GROUP BY status
            """, (today,))

            results = cursor.fetchall()
            stats = {'completed': 0, 'failed': 0, 'running': 0}

            for row in results:
                if row[0] == 'completed':
                    stats['completed'] = row[1]
                elif row[0] == 'failed':
                    stats['failed'] = row[1]
                elif row[0] == 'running':
                    stats['running'] = row[1]

            return stats
        except Exception as e:
            logger.error(f"Error en estadísticas de hoy: {e}")
            return {'completed': 0, 'failed': 0, 'running': 0}
        finally:
            conn.close()

    def clear_scheduler_history(self, older_than_days: int = 30) -> int:
        """Elimina registros de historial anteriores a X días"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cutoff_date = (datetime.now() - timedelta(days=older_than_days)).strftime('%Y-%m-%d')
            cursor.execute("DELETE FROM scheduler_history WHERE date(started_at) < ?", (cutoff_date,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"Error limpiando historial: {e}")
            return 0
        finally:
            conn.close()

    # ==================== CRUD PERFILES DE FILTROS ====================
    
    def get_all_filter_profiles(self) -> List[Dict]:
        """Obtiene todos los perfiles de filtros."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM filter_profiles ORDER BY is_active DESC, name ASC")
            rows = cursor.fetchall()
            profiles = []
            for row in rows:
                profile = dict(row)
                profile['include_keywords'] = json.loads(profile.get('include_keywords', '[]'))
                profile['exclude_keywords'] = json.loads(profile.get('exclude_keywords', '[]'))
                profiles.append(profile)
            return profiles
        except Exception as e:
            logger.error(f"Error obteniendo perfiles: {e}")
            return []
        finally:
            conn.close()
    
    def get_active_filter_profile(self) -> Optional[Dict]:
        """Obtiene el perfil de filtro activo."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM filter_profiles WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                profile = dict(row)
                profile['include_keywords'] = json.loads(profile.get('include_keywords', '[]'))
                profile['exclude_keywords'] = json.loads(profile.get('exclude_keywords', '[]'))
                return profile
            return None
        except Exception as e:
            logger.error(f"Error obteniendo perfil activo: {e}")
            return None
        finally:
            conn.close()
    
    def create_filter_profile(self, name: str, include_keywords: List[str] = None,
                              exclude_keywords: List[str] = None, mode: str = "OR",
                              enabled: bool = False) -> Optional[int]:
        """Crea un nuevo perfil de filtro."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO filter_profiles (name, include_keywords, exclude_keywords, mode, enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (name, json.dumps(include_keywords or []), json.dumps(exclude_keywords or []), mode, 1 if enabled else 0))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Perfil '{name}' ya existe")
            return None
        except Exception as e:
            logger.error(f"Error creando perfil: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def update_filter_profile(self, profile_id: int, **kwargs) -> bool:
        """Actualiza un perfil de filtro existente."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['name', 'include_keywords', 'exclude_keywords', 'mode', 'enabled']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field in ['include_keywords', 'exclude_keywords']:
                    value = json.dumps(value) if isinstance(value, list) else value
                elif field == 'enabled':
                    value = 1 if value else 0
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(profile_id)
        
        try:
            cursor.execute(f"""
                UPDATE filter_profiles 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error actualizando perfil: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_filter_profile(self, profile_id: int) -> bool:
        """Elimina un perfil de filtro."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # No eliminar si es el único perfil
            cursor.execute("SELECT COUNT(*) FROM filter_profiles")
            count = cursor.fetchone()[0]
            if count <= 1:
                logger.warning("No se puede eliminar el último perfil")
                return False
            
            cursor.execute("DELETE FROM filter_profiles WHERE id = ? AND is_active = 0", (profile_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                logger.warning("No se puede eliminar un perfil activo")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error eliminando perfil: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def set_active_filter_profile(self, profile_id: int) -> bool:
        """Establece un perfil como activo (desactiva los demás)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE filter_profiles SET is_active = 0")
            cursor.execute("UPDATE filter_profiles SET is_active = 1 WHERE id = ?", (profile_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error activando perfil: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def duplicate_filter_profile(self, profile_id: int, new_name: str) -> Optional[int]:
        """Duplica un perfil existente con un nuevo nombre."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM filter_profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self.create_filter_profile(
                name=new_name,
                include_keywords=json.loads(row['include_keywords'] or '[]'),
                exclude_keywords=json.loads(row['exclude_keywords'] or '[]'),
                mode=row['mode'],
                enabled=bool(row['enabled'])
            )
        except Exception as e:
            logger.error(f"Error duplicando perfil: {e}")
            return None
        finally:
            conn.close()
    
    # ==================== FIN CRUD PERFILES DE FILTROS ====================


