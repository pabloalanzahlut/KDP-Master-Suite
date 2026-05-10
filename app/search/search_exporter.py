"""
KDP MASTER - Search Exporter Module
=====================================
Módulos 42-45: Exportación CSV/TXT/MD/PDF
"""

import csv
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SearchExporter:
    """
    Exportador de resultados de búsqueda a múltiples formatos.
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.expanduser("~/Documents/KDP_Master")
        os.makedirs(self.base_path, exist_ok=True)
    
    def export_to_csv(self, results: List[Dict], filename: str = None,
                      include_content: bool = False) -> str:
        """
        MÓDULO 42: Exportación de Resultados a CSV
        
        Args:
            results: Lista de resultados
            filename: Nombre de archivo (auto-generado si None)
            include_content: Incluir contenido completo
            
        Returns:
            Ruta del archivo exportado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_results_{timestamp}.csv"
        
        filepath = os.path.join(self.base_path, filename)
        
        columns = ['id', 'title', 'category', 'type', 'date', 'words', 'source']
        
        if include_content:
            columns.append('content')
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                
                for result in results:
                    row = {
                        'id': result.get('id', ''),
                        'title': result.get('title', result.get('source', '')),
                        'category': result.get('category', ''),
                        'type': result.get('type', result.get('tipo', '')),
                        'date': result.get('date', ''),
                        'words': result.get('words', result.get('palabras', 0)),
                        'source': result.get('source', '')
                    }
                    
                    if include_content:
                        content = result.get('content', result.get('content_preview', ''))
                        row['content'] = content.replace('\n', ' ').replace('\r', '')
                    
                    writer.writerow(row)
            
            logger.info(f"CSV exportado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando CSV: {e}")
            raise
    
    def export_to_txt(self, results: List[Dict], filename: str = None) -> str:
        """
        MÓDULO 43: Exportación de Contenido a TXT
        
        Args:
            results: Lista de resultados
            filename: Nombre de archivo
            
        Returns:
            Ruta del archivo exportado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_content_{timestamp}.txt"
        
        filepath = os.path.join(self.base_path, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RESULTADOS DE BÚSQUEDA - KDP MASTER\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total de resultados: {len(results)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, result in enumerate(results, 1):
                    title = result.get('title', result.get('source', f'Entrada {result.get("id")}'))
                    category = result.get('category', 'Sin categoría')
                    tipo = result.get('type', result.get('tipo', 'Artículo'))
                    date = result.get('date', 'N/A')
                    content = result.get('content', result.get('content_preview', ''))
                    
                    f.write(f"\n--- RESULTADO {i} ---\n")
                    f.write(f"TÍTULO: {title}\n")
                    f.write(f"CATEGORÍA: {category}\n")
                    f.write(f"TIPO: {tipo}\n")
                    f.write(f"FECHA: {date}\n")
                    f.write(f"\nCONTENIDO:\n")
                    f.write("-" * 40 + "\n")
                    f.write(content[:2000])
                    if len(content) > 2000:
                        f.write(f"\n... [continúa: {len(content) - 2000} caracteres más]")
                    f.write("\n\n")
            
            logger.info(f"TXT exportado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando TXT: {e}")
            raise
    
    def export_to_markdown(self, results: List[Dict], filename: str = None,
                          query: str = None) -> str:
        """
        MÓDULO 43: Exportación de Contenido a MD
        
        Args:
            results: Lista de resultados
            filename: Nombre de archivo
            query: Query original de búsqueda
            
        Returns:
            Ruta del archivo exportado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_results_{timestamp}.md"
        
        filepath = os.path.join(self.base_path, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Resultados de Búsqueda - KDP Master\n\n")
                f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if query:
                    f.write(f"**Búsqueda:** `{query}`\n")
                f.write(f"**Total de resultados:** {len(results)}\n\n")
                f.write("---\n\n")
                
                for i, result in enumerate(results, 1):
                    title = result.get('title', result.get('source', f'Entrada {result.get("id")}'))
                    category = result.get('category', 'Sin categoría')
                    tipo = result.get('type', result.get('tipo', 'Artículo'))
                    date = result.get('date', 'N/A')
                    words = result.get('words', result.get('palabras', 0))
                    content = result.get('content', result.get('content_preview', ''))
                    
                    f.write(f"## {i}. {title}\n\n")
                    f.write(f"- **Categoría:** {category}\n")
                    f.write(f"- **Tipo:** {tipo}\n")
                    f.write(f"- **Fecha:** {date}\n")
                    f.write(f"- **Palabras:** {words}\n")
                    f.write(f"- **ID:** {result.get('id', 'N/A')}\n\n")
                    
                    f.write("### Contenido\n\n")
                    f.write(content[:1500])
                    if len(content) > 1500:
                        f.write(f"\n\n*[Contenido completo: {len(content) - 1500} caracteres más]*")
                    f.write("\n\n---\n\n")
            
            logger.info(f"Markdown exportado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando Markdown: {e}")
            raise
    
    def export_to_pdf(self, results: List[Dict], filename: str = None,
                      query: str = None) -> str:
        """
        MÓDULO 44: Exportación a PDF con Formato
        
        Args:
            results: Lista de resultados
            filename: Nombre de archivo
            query: Query original
            
        Returns:
            Ruta del archivo exportado
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_LEFT
        except ImportError:
            logger.warning("reportlab no disponible, generando HTML alternativo")
            return self.export_to_html(results, filename, query)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_results_{timestamp}.pdf"
        
        filepath = os.path.join(self.base_path, filename)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter,
                                   leftMargin=0.75*inch, rightMargin=0.75*inch,
                                   topMargin=1*inch, bottomMargin=0.75*inch)
            
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading2']
            body_style = styles['BodyText']
            
            story = []
            
            story.append(Paragraph("Resultados de Búsqueda - KDP Master", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            if query:
                story.append(Paragraph(f"<b>Búsqueda:</b> {query}", body_style))
            story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
            story.append(Paragraph(f"<b>Total de resultados:</b> {len(results)}", body_style))
            story.append(Spacer(1, 0.3*inch))
            
            for i, result in enumerate(results[:30]):
                if i > 0:
                    story.append(Spacer(1, 0.1*inch))
                
                title = result.get('title', result.get('source', f'Entrada {result.get("id")}'))
                category = result.get('category', 'Sin categoría')
                tipo = result.get('type', result.get('tipo', 'Artículo'))
                content = result.get('content', result.get('content_preview', ''))[:500]
                
                story.append(Paragraph(f"<b>{i+1}. {title}</b>", heading_style))
                story.append(Paragraph(f"Categoría: {category} | Tipo: {tipo}", body_style))
                story.append(Spacer(1, 0.05*inch))
                story.append(Paragraph(content.replace('\n', '<br/>'), body_style))
                
                if (i + 1) % 5 == 0:
                    story.append(PageBreak())
            
            doc.build(story)
            logger.info(f"PDF exportado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando PDF: {e}")
            raise
    
    def export_to_html(self, results: List[Dict], filename: str = None,
                       query: str = None) -> str:
        """
        Exportación alternativa a HTML si PDF no está disponible.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_results_{timestamp}.html"
        
        filepath = os.path.join(self.base_path, filename)
        
        try:
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Resultados de Búsqueda - KDP Master</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #1a365d; }}
        .result {{ margin-bottom: 20px; padding: 15px; border: 1px solid #e2e8f0; }}
        .meta {{ color: #64748b; font-size: 0.9em; }}
        .content {{ margin-top: 10px; }}
    </style>
</head>
<body>
    <h1>Resultados de Búsqueda - KDP Master</h1>
    <p><b>Fecha:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    {f'<p><b>Búsqueda:</b> {query}</p>' if query else ''}
    <p><b>Total de resultados:</b> {len(results)}</p>
    <hr>
"""
            
            for i, result in enumerate(results[:50], 1):
                title = result.get('title', result.get('source', f'Entrada {result.get("id")}'))
                category = result.get('category', 'Sin categoría')
                tipo = result.get('type', result.get('tipo', 'Artículo'))
                content = result.get('content', result.get('content_preview', ''))[:800]
                
                html += f"""
    <div class="result">
        <h3>{i}. {title}</h3>
        <p class="meta">Categoría: {category} | Tipo: {tipo}</p>
        <div class="content">{content.replace(chr(10), '<br>')}</div>
    </div>
"""
            
            html += """
</body>
</html>"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"HTML exportado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando HTML: {e}")
            raise
    
    def copy_to_clipboard(self, results: List[Dict], format: str = "text") -> str:
        """
        MÓDULO 45: Copiar Resultado al Portapapeles
        
        Args:
            results: Resultados a copiar
            format: 'text' o 'html'
            
        Returns:
            Texto formateado
        """
        try:
            import pyperclip
        except ImportError:
            logger.warning("pyperclip no disponible")
            return ""
        
        if format == "html":
            text = self._format_as_html(results[:10])
        else:
            text = self._format_as_text(results[:10])
        
        pyperclip.copy(text)
        logger.info(f"Copiado al portapapeles: {len(results)} resultados")
        return text
    
    def _format_as_text(self, results: List[Dict]) -> str:
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get('title', r.get('source', f'Entrada {r.get("id")}'))
            content = r.get('content_preview', r.get('content', ''))[:300]
            lines.append(f"{i}. {title}\n{content}\n")
        return "\n".join(lines)
    
    def _format_as_html(self, results: List[Dict]) -> str:
        html = "<ul>"
        for r in results:
            title = r.get('title', r.get('source', ''))
            html += f"<li><b>{title}</b></li>"
        html += "</ul>"
        return html