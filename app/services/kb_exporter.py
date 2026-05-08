"""
KDP MASTER - Knowledge Base Exporter
================================
Exporta la base de conocimiento (DB SQLite + archivos Markdown) a HTML/PDF.
Modo híbrido: combina entradas de DB con archivos MD estáticos.

Características:
- Detección real de WeasyPrint a nivel de runtime (test de renderizado)
- Fallback automático a HTML si PDF no disponible
- Split por categoría + umbral de tamaño configurable
- Resolución de assets locales
- UTF-8 completo vía font-family
- Timeout + cancelación para PDF
- Chequeo de espacio en disco
- Callbacks thread-safe
"""

import os
import re
import sys
import json
import hashlib
import sqlite3
import shutil
import threading
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, field
from queue import Queue

logger = logging.getLogger(__name__)

from app.core.constants import (
    EXPORT_MAX_FILE_SIZE_MB,
    EXPORT_MAX_TOTAL_SIZE_MB,
    EXPORT_TIMEOUT_SECONDS,
    EXPORT_IMAGE_SIZE_ESTIMATE_MB,
    EXPORT_SIZE_MARGIN
)


@dataclass
class ExportEntry:
    """Representa una entrada para exportar."""
    title: str
    category: str
    source: str
    content: str
    timestamp: Optional[str]
    content_hash: str
    
    @staticmethod
    def from_markdown(file_path: Path, category: str = None) -> 'ExportEntry':
        """Crea entrada desde archivo markdown."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            content = ""
            
        title = file_path.stem.replace('_', ' ').replace('-', ' ')
        
        if category is None:
            category = file_path.parent.name.capitalize()
            
        source = f"file://{file_path.name}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return ExportEntry(title, category, source, content, timestamp, content_hash)


@dataclass  
class ExportResult:
    """Resultado de una exportación."""
    success: bool
    output_path: str = None
    format: str = None
    entries_count: int = 0
    categories_count: int = 0
    file_size_bytes: int = 0
    content_hash: str = None
    warnings: List[str] = field(default_factory=list)
    error: str = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class ExportProgress:
    """Información de progreso para callbacks."""
    status: str
    current: int
    total: int
    message: str


class KBExporter:
    """Motor de exportación híbrido: SQLite + Markdown."""
    
    def __init__(self, db_path: str = None, kb_dir: str = None, output_dir: str = None,
                 ui_queue: Queue = None, progress_callback: Callable = None):
        """Inicializa el exporter."""
        if db_path is None:
            db_path = self._get_default_db_path()
        if kb_dir is None:
            kb_dir = self._get_default_kb_dir()
        if output_dir is None:
            output_dir = self._get_default_output_dir()
            
        self.db_path = db_path
        self.kb_dir = Path(kb_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ui_queue = ui_queue
        self.progress_callback = progress_callback
        self._cancel_requested = False
        self._lock = threading.Lock()
        
        self._weasyprint_ready = None
        self._categories_map = {
            "manuals": "Manuales",
            "playbooks": "Playbooks",
            ".": "General"
        }
    
    def _get_default_db_path(self) -> str:
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "knowledge" / "knowledge_base.db")
    
    def _get_default_kb_dir(self) -> str:
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "knowledge")
    
    def _get_default_output_dir(self) -> str:
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "knowledge" / "exports")
    
    def request_cancel(self):
        """Solicita cancelación de la exportación."""
        with self._lock:
            self._cancel_requested = True
    
    def _emit_progress(self, status: str, current: int, total: int, message: str):
        """Emite progreso via callback o queue (thread-safe)."""
        progress = ExportProgress(status, current, total, message)
        
        if self.ui_queue:
            self.ui_queue.put(("export_progress", progress))
        
        if self.progress_callback:
            try:
                self.progress_callback(current, total, message, status)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def _check_weasyprint_ready(self) -> bool:
        """Verifica si WeasyPrint está instalado Y funcional."""
        if self._weasyprint_ready is not None:
            return self._weasyprint_ready
        
        try:
            from weasyprint import HTML
            HTML(string="<p>test</p>").write_pdf()
            self._weasyprint_ready = True
            logger.info("WeasyPrint verificado y funcional")
            return True
        except ImportError:
            logger.warning("WeasyPrint no instalado")
            self._weasyprint_ready = False
            return False
        except Exception as e:
            logger.warning(f"WeasyPrint instalado pero no funcional: {e}")
            self._weasyprint_ready = False
            return False
    
    def _check_disk_space(self, estimated_bytes: int) -> bool:
        """Verifica espacio en disco disponible."""
        try:
            available = shutil.disk_usage(self.output_dir).free
            required = int(estimated_bytes * EXPORT_SIZE_MARGIN)
            return available >= required
        except Exception as e:
            logger.warning(f"Error verificando espacio: {e}")
            return True
    
    def _estimate_size(self, entries: List[ExportEntry]) -> int:
        """Estima tamaño en bytes basado en heurística."""
        total_bytes = 0
        image_count = 0
        
        for entry in entries:
            total_bytes += len(entry.content.encode('utf-8'))
            images_in_content = len(re.findall(r'!\[.*?\]\(.*?\)', entry.content))
            image_count += images_in_content
        
        estimated = total_bytes + (image_count * EXPORT_IMAGE_SIZE_ESTIMATE_MB * 1024 * 1024)
        return int(estimated)
    
    def _resolve_assets(self, content: str, embed_images: bool = False) -> Tuple[str, List[Path]]:
        """Resuelve assets (imágenes) para el contenido."""
        copied_assets = []
        resolved_content = content
        
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def replace_image(match):
            alt_text = match.group(1)
            path = match.group(2)
            
            if path.startswith(('http://', 'https://')):
                if embed_images:
                    return match.group(0)
                return f'<a href="{path}">{alt_text}</a>'
            
            asset_path = self.kb_dir / path
            if asset_path.exists():
                if embed_images:
                    try:
                        with open(asset_path, 'rb') as f:
                            data = base64.b64encode(f.read()).decode()
                            ext = asset_path.suffix.lower()
                            mime = f'image/{ext[1:]}' if ext else 'image/png'
                            return f'<img src="data:{mime};base64,{data}" alt="{alt_text}">'
                    except Exception:
                        return match.group(0)
                else:
                    copied_assets.append(asset_path)
                    return match.group(0)
            return match.group(0)
        
        resolved_content = re.sub(image_pattern, replace_image, content)
        return resolved_content, copied_assets
    
    def _split_by_category_size(self, grouped: Dict[str, List[ExportEntry]]) -> Dict[str, List[ExportEntry]]:
        """Divide categorías que excedan el umbral de tamaño."""
        max_bytes = EXPORT_MAX_FILE_SIZE_MB * 1024 * 1024
        result = {}
        
        for category, entries in grouped.items():
            combined = '\n'.join(e.content for e in entries)
            size = len(combined.encode('utf-8'))
            
            if size <= max_bytes:
                result[category] = entries
            else:
                sub_parts = []
                current_part = []
                current_size = 0
                
                for entry in entries:
                    entry_size = len(entry.content.encode('utf-8'))
                    if current_size + entry_size > max_bytes and current_part:
                        sub_parts.append(current_part)
                        current_part = []
                        current_size = 0
                    current_part.append(entry)
                    current_size += entry_size
                
                if current_part:
                    sub_parts.append(current_part)
                
                for i, part in enumerate(sub_parts):
                    cat_name = category if i == 0 else f"{category} (Parte {i+1})"
                    result[cat_name] = part
                
                logger.info(f"Categoría '{category}' dividida en {len(sub_parts)} partes")
        
        return result
    
    def db_has_entries(self) -> bool:
        """Verifica si la DB tiene entradas."""
        if not Path(self.db_path).exists():
            return False
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            logger.warning(f"Error checking DB: {e}")
            return False
    
    def fetch_from_database(self) -> List[ExportEntry]:
        """Extrae entradas desde SQLite."""
        entries = []
        if not Path(self.db_path).exists():
            return entries
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, category, source, content, timestamp
                FROM knowledge_entries
                ORDER BY timestamp DESC
            """)
            for row in cursor.fetchall():
                content = row['content'] or ''
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                title = self._extract_title_from_content(content)
                category = row['category'] or 'General'
                entries.append(ExportEntry(
                    title=title,
                    category=category,
                    source=row['source'] or 'Database',
                    content=content,
                    timestamp=row['timestamp'],
                    content_hash=content_hash
                ))
            conn.close()
            logger.info(f"Fetched {len(entries)} entries from database")
        except Exception as e:
            logger.error(f"Error fetching from DB: {e}")
            
        return entries
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extrae título desde el contenido."""
        if not content:
            return "Sin título"
        first_line = content.strip().split('\n')[0]
        title = re.sub(r'^#+\s*', '', first_line)
        title = title.strip()[:100]
        return title if title else "Sin título"
    
    def fetch_from_markdown(self, categories_map: Dict[str, str] = None) -> List[ExportEntry]:
        """Extrae entradas desde archivos Markdown."""
        entries = []
        
        if categories_map is None:
            categories_map = self._categories_map
            
        if not self.kb_dir.exists():
            logger.warning(f"KB directory does not exist: {self.kb_dir}")
            return entries
        
        md_files = []
        for ext in ['*.md', '*.MD', '*.txt']:
            md_files.extend(self.kb_dir.rglob(ext))
        
        for md_file in md_files:
            if md_file.name.startswith('.'):
                continue
                
            parent_dir = md_file.parent.name
            category = categories_map.get(parent_dir, categories_map.get('.', 'General'))
            
            try:
                content = md_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            if len(content.strip()) < 50:
                continue
            
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            title = md_file.stem.replace('_', ' ').replace('-', ' ')
            source = f"file://{md_file.relative_to(self.kb_dir)}"
            
            entries.append(ExportEntry(
                title=title,
                category=category,
                source=source,
                content=content,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                content_hash=content_hash
            ))
            
        logger.info(f"Fetched {len(entries)} entries from markdown files")
        return entries
    
    def collect_all_content(self, limit: int = None, embed_images: bool = False) -> List[ExportEntry]:
        """Recolecta contenido de DB + MD (modo híbrido)."""
        self._emit_progress("collecting", 0, 100, "Recolectando contenido...")
        
        entries = []
        
        if self.db_has_entries():
            entries.extend(self.fetch_from_database())
        
        entries.extend(self.fetch_from_markdown())
        
        entries = self._apply_title_normalization(entries)
        
        entries = self.deduplicate(entries)
        
        if limit and len(entries) > limit:
            logger.info(f"Limited from {len(entries)} to {limit} entries")
            entries = entries[:limit]
        
        logger.info(f"Total entries after collection: {len(entries)}")
        return entries
    
    # ============================================================
    # MÓDULO 1: DEDUPLICACIÓN ROBUSTA
    # Elimina duplicados exactos usando solo content_hash
    # ============================================================
    def deduplicate(self, entries: List[ExportEntry]) -> List[ExportEntry]:
        """Elimina duplicados exactos por content_hash único.
        
        Fundamentos de programación aplicados:
        - Separación de responsabilidades: hashing separado del filtro
        - Inmutabilidad: no modifica la lista original
        - Trazabilidad: log de duplicados para auditoría
        """
        seen_hashes = {}
        unique = []
        duplicates_log = []
        
        for entry in entries:
            if entry.content_hash not in seen_hashes:
                seen_hashes[entry.content_hash] = entry
                unique.append(entry)
            else:
                duplicates_log.append(entry.title[:50])
        
        if duplicates_log:
            logger.warning(f"Duplicados encontrados: {len(duplicates_log)}")
            for dup in duplicates_log[:5]:
                logger.debug(f"  - Dúplicate: {dup}...")
        
        return unique
    
    # -----------------------------------------------------------
    # FIN MÓDULO 1
    # -----------------------------------------------------------
    
    # ============================================================
    # MÓDULO 2: NORMALIZACIÓN DE TÍTULOS
    # Estandariza títulos para evitar duplicados por formato
    # ============================================================
    def normalize_title(self, title: str) -> str:
        """Normaliza títulos para evitar duplicados por variaciones de formato.
        
        Fundamentos de programación:
        - Funciones puras: misma entrada → misma salida
        - Legibilidad: código auto-documentado
        - Principio YAGNI: solo normalizaciones necesarias
        """
        if not title:
            return "Sin título"
        
        normalized = ' '.join(title.split())
        
        normalized = re.sub(r'^ROL\s+SOE\s+#\d+:\s*', 'ROL SOE: ', normalized, flags=re.IGNORECASE)
        
        normalized = re.sub(r'^Objetivo:\s*', 'OBJETIVO: ', normalized, flags=re.IGNORECASE)
        
        normalized = re.sub(r'^📄\s*ÍNDICE\s+CURRICULAR\s*-\s*', 'ÍNDICE CURRICULAR: ', normalized)
        
        normalized = re.sub(r'^INDICE\s+CURRICULAR\s*-\s*', 'ÍNDICE CURRICULAR: ', normalized, flags=re.IGNORECASE)
        
        normalized = re.sub(r'^MATRIZ\s+MAESTRA', 'MATRIZ MAESTRA', normalized, flags=re.IGNORECASE)
        
        return normalized.strip()[:100]
    
    def _apply_title_normalization(self, entries: List[ExportEntry]) -> List[ExportEntry]:
        """Aplica normalización a todos los títulos de entrada."""
        normalized_entries = []
        for entry in entries:
            entry.title = self.normalize_title(entry.title)
            normalized_entries.append(entry)
        return normalized_entries
    
    # -----------------------------------------------------------
    # FIN MÓDULO 2
    # -----------------------------------------------------------
    
    def group_by_category(self, entries: List[ExportEntry]) -> Dict[str, List[ExportEntry]]:
        """Agrupa entradas por categoría."""
        grouped = {}
        for entry in entries:
            cat = entry.category or 'General'
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(entry)
        return grouped
    
    def generate_toc(self, grouped: Dict[str, List[ExportEntry]]) -> List[Tuple[str, str, int]]:
        """Genera tabla de contenidos."""
        toc = []
        for category, entry_list in grouped.items():
            anchor = re.sub(r'[^\w\- ]', '', category.lower()).replace(' ', '-')
            toc.append((category, anchor, len(entry_list)))
        return toc
    
    def generate_html(self, entries: List[ExportEntry], grouped: Dict[str, List[ExportEntry]],
                 embed_images: bool = False) -> str:
        """Genera HTML con estilos profesionales y UTF-8 completo."""
        base_font = """@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');"""
        
        toc = self.generate_toc(grouped)
        
        toc_html = '<nav class="toc"><h2>Índice</h2><ul>'
        for category, anchor, count in toc:
            toc_html += f'<li><a href="#{anchor}">{category}</a> ({count})</li>'
        toc_html += '</ul></nav>'
        
        sections_html = ''
        for category, entry_list in grouped.items():
            anchor = re.sub(r'[^\w\- ]', '', category.lower()).replace(' ', '-')
            sections_html += f'<section id="{anchor}"><h2>{category}</h2>'
            sections_html += f'<p class="meta">{len(entry_list)} entradas</p>'
            
            for entry in entry_list:
                if self._cancel_requested:
                    return ""
                
                title = entry.title[:100]
                content = entry.content
                
                if not embed_images:
                    content, _ = self._resolve_assets(content, embed_images=False)
                
                content = self._render_content_html(content)
                sections_html += f'''
                <article>
                    <h3>{title}</h3>
                    <p class="entry-meta">Fuente: {entry.source} | Fecha: {entry.timestamp}</p>
                    <div class="content">{content}</div>
                </article>
                '''
            sections_html += '</section>'
        
        html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Base de Conocimiento KDP Master</title>
    <style>
        {base_font}
        :root {{
            --bg-color: #f5f5f5;
            --text-color: #333;
            --header-bg: #2c3e50;
            --header-text: #fff;
            --link-color: #0066cc;
            --toc-bg: #fff;
            --border-color: #ddd;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #1a1a1a;
                --text-color: #e0e0e0;
                --header-bg: #1a1a1a;
                --header-text: #e0e0e0;
                --link-color: #66b3ff;
                --toc-bg: #2a2a2a;
                --border-color: #444;
            }}
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Noto Sans', 'Segoe UI', Tahoma, sans-serif; line-height: 1.6; 
              background: var(--bg-color); color: var(--text-color); max-width: 1000px; 
              margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: var(--header-bg); border-bottom: 1px solid var(--border-color); 
                      padding-bottom: 8px; margin: 1em 0 0.5em; }}
        h1 {{ font-size: 1.8em; border-bottom: 2px solid var(--header-bg); }}
        h2 {{ font-size: 1.4em; }}
        h3 {{ font-size: 1.1em; border-bottom: none; color: var(--text-color); }}
        .toc {{ background: var(--toc-bg); padding: 15px; border-radius: 8px; 
               margin-bottom: 20px; position: sticky; top: 10px; z-index: 100;
               box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .toc h2 {{ font-size: 1.1em; margin-top: 0; }}
        .toc ul {{ list-style: none; padding-left: 15px; }}
        .toc li {{ margin: 5px 0; }}
        a {{ color: var(--link-color); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        section {{ background: var(--toc-bg); padding: 20px; margin: 10px 0; 
                 border-radius: 8px; }}
        article {{ margin: 20px 0; padding: 15px; border-left: 3px solid var(--link-color); 
                  background: rgba(0,0,0,0.02); }}
        .meta {{ font-size: 0.85em; color: #666; margin-bottom: 10px; }}
        .entry-meta {{ font-size: 0.8em; color: #888; margin-bottom: 10px; }}
        .content {{ margin-top: 10px; }}
        .content p {{ margin: 0.5em 0; }}
        .content img {{ max-width: 100%; height: auto; }}
        .content code {{ background: #eee; padding: 2px 4px; border-radius: 3px; }}
        .content pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; 
                       overflow-x: auto; }}
        .content table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        .content th, .content td {{ border: 1px solid var(--border-color); padding: 8px; 
                                     text-align: left; }}
        .content th {{ background: #f5f5f5; }}
        .header-info {{ text-align: center; margin-bottom: 20px; padding-bottom: 20px; 
                       border-bottom: 2px solid var(--border-color); }}
        .header-info h1 {{ border: none; margin: 0; }}
        .header-info p {{ font-size: 0.9em; color: #666; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; 
                   border-top: 1px solid var(--border-color); font-size: 0.85em; color: #888; }}
        .dark-toggle {{ position: fixed; top: 10px; right: 10px; padding: 5px 10px; 
                        background: var(--header-bg); color: var(--header-text); 
                        border: none; border-radius: 4px; cursor: pointer; }}
    </style>
</head>
<body>
    <button class="dark-toggle" onclick="toggleDark()">🌓</button>
    <header class="header-info">
        <h1>Base de Conocimiento KDP Master</h1>
        <p>Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Entradas: {len(entries)} | Categorías: {len(grouped)}</p>
    </header>
    {toc_html}
    <main>
        {sections_html}
    </main>
    <footer class="footer">
        <p>Generado por KDP Master Suite | v2.7.0</p>
    </footer>
    <script>
        function toggleDark() {{
            document.body.classList.toggle('dark');
        }}
    </script>
</body>
</html>'''
        return html
    
    def _render_content_html(self, content: str) -> str:
        """Renderiza contenido Markdown a HTML básico."""
        html = content
        
        html = re.sub(r'^### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        
        lines = html.split('\n')
        processed = []
        in_code = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code = not in_code
                processed.append('</code>' if in_code else '<code>')
            elif in_code:
                processed.append(line)
            elif line.strip().startswith('- '):
                processed.append(f'<li>{line.strip()[2:]}</li>')
            elif line.strip():
                processed.append(f'<p>{line}</p>')
            else:
                processed.append('')
        
        html = '\n'.join(processed)
        html = re.sub(r'\n<li>', r'\n<ul><li>', html)
        html = re.sub(r'</li>\n(?!<li>)', '</li></ul>', html)
        
        return html
    
    def _to_pdf_with_timeout(self, html_content: str, output_path: str) -> ExportResult:
        """Convierte HTML a PDF con timeout."""
        def render_pdf():
            try:
                for dll_path in [r"C:\msys64\mingw64\bin", r"C:\Program Files\GTK3-Runtime Win64\bin"]:
                    if os.path.exists(dll_path):
                        try:
                            os.add_dll_directory(dll_path)
                        except Exception:
                            pass
                
                from weasyprint import HTML
                HTML(string=html_content).write_pdf(output_path)
                return True
            except Exception as e:
                logger.error(f"PDF render error: {e}")
                return False
        
        render_thread = threading.Thread(target=render_pdf)
        render_thread.daemon = True
        render_thread.start()
        render_thread.join(timeout=EXPORT_TIMEOUT_SECONDS)
        
        if render_thread.is_alive():
            return ExportResult(success=False, error=f"Timeout ({EXPORT_TIMEOUT_SECONDS}s) excedido")
        
        if os.path.exists(output_path):
            return ExportResult(
                success=True,
                output_path=output_path,
                format='pdf',
                file_size_bytes=os.path.getsize(output_path)
            )
        
        return ExportResult(success=False, error="PDF no generado")
    
    def export(self, format: str = 'html', generate_pdf: bool = False, 
             embed_images: bool = False, limit: int = None) -> ExportResult:
        """Ejecuta la exportación completa."""
        warnings = []
        
        self._cancel_requested = False
        
        self._emit_progress("starting", 0, 100, "Iniciando exportación...")
        
        entries = self.collect_all_content(limit=limit, embed_images=embed_images)
        if not entries:
            return ExportResult(success=False, error="No hay contenido para exportar")
        
        self._emit_progress("grouping", 25, 100, "Agrupando por categoría...")
        
        grouped = self.group_by_category(entries)
        
        estimated_size = self._estimate_size(entries)
        
        if not self._check_disk_space(estimated_size):
            return ExportResult(
                success=False,
                error=f"Espacio insuficiente en disco. Se requiere ~{estimated_size/(1024*1024):.1f}MB"
            )
        
        if estimated_size > EXPORT_MAX_FILE_SIZE_MB * 1024 * 1024:
            self._emit_progress("splitting", 40, 100, "Dividiendo por tamaño...")
            grouped = self._split_by_category_size(grouped)
            warnings.append("Contenido dividido por categorías por tamaño")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self._emit_progress("rendering", 50, 100, "Generando HTML...")
        
        total = sum(len(v) for v in grouped.values())
        current = 0
        
        output_files = []
        
        for category, cat_entries in grouped.items():
            if self._cancel_requested:
                return ExportResult(success=False, error="Exportación cancelada por usuario")
            
            cat_grouped = {category: cat_entries}
            cat_html = self.generate_html(cat_entries, cat_grouped, embed_images=embed_images)
            
            safe_name = re.sub(r'[^\w\- ]', '', category.lower()).replace(' ', '_')
            cat_path = self.output_dir / f"KB_{safe_name}_{timestamp}.html"
            cat_path.write_text(cat_html, encoding='utf-8')
            output_files.append(cat_path)
            
            current += len(cat_entries)
            self._emit_progress("rendering", 50 + int(current/total*30), 100, 
                              f"Generado: {category}")
        
        output_path = self.output_dir / f"KB_Export_{timestamp}.html"
        combined_html = self.generate_html(entries, grouped, embed_images=embed_images)
        output_path.write_text(combined_html, encoding='utf-8')
        
        file_size = output_path.stat().st_size
        self._emit_progress("rendering", 80, 100, "HTML generado")
        
        if not generate_pdf:
            self._emit_progress("done", 100, 100, "Exportación completada")
            return ExportResult(
                success=True,
                output_path=str(output_path),
                format='html',
                entries_count=len(entries),
                categories_count=len(grouped),
                file_size_bytes=file_size,
                content_hash=hashlib.sha256(combined_html.encode()).hexdigest()[:16],
                warnings=warnings
            )
        
        if not self._check_weasyprint_ready():
            warnings.append("WeasyPrint no disponible, exportando solo HTML")
            self._emit_progress("done", 100, 100, "Exportación completada (HTML)")
            return ExportResult(
                success=True,
                output_path=str(output_path),
                format='html',
                entries_count=len(entries),
                categories_count=len(grouped),
                file_size_bytes=file_size,
                content_hash=hashlib.sha256(combined_html.encode()).hexdigest()[:16],
                warnings=warnings
            )
        
        self._emit_progress("pdf", 85, 100, "Convirtiendo a PDF...")
        
        pdf_path = self.output_dir / f"KB_Export_{timestamp}.pdf"
        
        result = self._to_pdf_with_timeout(combined_html, str(pdf_path))
        
        if result.success:
            self._emit_progress("done", 100, 100, "Exportación completada")
            return ExportResult(
                success=True,
                output_path=str(pdf_path),
                format='pdf',
                entries_count=len(entries),
                categories_count=len(grouped),
                file_size_bytes=result.file_size_bytes,
                content_hash=hashlib.sha256(combined_html.encode()).hexdigest()[:16],
                warnings=warnings
            )
        else:
            warnings.append(f"PDF no disponible: {result.error}")
            self._emit_progress("done", 100, 100, "Exportación completada (HTML)")
            return ExportResult(
                success=True,
                output_path=str(output_path),
                format='html',
                entries_count=len(entries),
                categories_count=len(grouped),
                file_size_bytes=file_size,
                content_hash=hashlib.sha256(combined_html.encode()).hexdigest()[:16],
                warnings=warnings
            )


def export_kb(format: str = 'html', db_path: str = None, kb_dir: str = None, 
             limit: int = 1000, generate_pdf: bool = False) -> ExportResult:
    """Función de conveniencia para exportar.
    
    Args:
        format: 'html' o 'pdf' (deprecated, use generate_pdf)
        db_path: Ruta a la DB (opcional)
        kb_dir: Directorio KB (opcional)
        limit: Límite de entradas (None para todas, por defecto 1000 para rendimiento)
        generate_pdf: Si True, intenta generar PDF con fallback a HTML
    """
    exporter = KBExporter(db_path, kb_dir)
    return exporter.export(format, generate_pdf=generate_pdf, limit=limit)


if __name__ == "__main__":
    result = export_kb('html', limit=500, generate_pdf=False)
    if result.success:
        print(f"✓ Exportado: {result.output_path}")
        print(f"  Entradas: {result.entries_count}")
        print(f"  Categorías: {result.categories_count}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
    else:
        print(f"✗ Error: {result.error}")