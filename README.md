# KDP Master Suite

**Version:** 2.4.3  
**Ultima actualizacion:** 2026-04-11

> **Pipeline**: YouTube - Transcripcion - Base de Conocimiento

---

## Inicio Rapido

### Opcion 1: Ejecutable (Recomendado)
```bash
dist\KDP_Transcriptions.exe
```

### Opcion 2: Desde codigo fuente
```bash
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
- Procesamiento paralelo de archivos

### Inteligencia (KB)
- Clasificacion automatica de contenido con IA (Gemini/OpenAI)
- Integracion a base de conocimiento categorizada
- Busqueda instantanea en transcripciones y KB mediante indexacion
- Exportacion de indice web HTML

### Monitor de Canales
- Monitoreo automatico de canales YouTube
- Deteccion de nuevos videos en tiempo real
- Descarga y procesamiento automatico de transcripciones
- Integracion automatica a la base de conocimiento

### Dashboard
- Servidor web para monitoreo remoto
- Visualizacion de estadisticas en tiempo real

---

## Arquitectura

```
KDP_MASTER/
├── gui_app.py                    # Aplicacion principal (GUI)
├── build_exe.py               # Script de compilacion PyInstaller
├── check_updates.py             # Verificador de actualizaciones GitHub
├── main.py                   # Entry point
├── requirements.txt            # Dependencias Python
├── dist/
│   └── KDP_Transcriptions.exe
├── modules/
│   ├── dashboard.py
│   ├── manual_analyzer.py
│   └── ...
├── .agent/                  # Reglas y workflows del sistema
│   ├── rules/
│   └── workflows/
└── knowledge/              # Base de conocimiento
```

---

## Dependencias Opcionales

### GTK3 Runtime (para exportar PDF)
Para generar archivos PDF desde la Base de Conocimiento, se requiere GTK3 Runtime:

1. Descargar el instalador desde: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
2. Ejecutar el instalador (gtk3-runtime-xxx-x64-setup.exe)
3. Reiniciar la aplicación KDP Master

Una vez instalado, la exportación a PDF funcionará automáticamente.

---

## Tech Stack

- **GUI:** tkinter (Python standard library)
- **Download:** yt-dlp
- **Database:** SQLite
- **AI:** Google Gemini / OpenAI
- **Build:** PyInstaller

---

## Licencia

Copyright 2026 KDP Master Solutions
Todos los derechos reservados.