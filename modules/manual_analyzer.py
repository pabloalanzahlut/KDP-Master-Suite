"""
KDP_MASTER - Manual Analyzer
=============================
Sistema de análisis de manuales que detecta contenido repetido y banal,
y permite agregar solo información nueva y valiosa sin borrar nada anterior.
"""

import os
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import Counter


class ManualAnalyzer:
    """Analiza manuales MD para detectar duplicados y contenido banal."""
    
    MANUALS_DIR = "knowledge/manuals"
    MANUAL_FILES = [
        "MANUAL_LEGALIDAD.md",
        "MANUAL de FÓRMULAS.MD",
        "MATRIZ_MAESTRA.md"
    ]
    
    BANAL_PATTERNS = [
        r'^\s*---\s*$',
        r'^\s*#{1,3}\s*$',
        r'^\s*$\n^\s*$',
        r'^(Kind|Language):\s*\w+\s*$',
        r'^\s*# Objetivo:.*$',
        r'^\s*# Contenido a incorporar.*$',
    ]
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            import sys
            if getattr(sys, 'frozen', False):
                self.base_dir = Path(sys.executable).parent
            else:
                self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        self.manuals_dir = self.base_dir / self.MANUALS_DIR
    
    def _read_manual(self, filename: str) -> Optional[str]:
        """Lee un archivo manual completo."""
        filepath = self.manuals_dir / filename
        if not filepath.exists():
            return None
        
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
    
    def _split_into_sections(self, content: str) -> List[Dict]:
        """Divide el contenido en secciones lógicas basadas en headers MD."""
        sections = []
        current_section = {"header": "INTRO", "content": [], "start_line": 0}
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#') and line.strip():
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "header": line.strip(),
                    "content": [line],
                    "start_line": i
                }
            else:
                current_section["content"].append(line)
        
        if current_section["content"]:
            sections.append(current_section)
        
        return sections
    
    def _section_hash(self, section_content: List[str]) -> str:
        """Genera un hash del contenido de una sección para comparar."""
        normalized = '\n'.join(section_content).lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'\[.*?\]\(.*?\)', '', normalized)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _is_banal(self, section_content: List[str]) -> bool:
        """Determina si una sección es banal (muy corta, solo metadata, etc)."""
        meaningful_lines = [
            line for line in section_content
            if line.strip()
            and not re.match(r'^\s*---+\s*$', line)
            and not re.match(r'^\s*#.*$', line)
            and not re.match(r'^(Kind|Language|FUENTE|FECHA):', line)
            and len(line.strip()) > 10
        ]
        
        if len(meaningful_lines) < 3:
            return True
        
        total_chars = sum(len(line.strip()) for line in meaningful_lines)
        if total_chars < 100:
            return True
        
        return False
    
    def _find_duplicate_sections(self, all_sections: Dict[str, List[Dict]]) -> List[Dict]:
        """Encuentra secciones duplicadas entre todos los manuales."""
        hash_to_sections = {}
        duplicates = []
        
        for manual_name, sections in all_sections.items():
            for section in sections:
                h = self._section_hash(section["content"])
                if h in hash_to_sections:
                    duplicates.append({
                        "hash": h,
                        "manual": manual_name,
                        "header": section["header"],
                        "start_line": section["start_line"],
                        "original_manual": hash_to_sections[h]["manual"],
                        "original_header": hash_to_sections[h]["header"],
                        "is_banal": self._is_banal(section["content"]),
                        "line_count": len(section["content"])
                    })
                else:
                    hash_to_sections[h] = {
                        "manual": manual_name,
                        "header": section["header"],
                        "start_line": section["start_line"]
                    }
        
        return duplicates
    
    def analyze_all_manuals(self) -> Dict:
        """Analiza todos los manuales y retorna un reporte completo."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "manuals_analyzed": [],
            "total_sections": 0,
            "duplicate_sections": [],
            "banal_sections": [],
            "unique_sections_per_manual": {},
            "summary": {}
        }
        
        all_sections = {}
        
        for filename in self.MANUAL_FILES:
            content = self._read_manual(filename)
            if content is None:
                result["manuals_analyzed"].append({
                    "file": filename,
                    "status": "NOT_FOUND"
                })
                continue
            
            sections = self._split_into_sections(content)
            all_sections[filename] = sections
            
            banal_count = sum(1 for s in sections if self._is_banal(s["content"]))
            
            result["manuals_analyzed"].append({
                "file": filename,
                "status": "OK",
                "total_lines": len(content.split('\n')),
                "total_sections": len(sections),
                "banal_sections": banal_count,
                "file_size_kb": round(len(content.encode('utf-8')) / 1024, 1)
            })
            
            result["total_sections"] += len(sections)
        
        duplicates = self._find_duplicate_sections(all_sections)
        result["duplicate_sections"] = duplicates
        
        for filename, sections in all_sections.items():
            unique = [s for s in sections if not self._is_banal(s["content"])]
            result["unique_sections_per_manual"][filename] = len(unique)
        
        result["summary"] = {
            "total_manuals": len([m for m in result["manuals_analyzed"] if m.get("status") == "OK"]),
            "total_sections": result["total_sections"],
            "total_duplicates": len(duplicates),
            "total_banal": sum(1 for m in result["manuals_analyzed"] for s in all_sections.get(m.get("file", ""), []) if self._is_banal(s["content"])),
            "health_score": self._calculate_health_score(result, all_sections)
        }
        
        return result
    
    def _calculate_health_score(self, result: Dict, all_sections: Dict) -> float:
        """Calcula un score de salud del 0-100."""
        if result["total_sections"] == 0:
            return 0.0
        
        duplicate_ratio = len(result["duplicate_sections"]) / max(result["total_sections"], 1)
        banal_count = sum(
            1 for sections in all_sections.values()
            for s in sections if self._is_banal(s["content"])
        )
        banal_ratio = banal_count / max(result["total_sections"], 1)
        
        score = (1 - duplicate_ratio - banal_ratio) * 100
        return max(0, min(100, round(score, 1)))
    
    def generate_report(self, analysis: Dict) -> str:
        """Genera un reporte legible del análisis."""
        lines = []
        lines.append("# REPORTE DE ANÁLISIS DE MANUALES")
        lines.append(f"Fecha: {analysis['timestamp']}")
        lines.append("")
        
        summary = analysis["summary"]
        lines.append("## RESUMEN")
        lines.append(f"- Manuales analizados: {summary['total_manuals']}")
        lines.append(f"- Total secciones: {summary['total_sections']}")
        lines.append(f"- Secciones duplicadas: {summary['total_duplicates']}")
        lines.append(f"- Secciones banales: {summary['total_banal']}")
        lines.append(f"- Score de salud: {summary['health_score']}/100")
        lines.append("")
        
        lines.append("## DETALLE POR MANUAL")
        for m in analysis["manuals_analyzed"]:
            lines.append(f"\n### {m['file']}")
            if m.get("status") == "NOT_FOUND":
                lines.append("  ⚠️ Archivo no encontrado")
            else:
                lines.append(f"  - Líneas: {m.get('total_lines', 'N/A')}")
                lines.append(f"  - Secciones: {m.get('total_sections', 0)}")
                lines.append(f"  - Banales: {m.get('banal_sections', 0)}")
                lines.append(f"  - Tamaño: {m.get('file_size_kb', 0)} KB")
        
        if analysis["duplicate_sections"]:
            lines.append("\n## SECCIONES DUPLICADAS")
            for dup in analysis["duplicate_sections"][:20]:
                banal_tag = " [BANAL]" if dup["is_banal"] else ""
                lines.append(f"- `{dup['header']}` en {dup['manual']} (línea {dup['start_line']}){banal_tag}")
                lines.append(f"  → Duplicado de: `{dup['original_header']}` en {dup['original_manual']}")
        
        lines.append("")
        lines.append("---")
        lines.append("*Generado por KDP Master Suite - Manual Analyzer*")
        
        return '\n'.join(lines)
    
    def save_report(self, analysis: Dict, output_path: str = None) -> str:
        """Guarda el reporte en un archivo."""
        if output_path is None:
            output_path = self.base_dir / "reports" / f"manual_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report(analysis)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_path)
    
    def save_analysis_json(self, analysis: Dict, output_path: str = None) -> str:
        """Guarda el análisis completo en formato JSON."""
        if output_path is None:
            output_path = self.base_dir / "reports" / f"manual_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
