# ⚙️ Manual de Operaciones - KDP Master Suite

**Versión:** 2.5.1  
**Última actualización:** 2026-04-09

---

## 1. Requisitos del Sistema

- **Sistema Operativo**: Windows 10/11 (x64).
- **Runtime**: Python 3.10+ (solo si se ejecuta desde código fuente).
- **IA (Opcional)**: API Key de Gemini o OpenAI para clasificación inteligente.
- **Hardware**: Mínimo 4GB RAM, 500MB espacio en disco + almacenamiento para transcripciones y KB.
- **Red**: Conexión a internet para descargas de YouTube y consultas a IA.

## 2. Instalación y Despliegue

1. **Ejecutable (Recomendado)**: Ejecute `dist\KDP_Transcriptions.exe`. No requiere instalación.
2. **Código Fuente**: `pip install -r requirements.txt` → `python gui_app.py`.
3. **Modo Desarrollo**: `python watcher.py` para hot reloading.
4. **Verificación**: Al iniciar, el sistema valida archivos, directorios y conexión automáticamente.

## 3. Gestión de Configuración

### Variables de Entorno (`.env`)

| Parámetro | Descripción | Valor por Defecto |
|-----------|-------------|-------------------|
| `AI_PROVIDER` | Proveedor de IA para clasificación | `none` |
| `AI_API_KEY` | Clave API encriptada (Gemini/OpenAI) | _(vacío)_ |
| `MONITOR_INTERVAL_MINUTES` | Intervalo de monitoreo de canales | `60` |
| `MAX_VIDEOS_PER_CHECK` | Máximo de videos a procesar por ciclo | `30` |
| `AUTO_MONITOR_ENABLED` | Activar monitoreo automático al iniciar | `true` |
| `DOWNLOAD_DIR` | Directorio de transcripciones crudas | `data/transcriptions` |
| `PROCESSED_DIR` | Directorio de transcripciones procesadas | `outputs/transcriptions_processed` |

### Configuración de IA

- **Acceso**: Herramientas → Configurar IA
- **Proveedores**: `none` (clasificación local), `gemini`, `openai`
- **Seguridad**: Las API keys se encriptan con AES-256-GCM antes de guardar

## 4. Procedimientos de Mantenimiento

### 4.1 Respaldo y Recuperación (Disaster Recovery)

**Respaldo Automático:**
- Se genera al cerrar la aplicación.
- Guarda `knowledge/` en `backups/` como ZIP con timestamp.

**Respaldo Manual (Pánico):**
- **Herramientas → Backup de Pánico**. Genera snapshot instantáneo.

**Restauración:**
1. Detenga la aplicación.
2. **Herramientas → Restaurar Backup**.
3. Seleccione el archivo ZIP de `backups/`.
4. Reinicie la aplicación.

### 4.2 Limpieza de Caché

- **yt-dlp**: Menú **Mantenimiento → Limpiar Caché yt-dlp**.
- **Sesión**: Menú **Mantenimiento → Resetear Sesión** (restablece estado de la app).

### 4.3 Integridad de la Base de Conocimiento

- **Verificación**: Menú **Mantenimiento → Reparar Integridad**.
- **Checksums**: El sistema verifica MD5 de manuales maestros para detectar modificaciones.
- **Reporte**: Menú **Mantenimiento → Reporte de Categorías** genera resumen de KB.

### 4.4 Monitoreo de Recursos

- **Indicadores**: Barra inferior muestra estado del sistema, progreso y espacio en disco.
- **Alertas**:
  - 🟡 **Amarillo**: Espacio en disco bajo. Planificar limpieza.
  - 🔴 **Rojo**: Espacio crítico. El procesamiento batch podría detenerse.

### 4.5 Monitor de Canales

- **Iniciar/Detener**: Pestaña Monitor de Canales → botón de control.
- **Añadir Canal**: Aceptar formatos `@canal`, `/c/Canal`, `/channel/ID`.
- **Ciclo**: Verifica → Detecta nuevos videos → Descarga VTT/SRT → Procesa → Integra en KB.

## 5. Solución de Problemas (Troubleshooting)

### Incidente: "La aplicación no inicia"
- **Diagnóstico**: Ejecute `python gui_app.py` desde terminal para ver errores.
- **Solución**: Elimine el archivo `.app.lock` si existe. Verifique Python 3.10+.

### Incidente: "Error de API Key"
- **Diagnóstico**: La clave es inválida o el proveedor no responde.
- **Solución**: Vaya a **Herramientas → Configurar IA**. Verifique la clave o cambie a `none`.

### Incidente: "Monitor no detecta videos"
- **Diagnóstico**: URLs inválidas o problema de conexión.
- **Solución**: Verifique que las URLs de canales sean correctas. Compruebe conexión a internet. Aumente `MONITOR_INTERVAL_MINUTES` si hay rate limiting.

### Incidente: "La KB no se actualiza"
- **Diagnóstico**: No hay archivos procesados o error de clasificación.
- **Solución**: Verifique que haya archivos `.txt` en el directorio de salida. Ejecute **Mantenimiento → Reparar Integridad**. Revise `logs/audit.log`.

### Incidente: "Error de rutas en ejecutable"
- **Diagnóstico**: PyInstaller apunta a directorio temporal `_MEIxxxxx`.
- **Solución**: Corregido en v2.5.0. Si persiste, ejecute desde código fuente.

## 6. Auditoría y Seguridad

- **App Lock**: Previene ejecución dual simultánea.
- **API Keys**: Encriptadas con AES-256-GCM. Nunca se envían fuera del sistema.
- **Atomic Writes**: Configuración guardada de forma atómica para evitar corrupción.
- **Path Sanitization**: Protección contra ZIP traversal en importaciones.
- **Logs de Auditoría**: `logs/audit.log` registra cada paso del pipeline.
- **Deduplicación**: Hash MD5 de contenido real evita procesamiento duplicado.

## 7. Health Check

- **Acceso**: Menú **Mantenimiento → Health Check**.
- **Verifica**: Configuración, conexión, directorios, base de datos, estado de IA.
- **Resultado**: Reporte completo del estado del sistema.

---

**Soporte Técnico**: Consulte MANUAL_USUARIO.md para guía completa del usuario.  
**Documentación Técnica**: Consulte DOCUMENTACION_TECNICA.md para arquitectura y desarrollo.
