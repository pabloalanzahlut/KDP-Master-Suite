# 📋 SPEC.md — Especificación de Requisitos
## KDP Master Suite v2.6.0

**Fecha:** 2026-04-09  
**Versión:** 2.6.0  
**Estado:** Producción con detección de duplicados implementada

---

## 1. Visión del Producto

Plataforma de gestión de conocimiento automatizada que extrae contenido de YouTube, lo organiza en transcripciones y lo clasifica en una base de conocimiento categorizada para investigación de nichos KDP.

**Pipeline:**
```
YouTube → Transcripción (VTT/SRT) → Limpieza → Base de Conocimiento (KB)
```

---

## 2. Requisitos Funcionales

### 2.1 Descarga de Contenido

| ID | Requisito | Prioridad | Estado |
|----|------------|----------|--------|
| RF-001 | Descargar subtitles VTT/SRT desde URLs de YouTube | Must Have | ✅ |
| RF-002 | Normalización de URLs (@canal, /c/, /channel/) | Must Have | ✅ |
| RF-003 | Cola de descargas con reintentos automáticos | Must Have | ✅ |
| RF-004 | Drag & drop de archivos | Should Have | ✅ |
| RF-005 | Validación de integridad post-descarga (MD5) | Should Have | ✅ |

### 2.2 Procesamiento

| ID | Requisito | Prioridad | Estado |
|----|------------|----------|--------|
| RF-006 | Limpieza y normalización de transcripciones | Must Have | ✅ |
| RF-007 | Eliminación de timestamps y metadatos | Must Have | ✅ |
| RF-008 | Detección de duplicados por hash MD5 | Must Have | ✅ |
| RF-009 | Procesamiento paralelo de archivos | Should Have | ✅ |
| RF-010 | Metadata enriquecida (título, descripción, tags, duración) | Could Have | ✅ |
| RF-010A | Detección de contenido duplicado entre canales | Must Have | ✅ |
| RF-010B | Motor híbrido de detección (Hash → Duration → Title → Tags → IA) | Should Have | ✅ |
| RF-010C | UI de decisión para contenido duplicado | Should Have | ✅ |

### 2.3 Inteligencia y Clasificación

| ID | Requisito | Prioridad | Estado |
|----|------------|----------|--------|
| RF-011 | Clasificación automática con IA (Gemini/OpenAI) | Must Have | ✅ |
| RF-012 | Clasificación por reglas locales (fallback) | Must Have | ✅ |
| RF-013 | Integración con Base de Conocimiento categorizada | Must Have | ✅ |
| RF-014 | Búsqueda indexada en transcripciones y KB | Should Have | ❌ |
| RF-015 | Exportación de índice web HTML | Should Have | ✅ |
| RF-016 | Exportación KB a PDF/HTML profesional | Could Have | ❌ |

### 2.4 Monitor de Canales

| ID | Requisito | Prioridad | Estado |
|----|------------|----------|--------|
| RF-017 | Monitoreo automático de canales YouTube | Must Have | ✅ |
| RF-018 | Detección de nuevos videos en tiempo real | Must Have | ✅ |
| RF-019 | Descarga y procesamiento automático | Must Have | ✅ |
| RF-020 | Circuit breaker para protección rate limiting | Must Have | ✅ |
| RF-021 | Filtros por palabras clave | Could Have | ✅ |
| RF-022 | Programación horaria del monitor | Could Have | ❌ |
| RF-023 | Notificaciones Windows Toast | Could Have | ✅ |

### 2.5 Interfaz de Usuario

| ID | Requisito | Prioridad | Estado |
|----|------------|----------|--------|
| RF-024 | GUI con pestañas modulares | Must Have | ✅ |
| RF-025 | Tema Dark/Light con framework centralizado | Must Have | ✅ |
| RF-026 | Recarga en caliente de configuraciones | Should Have | ✅ |
| RF-027 | Dashboard web para monitoreo remoto (embebido + externo) | Should Have | ✅ |
| RF-028 | Barra de progreso global y por archivo | Should Have | ✅ |
| RF-029 | Resumen post-batch con reintento | Could Have | ✅ |
| RF-030 | Scoring de relevancia KDP IA en flujo de descarga | Should Have | ✅ |
| RF-031 | Perfiles múltiples de filtros por palabras clave | Could Have | ✅ |

---

## 3. Requisitos No Funcionales

### 3.1 Rendimiento

| ID | Requisito | Meta |
|----|------------|------|
| RNF-001 | Tiempo de procesamiento por transcripción | < 30 segundos |
| RNF-002 | Detección exitosa de nuevos videos | 99% |
| RNF-003 | Búsqueda en KB | < 1 segundo |

### 3.2 Seguridad

| ID | Requisito | Estado |
|----|------------|--------|
| RNF-004 | API keys encriptadas con AES-256-GCM | ✅ |
| RNF-005 | App Lock para ejecución dual | ✅ |
| RNF-006 | Path Sanitization contra ZIP traversal | ✅ |
| RNF-007 | Atomic Writes para configuración | ✅ |

### 3.3 Escalabilidad

| ID | Requisito | Estado |
|----|------------|--------|
| RNF-008 | Arquitectura SOMD (Service-Oriented) | ✅ |
| RNF-009 | Plugins cargables dinámicamente | ✅ |
| RNF-010 | Base de datos SQLite normalizada | ✅ |

### 3.4 Fiabilidad

| ID | Requisito | Estado |
|----|------------|--------|
| RNF-011 | Backup automático al cerrar | ✅ |
| RNF-012 | Logs de auditoría estructurados | ✅ |
| RNF-013 | Checksums de integridad en KB | ✅ |
| RNF-014 | Deduplicación por MD5 | ✅ |

---

## 4. Arquitectura del Sistema

### 4.1 Estructura de Directorios

```
PROYECTO/
├── app/
│   ├── core/                    # Lógica fundamental
│   │   ├── config.py           # Gestión de configuración
│   │   ├── security.py       # Encriptación AES
│   │   ├── logger.py         # Logging
│   │   ├── ui_framework.py  # Tema y animaciones
│   │   └── plugin_manager.py # Sistema de plugins
│   ├── database/              # Persistencia
│   │   └── db_manager.py     # SQLite
│   ├── services/              # Lógica de negocio
│   │   ├── download_service.py
│   │   ├── processing_service.py
│   │   ├── monitor_service.py
│   │   └── knowledge_integrator.py
│   └── ui/                    # Interfaz
│       └── tabs/              # Pestañas modulares
├── data/                     # Datos entrada
├── outputs/                   # Datos salida
├── knowledge/                # Base de conocimiento
├── logs/                     # Logs
└── gui_app.py                # Entry point
```

### 4.2 Componentes Core

| Componente | Responsabilidad |
|-----------|----------------|
| `Config` | Rutas, API Keys, variables de entorno |
| `SecurityManager` | Encriptación AES-256-GCM |
| `Logger` | Logs rotativos + auditoría |
| `ThemeManager` | Temas Dark/Light |
| `PluginManager` | Carga dinámica de plugins |
| `DatabaseManager` | SQLite con migraciones |
| `DownloadService` | yt-dlp wrapper |
| `ProcessingService` | Limpieza + deduplicación |
| `MonitorService` | Vigilancia automática |
| `KnowledgeIntegrator` | Clasificación + KB |

---

## 5. Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| UI | Tkinter + sv_ttk |
| Backend | Python 3.10+ |
| Base de Datos | SQLite3 |
| Descargas | yt-dlp |
| Encriptación | cryptography |
| Build | PyInstaller |

---

## 6. Criterios de Aceptación

### 6.1 Funcionales

- [ ] El sistema puede descargar subtitles de cualquier URL de YouTube válida
- [ ] Las transcripciones se limpian y guardan en `outputs/`
- [ ] El contenido se clasifica automáticamente en 6 categorías
- [ ] El monitor detecta nuevos videos cada N minutos
- [ ] La configuración persiste entre sesiones

### 6.2 No Funcionales

- [ ] La aplicación inicia en menos de 5 segundos
- [ ] No hay vulnerabilidad crítica de seguridad
- [ ] El ejecutable portable funciona sin instalación
- [ ] El backup se genera automáticamente al cerrar

---

## 7. Léxico de Errores (Referencia)

| Código | Descripción | Solución |
|--------|------------|--------|
| E001 | URL de YouTube inválida | Verificar formato de URL |
| E002 | Error de conexión | Verificar internet |
| E003 | API key inválida | Revisar clave en configuración |
| E004 | Archivo corrupto | Eliminar y volver a descargar |
| E005 | Rate limit excedido | Esperar y reintentar |

---

## 8. Glosario

| Término | Definición |
|---------|-----------|
| **KB** | Base de Conocimiento (knowledge/) |
| **SOMD** | Service-Oriented Modular Desktop |
| **GEM** | Generative Expert Modules (eliminado en v2.5.1) |
| **Deduplicación** | avoiding procesamiento de contenido duplicado |
| **Circuit Breaker** | Protección contra rate limiting |
| **Dual-write** | Escritura simultánea a DB y archivos |

---

**Documento generado automáticamente desde PRODUCT_BACKLOG.md, PRODUCT_ROADMAP.md y ANALISIS_EXPERTOS.md**

*Última actualización: 2026-04-09*