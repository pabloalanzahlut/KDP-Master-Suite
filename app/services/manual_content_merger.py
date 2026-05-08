"""
KDP_MASTER - Manual Content Merger
====================================
Sistema que lee los 3 manuales protegidos, analiza contenido nuevo,
detecta duplicados y banalidad, y escribe SOLO contenido nuevo y valioso.
NUNCA borra ni elimina nada anterior.
"""

import os
import re
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set


class ManualContentMerger:
    """
    Analiza y fusiona contenido en los 3 manuales protegidos.
    Regla de oro: NUNCA borra, solo añade contenido nuevo no-duplicado no-banal.
    """
    
    PROTECTED_MANUALS = {
        "LEGALIDAD": "MANUAL_LEGALIDAD.md",
        "FORMULAS": "MANUAL de FÓRMULAS.MD",
        "MATRIZ": "MATRIZ_MAESTRA.md"
    }
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            import sys
            if getattr(sys, 'frozen', False):
                self.base_dir = Path(sys.executable).parent
            else:
                self.base_dir = Path(__file__).parent.parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        self.manuals_dir = self.base_dir / "knowledge" / "manuals"
        self.backups_dir = self.manuals_dir / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_manual_path(self, key: str) -> Optional[Path]:
        if key not in self.PROTECTED_MANUALS:
            return None
        return self.manuals_dir / self.PROTECTED_MANUALS[key]
    
    def create_backup(self, key: str) -> Optional[str]:
        """Crea backup timestamped de un manual antes de cualquier modificación."""
        filepath = self._get_manual_path(key)
        if not filepath or not filepath.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
        backup_path = self.backups_dir / backup_name
        
        shutil.copy2(filepath, backup_path)
        return str(backup_path)
    
    def read_manual(self, key: str) -> Optional[str]:
        filepath = self._get_manual_path(key)
        if not filepath or not filepath.exists():
            return None
        
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """
        Divide contenido en secciones por headers MD (## o ###).
        Cada sección incluye el header + contenido hasta el siguiente header.
        """
        sections = []
        lines = content.split('\n')
        current = {"header": "PREAMBLE", "lines": [], "start": 0}
        
        for i, line in enumerate(lines):
            if re.match(r'^#{2,4}\s+', line.strip()):
                if current["lines"]:
                    sections.append(current)
                current = {"header": line.strip(), "lines": [line], "start": i}
            else:
                current["lines"].append(line)
        
        if current["lines"]:
            sections.append(current)
        
        return sections
    
    def _section_content_hash(self, lines: List[str]) -> str:
        """Hash del contenido semántico de una sección (ignora formato menor)."""
        text = '\n'.join(lines).lower()
        text = re.sub(r'#{2,4}\s+', '', text)
        text = re.sub(r'\*\*|__|\*|_', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _is_banal_section(self, lines: List[str]) -> bool:
        """
        Determina si una sección es banal:
        - Menos de 3 líneas significativas
        - Solo contiene metadata (FUENTE, FECHA, Kind, Language)
        - Texto total < 150 caracteres significativos
        """
        meaningful = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r'^#{2,4}\s+', stripped):
                continue
            if re.match(r'^---+\s*$', stripped):
                continue
            if re.match(r'^(Kind|Language|FUENTE|FECHA):\s*', stripped):
                continue
            if len(stripped) > 15:
                meaningful.append(stripped)
        
        if len(meaningful) < 3:
            return True
        
        total_chars = sum(len(l) for l in meaningful)
        if total_chars < 150:
            return True
        
        return False
    
    def _get_all_existing_hashes(self, key: str) -> Set[str]:
        """Obtiene todos los hashes de secciones existentes en un manual."""
        content = self.read_manual(key)
        if not content:
            return set()
        
        sections = self._extract_sections(content)
        return {self._section_content_hash(s["lines"]) for s in sections}
    
    def analyze_new_content(self, key: str, new_content: str) -> Dict:
        """
        Analiza contenido nuevo contra un manual existente.
        Retorna qué secciones son nuevas (no duplicadas, no banales).
        """
        existing_hashes = self._get_all_existing_hashes(key)
        
        new_sections = self._extract_sections(new_content)
        
        result = {
            "total_new_sections": len(new_sections),
            "added": [],
            "skipped_duplicate": [],
            "skipped_banal": [],
            "backup_path": None
        }
        
        for section in new_sections:
            h = self._section_content_hash(section["lines"])
            
            if h in existing_hashes:
                result["skipped_duplicate"].append({
                    "header": section["header"],
                    "reason": "Duplicado exacto"
                })
                continue
            
            if self._is_banal_section(section["lines"]):
                result["skipped_banal"].append({
                    "header": section["header"],
                    "reason": "Contenido banal o insuficiente"
                })
                continue
            
            result["added"].append({
                "header": section["header"],
                "line_count": len(section["lines"]),
                "hash": h
            })
            existing_hashes.add(h)
        
        return result
    
    def merge_new_content(self, key: str, new_content: str, 
                          source: str = "Manual Merger") -> Dict:
        """
        Fusiona contenido nuevo en un manual protegido.
        - Crea backup automático
        - Solo añade secciones no-duplicadas y no-banales
        - NUNCA borra ni modifica contenido existente
        """
        filepath = self._get_manual_path(key)
        if not filepath:
            return {"error": f"Manual no encontrado: {key}"}
        
        analysis = self.analyze_new_content(key, new_content)
        
        if not analysis["added"]:
            analysis["message"] = "No hay contenido nuevo válido para añadir."
            return analysis
        
        backup_path = self.create_backup(key)
        analysis["backup_path"] = backup_path
        
        existing_content = self.read_manual(key) or ""
        
        merge_block = f"\n\n---\n\n## 🔄 CONTENIDO AGREGADO AUTOMÁTICAMENTE\n"
        merge_block += f"- **Fuente:** {source}\n"
        merge_block += f"- **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        merge_block += f"- **Secciones añadidas:** {len(analysis['added'])}\n"
        merge_block += f"- **Duplicados omitidos:** {len(analysis['skipped_duplicate'])}\n"
        merge_block += f"- **Banales omitidos:** {len(analysis['skipped_banal'])}\n"
        merge_block += f"\n---\n\n"
        
        for section in self._extract_sections(new_content):
            h = self._section_content_hash(section["lines"])
            is_added = any(a["hash"] == h for a in analysis["added"])
            
            if is_added:
                merge_block += '\n'.join(section["lines"]) + '\n\n---\n\n'
        
        # Asegurar que el archivo termina con newline antes de append
        needs_newline = False
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, 'rb') as f:
                f.seek(-1, 2)
                needs_newline = f.read(1) != b'\n'
        
        with open(filepath, 'a', encoding='utf-8') as f:
            if needs_newline:
                f.write('\n')
            f.write(merge_block)
        
        analysis["message"] = (
            f"✅ {len(analysis['added'])} secciones añadidas a {self.PROTECTED_MANUALS[key]}\n"
            f"⏭️ {len(analysis['skipped_duplicate'])} duplicados omitidos\n"
            f"📄 {len(analysis['skipped_banal'])} banales omitidos\n"
            f"💾 Backup: {backup_path}"
        )
        
        return analysis
    
    def scan_transcription_for_manuals(self, transcription_text: str, 
                                        source_name: str = "Transcripción") -> Dict:
        """
        Escanea una transcripción y distribuye contenido relevante a los 3 manuales.
        Usa clasificación por palabras clave para determinar a qué manual va cada sección.
        """
        blocks = [b.strip() for b in transcription_text.split('\n\n') if b.strip() and len(b.strip()) > 100]
        
        results = {
            "LEGALIDAD": {"added": 0, "skipped": 0},
            "FORMULAS": {"added": 0, "skipped": 0},
            "MATRIZ": {"added": 0, "skipped": 0}
        }
        
        for block in blocks:
            target = self._classify_block(block)
            if target not in results:
                continue
            
            section_content = f"### 📝 Extraído de: {source_name}\n\n{block}\n"
            analysis = self.analyze_new_content(target, section_content)
            
            if analysis["added"]:
                self.merge_new_content(target, section_content, source=source_name)
                results[target]["added"] += len(analysis["added"])
            else:
                results[target]["skipped"] += 1
        
        return results
    
    def _classify_block(self, text: str) -> Optional[str]:
        """Clasifica un bloque de texto al manual correspondiente."""
        t = text.lower()
        
        if any(w in t for w in ["términos", "legal", "copyright", "licencia", "marca", 
                                  "suspensión", "bloqueo", "infracción", "política", 
                                  "compliance", "drm", "fiscal", "regalía", "impuesto"]):
            return "LEGALIDAD"
        
        if any(w in t for w in ["fórmula", "cálculo", "roi", "acos", "bsr", 
                                  "margen", "royalty", "beneficio", "ganancia",
                                  "métrica", "kpi", "porcentaje"]):
            return "FORMULAS"
        
        if any(w in t for w in ["rol", "fase soe", "taxonomía", "arquitectura", 
                                  "checklist", "matriz", "gates de decisión",
                                  "entregable", "dependencia"]):
            return "MATRIZ"
        
        return None
    
    def full_analysis_report(self) -> str:
        """Genera un reporte completo del estado de los 3 manuales."""
        lines = []
        lines.append("# REPORTE DE ESTADO DE MANUALES PROTEGIDOS")
        lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        total_sections = 0
        total_banal = 0
        total_unique = 0
        
        for key, filename in self.PROTECTED_MANUALS.items():
            content = self.read_manual(key)
            if not content:
                lines.append(f"## ❌ {filename}: NO ENCONTRADO")
                lines.append("")
                continue
            
            sections = self._extract_sections(content)
            banal = sum(1 for s in sections if self._is_banal_section(s["lines"]))
            unique = len(sections) - banal
            
            total_sections += len(sections)
            total_banal += banal
            total_unique += unique
            
            size_kb = len(content.encode('utf-8')) / 1024
            
            lines.append(f"## 📄 {filename}")
            lines.append(f"- Secciones totales: {len(sections)}")
            lines.append(f"- Secciones únicas/valiosas: {unique}")
            lines.append(f"- Secciones banales: {banal}")
            lines.append(f"- Tamaño: {size_kb:.1f} KB")
            lines.append(f"- Líneas: {len(content.splitlines())}")
            lines.append("")
        
        lines.append("---")
        lines.append("## RESUMEN GLOBAL")
        lines.append(f"- Total secciones: {total_sections}")
        lines.append(f"- Contenido valioso: {total_unique}")
        lines.append(f"- Contenido banal: {total_banal}")
        if total_sections > 0:
            health = (total_unique / total_sections) * 100
            lines.append(f"- Score de salud: {health:.1f}%")
        
        lines.append("")
        lines.append(f"*Generado por KDP Master Suite - Manual Content Merger*")
        
        return '\n'.join(lines)
