# 🚀 KDP Master Suite - Release Notes

**Versión actual:** 2.5.1  
**Última actualización:** 2026-04-09

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
