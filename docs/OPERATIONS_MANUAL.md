# MANUAL DE OPERACIONES — KDP Master Suite

**Versión:** 2.5.1  
**Última actualización:** 2026-04-09

---

## Guía de Operaciones para Administradores del Sistema

---

## 1. Requisitos del Sistema

| Componente | Mínimo | Recomendado |
|---|---|---|
| **Sistema Operativo** | Windows 10 | Windows 11 |
| **RAM** | 4 GB | 8 GB |
| **Disco** | 500 MB libres | 2 GB+ (para transcripciones) |
| **Python** | 3.10+ | 3.11 |
| **Conexión** | Requerida (descargas YouTube) | Estable (anti-rate-limit) |

### Dependencias Críticas
- `yt-dlp` — Descarga de subtítulos
- `cryptography` — Encriptación AES-256
- `sv_ttk` — Tema visual moderno
- `sqlite3` — Base de datos (incluida en Python)

---

## 2. Instalación / Despliegue

### Modo Portable (Recomendado)
1. Copiar `KDP_Transcriptions.exe` a cualquier carpeta
2. Ejecutar — crea automáticamente: `data/`, `logs/`, `knowledge/`, `outputs/`

### Modo Desarrollo
```bash
cd KDP_MASTER
pip install -r requirements.txt
python gui_app.py
```

### Archivo `.env` (Opcional)
```env
GEMINI_API_KEY=tu_api_key_aqui
AI_PROVIDER=gemini
MONITOR_INTERVAL_MINUTES=60
YT_SLEEP_INTERVAL=5
YT_MAX_SLEEP_INTERVAL=30
```

---

## 3. Configuración

| Parámetro | Ubicación | Valor Default | Descripción |
|---|---|---|---|
| `input_dir` | `settings.json` | `data/transcriptions` | Directorio de descargas VTT/SRT |
| `output_dir` | `settings.json` | `outputs/transcriptions_processed` | Directorio de archivos CLEAN |
| `channels` | `data/channel_monitor.db` | `[]` | Canales monitoreados (SQLite) |
| `download_queue` | `settings.json` | `[]` | Cola de descargas pendientes |
| `MONITOR_INTERVAL_MINUTES` | `.env` | `60` | Intervalo de escaneo del monitor |
| `YT_SLEEP_INTERVAL` | `.env` | `5` | Pausa mínima entre requests a YouTube |
| `AI_PROVIDER` | `.env` | `none` | Proveedor IA: `gemini`, `openai`, `none` |

---

## 4. Procedimientos de Mantenimiento

### 4.1 Limpieza de Caché yt-dlp
- **Desde la app:** Pestaña Descargas → "🧹 Limpiar Caché"
- **Manual:** Eliminar carpeta `%TEMP%\yt-dlp\`
- **Frecuencia:** Semanal o después de errores de descarga

### 4.2 Backup de Base de Conocimiento
- **Automático:** Se ejecuta al cerrar la aplicación
- **Ubicación:** `backups/knowledge_backup_YYYY-MM-DD_HH-MM-SS.zip`
- **Manual:** Copiar carpeta `knowledge/` completa

### 4.3 Backup de Base de Datos (Canales)
- **Archivo:** `data/channel_monitor.db`
- **Frecuencia:** Semanal
- **Comando:** `copy data\channel_monitor.db data\channel_monitor.db.bak`

### 4.4 Rotación de Logs
- **App log:** `logs/app.log` — Rotación automática cada 5 MB (3 backups)
- **Audit log:** `logs/audit.log` — Rotación automática cada 1 MB (5 backups)
- **Limpieza manual:** Eliminar archivos `logs/app_*.log` antiguos

### 4.5 Reparación de Integridad de DB
- **Desde la app:** Menú Mantenimiento → "🔧 Reparar Integridad de Base de Datos"
- **Qué hace:** Verifica tablas, índices, y reconstruye si es necesario

---

## 5. Monitoreo del Sistema

### Indicadores de Salud
| Indicador | Cómo Verificar | Estado Normal |
|---|---|---|
| **Espacio en disco** | `shutil.disk_usage(input_dir)` | > 200 MB libres |
| **Conexión a internet** | Botón "Reintentar" en modo offline | Activa |
| **Base de datos** | Menú Mantenimiento → Diagnóstico | Sin errores |
| **Monitor activo** | Pestaña Monitor → "▶️ Verificar Ahora" | Responde en < 30s |
| **Cola de descargas** | Pestaña Descargas → Contador | Procesando o vacía |

### Recursos del Sistema
- **Memoria RAM:** ~150-300 MB en operación normal
- **CPU:** Picos durante procesamiento de archivos (< 50%)
- **Red:** Variable según velocidad de descarga de YouTube

---

## 6. Resolución de Incidentes

### Incidente: La aplicación no inicia
1. Verificar que Python 3.10+ esté instalado (modo desarrollo)
2. Eliminar archivo `.app.lock` si existe
3. Verificar que `settings.json` no esté corrupto
4. Revisar `logs/app.log` para errores de inicio

### Incidente: Error de API Key
1. Verificar que `.env` tenga `GEMINI_API_KEY` válido
2. Verificar que `AI_PROVIDER=gemini` en `.env`
3. Probar la API en https://aistudio.google.com/

### Incidente: Monitor no detecta videos
1. Verificar que haya canales activos en la DB
2. Ejecutar "▶️ Verificar Ahora" manualmente
3. Revisar `logs/app.log` para errores de yt-dlp
4. Verificar conexión a internet

### Incidente: Base de Conocimiento no se actualiza
1. Verificar que existan archivos `.txt` en `outputs/transcriptions_processed/`
2. Ejecutar análisis de manuales: Menú Mantenimiento → "📊 Analizar Manuales"
3. Verificar checksums: `knowledge/checksums.json`

### Incidente: Cola de descargas se congela
1. Botón "⏸️ Pausar" → "▶️ Reanudar"
2. Si persiste: cerrar y reabrir la aplicación
3. La cola se guarda en `settings.json` y se restaura

---

## 7. Auditoría y Seguridad

### Registro de Auditoría
- **Archivo:** `logs/audit.log`
- **Registra:** Importaciones/exportaciones de canales, cambios de configuración, errores críticos
- **Retención:** 5 archivos de backup (rotación automática)

### Archivos Sensibles
| Archivo | Contenido | Protección |
|---|---|---|
| `.master.key` | Clave AES-256 | Oculto en Windows (attribute hidden) |
| `.env` | API Keys | No se incluye en el EXE |
| `settings.json` | Configuración | Texto plano (no contiene secrets) |
| `channel_monitor.db` | Canales y videos | SQLite sin encriptación |

### Recomendaciones de Seguridad
1. No compartir `.master.key` ni `.env`
2. Backup de `data/` completo antes de cambios mayores
3. Ejecutar diagnóstico de salud semanalmente
4. Mantener yt-dlp actualizado (`pip install --upgrade yt-dlp`)
