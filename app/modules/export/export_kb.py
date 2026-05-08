import os
import sys
from pathlib import Path
import zipfile
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
import shutil
import re
import json
from app.modules.export.convert_to_pdf import ExportConfig, convert_md_to_html, convert_md_to_pdf_with_styles, generate_toc, render_toc_html, rewrite_internal_links, resolve_images, ExportResult, get_weasyprint
import markdown2
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

MAX_CONTENT_SIZE = 5000000

# --- INICIO FUNCIONALIDAD US-PDF-AUTO: DETECCIÓN DINÁMICA DE GTK3 v3.4.7 ---
def check_pdf_capability():
    """Verifica algorítmicamente si el entorno soporta exportación PDF."""
    try:
        from weasyprint import HTML
        return False # Si llega aquí, GTK3 está presente
    except:
        return True

SKIP_PDF = check_pdf_capability()
# --- FIN FUNCIONALIDAD ---


class KBExporter:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            if getattr(sys, 'frozen', False):
                self.base_dir = Path(sys.executable).parent
            else:
                self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        
        self.manuals_dir = self.base_dir / "knowledge" / "manuals"
        self.output_dir = self.base_dir / "knowledge" / "exports"
        self.assets_dir = self.output_dir / "assets"
        self.manuals_output_dir = self.output_dir / "manuals"
        # --- INICIO FUNCIONALIDAD US-E-CONFIG: CONFIGURACIÓN ELITE v3.4.7 ---
        self.export_settings = {
            "format": "html",
            "zip_output": True,
            "incremental": False,
            "categories": [],
            "date_filter": None, # 'week', 'month', or None
            "template": "complete",
            "auto_sched": "none" # daily, weekly
        }
        # --- FIN FUNCIONALIDAD ---
        
        self.config = ExportConfig()
        self.config.ASSETS_DIR = str(self.assets_dir)
        self.config.COPY_IMAGES = True

    # --- INICIO FUNCIONALIDAD US-E-FILTER: FILTRADO PRE-EXPORT v3.4.6 ---
    def _get_sqlite_entries(self, categories: List[str] = None, since_days: int = None) -> str:
        """Extrae entradas de la base de datos SQLite para incluir en la exportación."""
        db_path = self.base_dir / "knowledge" / "knowledge_base.db"
        if not db_path.exists():
            return ""
        
        md_content = "\n\n# 🗄️ Entradas de Base de Datos (Persistencia)\n\n"
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """SELECT category, source, content, timestamp,
                       metadata_json, keywords, duration_seconds, is_short,
                       view_count, like_count FROM knowledge_entries WHERE 1=1"""
            params = []
            
            if categories:
                query += f" AND category IN ({','.join(['?' for _ in categories])})"
                params.extend(categories)
            
            if since_days:
                date_limit = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d %H:%M")
                query += " AND timestamp >= ?"
                params.append(date_limit)
                
            query += " ORDER BY timestamp DESC"
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            if not rows:
                return ""
                
            for row in rows:
                md_content += f"## 🟢 MÓDULO: {row['category']}\n"
                md_content += f"- **FUENTE:** {row['source']}\n"
                md_content += f"- **FECHA:** {row['timestamp']}\n\n"
                
                # US-010-EXP: Incluir metadatos enriquecidos en el reporte
                if row['duration_seconds']:
                    minutes = row['duration_seconds'] // 60
                    seconds = row['duration_seconds'] % 60
                    md_content += f"- **DURACIÓN:** {minutes:02d}:{seconds:02d}\n"
                if row['view_count']:
                    md_content += f"- **VISTAS:** {row['view_count']:,}\n"
                if row['like_count']:
                    md_content += f"- **LIKES:** {row['like_count']:,}\n"
                if row['is_short'] is not None:
                    md_content += f"- **SHORTS:** {'Sí' if row['is_short'] else 'No'}\n"
                if row['keywords']:
                    md_content += f"- **KEYWORDS:** {', '.join(json.loads(row['keywords']))}\n"
                
                md_content += f"{row['content']}\n\n---\n\n"
            
            conn.close()
            return md_content
        except Exception as e:
            logger.error(f"Error extrayendo datos SQLite: {e}")
            return f"\n\n> ⚠️ Error al extraer datos de SQLite: {e}\n\n"
    # --- FIN FUNCIONALIDAD US-E-FILTER ---
        
    def get_markdown_files(self) -> List[Path]:
        md_files = []
        seen_names = set()
        
        if self.manuals_dir.exists():
            for ext in ['.md', '.MD', '.markdown']:
                for f in self.manuals_dir.glob(f"*{ext}"):
                    # Deduplicar por nombre normalizado
                    name = f.name.lower().replace("_", "").replace("-", "")
                    if name not in seen_names:
                        seen_names.add(name)
                        md_files.append(f)
        
        return sorted(md_files, key=lambda x: x.name)
    
    def normalize_title(self, title: str) -> str:
        """Normaliza título para evitar duplicados y mostrar correctamente."""
        # Remover emojis y caracteres especiales
        title = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑüÜ-]', '', title)
        # Normalizar espacios
        title = re.sub(r'\s+', ' ', title).strip()
        # Remover prefijos comunes
        title = re.sub(r'^(MANUAL|MATRIZ|KB)\s*[-:]?\s*', '', title, flags=re.IGNORECASE)
        return title.title()
    
    def get_title_from_content(self, md_path: Path) -> str:
        try:
            content = md_path.read_text(encoding='utf-8', errors='ignore')
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                raw_title = match.group(1).strip()
                return self.normalize_title(raw_title)
        except:
            pass
        return self.normalize_title(md_path.stem.replace("_", " ").replace("-", " "))
    
    def export_single(self, md_path: Path, force: bool = False) -> Dict:
        logger.info(f"Exportando: {md_path.name}")
        
        result = {"file": md_path.name, "html": None, "pdf": None, "warnings": [], "error": None}
        
        manuals_dir = self.manuals_output_dir / md_path.stem
        html_path = manuals_dir / f"{md_path.stem}.html"

        # --- INICIO FUNCIONALIDAD US-037-INC: LÓGICA INCREMENTAL ---
        if not force and html_path.exists():
            if html_path.stat().st_mtime > md_path.stat().st_mtime:
                logger.info(f"  ⏭️ Saltando (Incremental): {md_path.name} no ha cambiado.")
                result["html"] = str(html_path)
                return result
        # --- FIN FUNCIONALIDAD ---
        
        try:
            html_content, toc_entries, warnings = convert_md_to_html(md_path, self.config)
            result["warnings"] = warnings
            
            manuals_dir = self.manuals_output_dir / md_path.stem
            manuals_dir.mkdir(parents=True, exist_ok=True)
            
            html_path = manuals_dir / f"{md_path.stem}.html"
            html_path.write_text(html_content, encoding='utf-8')
            result["html"] = str(html_path)
            
            if not SKIP_PDF:
                from app.modules.export.convert_to_pdf import get_weasyprint
                HTML = get_weasyprint()
                if HTML is not None:
                    pdf_result = convert_md_to_pdf_with_styles(
                        str(md_path), 
                        str(manuals_dir / f"{md_path.stem}.pdf"),
                        self.get_title_from_content(md_path),
                        self.config
                    )
                    result["pdf"] = pdf_result.path if pdf_result.success else None
                    result["warnings"].extend(pdf_result.warnings)
                    if not pdf_result.success:
                        result["error"] = pdf_result.error
                else:
                    result["warnings"].append("PDF no generado: WeasyPrint no disponible")
            else:
                result["warnings"].append("PDF omitido (SKIP_PDF=True)")
                
        except Exception as e:
            logger.error(f"Error exportando {md_path.name}: {e}")
            result["error"] = str(e)
        
        return result
    
    def generate_index_html(self, exports: List[Dict]) -> str:
        # Deduplicar por nombre de archivo
        seen_files = set()
        unique_exports = []
        
        for exp in exports:
            file_name = exp["file"].lower()
            if file_name not in seen_files:
                seen_files.add(file_name)
                unique_exports.append(exp)
        
        # Ordenar alfabéticamente
        unique_exports.sort(key=lambda x: x["file"])
        
        manual_links = []
        
        for exp in unique_exports:
            name = exp["file"].replace(".md", "").replace(".MD", "")
            title = self.get_title_from_content(self.manuals_dir / exp["file"])
            
            pdf_link = f'<a href="manuals/{name}/{name}.pdf" target="_blank">PDF</a>' if exp["pdf"] else "—"
            html_link = f'<a href="manuals/{name}/{name}.html" target="_blank">HTML</a>' if exp["html"] else "—"
            status = "✓" if exp["pdf"] else ("⚠️" if exp["html"] else "✗")
            
            manual_links.append(f'''
                <tr>
                    <td>{status}</td>
                    <td><strong>{title}</strong></td>
                    <td>{pdf_link}</td>
                    <td>{html_link}</td>
                </tr>
            ''')
        
        index_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KDP Master - Base de Conocimiento</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .subtitle {{ font-size: 1.1em; opacity: 0.9; }}
        .actions {{ margin: 20px 0; display: flex; gap: 15px; flex-wrap: wrap; }}
        .btn {{ display: inline-block; padding: 12px 25px; background: #3498db; color: white; text-decoration: none; border-radius: 6px; font-weight: 500; transition: background 0.3s; }}
        .btn:hover {{ background: #2980b9; }}
        .btn.secondary {{ background: #27ae60; }}
        .btn.secondary:hover {{ background: #219a52; }}
        .search-box {{ flex: 1; min-width: 250px; }}
        .search-box input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; }}
        table {{ width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 15px; text-align: left; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        .status-ok {{ color: #27ae60; font-weight: bold; }}
        .status-warn {{ color: #f39c12; }}
        .status-err {{ color: #e74c3c; }}
        footer {{ text-align: center; padding: 20px; color: #666; margin-top: 30px; }}
        @media (max-width: 600px) {{ th, td {{ font-size: 0.9em; padding: 8px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Base de Conocimiento KDP Master</h1>
            <p class="subtitle">Exportación: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <div class="actions">
                <a href="KB_Consolidado.html" class="btn">📖 Ver Consolidado HTML</a>
                <a href="KB_Consolidado.pdf" class="btn secondary">📄 Descargar Consolidado PDF</a>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="🔍 Buscar manual..." oninput="filterTable()">
                </div>
            </div>
        </header>
        
        <table id="manualTable">
            <thead>
                <tr>
                    <th style="width: 50px;">Estado</th>
                    <th>Manual</th>
                    <th style="width: 80px;">PDF</th>
                    <th style="width: 80px;">HTML</th>
                </tr>
            </thead>
            <tbody>
                {''.join(manual_links)}
            </tbody>
        </table>
        
        <footer>
            <p>KDP Master v3.4 | Total: {len(exports)} manuales</p>
        </footer>
    </div>
    
    <script>
    function filterTable() {{
        const input = document.getElementById('searchInput');
        const filter = input.value.toLowerCase();
        const table = document.getElementById('manualTable');
        const rows = table.getElementsByTagName('tr');
        
        for (let i = 1; i < rows.length; i++) {{
            const title = rows[i].getElementsByTagName('td')[1];
            if (title) {{
                rows[i].style.display = title.textContent.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
            }}
        }}
    }}
    </script>
</body>
</html>'''
        
        return index_html
    
    def generate_consolidated_html(self, exports: List[Dict]) -> str:
        sections = []
        
        for exp in exports:
            md_path = self.manuals_dir / exp["file"]
            if not md_path.exists():
                continue
            
            title = self.get_title_from_content(md_path)
            content = md_path.read_text(encoding='utf-8', errors='ignore')
            
            if len(content) > MAX_CONTENT_SIZE:
                content = content[:MAX_CONTENT_SIZE]
            
            content = rewrite_internal_links(content, str(md_path), "html")
            
            content, img_warnings = resolve_images(content, md_path, self.assets_dir, self.config.COPY_IMAGES)
            
            html_body = markdown2.markdown(content, extras=["tables", "fenced-code-blocks", "strikeout"])
            
            sections.append(f'''
            <section id="{md_path.stem}">
                <h1>{title}</h1>
                <div class="manual-content">
                    {html_body}
                </div>
            </section>
            ''')

        # --- INICIO FUNCIONALIDAD: INCLUIR DATOS SQLITE EN CONSOLIDADO ---
        sql_md = self._get_sqlite_entries()
        if sql_md:
            sql_html = markdown2.markdown(sql_md, extras=["tables", "fenced-code-blocks"])
            sections.append(f'''
            <section id="database_entries">
                {sql_html}
            </section>
            ''')
        # --- FIN FUNCIONALIDAD ---
        
        consolidated = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KB Consolidada - KDP Master</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .sidebar {{ position: fixed; top: 0; left: 0; width: 280px; height: 100vh; background: #2c3e50; color: white; overflow-y: auto; padding: 20px; }}
        .sidebar h2 {{ font-size: 1.3em; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #34495e; }}
        .sidebar ul {{ list-style: none; }}
        .sidebar li {{ margin: 8px 0; }}
        .sidebar a {{ color: #ecf0f1; text-decoration: none; display: block; padding: 8px 12px; border-radius: 4px; transition: background 0.2s; }}
        .sidebar a:hover {{ background: #34495e; }}
        .main {{ margin-left: 280px; padding: 30px; max-width: 900px; }}
        section {{ background: white; padding: 30px; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #ecf0f1; }}
        code {{ background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #3498db; padding-left: 15px; color: #666; margin: 1em 0; }}
        @media (max-width: 900px) {{ .sidebar {{ position: relative; width: 100%; height: auto; }} .main {{ margin-left: 0; }} }}
    </style>
</head>
<body>
    <nav class="sidebar">
        <h2>📚 Índice</h2>
        <ul>
            <li><a href="#">↑ Volver al Índice</a></li>
            {''.join(f'<li><a href="#{Path(exp["file"]).stem}">{self.get_title_from_content(self.manuals_dir / exp["file"])}</a></li>' for exp in exports if (self.manuals_dir / exp["file"]).exists())}
        </ul>
    </nav>
    
    <main class="main">
        <h1>📖 Base de Conocimiento Consolidada</h1>
        <p><em>Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(exports)} manuales</em></p>
        
        {''.join(sections)}
    </main>
</body>
</html>'''
        
        return consolidated
    
    def generate_consolidated_pdf(self, exports: List[Dict]) -> ExportResult:
        if SKIP_PDF:
            logger.info("PDF omitido (SKIP_PDF=True)")
            return ExportResult(False, error="PDF deshabilitado por SKIP_PDF")
        
        logger.info("Generando PDF consolidado...")
        
        combined_content = []
        
        for exp in exports:
            md_path = self.manuals_dir / exp["file"]
            if not md_path.exists():
                continue
            
            title = self.get_title_from_content(md_path)
            content = md_path.read_text(encoding='utf-8', errors='ignore')
            
            if len(content) > MAX_CONTENT_SIZE:
                content = content[:MAX_CONTENT_SIZE]
            
            content = rewrite_internal_links(content, str(md_path), "pdf")
            content, img_warnings = resolve_images(content, md_path, self.assets_dir, self.config.COPY_IMAGES)
            
            html_body = markdown2.markdown(content, extras=["tables", "fenced-code-blocks"])
            
            combined_content.append(f'''
            <section>
                <h1>{title}</h1>
                {html_body}
            </section>
            ''')
        
        full_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>KB Consolidada - KDP Master</title>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        h1 {{ color: #2c3e50; font-size: 1.8em; border-bottom: 2px solid #3498db; padding-bottom: 10px; page-break-after: avoid; margin-top: 0; }}
        h2 {{ color: #34495e; font-size: 1.4em; page-break-after: avoid; }}
        h3 {{ color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; page-break-inside: avoid; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
        code {{ background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
        pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; page-break-inside: avoid; }}
        blockquote {{ border-left: 4px solid #3498db; padding-left: 15px; color: #666; margin: 1em 0; }}
        section {{ page-break-after: always; }}
        section:last-child {{ page-break-after: avoid; }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #2c3e50; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Base de Conocimiento KDP Master</h1>
        <p>Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(exports)} manuales</p>
    </div>
    
    {''.join(combined_content)}
    
    <div class="footer">
        <p>Generado por KDP Master v3.4</p>
    </div>
</body>
</html>        '''
        
        try:
            from weasyprint import HTML
            output_path = self.output_dir / "KB_Consolidado.pdf"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            HTML(string=full_html).write_pdf(output_path)
            return ExportResult(True, str(output_path))
        except ImportError:
            logger.warning("WeasyPrint no disponible. Se omitirá la generación del PDF consolidado.")
            return ExportResult(False, error="WeasyPrint no instalado. Instalar: pip install weasyprint")
        except Exception as e:
            logger.error(f"Error generando PDF consolidado: {e}")
            return ExportResult(False, error=str(e))
    
    # --- INICIO FUNCIONALIDAD US-E-ZIP: COMPRESIÓN DE ACTIVOS v3.4.6 ---
    def _compress_exports(self):
        """Comprime la carpeta de exportación en un archivo ZIP."""
        zip_path = self.output_dir / f"KB_Export_Full_{datetime.now().strftime('%Y%m%d')}.zip"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.output_dir):
                    for file in files:
                        if file.endswith('.zip') or 'exports' in file: continue 
                        file_path = Path(root) / file
                        zipf.write(file_path, file_path.relative_to(self.output_dir))
            return str(zip_path)
        except Exception as e:
            logger.error(f"Error comprimiendo exportación: {e}")
            return None
    # --- FIN FUNCIONALIDAD ---

    # --- INICIO FUNCIONALIDAD US-E-HIST: LOG DE AUDITORÍA EN DB v3.4.6 ---
    def _log_export_to_db(self, format_type, count, file_path):
        """Registra la exportación en el historial de la DB."""
        db_path = self.base_dir / "data" / "kdp_master.db"
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS export_history 
                            (id INTEGER PRIMARY KEY, date TEXT, format TEXT, 
                             count INTEGER, path TEXT, size REAL, status TEXT)""")
            
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            cursor.execute("""INSERT INTO export_history (date, format, count, path, size, status) 
                             VALUES (?, ?, ?, ?, ?, ?)""",
                          (datetime.now().isoformat(), format_type, count, 
                           str(file_path), round(size_mb, 2), "SUCCESS"))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error en log de auditoría export: {e}")
            return False
    # --- FIN FUNCIONALIDAD ---

    def export_all(self, force: bool = False, settings: Dict = None) -> Dict:
        logger.info("=" * 50)
        logger.info("INICIANDO EXPORTACIÓN DE BASE DE CONOCIMIENTO")
        logger.info("=" * 50)
        
        if settings:
            self.export_settings.update(settings)
        
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manuals_output_dir.mkdir(parents=True, exist_ok=True)
        
        md_files = self.get_markdown_files()
        
        if not md_files:
            logger.warning("No se encontraron archivos Markdown en knowledge/manuals/")
            return {"success": False, "exports": [], "error": "No hay archivos Markdown"}
        
        logger.info(f"Encontrados {len(md_files)} archivos Markdown")
        
        exports = []
        for md_file in md_files:
            # US-E-INC: Lógica incremental
            result = self.export_single(md_file, force=force)
            exports.append(result)
            
            status = "✓" if result["pdf"] else ("⚠️" if result["html"] else "✗")
            logger.info(f"  {status} {result['file']}")
        
        logger.info("\nGenerando índice y versiones consolidadas...")
        
        index_html = self.generate_index_html(exports)
        (self.output_dir / "index.html").write_text(index_html, encoding='utf-8')
        
        consolidated_html = self.generate_consolidated_html(exports)
        (self.output_dir / "KB_Consolidado.html").write_text(consolidated_html, encoding='utf-8')
        
        consolidated_pdf = self.generate_consolidated_pdf(exports)
        
        success_count = sum(1 for e in exports if e["html"] or e["pdf"])
        
        logger.info("=" * 50)
        logger.info(f"EXPORTACION COMPLETADA: {success_count}/{len(exports)} manuales")
        logger.info(f"Salida: {self.output_dir}")
        logger.info("=" * 50)
        
        return {
            "success": success_count > 0,
            "total": len(md_files),
            "exported": success_count,
            "output_dir": str(self.output_dir),
            "exports": exports,
            "consolidated_pdf": consolidated_pdf.path if consolidated_pdf.success else None,
            "consolidated_html": str(self.output_dir / "KB_Consolidado.html"),
            "index": str(self.output_dir / "index.html")
        }


def main():
    base_dir = None
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    
    exporter = KBExporter(base_dir)
    result = exporter.export_all()
    
    if result["success"]:
        print(f"\n[OK] Exportacion exitosa:")
        print(f"  - Manuales exportados: {result['exported']}/{result['total']}")
        print(f"  - Indice: {result['index']}")
        print(f"  - Consolidado HTML: {result['consolidated_html']}")
        if result.get('consolidated_pdf'):
            print(f"  - Consolidado PDF: {result['consolidated_pdf']}")
    else:
        print(f"\n[ERROR] {result.get('error', 'Sin detalles')}")
        sys.exit(1)


if __name__ == "__main__":
    main()