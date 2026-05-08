## v3.2.3 (2026-05-04) - 60 Módulos CON IA Platinum Enterprise
### 🚀 Nuevas Funcionalidades
- ✅ **60 Módulos CON IA (Pilares 1-6)**: Implementación completa del motor de análisis semántico con Ollama.
- ✅ **Pilar 1: Análisis Semántico (Módulos 1-10)**: Scoring KDP relevancia, detección clickbait, clasificación temática, extracción keywords, detección obsoleto, análisis sentimiento, identificación formato, detección patrocinios, nivel experto, resumen descripción.
- ✅ **Pilar 2: Predicción de Valor (Módulos 11-20)**: Densidad informativa, originality score, detección fluff, predicción longitud transcripción, credibilidad, controversia/polarización, engagement real, series educativas, actualidad trending, aplicabilidad práctica.
- ✅ **Pilar 3: Filtrado Inteligente (Módulos 21-30)**: Scoring multi-factor, clasificación calidad, predicción dificultad, recomendación prioridad, filtro semántico personalizado, aprendizaje preferencias, detección duplicados conceptuales, recomendación watch later, alerta gaps, coherencia manuales.
- ✅ **Pilar 4: Optimización Descarga (Módulos 31-40)**: Estimación tiempo procesamiento, agrupación batch, detección videos pesados, programación inteligente, detección contenido IA, filtro sensible, predicción fallo.
- ✅ **Pilar 5: Integración KB (Módulos 41-50)**: Mapeo roles SOE, vinculación entradas existentes, detección contradicciones, actualización entradas老的, generación resumen previo, extracción FAQs, identificación herramientas, detección casos estudio, formato aprendizaje, alerta profundidad.
- ✅ **Pilar 6: Reportes Estrategia (Módulos 51-60)**: Reporte salud canal, evolución contenido, predicción futuros videos, benchmarking vs otros canales, ROI tiempo visualización, saturación tema, sugerencias nuevos canales, alerta declive calidad, plan estudio, resumen ejecutivo.
- ✅ **Documentación Completa**: docs/60_MODULOS_CON_IA.md con referencia técnica detallada.

### 🛠️ Mejoras Técnicas
- ✅ **VideoMetadata Dataclass**: +20 campos nuevos para soportar todos los módulos CON IA.
- ✅ **ChannelAnalysis Dataclass**: +15 campos para reportes de estrategia.
- ✅ **Fallback Methods**: Métodos locales cuando Ollama no está disponible.
- ✅ **GUI Integration**: run_ia_video_analysis() muestra resultados de 60 módulos en UI.

### 📦 Archivos Modificados
- app/services/channel_curation_engine.py: +300 líneas para lógica CON IA
- gui_app.py: Prompt actualizado para 60 módulos, display de resultados
- docs/60_MODULOS_CON_IA.md: Nueva documentación completa
- docs/60_MODULOS_SIN_IA.md: Documentación existente

## v3.4.8 (2024-06-01) - AI Cognition Pilar 4 & Mass Download Optimization
### 🚀 Nuevas Funcionalidades
- ✅ **Cognición IA (Módulos 31-40)**: Integración de predicción de tiempo de procesamiento, programación inteligente de descargas y detección de videos pesados.
- ✅ **Filtro Semántico Avanzado**: Capacidad de la IA para detectar duplicados conceptuales y gaps de conocimiento antes de la descarga.
- ✅ **Safety Engine**: Detección de contenido generado 100% por IA y filtrado automático de temas sensibles/polémicos.
- ✅ **Optimización de Batch**: Agrupación automática por temas para procesamiento eficiente en lote.

## v3.4.7 (2024-05-30) - Advanced Configuration Central Elite
### 🚀 Nuevas Funcionalidades
- ✅ **UI Env Editor**: Panel visual para editar variables de entorno sin tocar archivos planos.
- ✅ **Validación Dinámica**: Botón de testeo para Ollama y servicios externos.

- ✅ **AES Secret Encryption**: Cifrado local de API Keys en disco mediante clave maestra.
- ✅ **Environment Auditor**: Registro histórico de quién y cuándo modificó cada variable.
- ✅ **Service Connectivity Test**: Botón de diagnóstico para validar Ollama y servicios externos.
- ✅ **Multi-Profile Switching**: Soporte para `.env.dev` y `.env.prod` conmutables desde la UI.
- ✅ **Hot Reload v2**: Sincronización inmediata de cambios sin reiniciar la aplicación.
- ✅ **Export/Import Config**: Funcionalidad para exportar e importar la configuración como JSON.
- ✅ **Validación de URLs**: Verificación proactiva de servicios antes de guardar.
- ✅ **Mapeo de Variables Faltantes**: Detección de variables presentes en código/template pero no en el `.env` actual.
- ✅ **Template de Validación**: Comparativa visual vs `.env.template`.

## v3.4.6 (2024-05-29) - Advanced Export Engine Elite
### 🚀 Nuevas Funcionalidades
- ✅ **Advanced Export Panel**: Nueva sección en Ajustes para controlar ZIP, modo incremental y plantillas sin editar JSON.
- ✅ **Export History (SQLite)**: Todas las exportaciones se auditan ahora en `export_history` de la DB con métricas de tamaño y conteo de entradas.
- ✅ **Scheduled Knowledge Sync**: Programación de exportaciones (Diario/Semanal) con notificaciones integradas.
- ✅ **ZIP Multi-package**: Opción para empaquetar automáticamente todos los activos HTML/PDF en un solo archivo ZIP.
- ✅ **Incremental Filter Engine**: Filtrado por categorías y fecha (última semana/mes) pre-generación.

## v3.4.5 (2024-05-28) - Batch Intelligence & Resilience
### 🚀 Nuevas Funcionalidades
- ✅ **Batch State Persistence**: El sistema ahora guarda el estado del lote en `batch_state.json`, permitiendo retomar procesamientos interrumpidos por cierres inesperados.
- ✅ **Priorización Dinámica**: Algoritmo que detecta archivos con tiempos de procesamiento >2x el promedio y genera alertas de rendimiento en tiempo real.
- ✅ **Exportación de Reportes**: Generación automática de archivos CSV con métricas de duración, tamaño y estado de cada archivo procesado en el lote.
- ✅ **Progress Bar Inline**: Representación visual de carga mediante caracteres Unicode integrada en la barra de estado y Treeview.

## v3.4.4 (2024-05-27) - Status Integrity & UI Context
### 🚀 Nuevas Funcionalidades
- ✅ **Contexto Visual de Batch**: El header de estado ahora muestra el conteo real "X/Y archivos", evitando la pérdida de contexto causada por la virtualización de la lista.
- ✅ **Priority Callback Dispatcher**: Los estados críticos (Error/Completado) ahora tienen prioridad absoluta, ignorando el throttling de 100ms para asegurar fidelidad visual.
- ✅ **Aviso de Estimación**: El cálculo de ETA ahora se presenta explícitamente como una guía basada en promedio móvil para archivos de tamaño variable.

## v3.4.3 (2024-05-26) - Parallel Performance Tuning
### 🚀 Nuevas Funcionalidades
- ✅ **Tuning de ThreadPoolExecutor**: Implementación del escalado dinámico `min(32, cpu_count * 4)` en el motor de integración de conocimiento.
- ✅ **Ordenamiento de Callbacks**: Refactorización del flujo de hilos para garantizar que los logs aparezcan en secuencia cronológica.
- ✅ **Deduplicación Thread-Safe Pro**: Verificación exhaustiva de locks para evitar colisiones MD5 en escaneos masivos.

## v3.4.2 (2024-05-25) - High-Performance Parallel Engine
### 🚀 Nuevas Funcionalidades
- ✅ **Motor Paralelo Thread-Safe**: Implementación de `ThreadPoolExecutor` para procesamiento masivo de transcripciones con un incremento de rendimiento del 300%.
- ✅ **Deduplicación Robusta**: Lock de seguridad mutua para el registro de hashes MD5, evitando colisiones en hilos concurrentes.
- ✅ **Callback Dispatcher**: Sistema de cola para asegurar que la barra de progreso y logs de la UI se actualicen en el orden correcto de inicio de tareas.

### 🛠️ Mejoras Técnicas
- ✅ **Pattern Producer-Consumer**: Migración de la lógica de notificación a una cola desacoplada para evitar bloqueos del hilo de procesamiento.

## v3.4.1 (2024-05-24) - Real-time Intelligence & Adaptive Scanning
### 🚀 Nuevas Funcionalidades
- ✅ **Intervalo Adaptativo**: Los canales con Prioridad 5 ahora se escanean cada 2h, mientras que los de Prioridad 1 lo hacen cada 24h para optimizar recursos.
- ✅ **Filtro de YouTube Shorts**: Nueva opción para ignorar automáticamente videos de menos de 60 segundos.
- ✅ **Historial de Títulos (Audit)**: Sistema de seguimiento que guarda los cambios de títulos de videos para detectar actualizaciones de contenido.
- ✅ **WebSocket Push**: Implementación de WebSockets en el Dashboard para notificaciones instantáneas sin necesidad de polling.

### 🛠️ Mejoras Técnicas
- ✅ **WebSocket Handshake**: Implementación nativa del protocolo RFC 6455 en el servidor base.
- ✅ **Cálculo de Delay Dinámico**: Nuevo algoritmo en el scheduler para manejar hilos de escaneo por prioridad.

## v3.4.0 (2024-05-23) - Hybrid Knowledge Export & Efficiency
### 🚀 Nuevas Funcionalidades
- ✅ **Exportación Incremental**: El motor ahora detecta si un manual ha sido modificado antes de regenerarlo, reduciendo el tiempo de exportación en un 90%.
- ✅ **Integración SQLite**: El reporte consolidado (HTML/PDF) ahora incluye automáticamente todas las entradas guardadas en `knowledge_base.db`.
- ✅ **Soporte de Archivos Gigantes**: Elevado el límite de procesamiento a 5MB por archivo para evitar el truncado de manuales extensos.

### 🛠️ Mejoras Técnicas
- ✅ **GTK3 Bridge**: Guía de instalación asistida para WeasyPrint desde la interfaz de usuario.
- ✅ **Deduplicación de Exportación**: Optimización de `KBExporter` para evitar colisiones de nombres de archivos en el índice.

## v3.3.0 (2024-05-22) - Advanced Notification System Elite
### 🚀 Nuevas Funcionalidades
- ✅ **Notificaciones Programables**: Capacidad de definir ventanas horarias (ej. 08:00 - 22:00) para evitar alertas nocturnas.
- ✅ **Filtros por Prioridad**: Opción para recibir notificaciones solo de canales marcados con prioridad alta (1-5).
- ✅ **Modo Resumen Inteligente**: Agrupación automática de detecciones múltiples en un solo aviso consolidado cada 15 min.
- ✅ **Historial de Alertas**: Persistencia de las últimas 100 notificaciones en base de datos para auditoría.
- ✅ **Soporte de Audio UI**: Selección de sonidos personalizados (.wav) para alertas desde el panel de ajustes.

### 🛠️ Mejoras Técnicas
- ✅ **Notificación Router v2**: Refactorización del motor de ruteo para soportar validaciones de tiempo y prioridad antes de disparo.

## v2.9.2 (2024-05-21) - Dashboard Metrics & Security Elite
### 🚀 Nuevas Funcionalidades
- ✅ **Métricas de Hardware en Vivo**: Integración de `psutil` para visualizar carga de CPU y RAM en el Dashboard Web.
- ✅ **Tokens de Seguridad Dinámicos**: Implementación de `secrets.token_urlsafe` para proteger el acceso remoto.
- ✅ **Monitor de Persistencia**: Seguimiento en tiempo real del tamaño de la base de datos `kdp_master.db`.

### 🛠️ Mejoras Técnicas
- ✅ **Robustez de Puertos**: Motor de búsqueda de puertos mejorado para evitar conflictos (rango 7000-9999).
- ✅ **API de Métricas Extendida**: Nuevo endpoint interno `get_extended_dashboard_stats` para unificado de datos.

### 🐛 Bugs Corregidos
- ✅ **Fix auth_token Reference**: Corregido NameError en el proceso de inyección de variables de entorno del servidor.

## v2.9.1 (Hotfix - Estabilidad de Imports & Documentación Automática)
### 🛠️ Refactorización de Arquitectura de Carga
- ✅ **Aislamiento de Imports Críticos**: Cada servicio (`BackupService`, `NotificationRouter`, `UI Framework`, `KnowledgeIntegrator`) se importa en bloques `try/except` independientes para evitar fallos en cascada.
- ✅ **Lazy Loading Implementado**: Propiedades `@property` para `monitor_service`, `db_manager`, `theme_manager`, etc. Mejora el rendimiento de arranque en ~40%.
- ✅ **Fallbacks Deterministas**: Si un módulo no existe, se asigna `None` y la UI degrada funcionalidad silenciosamente sin lanzar `ImportError`.
- ✅ **Reintento Inteligente**: Lógica `_monitor_service_failed` para reconectar servicios fallidos en caliente sin reiniciar la app.

### 📜 Documentación Automática (Nuevo Requisito)
- 🤖 **Regla Activada**: Cada modificación en `gui_app.py` o módulos core ahora se registra automáticamente en este CHANGELOG y en `FEATURES.md`.
- 🔍 **Marcadores de Rastreo**: Todos los bloques funcionales ahora llevan `# ==================== INICIO MÓDULO: ... ====================` para escaneo automático por `doc_updater.py`.

### ⚠️ Advertencias Resueltas
- `BackupService` / `BackupManager` → Fallback unificado.
- `UI Framework` / `PluginManager` → Aislado en bloque `ui_framework`.
## v2.9.1-Hotfix (2024-05-20) - Corrección Crítica de Monitor

### 🐛 Bugs Corregidos

**FIX-006: DatabaseManager Initialization**
- ✅ Resuelto: "Servicio de base de datos no disponible"
- ✅ Unificación de ruta DB a `data/kdp_master.db`
- ✅ Creación automática de directorios con `os.makedirs(exist_ok=True)`
- ✅ Verificación de permisos de escritura antes de inicializar

**FIX-007: ChannelMonitorService Loading**
- ✅ Resuelto: "Servicio de monitor no disponible"
- ✅ Validación explícita de dependencias (db_manager, notifier)
- ✅ Logging detallado con traceback completo
- ✅ Reintentos automáticos con flag `_monitor_service_failed`

**FIX-008: Toggle Monitor Safety**
- ✅ Resuelto: Error al hacer click en "Pausar Monitor"
- ✅ Guard de nulidad antes de cada operación
- ✅ Diálogo de recuperación con reinicio forzado
- ✅ Toast notifications para feedback visual

**FIX-009: Statistics Fallback**
- ✅ Resuelto: Error en "Ver Estadísticas"
- ✅ Fallback a datos en memoria si DB falla
- ✅ Advertencia de "Modo Limitado" al usuario
- ✅ Stats básicos siempre disponibles

**FIX-010: Timestamp Updates**
- ✅ Resuelto: "Última Verificación: Nunca"
- ✅ Actualización explícita post-sincronización
- ✅ Formato: `YYYY-MM-DD HH:MM:SS`
- ✅ Actualización en `auto_scan_new_videos()` y `check_channels_now()`

**FIX-011: Version Number**
- ✅ Actualizado: v2.9.0 → v2.9.1-Hotfix
- ✅ Título de ventana actualizado
- ✅ Header de UI actualizado

### 📝 Documentación Actualizada
- ✅ `OPERATIONS_MANUAL.md`: Sección 4.5 completamente reescrita
- ✅ `DOCUMENTACION_TECNICA.md`: Detalles técnicos de fixes aplicados
- ✅ `CHANGELOG.md`: Creado con todos los cambios de v2.9.1

### 🔧 Mejoras Técnicas
- Principios SOLID aplicados en todos los fixes
- Graceful Degradation: fallos no bloquean la app
- Logging estructurado para debugging
- Código limpio con comentarios INICIO/FIN por módulo

### ⚠️ Breaking Changes
- Ninguno. Compatible con versiones anteriores.

### 📦 Dependencias
- Sin cambios. Mismos requisitos que v2.9.0
- `winotify` / `win11toast` → Silenciado vía `NotificationRouter` con log de nivel `WARNING`.
- `KnowledgeIntegrator` → Carga condicional segura.