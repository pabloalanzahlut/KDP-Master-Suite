# ==================== INICIO MÓDULO: DOC_UPDATER CORE (v3.0) ====================
"""
doc_updater.py — Sistema de actualización automática de documentación Markdown.
Compatible con DOCUMENTACION_TECNICA.md y OPERATIONS_MANUAL.md del proyecto KDP Master Suite.

Principios aplicados:
- SRP: Cada método tiene una única responsabilidad clara.
- OCP: Extensible sin modificar código existente (nuevos docs vía configuración).
- DIP: Depende de abstracciones (path, regex), no de implementaciones concretas.
"""
import os
import re
import json
from datetime import datetime
import logging
from typing import List, Dict, Optional
from pathlib import Path
# ==================== FIN MÓDULO: DOC_UPDATER CORE (v3.0) ====================


# ==================== INICIO MÓDULO: CONFIGURACIÓN DE DOCUMENTOS ====================
class DocConfig:
    """Configuración centralizada de documentos soportados y sus estructuras."""
    
    # Documentos objetivo del proyecto
    TARGET_DOCS = {
        "technical": {
            "path": "docs/DOCUMENTACION_TECNICA.md",
            "section_markers": {
                "architecture": "🏗️ Arquitectura",
                "components": "🔧 Componentes del Sistema",
                "updates": "🔄 Actualizaciones de Arquitectura"
            }
        },
        "operations": {
            "path": "docs/OPERATIONS_MANUAL.md",
            "section_markers": {
                "notes": "📋 Notas de Operación y Cambios Recientes",
                "health": "7. Health Check"
            }
        }
    }
    
    # Patrón para detectar módulos en código fuente
    MODULE_PATTERN = re.compile(
        r'#\s*={20,}\s*INICIO MÓDULO[:\s]+([^{]+?)\s*={20,}.*?'
        r'#\s*={20,}\s*FIN MÓDULO\s*={20,}',
        re.DOTALL | re.IGNORECASE
    )
    
    # Patrón para tablas de funcionalidades (compatibilidad legacy)
    FEATURE_TABLE_PATTERN = re.compile(
        r'\|\s*ID\s*\|\s*Funcionalidad\s*\|\s*Estado\s*\|',
        re.IGNORECASE
    )
# ==================== FIN MÓDULO: CONFIGURACIÓN DE DOCUMENTOS ====================


# ==================== INICIO MÓDULO: CLASE PRINCIPAL DOCUPDATER ====================
class DocUpdater:
    """
    Gestor de actualización automática de documentación Markdown.
    Soporta: DOCUMENTACION_TECNICA.md, OPERATIONS_MANUAL.md y tablas legacy.
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.logger = logging.getLogger('KDP_DOC_UPDATER')
        self._configure_logger()
        self.config = DocConfig()
        self._cache = {}  # Cache simple para lecturas frecuentes

    def _configure_logger(self):
        """Configura el logger si no tiene handlers."""
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # ==================== INICIO MÓDULO: LECTURA/ESCRITURA SEGURA ====================
    def _read_file(self, file_path: str) -> List[str]:
        """Lee archivo con manejo robusto de errores y cache opcional."""
        try:
            full_path = self.base_dir / file_path
            if str(full_path) in self._cache:
                return self._cache[str(full_path)]
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
                self._cache[str(full_path)] = content
                return content
        except FileNotFoundError:
            self.logger.warning(f"📄 Archivo no encontrado: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error leyendo {file_path}: {e}")
            return []

    def _write_file(self, file_path: str, lines: List[str], invalidate_cache: bool = True):
        """Escribe archivo con invalidación de cache si se solicita."""
        try:
            full_path = self.base_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            if invalidate_cache and str(full_path) in self._cache:
                del self._cache[str(full_path)]
                
            self.logger.info(f"✅ Documento actualizado: {file_path}")
        except Exception as e:
            self.logger.error(f"❌ Error escribiendo {file_path}: {e}")
    # ==================== FIN MÓDULO: LECTURA/ESCRITURA SEGURA ====================

    # ==================== INICIO MÓDULO: ACTUALIZACIÓN DE TABLAS LEGACY ====================
    def update_feature_status_in_markdown(
        self, 
        doc_path_relative: str, 
        feature_id: str, 
        new_status: str, 
        last_updated: str = None
    ) -> bool:
        """Actualiza estado de funcionalidad en tabla Markdown (compatibilidad legacy)."""
        file_path = os.path.join(self.base_dir, doc_path_relative)
        lines = self._read_file(file_path)
        if not lines:
            return False

        # Buscar header de tabla
        table_start = next(
            (i for i, l in enumerate(lines) 
             if self.config.FEATURE_TABLE_PATTERN.search(l)), 
            -1
        )
        if table_start == -1:
            self.logger.warning(f"⚠️ Tabla de funcionalidades no encontrada en {doc_path_relative}")
            return False

        # Procesar y actualizar fila
        updated = False
        new_lines = []
        current_date = last_updated or datetime.now().strftime('%Y-%m-%d')
        
        for i, line in enumerate(lines):
            if i > table_start + 1 and line.strip().startswith('|'):
                match = re.match(
                    r'\|\s*(' + re.escape(feature_id) + r')\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|',
                    line, re.IGNORECASE
                )
                if match:
                    # Reconstruir línea con nuevo estado
                    cols = [c.strip() for c in match.groups()]
                    new_line = (
                        f"| {cols[0]:<7} | {cols[1]:<40} | {new_status:<11} | "
                        f"{cols[3]:<10} | {current_date:<12} |\n"
                    )
                    new_lines.append(new_line)
                    self.logger.info(f"🔄 Feature '{feature_id}' → {new_status} en {doc_path_relative}")
                    updated = True
                    continue
            new_lines.append(line)

        if updated:
            self._write_file(file_path, new_lines)
            return True
        else:
            self.logger.warning(f"⚠️ Feature '{feature_id}' no encontrada en {doc_path_relative}")
            return False

    def add_feature_to_markdown(
        self, 
        doc_path_relative: str, 
        feature_id: str, 
        description: str, 
        status: str = "🚧 In Progress", 
        priority: str = "Media"
    ) -> bool:
        """Agrega nueva funcionalidad al final de tabla Markdown."""
        lines = self._read_file(doc_path_relative)
        if not lines:
            return False

        # Verificar duplicado
        if any(re.match(rf'\|\s*{re.escape(feature_id)}\s*\|', l, re.I) for l in lines):
            self.logger.info(f"ℹ️ Feature '{feature_id}' ya existe en {doc_path_relative}")
            return False

        # Encontrar fin de tabla
        table_end = next(
            (i for i in reversed(range(len(lines))) if lines[i].strip().startswith('|')),
            -1
        )
        if table_end == -1:
            self.logger.warning(f"⚠️ No se encontró tabla en {doc_path_relative}")
            return False

        # Insertar nueva fila
        new_line = (
            f"| {feature_id:<7} | {description:<40} | {status:<11} | "
            f"{priority:<10} | {datetime.now().strftime('%Y-%m-%d'):<12} |\n"
        )
        new_lines = lines[:table_end + 1] + [new_line] + lines[table_end + 1:]
        
        self._write_file(doc_path_relative, new_lines)
        self.logger.info(f"✅ Feature '{feature_id}' agregada a {doc_path_relative}")
        return True
    # ==================== FIN MÓDULO: ACTUALIZACIÓN DE TABLAS LEGACY ====================

    # ==================== INICIO MÓDULO: ESCANEO DE MÓDULOS EN CÓDIGO ====================
    def scan_source_modules(self, source_dir: Optional[str] = None) -> List[Dict]:
        """
        Escanea archivos .py en busca de bloques INICIO/FIN MÓDULO.
        Retorna lista de módulos detectados con metadata.
        """
        scan_dir = Path(source_dir) if source_dir else self.base_dir
        modules = []
        
        for py_file in scan_dir.rglob("*.py"):
            # Excluir directorios virtuales y de build
            if any(excl in str(py_file) for excl in ['.venv', '__pycache__', 'build', 'dist']):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                for match in self.config.MODULE_PATTERN.finditer(content):
                    module_name = match.group(1).strip()
                    # Calcular líneas del módulo
                    start_pos = match.start()
                    end_pos = match.end()
                    line_count = content.count('\n', start_pos, end_pos) + 1
                    
                    modules.append({
                        'file': str(py_file.relative_to(self.base_dir)),
                        'name': module_name,
                        'lines': line_count,
                        'file_size': py_file.stat().st_size
                    })
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo escanear {py_file}: {e}")
        
        self.logger.info(f"🔍 Escaneo completado: {len(modules)} módulos detectados")
        return modules
    # ==================== FIN MÓDULO: ESCANEO DE MÓDULOS EN CÓDIGO ====================

    # ==================== INICIO MÓDULO: ACTUALIZACIÓN DE DOCUMENTOS OBJETIVO ====================
    def update_technical_docs(self, modules: List[Dict], version: str = "2.9.1") -> bool:
        """Actualiza sección de actualizaciones en DOCUMENTACION_TECNICA.md."""
        doc_key = "technical"
        doc_path = self.config.TARGET_DOCS[doc_key]["path"]
        lines = self._read_file(doc_path)
        if not lines:
            return False

        # Buscar sección de actualizaciones
        update_marker = self.config.TARGET_DOCS[doc_key]["section_markers"]["updates"]
        section_idx = next(
            (i for i, l in enumerate(lines) if update_marker in l),
            -1
        )
        
        if section_idx == -1:
            # Crear sección si no existe
            self.logger.info(f"📝 Creando sección '{update_marker}' en {doc_path}")
            lines.append(f"\n## {update_marker} (v{version})\n")
            section_idx = len(lines) - 1

        # Generar entrada de changelog
        today = datetime.now().strftime('%Y-%m-%d')
        entry = [
            f"\n### 🛠️ Refactorización de Carga de Módulos ({today})\n",
            f"- ✅ **Módulos detectados**: {len(modules)}\n"
        ]
        
        # Listar módulos agrupados por archivo
        by_file = {}
        for mod in modules:
            by_file.setdefault(mod['file'], []).append(mod['name'])
        
        for file, names in by_file.items():
            entry.append(f"- 📦 `{file}`: {', '.join(names[:3])}{'...' if len(names)>3 else ''}\n")
        
        entry.append("\n---\n")
        
        # Insertar entrada después del header de sección
        new_lines = lines[:section_idx + 1] + entry + lines[section_idx + 1:]
        self._write_file(doc_path, new_lines)
        return True

    def update_operations_manual(self, changes: List[str], version: str = "2.9.1") -> bool:
        """Actualiza notas de operación en OPERATIONS_MANUAL.md."""
        doc_key = "operations"
        doc_path = self.config.TARGET_DOCS[doc_key]["path"]
        lines = self._read_file(doc_path)
        if not lines:
            return False

        # Buscar sección de notas
        notes_marker = self.config.TARGET_DOCS[doc_key]["section_markers"]["notes"]
        section_idx = next(
            (i for i, l in enumerate(lines) if notes_marker in l),
            -1
        )
        
        if section_idx == -1:
            self.logger.warning(f"⚠️ Sección '{notes_marker}' no encontrada en {doc_path}")
            return False

        # Generar entrada de notas
        today = datetime.now().strftime('%Y-%m-%d')
        entry = [
            f"\n### ✅ Mejoras en Estabilidad (v{version} - {today})\n"
        ]
        for change in changes:
            entry.append(f"- {change}\n")
        entry.append("\n")
        
        # Insertar después del header de sección
        new_lines = lines[:section_idx + 1] + entry + lines[section_idx + 1:]
        self._write_file(doc_path, new_lines)
        return True
    # ==================== FIN MÓDULO: ACTUALIZACIÓN DE DOCUMENTOS OBJETIVO ====================

    # ==================== INICIO MÓDULO: SINCRONIZACIÓN AUTOMÁTICA COMPLETA ====================
    def auto_sync_all(self, version: str = None) -> bool:
        """
        Ejecuta sincronización completa: escanea código, actualiza docs.
        Diseñado para ser llamado desde build_exe.py o hooks de Git.
        """
        self.logger.info("🚀 Iniciando sincronización automática de documentación...")
        
        # 1. Escanear módulos en código fuente
        modules = self.scan_source_modules()
        
        # 2. Preparar metadata de versión
        if not version:
            version = self._detect_version_from_code()
        
        # 3. Actualizar DOCUMENTACION_TECNICA.md
        tech_updated = self.update_technical_docs(modules, version)
        
        # 4. Actualizar OPERATIONS_MANUAL.md con cambios relevantes
        changes = [
            f"Refactorización de imports con degradación elegante",
            f"Implementación de lazy loading para {len([m for m in modules if 'service' in m['name'].lower()])} servicios",
            f"Corrección de sintaxis para compatibilidad con PyInstaller"
        ]
        ops_updated = self.update_operations_manual(changes, version)
        
        # 5. Log de resultados
        if tech_updated and ops_updated:
            self.logger.info(f"✅ Sincronización completada (v{version}): {len(modules)} módulos documentados")
            return True
        else:
            self.logger.warning("⚠️ Sincronización parcial: revisar logs para detalles")
            return False

    def _detect_version_from_code(self) -> str:
        """Intenta detectar versión desde gui_app.py o config."""
        gui_path = self.base_dir / "gui_app.py"
        if gui_path.exists():
            content = gui_path.read_text(encoding='utf-8')
            match = re.search(r'v[\d\.]+(?:-[A-Z]+)?', content, re.I)
            if match:
                return match.group(0)
        return "2.9.1"  # Fallback
    # ==================== FIN MÓDULO: SINCRONIZACIÓN AUTOMÁTICA COMPLETA ====================

    # ==================== INICIO MÓDULO: UTILIDADES ADICIONALES ====================
    def clear_cache(self):
        """Limpia cache interno de lecturas de archivo."""
        self._cache.clear()
        self.logger.debug("🗑️ Cache de DocUpdater limpiado")

    def get_document_status(self, doc_key: str) -> Dict:
        """Retorna metadata sobre un documento objetivo."""
        if doc_key not in self.config.TARGET_DOCS:
            return {"error": f"Documento '{doc_key}' no configurado"}
        
        doc_info = self.config.TARGET_DOCS[doc_key]
        full_path = self.base_dir / doc_info["path"]
        
        return {
            "exists": full_path.exists(),
            "size": full_path.stat().st_size if full_path.exists() else 0,
            "last_modified": datetime.fromtimestamp(
                full_path.stat().st_mtime
            ).isoformat() if full_path.exists() else None,
            "sections": list(doc_info["section_markers"].keys())
        }
    # ==================== FIN MÓDULO: UTILIDADES ADICIONALES ====================
# ==================== FIN MÓDULO: CLASE PRINCIPAL DOCUPDATER ====================


# ==================== INICIO MÓDULO: PUNTO DE ENTRADA STANDALONE ====================
if __name__ == "__main__":
    """Ejecución directa para testing o CI/CD."""
    import sys
    
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    version = sys.argv[2] if len(sys.argv) > 2 else None
    
    updater = DocUpdater(base)
    success = updater.auto_sync_all(version)
    
    sys.exit(0 if success else 1)
# ==================== FIN MÓDULO: PUNTO DE ENTRADA STANDALONE ====================