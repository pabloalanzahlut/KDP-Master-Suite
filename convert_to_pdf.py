import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging
import markdown2

for dll_path in [
    r"C:\msys64\mingw64\bin",
    r"C:\Program Files\GTK3-Runtime Win64\bin",
    r"C:\Program Files\GTK3-Runtime Win64",
]:
    if os.path.exists(dll_path):
        try:
            os.add_dll_directory(dll_path)
        except Exception:
            pass

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_weasyprint():
    """Retorna HTML de weasyprint si está disponible, None si no."""
    for dll_path in [
        os.environ.get("WEASYPRINT_DLL_DIRECTORIES", ""),
        r"C:\msys64\mingw64\bin",
        r"C:\Program Files\GTK3-Runtime Win64\bin",
        r"C:\Program Files\GTK3-Runtime Win64",
    ]:
        if dll_path and os.path.exists(dll_path):
            try:
                os.add_dll_directory(dll_path)
            except Exception:
                pass
    
    try:
        from weasyprint import HTML
        return HTML
    except (ImportError, OSError) as e:
        logger.warning(f"WeasyPrint no disponible: {e}")
        return None


def check_weasyprint_installation() -> str:
    """Verifica la instalación de WeasyPrint y retorna instrucciones."""
    issues = []
    
    if os.path.exists(r"C:\msys64\mingw64\bin\libgobject-2.0-0.dll"):
        pass
    elif os.path.exists(r"C:\Program Files\GTK3-Runtime Win64\bin\libgobject-2.0-0.dll"):
        pass
    else:
        issues.append("GTK3 Runtime no instalado")
    
    try:
        from weasyprint import HTML
        return "OK"
    except OSError as e:
        if "gobject" in str(e).lower():
            return f"Faltan dependencias GTK: {e}\n\nInstala GTK3 Runtime desde:\nhttps://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases"
        return str(e)
    except ImportError as e:
        return f"WeasyPrint no instalado: pip install weasyprint"


class ExportConfig:
    EMBED_IMAGES = False
    OUTPUT_DIR = "knowledge/exports"
    ASSETS_DIR = "knowledge/exports/assets"
    COPY_IMAGES = True


class ExportResult:
    def __init__(self, success: bool, path: str = None, warnings: List[str] = None, error: str = None):
        self.success = success
        self.path = path
        self.warnings = warnings or []
        self.error = error


def generate_toc(markdown_text: str) -> str:
    headings = []
    for match in re.finditer(r'^(#{1,6})\s+(.+)$', markdown_text, re.MULTILINE):
        level = len(match.group(1))
        title = match.group(2).strip()
        anchor = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        headings.append((level, title, anchor))
    return headings


def render_toc_html(toc_entries: List[Tuple[int, str, str]], max_level: int = 3) -> str:
    if not toc_entries:
        return ""
    
    html = '<nav class="toc"><ul>'
    prev_level = 0
    
    for level, title, anchor in toc_entries:
        if level > max_level:
            continue
        if level > prev_level:
            html += '<ul>' * (level - prev_level)
        elif level < prev_level:
            html += '</ul>' * (prev_level - level)
        
        html += f'<li><a href="#{anchor}">{title}</a></li>'
        prev_level = level
    
    html += '</ul>' * prev_level
    html += '</nav>'
    return html


def rewrite_internal_links(content: str, source_file: str, export_format: str = "html") -> str:
    pattern = r'\[([^\]]+)\]\(([^#)]+)(#([^)]+))?\)'
    
    def replace_link(match):
        text = match.group(1)
        target_file = match.group(2).strip()
        anchor = match.group(4) or ""
        
        if export_format == "html":
            target_html = Path(target_file).stem.replace(" ", "_") + ".html"
            return f'<a href="{target_html}{"#" + anchor if anchor else ""}">{text}</a>'
        elif export_format == "pdf":
            if anchor:
                return f'<a href="#{anchor}">{text}</a>'
            return text
        return text
    
    return re.sub(pattern, replace_link, content)


def resolve_images(content: str, source_md_path: Path, assets_dir: Path, copy_images: bool = True) -> Tuple[str, List[str]]:
    warnings = []
    resolved_content = content
    
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image(match):
        alt_text = match.group(1)
        image_path = match.group(2).strip()
        
        if image_path.startswith(('http://', 'https://')):
            return match.group(0)
        
        try:
            source_img = (source_md_path.parent / image_path).resolve()
            if not source_img.exists():
                warnings.append(f"Imagen no encontrada: {image_path}")
                return f'<p class="image-missing">🖼️ [Imagen no encontrada: {image_path}]</p>'
            
            if copy_images:
                assets_dir.mkdir(parents=True, exist_ok=True)
                dest_img = assets_dir / source_img.name
                if not dest_img.exists():
                    shutil.copy2(source_img, dest_img)
                relative_path = f"assets/{source_img.name}"
                return f'<figure><img src="{relative_path}" alt="{alt_text}"/><figcaption>{alt_text}</figcaption></figure>'
            else:
                return f'<figure><img src="{source_img}" alt="{alt_text}"/><figcaption>{alt_text}</figcaption></figure>'
        except Exception as e:
            warnings.append(f"Error procesando imagen {image_path}: {e}")
            return match.group(0)
    
    resolved_content = re.sub(image_pattern, replace_image, content)
    return resolved_content, warnings


def convert_md_to_html(md_path: Path, config: ExportConfig = None, max_size: int = 500000) -> Tuple[str, List[Tuple[int, str, str]], List[str]]:
    if config is None:
        config = ExportConfig()
    
    warnings = []
    markdown_text = md_path.read_text(encoding='utf-8')
    
    if len(markdown_text) > max_size:
        warnings.append(f"Archivo truncado a {max_size} caracteres para evitar timeout")
        markdown_text = markdown_text[:max_size]
    
    markdown_text = rewrite_internal_links(markdown_text, str(md_path), "html")
    
    assets_dir = Path(config.ASSETS_DIR)
    markdown_text, img_warnings = resolve_images(markdown_text, md_path, assets_dir, config.COPY_IMAGES)
    warnings.extend(img_warnings)
    
    toc_entries = generate_toc(markdown_text)
    
    html_text = markdown2.markdown(markdown_text, extras=[
        "tables", "fenced-code-blocks", "strikeout", "underline"
    ])
    
    styled_html = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <title>{md_path.stem}</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3, h4, h5, h6 {{ color: #2c3e50; border-bottom: 1px solid #ccc; padding-bottom: 5px; page-break-after: avoid; }}
                h1 {{ font-size: 2em; border-bottom: 2px solid #2c3e50; }}
                h2 {{ font-size: 1.5em; }}
                h3 {{ font-size: 1.25em; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; page-break-inside: avoid; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                code {{ background-color: #eee; padding: 2px 4px; border-radius: 4px; font-family: 'Courier New', monospace; }}
                pre > code {{ display: block; padding: 10px; white-space: pre-wrap; }}
                figure {{ margin: 1em 0; text-align: center; }}
                figcaption {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
                .toc {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .toc h2 {{ font-size: 1.2em; border-bottom: none; }}
                .toc ul {{ padding-left: 20px; }}
                .toc li {{ margin: 5px 0; }}
                a {{ color: #0066cc; }}
                blockquote {{ border-left: 4px solid #ddd; padding-left: 15px; color: #666; margin: 1em 0; }}
                hr {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
            </style>
        </head>
        <body>
            {html_text}
        </body>
    </html>
    """
    return styled_html, toc_entries, warnings


def convert_md_to_pdf(input_md_path: str, output_pdf_path: str, config: ExportConfig = None) -> ExportResult:
    if config is None:
        config = ExportConfig()
    
    warnings = []
    try:
        md_path = Path(input_md_path)
        pdf_path = Path(output_pdf_path)
        
        if not md_path.exists():
            return ExportResult(False, error=f"Archivo no encontrado: {md_path}")
        
        html_content, toc_entries, img_warnings = convert_md_to_html(md_path, config)
        warnings.extend(img_warnings)
        
        toc_html = render_toc_html(toc_entries)
        full_html = html_content.replace('<body>', f'<body>{toc_html}', 1)
        
        HTML = get_weasyprint()
        if HTML is None:
            return ExportResult(False, error="WeasyPrint no está instalado. Instala las dependencias: pip install weasyprint", warnings=warnings)
        
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=full_html, base_url=str(md_path.parent)).write_pdf(pdf_path)
        
        return ExportResult(True, str(pdf_path), warnings)
    except Exception as e:
        logger.error(f"Error convirtiendo {input_md_path} a PDF: {e}")
        return ExportResult(False, error=str(e), warnings=warnings)


def convert_md_to_pdf_with_styles(input_md_path: str, output_pdf_path: str, title: str = None, 
                                   config: ExportConfig = None) -> ExportResult:
    if config is None:
        config = ExportConfig()
    
    warnings = []
    try:
        md_path = Path(input_md_path)
        pdf_path = Path(output_pdf_path)
        
        if not md_path.exists():
            return ExportResult(False, error=f"Archivo no encontrado: {md_path}")
        
        if title is None:
            title = md_path.stem.replace("_", " ").replace("-", " ")
        
        markdown_text = md_path.read_text(encoding='utf-8')
        markdown_text = rewrite_internal_links(markdown_text, str(md_path), "pdf")
        
        assets_dir = Path(config.ASSETS_DIR)
        markdown_text, img_warnings = resolve_images(markdown_text, md_path, assets_dir, config.COPY_IMAGES)
        warnings.extend(img_warnings)
        
        toc_entries = generate_toc(markdown_text)
        
        html_text = markdown2.markdown(markdown_text, extras=[
            "tables", "fenced-code-blocks", "strikeout", "underline"
        ])
        
        toc_html = render_toc_html(toc_entries)
        
        styled_html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                <style>
                    @page {{ size: A4; margin: 2cm; @top-right {{ content: counter(page); }} }}
                    body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
                    h1, h2, h3, h4, h5, h6 {{ color: #2c3e50; border-bottom: 1px solid #ccc; padding-bottom: 5px; page-break-after: avoid; }}
                    h1 {{ font-size: 2em; border-bottom: 2px solid #2c3e50; margin-top: 0; }}
                    h2 {{ font-size: 1.5em; }}
                    h3 {{ font-size: 1.25em; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; page-break-inside: avoid; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    code {{ background-color: #eee; padding: 2px 4px; border-radius: 4px; font-family: 'Courier New', monospace; }}
                    pre > code {{ display: block; padding: 10px; white-space: pre-wrap; overflow-x: auto; }}
                    figure {{ page-break-inside: avoid; margin: 1em 0; text-align: center; }}
                    figcaption {{ font-size: 0.85em; color: #666; margin-top: 5px; text-align: center; }}
                    .toc {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; page-break-after: avoid; }}
                    .toc h2 {{ font-size: 1.2em; border-bottom: none; color: #2c3e50; }}
                    .toc ul {{ padding-left: 20px; margin: 10px 0; }}
                    .toc li {{ margin: 5px 0; }}
                    a {{ color: #0066cc; text-decoration: none; }}
                    blockquote {{ border-left: 4px solid #ddd; padding-left: 15px; color: #666; margin: 1em 0; }}
                    hr {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
                    .header-info {{ font-size: 0.9em; color: #666; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ddd; }}
                    .footer-info {{ font-size: 0.8em; color: #999; margin-top: 20px; padding-top: 10px; border-top: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <div class="header-info">
                    <strong>{title}</strong><br>
                    Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                </div>
                {toc_html}
                <hr>
                {html_text}
                <div class="footer-info">
                    Generado por KDP Master - Base de Conocimiento
                </div>
            </body>
        </html>
        """
        
        HTML = get_weasyprint()
        if HTML is None:
            return ExportResult(False, error="WeasyPrint no está instalado. Instala las dependencias: pip install weasyprint", warnings=warnings)
        
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=styled_html, base_url=str(md_path.parent)).write_pdf(pdf_path)
        
        return ExportResult(True, str(pdf_path), warnings)
    except Exception as e:
        logger.error(f"Error convirtiendo {input_md_path} a PDF: {e}")
        return ExportResult(False, error=str(e), warnings=warnings)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python convert_to_pdf.py <archivo.md> <salida.pdf> [título]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    pdf_file = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = convert_md_to_pdf_with_styles(md_file, pdf_file, title)
    
    if result.success:
        print(f"✓ PDF generado: {result.path}")
        if result.warnings:
            for w in result.warnings:
                print(f"  ⚠️ {w}")
    else:
        print(f"✗ Error: {result.error}")