# KDP Master Suite

**Version:** 3.4.7-Elite Platinum
**Ultima actualizacion:** 2024-05-30
**Actualización Automática (v3.4.7):** Gestión Avanzada de Entornos y Seguridad
> **Pipeline**: YouTube → Transcripcion → Base de Conocimiento

---

## Inicio Rapido

### Opcion 1: Ejecutable (Recomendado)
```bash
dist\KDP_Transcriptions.exe
```

### Opcion 2: Desde codigo fuente
```bash
pip install -r requirements.txt
python gui_app.py
```

### Opcion 3: Modo desarrollo
```bash
pip install watchdog
python watcher.py
```

---

## Caracteristicas

### Descargas
- Descarga automatica de subtitulos VTT/SRT desde YouTube
- Cola de descargas con reintentos automaticos
- Drag & drop de archivos
- Normalizacion de URLs de YouTube

### Procesamiento
- Limpieza y normalizacion de transcripciones
- Eliminacion de timestamps y metadatos
- Deteccion de duplicados por hash MD5
- **NUEVO:** Deduplicación semántica por `content_checksum` (evita integrar texto idéntico)
- Procesamiento paralelo de archivos
- **NUEVO:** Deteccion de contenido duplicado entre canales

### Inteligencia (KB)
- Clasificacion automatica de contenido con IA (Gemini/OpenAI)
- Integracion a base de conocimiento categorizada
- **NUEVO:** Sincronización automática de títulos si cambian en YouTube
- Busqueda instantanea en transcripciones y KB mediante indexacion
- Exportacion de indice web HTML

### Monitor de Canales
- Monitoreo automatico de canales YouTube
- Deteccion de nuevos videos en tiempo real
- Normalizacion de handles (@canal, /c/Canal, /channel/ID)
- Descarga y procesamiento automatico de transcripciones
- **NUEVO:** Filtrado inteligente de Shorts (videos < 60s)
- **NUEVO:** Filtrado por antigüedad configurable (`max_age_days`)
- **NUEVO:** Notificaciones diferenciadas de estado (Nuevos/Reposts/Actualizados)
- Integracion automatica a la base de conocimiento

### Gestión de Entornos (NUEVO v3.4.7)
- Editor visual de archivos `.env` integrado.
- Cifrado AES-256 de secretos (API Keys) localmente.
- Auditoría de cambios con historial de usuarios.
- Validación dinámica de conectividad (Ollama/APIs).
- Soporte para perfiles conmutables (Dev/Prod).
- Exportación/Importación de configuración en JSON.

### Dashboard
- Servidor web para monitoreo remoto
- **NUEVO:** Métricas de hardware en vivo (CPU, RAM) mediante `psutil`
- **NUEVO:** Autenticación mediante tokens dinámicos `secrets-based`
- **NUEVO:** Seguimiento del tamaño físico de la base de datos
- Visualización de estadísticas y actividad reciente en tiempo real

---

## Arquitectura

```
KDP_MASTER/
├── gui_app.py                    # Aplicacion principal (GUI)
├── build_exe.py                  # Script de compilacion PyInstaller
├── check_updates.py              # Verificador de actualizaciones
├── main.py                       # Entry point alternativo
├── requirements.txt              # Dependencias Python
├── SPEC.md                       # Especificacion de requisitos
├── dist/
│   └── KDP_Transcriptions.exe    # Ejecutable portable
├── app/
│   ├── api/                      # Endpoints para el dashboard web
│   ├── core/                     # Core (config, security, logger, ui_framework)
│   ├── database/                 # SQLite database manager
│   ├── services/                 # Servicios (download, processing, monitor, knowledge)
│   └── ui/                       # Interfaz de usuario
│       └── tabs/                 # Pestanas modulares
├── data/                        # Datos de entrada (transcripciones crudas)
├── outputs/                     # Datos procesados
├── knowledge/                   # Base de conocimiento categorizada
├── logs/                        # Archivos de log
├── backups/                     # Backups automaticos
├── .agent/                      # Reglas y workflows del sistema
│   ├── rules/                   # 10 reglas de comportamiento
│   └── workflows/               # 20 flujos de trabajo
└── .agent-templates/            # Templates para nuevos proyectos
    └── templates/
        └── SOFTWARE_TEMPLATE.md # Template generico SOMD
```

---

## Cambios en v2.5.2

- Gestor de Temas JSON personalizado con editor visual
- ThemeEditorWindow con validación en tiempo real
- Sistema de herencia de temas (dark/light base)
- Templates: purple_dream.json, ocean_light.json

## Cambios en v2.5.1

- Eliminacion de agentes GEM internos (ya no necesarios)
- Pipeline simplificado: YouTube → Transcripcion → KB
- Pestana "Agentes" eliminada de la UI
- Categoria "Matriz de Roles (GEM)" eliminada del sistema de clasificacion
- Agregado SPEC.md con especificacion de requisitos
- Agregado SOFTWARE_TEMPLATE.md como template reutilizable

---

## Tech Stack

- **GUI:** tkinter + sv-ttk (tema moderno)
- **Download:** yt-dlp
- **Database:** SQLite
- **AI:** Google Gemini / OpenAI
- **Security:** AES-256-GCM para API keys
- **Build:** PyInstaller

---

## Configuracion

### Modo DEMO (Sin API Key)
Funciona inmediatamente sin configuracion adicional.

### Modo PRODUCCION (Con IA)
1. Obtén tu API key: https://aistudio.google.com/app/apikey
2. Ve a **Herramientas → Configurar IA** en la app
3. Selecciona proveedor (Gemini/OpenAI) e ingresa la clave
4. La clave se encripta automaticamente

### Variables de Entorno (.env)
```env
AI_PROVIDER=gemini
AI_API_KEY=tu_clave_aqui
MONITOR_INTERVAL_MINUTES=60
MAX_VIDEOS_PER_CHECK=30
AUTO_MONITOR_ENABLED=true
```

---

## Licencia

Copyright 2026 Editorial Zahlut
Todos los derechos reservados.