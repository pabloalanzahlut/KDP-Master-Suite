# Documentación Técnica - KDP Master Suite v3.2.3 Platinum Enterprise

## 🏗️ Arquitectura de Robustez (ISO 25010)

El sistema implementa una capa de resiliencia basada en tres pilares:

1. **Backup Service**: Localizado en `app/services/backup_service.py`, gestiona copias incrementales y rotación automática (7 días) de la base de datos `channel_monitor.db`.
2. **Integrity Checker**: Valida la integridad física (MD5) y estructural (SQLite PRAGMA) al inicio de `gui_app.py`.
3. **Recovery Tool**: Mecanismo de auto-restauración que detecta corrupción y ofrece volver al último punto estable conocido.

## 🚀 Pipeline de CI/CD

El sistema cuenta con un pipeline de calidad integral:
- **run_tests.py**: Suite de pruebas unitarias para servicios core.
- **dependency_auditor.py**: Escaneo de seguridad y gestión de versiones de librerías.
- **smoke_test.py**: Validación de estabilidad post-build.

## ⚙️ Gestión de Configuración (v3.0.0)

Se ha implementado `app/core/config_manager.py` basado en **Pydantic**.
- **Validación de Tipos**: Previene errores por datos corruptos en settings.json.
- **Defaults Inteligentes**: Asegura que el sistema inicie incluso ante fallos de lectura.

## ☁️ Sincronización Cloud (v2.9.0)

El sistema utiliza GitHub como motor de persistencia remota:
- **Automatización**: Ejecución vía `subprocess` de comandos Git.
- **Estrategia**: Los backups de la base de datos se versionan en un repositorio privado.
- **Configuración**: Activación opcional mediante la sección `cloud_sync` en `settings.json`.
- **Performance**: Operaciones asíncronas para evitar bloqueos en la UI.

## 📅 Motor de Programación (v2.8.0)

El sistema incluye un `ScheduleManager` que permite:
- Programación de tareas recurrentes de monitoreo.
- Registro de logs de ejecución en `logs/scheduler.log`.
- Interfaz visual en la pestaña "Programación" con control de estado thread-safe.

## 📊 Motor de Persistencia y Búsqueda

La base de datos SQLite ha sido optimizada con:

- **FTS5 (Full Text Search)**: Implementado para búsquedas instantáneas en transcripciones.
- **Deduplicación Semántica**: Uso de `content_checksum` en la tabla `videos` para evitar procesar contenido idéntico con diferentes IDs de YouTube.
- **Metadatos v2.6**: Soporte para tags, duración y métricas de engagement.

## 📦 Modo Portable

La aplicación detecta automáticamente su entorno de ejecución mediante `tools/packaging/portable_check.py`.

- **Instalado**: Usa rutas de sistema (`%APPDATA%`) para logs y persistencia.
- **Portable**: Mantiene todos los datos en la carpeta raíz (ideal para unidades externas).

## 🛡️ Seguridad y Gestión de Entornos (v3.4.7)

### EnvManager (Core) - Gestión de Variables de Entorno

Ubicado en `app/core/env_manager.py`, este módulo centraliza el acceso a la configuración del sistema:
- **Cifrado AES**: Utiliza `cryptography.fernet` para asegurar secretos en disco marcados con el prefijo `ENC:`.
- **Trazabilidad**: Implementa un logger de auditoría que guarda deltas de cambios en `data/env_history.json`.
- **Validación de Capa 4/7**: Verifica disponibilidad de servicios mediante sockets (L4) y peticiones HEAD (L7).
- **Atomicidad**: Las escrituras en `.env` son atómicas para prevenir corrupción de archivos.
- **Múltiples Entornos**: Soporte para `.env`, `.env.dev`, `.env.prod` conmutables desde la UI.
- **Exportación/Importación**: Permite guardar y cargar configuraciones como archivos JSON.
- **Hot Reload**: Recarga la configuración en memoria sin reiniciar la aplicación.

- **Cifrado de API Keys**: Implementado mediante `SecurityManager` para proteger claves de OpenAI y Gemini en el archivo `settings.json`.
- **Logs de Auditoría**: Registro persistente en `logs/audit.log` para cambios críticos de configuración.

---

## 🔧 Proceso de Build y Empaquetado (v2.9.2)

### Script: `build_exe.py`

El script de build utiliza **PyInstaller** para generar el ejecutable standalone:

| Recurso | Ruta Desarrollo | Ruta Frozen |
|---------|-----------------|-------------|
| Base dir | `os.path.dirname(__file__)` | `sys.executable` parent |
| Data | `./data/` | `{exe_dir}/data/` |
| Logs | `./logs/` | `{exe_dir}/logs/` |
| DB | `./data/kdp_master.db` | `{exe_dir}/data/kdp_master.db` |

---

## 🤖 60 Módulos SIN IA - v3.2.3 Platinum Enterprise

**Estado**: ✅ 100% Implementado (60/60 módulos)

Los 60 módulos SIN IA proporcionan funcionalidad sin inteligencia artificial:

| Pilar | Módulos | Descripción |
|-------|---------|-------------|
| 1 | 1-10 | Paginación y Renderizado Virtual |
| 2 | 11-20 | Validación Pre-Descarga |
| 3 | 21-30 | Throttling y API |
| 4 | 31-40 | Selección Masiva |
| 5 | 41-50 | Auditoría y Logging |
| 6 | 51-60 | Integración KDP |

**Ubicación**: [docs/60_MODULOS_SIN_IA.md](docs/60_MODULOS_SIN_IA.md)

---

## 🤖 60 Módulos CON IA - v3.2.3 Platinum Enterprise

**Estado**: ✅ 100% Implementado (60/60 módulos)

Los 60 módulos CON IA utilizan Ollama para análisis semántico avanzado:

| Pilar | Módulos | Descripción | Motor |
|-------|---------|-------------|-------|
| 1 | 1-10 | Análisis Semántico | Ollama |
| 2 | 11-20 | Predicción de Valor | Ollama |
| 3 | 21-30 | Filtrado Inteligente | Ollama |
| 4 | 31-40 | Optimización Descarga | Ollama |
| 5 | 41-50 | Integración KB | Ollama |
| 6 | 51-60 | Reportes Estrategia | Ollama |

**Motor IA**: Ollama (localhost:11434)

**Ubicación**: [docs/60_MODULOS_CON_IA.md](docs/60_MODULOS_CON_IA.md)

### Archivos Clave para CON IA

- **Engine**: `app/services/channel_curation_engine.py`
- **Dataclasses**: `VideoMetadata` (53 campos), `ChannelAnalysis` (13 campos)
- **GUI**: `gui_app.py` - `run_ia_video_analysis()`

### Testing

```python
from app.services.channel_curation_engine import ChannelCurationEngine, VideoMetadata

engine = ChannelCurationEngine()
result = engine.analyze_title_semantics("Amazon KDP Tutorial", "Learn publishing")
print(f"Relevancia: {result.kdp_relevance_score}")
```

---

## 🧪 Testing y Validación

### test_120.py

Script de prueba para verificar los 120 módulos:

```bash
python test_120.py
```

**Resultados esperados**:
- Import channel_curation_engine: OK
- Import db_manager: OK
- VideoMetadata fields: 53 fields
- ChannelAnalysis fields: 13 fields
- CON IA Pipeline: Health=40

---

*Generado automáticamente para KDP Master Suite Platinum Enterprise v3.2.3*
*Fecha: 2026-05-04*