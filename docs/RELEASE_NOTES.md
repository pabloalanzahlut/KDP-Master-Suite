# KDP Master Suite - Release Notes

**Version actual:** 3.4.8
**Ultima actualizacion:** 2026-05-08

---

## v3.4.8 - Fix: Error tkinter -style

**Fecha:** 8 de Mayo, 2026
**Estado:** Producción Estable (Bug Fix)

### Problema Resuelto

| # | Problema | Descripcion |
|---|---------|-------------|
| 1 | unknown option "-style" | Error al iniciar aplicación en línea 3259 |
| 2 | Pestaña Configuración invisible | No se mostraba por error de sintaxis |
| 3 | customtkinter no incluido | Faltaba en spec de PyInstaller |

### Solución Implementada

- Eliminado línea inválida `new_videos_frame.configure(style=)` en línea 3259
- Actualizado spec de PyInstaller para incluir customtkinter
- Agregados módulos de Inteligencia (Ollama) al build
- Incluido directorio app/ y modules/ en el spec
- Corregido error de sintaxis en try/except de settings_tab

### Cambios en Spec

```python
# Agregado al spec:
datas += [('app', 'app'), ('modules', 'modules')]
hiddenimports += ['customtkinter', 'app.ui.tabs.settings_tab', 
                  'app.modules.processing.integrate_knowledge', 
                  'app.core.ollama_pool']
```

---

## v3.4.7 - Advanced Configuration Central (Elite)

**Fecha:** 30 de Mayo, 2024
**Estado:** Producción Estable (Enterprise)

### Hitos Logrados

| # | Funcionalidad | Descripción | Estado |
|---|---------------|-------------|--------|
| 1 | Panel UI .env | Editor visual con resaltado y soporte multi-perfil | ✅ PASS |
| 2 | Secrets Cifrados| Protección AES-256 para llaves de Gemini/OpenAI | ✅ PASS |
| 3 | Validación URL | Comprobación proactiva de conectividad antes de guardar | ✅ PASS |
| 4 | Export/Import Config | Exportación e importación de perfiles en JSON | ✅ PASS |
| 5 | Hot Reload | Recarga de variables sin reiniciar la aplicación | ✅ PASS |
| 6 | Historial de Cambios | Visor visual de auditoría de cambios | ✅ PASS |
| 7 | Mapeo de Variables | Detección de variables presentes en código/template | ✅ PASS |
| 8 | Template de Validación | Comparativa visual vs `.env.template` | ✅ PASS |
| 9 | Entornos Múltiples | Switcher de perfiles `.env`, `.env.dev`, `.env.prod` | ✅ PASS |
| 10| Validación Dinámica | Botón de testeo para Ollama y servicios externos | ✅ PASS |

---

## v2.6.2 - Fix: SERVICE UNAVAILABLE Error

**Fecha:** 20 de Abril, 2026
**Estado:** Producción Estable (Stable)

### Problema Resuelto

| # | Problema | Descripcion |
|---|---------|-------------|
| 1 | SERVICE UNAVAILABLE | Error al hacer clic en "Pausar Monitor" o cualquier botón del Monitor |

### Causa Raíz

El patrón de lazy loading de `db_manager` y `monitor_service` fallaba silenciosamente en la primera inicialización, asignando `False` como centinela y impidiendo reintentos.

### Solución Implementada (FIX-A)

- Añadidas variables `_db_manager_failed` y `_monitor_service_failed` para trackear fallos
- Modificadas las properties lazy loading para reintentar inicialización si hubo fallo anterior
- Mejorados mensajes de error para mostrar el error real en lugar de "Servicio no disponible"
- Logging detallado de cada intento de inicialización

### Archivos Modificados

| # | Archivo | Cambio |
|---|--------|-------|
| 1 | gui_app.py | Props db_manager y monitor_service ahora reintentan al fallar |
| 2 | gui_app.py | toggle_monitor_service mejorado con lógica de reintento |
| 3 | app/ui/tabs/monitor_tab.py | start_monitor, stop_monitor, check_now con validación previa |

---

## v2.6.1 - Mejor Logging y Notificaciones

**Fecha:** 21 de Abril, 2026
**Estado:** Producción Estable (Stable)

### Cambios Realizados

| # | Cambio | Descripcion | Estado |
|---|--------|-------------|--------|
| 1 | Notificaciones Diferenciadas | Formato "X nuevos | Y reposts | Z actualizados" en el resumen final | ✅ PASS |
| 2 | Logging Estructurado | Auditoría JSON detallada para shorts, cambios de título y reposts | ✅ PASS |

## v2.6.0 - Monitoreo Inteligente y Deduplicación Semántica

**Fecha:** 20 de Abril, 2026
**Estado:** Producción Estable (Stable)

### Cambios Realizados

| # | Cambio | Descripcion | Estado |
|---|--------|-------------|--------|
| 1 | Detección de Shorts | Filtrado automático de videos < 60s para optimizar la KB | ✅ PASS |
| 2 | Sincronización de Títulos | Actualización automática en DB si el título cambia en YouTube | ✅ PASS |
| 3 | Filtrado por Fecha | Parámetro `max_age_days` para ignorar contenido histórico irrelevante | ✅ PASS |
| 4 | Deduplicación Semántica | Implementación de `content_checksum` para evitar transcripciones duplicadas | ✅ PASS |
| 5 | Detección de Reposts | Análisis de antigüedad de videos "nuevos" en el feed del canal | ✅ PASS |

### Mejoras Técnicas

- **Base de Datos**: Migración v2.8 completada. Se añadieron campos `content_checksum`, `duration_seconds` y `tags` con índices optimizados.
- **Monitor Service**: Refactorización del flujo de detección para usar `ThreadPoolExecutor` en escaneos paralelos y orquestador de inteligencia.

---

## v2.5.10 - Mantenimiento y Estabilidad

**Fecha:** 14 de Abril, 2026  
**Estado:** Producción Estable (Stable)

### Cambios Realizados

| # | Cambio | Descripcion | Estado |
|---|--------|-------------|--------|
| 1 | Detección de Shorts | Omisión automática de videos < 60 segundos para calidad de KB | ✅ PASS |
| 2 | Sincronización de Títulos | Actualización automática en DB si el título cambia en YouTube | ✅ PASS |
| 3 | Filtrado por Fecha | Parámetro `max_age_days` para ignorar contenido antiguo | ✅ PASS |
| 4 | Deduplicación Semántica | Implementación de `content_checksum` en `videos` y `db_manager` | ✅ PASS |
| 5 | Detección de Reposts | Análisis cronológico entre fecha de subida y descubrimiento | ✅ PASS |

### Mejoras en Base de Datos

- **Tabla `videos`**: Añadida columna `content_checksum` e índice `idx_videos_content_checksum`.
- **Métodos**: `check_content_checksum_exists` y `update_video_content_checksum` implementados.

### Lógica de Monitoreo

- El monitor ahora realiza una extracción plana optimizada y aplica un orquestador de inteligencia antes de proceder a la descarga, ahorrando recursos y ancho de banda.
- Se corrigió la redundancia en llamadas a `yt-dlp` en el flujo de escaneo de canales.

---

## v2.5.9 - Dashboard Ports + IA Fix

**Fecha:** 14 de Abril, 2026  
**Estado:** Produccion Estable (Stable)

### Cambios Realizados

| # | Cambio | Descripcion | Estado |
|---|--------|-------------|--------|
| 1 | Rango puertos dashboard | Expandido a 7000-9999 (antes 8000-9000) | ✅ PASS |
| 2 | Fix error IA image.png | KnowledgeIntegrator inicializado en modo seguro (ai_provider="none") | ✅ PASS |
| 3 | Build output folder | Cambiado de dist/ a output/ para evitar conflictos | ✅ PASS |
| 4 | Auto-build script | Script automatizado para build sin manual intervention | ✅ PASS |

### Problema Resuelto

- Error "Cannot read image.png (this model does not support image input)" al iniciar la app
- Solucion: KnowledgeIntegrator iniciado en modo local (sin IA) por defecto para evitar errores de imagen

### Build Resultado

| Metrica | Valor |
|---------|-------|
| Artefacto | `output/KDP_Transcriptions/KDP_Transcriptions.exe` |
| Tamano | 36.1 MB (onedir) |
| Tiempo | 118.3s |
| Warning deprecated | 0 |

---

## v2.5.8 - Google GenAI SDK Migration

**Fecha:** 14 de Abril, 2026  
**Estado:** Produccion Estable (Stable)

Migracion completa de `google-generativeai` (EOL) a `google-genai` SDK.

### Cambios Realizados

| # | Cambio | Descripcion | Estado |
|---|--------|-------------|--------|
| 1 | Dependencia desinstalada | `pip uninstall google-generativeai -y` | ✅ PASS |
| 2 | Hidden imports PyInstaller | `"google.generativeai"` → `"google.genai"`, `"google.api_core"` | ✅ PASS |
| 3 | Collect-all google.genai | Agregado al build config | ✅ PASS |
| 4 | integrate_knowledge.py | Import actualizado a nueva SDK | ✅ PASS |
| 5 | Limpieza fallback | Eliminado codigo legacy de fallback | ✅ PASS |

### Warnings PyInstaller Resueltos

| # | Mensaje Anterior | Estado Actual |
|---|------------------|---------------|
| 1 | `google.generativeai deprecated` | ✅ RESUELTO |
| 2 | `pycparser.lextab not found` | ⚠️ Ignorable (cache parser) |
| 3 | `matplotlib.tests OSError` | ⚠️ Ignorable (test data) |
| 4 | `urllib.contrib.emscripten` | ⚠️ Ignorable (optional) |
| 5 | `tbb12.dll not found` | ⚠️ Ignorable (numba optional) |

### Build Resultado

| Metrica | Valor |
|---------|-------|
| Artefacto | `dist/KDP_Transcriptions/KDP_Transcriptions.exe` |
| Tamano | 636.2 MB (onedir) |
| Tiempo | 178.9s |
| Warnings deprecacion | 0 |

### Prevencion Futura

- Paquete `google-generativeai` DESINSTALADO del entorno
- Solo `google-genai` (v1.72.0) permitido en requirements
- Build verificara ausencia de `google.generativeai` antes de compilar

---

## v2.5.7 - CI/CD Pipeline + Packaging Enterprise

**Fecha:** 14 de Abril, 2026  
**Estado:** Produccion Estable (Stable)

Esta version introduce herramientas de automatizacion corporativa: CI/CD, backup, packaging y health checks.

### Nuevas Herramientas Implementadas

#### Bloque 1: CI/CD (tools/ci_cd/)
| Herramienta | Descripcion | Estado |
|-------------|------------|--------|
| run_tests.py | Test runner con coverage y reportes | PASS |
| run_build.py | Pipeline de build centralizado | PASS |
| smoke_test.py | Post-build validation | PASS |

#### Bloque 2: Backup y Recovery (tools/backup/)
| Herramienta | Descripcion | Estado |
|-------------|------------|--------|
| backup_manager.py | Backup incremental con rotacion | PASS |
| integrity_check.py | Validacion de estado al inicio | PASS |
| restore.py | Restauracion desde backups | PASS |

#### Bloque 3: Packaging Enterprise (tools/packaging/)
| Herramienta | Descripcion | Estado |
|-------------|------------|--------|
| silent_install.py | Instalador silencioso | PASS |
| portable_check.py | Modo portable detection | PASS |
| checksum.py | SHA256 checksums | PASS |

#### Bloque 4: Scripts (tools/scripts/)
| Herramienta | Descripcion | Estado |
|-------------|------------|--------|
| health_check.py | Health endpoint HTTP | PASS |
| version.py | Semver auto-increment | PASS |

#### Bloque 5: Orchestrator
| Herramienta | Descripcion | Estado |
|-------------|------------|--------|
| pipeline.py | Orchestra todos los modulos | PASS |

### Tests de Validacion

| Test | Resultado |
|------|----------|
| Integrity Check | PASS (130 canales, 117 transcripciones) |
| Health Check | PASS (DB OK, Ollama OK, 401GB free) |
| Version Manager | PASS (v2.5.6) |
| Smoke Test | PASS (exe 37.22 MB) |

### Uso de las Herramientas

```bash
# Pipeline completo
python tools/pipeline.py --full

# Quick build
python tools/pipeline.py --quick

# Health check
python tools/pipeline.py --health
python tools/scripts/health_check.py --server

# Backup
python tools/backup/backup_manager.py --backup

# Version bump
python tools/scripts/version.py --bump minor

# Checksums
python tools/packaging/checksum.py --generate
```

---

## v2.5.6 - Test Suite + Favoritos Verificacion

**Fecha:** 13 de Abril, 2026  
**Estado:** Produccion Estable (Stable)

Esta version valida el pipeline completo con tests automatizados y verificacion de persistencia de favoritos.

### Tests Automatizados Ejecutados

| # | Test | Resultado |
|---|------|----------|
| 1 | Import gui_app.py | ✅ PASS |
| 2 | DB connection (SQLite) | ✅ PASS (130 channels) |
| 3 | Persistence data | ✅ PASS (117 canales) |
| 4 | Ollama connection | ✅ PASS (reachable) |
| 5 | yt-dlp functionality | ✅ PASS (v2026.03.17) |
| 6 | KnowledgeIntegrator | ✅ PASS |

### Verificación de Favoritos

- **Canales definidos:** Priority 3 (normal) = 130 canales
- **Favoritos (Priority 1):** 0 canales
- **Sistema de favoritos:** Campo `priority` en DB (1-5)

### Pipeline de Build

| Fase | Descripción | Estado |
|------|------------|--------|
| 1 | Clean build (__pycache__/build/dist/) | ✅ PASS |
| 2 | PyInstaller build | ✅ PASS |
| 3 | Verificación .exe | ✅ PASS |

### Artefacto Generado

- **Ejecutable:** `dist/KDP_Transcriptions/KDP_Transcriptions.exe`
- **Tamaño:** 708 MB (onedir mode)
- **Data incluido:** Yes (transcriptions + DB + nichos)

### Notas de Despliegue

- El ejecutable incluye `data/` dentro del bundle
- 117 canales con transcripciones verificadas
- Ollama debe estar corriendo en localhost:11434

---

## v2.5.5 - Build Pipeline Completo + Tests + Clean Build

**Fecha:** 13 de Abril, 2026  
**Estado:** Producción Estable (Stable)

Esta versión ejecuta el pipeline completo de validación con tests unitarios, clean build y verificación de persistencia.

### Pipeline Ejecutado

| Fase | Descripción | Estado | Resultado |
|------|-------------|--------|----------|
| 1 | Validación de gobernanza | ✅ PASS | 10 reglas + 20 workflows verificados |
| 2 | Tests unitarios (pytest) | ✅ PASS | 33/33 tests passed in 1.65s |
| 3 | Clean build | ✅ PASS | build/ + dist/ limpiados |
| 4 | PyInstaller build | ✅ PASS | KDP_Transcriptions.exe (743.6 MB) |
| 5 | Persistencia | ✅ PASS | data/ externo preservado |

### Warn/Error PyInstaller Analizados

| # | Mensaje | Origen | Impacto | Solución | Estado |
|---|---------|--------|---------|----------|--------|
| 1 | `pycparser.lextab not found` | Hidden imports | Bajo | Ignorable (caché parser) | ⚠️ Advertencia |
| 2 | `pycparser.yacctab not found` | Hidden imports | Bajo | Ignorable (caché parser) | ⚠️ Advertencia |
| 3 | `matplotlib.tests OSError` | Test data not installed | Bajo | Ignorable (no runtime) | ⚠️ Advertencia |
| 4 | `urllib.contrib.emscripten ModuleNotFoundError` | Hook optional | Bajo | Ignorable | ⚠️ Advertencia |
| 5 | `google.generativeai deprecated` | Paquete EOL | Medio | Migrar a google.genai | ⚠️ Warning |
| 6 | `Library not found: tbb12.dll` | numba dependency | Bajo | Ignorable (no blocking) | ⚠️ Advertencia |

### Métricas del Build

- **Tiempo total:** 61.0s
- **Artefacto:** `dist/KDP_Transcriptions/KDP_Transcriptions.exe`
- **Tamaño:** 743.6 MB (onedir mode)
- **Python:** 3.11.9
- **PyInstaller:** 7.0+

### Notas de Despliegue

- El ejecutable espera `data/` junto a la raíz del proyecto
- Cola vacía: `queue_state.json = []`
- Base de datos: `data/channel_monitor.db` activa

---

## v2.5.4 - Build de Validación PyInstaller

**Fecha:** 13 de Abril, 2026  
**Estado:** Producción Estable (Stable)

Esta versión valida el build completo del ejecutable standalone con integración de datos de usuario.

### Cambios Realizados

**Módulo 1: Clean Build Pipeline**
- Limpieza de `__pycache__/`, `build/`, `dist/` previo al build
- Build con `kdp.spec` → `KDP_Master_Suite.exe` (225.7 MB)

**Módulo 2: Validación de Warn/Error PyInstaller**
| # | Mensaje | Origen | Impacto | Estado |
|---|---------|--------|---------|--------|
| 1 | `urllib.contrib.emscripten ModuleNotFoundError` | PyInstaller hook | Bajo | ⚠️ Ignorable |
| 2 | `Hidden import 'Pillow' not found` | Hook optional | Bajo | ⚠️ Ignorable (PIL disponible) |
| 3 | `Library not found: tbb12.dll` | numba dependency | Bajo | ⚠️ Ignorable (no blocking) |

**Módulo 3: Verificación de Persistencia de Estado**
- `data/processed_videos.json`: ✅ 34,059 líneas - Tracking activo de videos
- `data/transcriptions/`: ✅ Múltiples canales con transcripciones
- `data/CANALES_LISTOS.csv`: ✅ Lista de canales monitoreados

### Notas de Despliegue

- El ejecutable se genera en: `dist/KDP_Master_Suite.exe`
- Los datos de usuario persisten en `data/` (fuera del bundle)
- El código espera `data/` junto al ejecutable o en la raíz del proyecto

---

## v2.5.3 - Fix TCL/Tk Runtime y Dashboard Auto-Start

**Fecha:** 13 de Abril, 2026  
**Estado:** Producción Estable (Stable)

Esta versión corrige el error crítico de Tcl/Tk en ejecutables empaquetados.

### Cambios Realizados

**Módulo 1: Fix TCL/Tk Runtime Hook** (`hooks/rthook_tcl.py`)
- Reescrito hook runtime para buscar carpetas tcl/tk en bundle usando glob
- Fallback a instalación original de Python

**Módulo 2: Fix Dashboard Variable Scope** (`gui_app.py`)
- Corregido UnboundLocalError en setup_dashboard_tab
- Widgets definidos ANTES de funciones anidadas que los usan

**Módulo 3: Auto-Inicio Dashboard** (`gui_app.py`)
- Dashboard se inicia automáticamente 2 segundos después de abrir la app
- Navegador se abre automáticamente

### Issues Resueltos

- FileNotFoundError: Tcl data directory not found (PyInstaller bootstrap)
- UnboundLocalError: cannot access local variable 'btn_server'

---

## v2.5.2 - Gestor de Temas Personalizados

## v2.5.2 - Gestor de Temas Personalizados

**Fecha:** 12 de Abril, 2026  
**Estado:** Producción Estable (Stable)

Esta versión implementa elGestor de Temas JSON con validación estricta y sistema de herencia.

### Cambios Realizados

- **Módulo 1: ThemeManager Extendido** (`app/core/ui_framework.py`)
  - Validación estricta de esquema JSON (colores hex válidos, fuentes del sistema)
  - Sistema de herencia (deep merge) con base "dark" o "light"
  - Métodos save_theme, load_custom_theme, list_available_themes
  
- **Módulo 2: Editor Visual JSON** (`app/ui/components/theme_editor.py`)
  - Nueva ventanaThemeEditorWindow con:
    - Panel izquierdo: Lista de temas disponibles
    - Panel central: Editor JSON con validación en tiempo real
    - Panel inferior: Botones (Nuevo / Guardar / Importar / Exportar / Preview / Validar)
  
- **Módulo 3: Conexión con Menú** (`gui_app.py`)
  - Menú "Gestionar Temas Personalizados..." conectado al editor
  - Carpeta `themes/` creada automáticamente al inicio
  
- **Módulo 4: Templates de Ejemplo** (`themes/`)
  - `purple_dream.json`: Tema oscuro con acentos morados
  - `ocean_light.json`: Tema claro con acentos azules

### Archivos Nuevos

- `app/ui/components/theme_editor.py` (Editor visual)
- `themes/purple_dream.json` (Template)
- `themes/ocean_light.json` (Template)

### Archivos Modificados

- `app/core/ui_framework.py`: ThemeManager extendido
- `gui_app.py`: Integración del editor

### Estructura del Tema JSON

```json
{
  "name": "Mi Tema",
  "base": "dark",
  "colors": {
    "accent": "#FF6B35"
  }
}
```

### Características de Seguridad

- Validación estricta: colores hex (#RGB o #RRGGBB), campos requeridos
- Herencia obligatoria: todos los temas heredan de "dark" o "light"
- Deep merge: sobrescribe solo lo definido en "colors"/"fonts"
- Imposible romper la app con tema mal formado

---

## v2.5.1 - Release de Simplificación

**Fecha:** 9 de Abril, 2026  
**Estado:** Producción Estable (Stable)

Esta versión simplifica el pipeline eliminando los agentes GEM internos que no eran necesarios para el workflow básico.

### Cambios Realizados

- **Eliminación de Agentes GEM**: Los agentes (copywriter, SEO, PPC, compliance) fueron eliminados del proyecto.
- **Pipeline Simplificado**: YouTube → Transcripción → Base de Conocimiento
- **Pestaña Agentes eliminada**: Ya no hay pestaña de agentes en la UI.
- **Categoría eliminada**: "Matriz de Roles (GEM)" eliminada del sistema de clasificación.
- **Documentación actualizada**: README, VALUE_PROPOSITION, backlog, roadmap reflejan los cambios.
- **SPEC.md agregado**: Archivo de especificación de requisitos (28 RF + 14 RNF).
- **SOFTWARE_TEMPLATE.md agregado**: Template genérico SOMD para nuevos proyectos.

### Archivos Eliminados

- `agents/` (gem_02_copywriter.py, gem_06_seo.py, etc.)
- `app/ui/tabs/agents_tab.py`

### Archivos Modificados

- `gui_app.py`: Eliminada pestaña Agentes, imports de AgentLoader
- `app/ui/main_window.py`: Eliminada pestaña Agentes
- `app/services/knowledge_integrator.py`: Categoría GEM eliminada
- `integrate_knowledge.py`: Categoría GEM eliminada

### Categorías de Clasificación (6 categorías)

1. Legalidad y Compliance
2. Matriz de Roles y Fases SOE
3. Fórmulas y Métricas
4. Investigación de Nichos
5. Amazon Ads y Marketing
6. Conocimiento General KDP

---

## v2.5.0 - Enterprise Gold Edition

**Fecha:** 4 de Abril, 2026  
**Estado:** Producción Estable (Stable)

Esta versión consolida KDP Master Suite como la plataforma definitiva para la gestión de conocimiento KDP, introduciendo arquitectura modular SOMD, monitor de canales mejorado y dashboard web.

---

## ✨ Novedades Destacadas

### 🏗️ Arquitectura SOMD

- **Migración Modular**: Reestructuración completa de monolito a servicios orientados (`app/core/`, `app/services/`, `app/ui/`).
- **Pestañas Modulares**: Cada pestaña es un módulo independiente con su propia lógica y widgets.
- **Hot Reloading**: Recarga de configuraciones sin reiniciar la aplicación.

### 📺 Monitor de Canales Mejorado

- **Normalización Robusta de Handles**: `@nombre` → URLs completas de forma automática.
- **Circuit Breaker**: Protección contra rate limiting de YouTube.
- **Acceso Directo a /videos**: Evita cache de la pestaña principal para detección precisa.
- **Logs Estructurados**: JSON en `logs/audit.log` para auditoría completa.

### 🧠 Base de Conocimiento

- **Clasificación Inteligente**: IA (Gemini/OpenAI) o reglas locales para categorización automática.
- **Checksums de Integridad**: MD5 para detectar modificaciones no autorizadas en manuales maestros.
- **Deduplicación Enterprise**: Hash MD5 de contenido real evita procesamiento duplicado.
- **7+ Categorías KDP**: Legalidad, Matriz de Roles, SOE, Fórmulas, Nichos, Amazon Ads, General.

### 🤖 Reglas del Sistema

- **10 Reglas del Sistema**: Comportamiento, seguridad, UI, arquitectura, documentación.
- **20 Workflows Definidos**: Flujos de trabajo para KB, transcripciones, pipelines, auditorías.

### 📊 Dashboard Web

- **Servidor Web Integrado**: Monitoreo remoto desde navegador.
- **Estadísticas en Tiempo Real**: Visualización de métricas del sistema.

### 🛡️ Seguridad Reforzada

- **API Keys**: Encriptación AES-256-GCM.
- **App Lock**: Prevención de ejecución dual.
- **Path Sanitization**: Protección contra ZIP traversal.
- **Atomic Writes**: Configuración guardada de forma atómica.

---

## 🛠️ Cambios Técnicos

- **14 Bugs Críticos Corregidos**: Desde `update_channel_stats_ui` no existente hasta ZIP path traversal vulnerability.
- **Rutas PyInstaller**: Corregido el problema de directorios temporales `_MEIxxxxx`.
- **Código Legacy**: Eliminado código duplicado y funciones no utilizadas.
- **Logger**: Sistema de logs rotativos con niveles + auditoría estructurada.

---

## 🐛 Bugs Corregidos

| # | Bug | Estado |
|---|-----|--------|
| 1 | `update_channel_stats_ui` no existía | ✅ Fix |
| 2 | `urllib.error.URLError` sin importar | ✅ Fix |
| 3 | `self.logger` usado antes de init | ✅ Fix |
| 4 | `self.blacklist` no definido si config corrupto | ✅ Fix |
| 5 | `db_manager` inicializado 2 veces | ✅ Fix |
| 6 | `disk_label` creado 2 veces | ✅ Fix |
| 7 | Menú "Ayuda" duplicado | ✅ Fix |
| 8 | `setup_agents_tab` no asignado a la clase | ✅ Fix |
| 9 | Error "image.png" en modelo de texto | ✅ Fix |
| 10 | Rutas PyInstaller apuntaban a `_MEIxxxxx` | ✅ Fix |
| 11 | ZIP path traversal vulnerability | ✅ Fix |
| 12 | `save_config` podía corromper archivo | ✅ Fix |
| 13 | `knowledge_integrator` base_dir incorrecto | ✅ Fix |
| 14 | Código legacy duplicado | ✅ Eliminado |

---

## 📦 Instalación

### Opción 1: Ejecutable (Recomendado)

```bash
dist\KDP_Transcriptions.exe
```

### Opción 2: Código Fuente

```bash
pip install -r requirements.txt
python gui_app.py
```

### Modo DEMO

Funciona inmediatamente sin configuración adicional. Sin API key, usa clasificación local por reglas.

---

*Desarrollado por Editorial Zahlut - Uso Privado*
