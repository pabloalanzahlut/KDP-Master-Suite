# 📖 Manual de Usuario - KDP Master Suite v2.5.1

**Versión:** 2.6.0  
**Última actualización:** 2026-04-20

## Índice

1. [Introducción](#1-introducción)
2. [Instalación](#2-instalación)
3. [Primer Inicio](#3-primer-inicio)
4. [Interfaz Principal](#4-interfaz-principal)
5. [Pestaña Descargas](#5-pestaña-descargas)
6. [Pestaña Procesamiento](#6-pestaña-procesamiento)
7. [Pestaña Inteligencia](#7-pestaña-inteligencia)
8. [Pestaña Búsqueda](#8-pestaña-búsqueda)
9. [Pestaña Monitor de Canales](#9-pestaña-monitor-de-canales)
10. [Pestaña Dashboard](#10-pestaña-dashboard)
11. [Menús](#11-menús)
12. [Configuración de IA](#12-configuración-de-ia)
13. [Gestión de Canales](#13-gestión-de-canales)
14. [Backup y Restauración](#14-backup-y-restauración)
15. [Solución de Problemas](#15-solución-de-problemas)
16. [Atajos de Teclado](#16-atajos-de-teclado)

---

## 1. Introducción

KDP Master Suite es una aplicación de escritorio para la gestión integral de contenido KDP a través de transcripciones de YouTube.

### Pipeline Principal
```
YouTube → Transcripción → Base de Conocimiento
```

### Requisitos
- Windows 10/11
- Python 3.11+ (solo si usas código fuente)
- Conexión a internet (para descargas y IA)

---

## 2. Instalación

### Método 1: Ejecutable
1. Ejecuta `dist\KDP_Transcriptions.exe`
2. No requiere instalación adicional

### Método 2: Código Fuente
```bash
pip install -r requirements.txt
python gui_app.py
```

---

## 3. Primer Inicio

Al abrir la aplicación por primera vez:

1. **Verificación de configuración**: El sistema valida archivos y directorios
2. **Verificación de conexión**: Detecta si hay internet
3. **Wizard inicial** (si es primera vez): Guía de configuración básica
4. **Interfaz lista**: Las 7 pestañas están disponibles

### Modo Offline
Si no hay conexión a internet, la aplicación entra en modo offline automáticamente. Las funciones de descarga e IA se desactivan, pero puedes trabajar con archivos locales.

---

## 4. Interfaz Principal

```
┌─────────────────────────────────────────────────────┐
│  Archivo  Ver  Mantenimiento  Herramientas  Ayuda   │  ← Barra de menús
├─────────────────────────────────────────────────────┤
│  [📥 Descargas] [⚙️ Proceso] [🧠 IA] ...            │  ← Pestañas
│                                                     │
│                                                     │
│              Contenido de la pestaña                │
│                                                     │
├─────────────────────────────────────────────────────┤
│  🛡️ Sistema listo    [████░░░░] 0%  💾 Disco: --  │  ← Barra de estado
└─────────────────────────────────────────────────────┘
```

### Barra de Estado
- **🛡️ Estado**: Mensaje del sistema
- **Barra de progreso**: Progreso de descargas/procesamiento
- **💾 Disco**: Espacio disponible
- **Versión**: v2.5.0-GOLD

---

## 5. Pestaña Descargas

### Funciones
- **Campo URL**: Ingresa URLs de YouTube para descargar subtítulos
- **Botón Descargar**: Inicia la descarga de subtítulos VTT/SRT
- **Cola de descargas**: Muestra descargas pendientes y en progreso
- **Drag & Drop**: Arrastra archivos a la zona de carga

### Formatos Soportados
- URLs de YouTube: `youtube.com/watch?v=...`, `youtu.be/...`
- Handles de canal: `@nombre`, `youtube.com/@nombre`
- Archivos VTT/SRT locales

### Controles de Cola
| Botón | Función |
|-------|---------|
| ▶️ Iniciar | Inicia descarga de la cola |
| ⏸️ Pausar | Pausa la descarga actual |
| ❌ Limpiar | Limpia la cola |
| ➕ Añadir | Añade URL a la cola |

---

## 6. Pestaña Procesamiento

### Funciones
- **Lista de archivos**: Muestra archivos en directorio de entrada
- **Procesar**: Limpia y normaliza transcripciones
- **Metadatos**: Muestra información del video (título, canal, fecha)
- **Eliminar**: Borra archivos seleccionados

### Proceso de Limpieza
1. Elimina timestamps y números de línea
2. Normaliza espacios y saltos de línea
3. Convierte VTT a texto plano
4. Genera archivos procesados en `outputs/`

---

## 7. Pestaña Inteligencia

### Funciones
- **🧠 Integrar Conocimiento**: Escanea archivos procesados y los clasifica
- **🌐 Exportar Índice Web**: Genera HTML con el índice de la KB

### Categorías de Clasificación
| Categoría | Descripción |
|-----------|-------------|
| Legalidad y Compliance | Aspectos legales de KDP |
| Matriz de Roles y Fases SOE | Roles y responsabilidades |
| Matriz de Roles y Fases SOE | Fases del sistema operativo |
| Fórmulas y Métricas | Cálculos y KPIs |
| Investigación de Nichos | Análisis de mercado |
| Amazon Ads y Marketing | Publicidad y promoción |
| Conocimiento General KDP | Información general |

### Modo IA
- **Sin IA**: Clasificación por reglas locales (rápido, gratis)
- **Con Gemini**: Clasificación inteligente con IA (requiere API key)
- **Con OpenAI**: Clasificación con GPT (requiere API key)

---

## 8. Pestaña Búsqueda

### Funciones
- **Campo de búsqueda**: Ingresa términos a buscar
- **Alcance**: Busca en transcripciones, procesados y base de datos
- **Resultados**: Muestra coincidencias con contexto

### Tipos de Búsqueda
- **Texto completo**: Busca en todos los archivos
- **Base de datos**: Busca en registros SQLite
- **Transcripciones crudas**: Busca en archivos VTT/SRT originales

---

## 9. Pestaña Monitor de Canales

### Funciones
- **Añadir canales**: Ingresa URLs de canales YouTube
- **Lista de canales**: Muestra canales monitoreados
- **Estadísticas**: Videos detectados, transcripciones, estado
- **Control**: Iniciar/detener monitoreo

### Formatos de URL Aceptados
```
@nombre_canal
https://youtube.com/@nombre_canal
https://youtube.com/c/NombreCanal
https://youtube.com/channel/UCxxxxxxxx
```

### Ciclo de Monitoreo
1. Verifica canales cada N minutos (configurable)
2. Detecta nuevos videos
3. Descarga subtítulos automáticamente
4. Procesa y limpia transcripciones
5. Integra en la base de conocimiento

---

## 10. Pestaña Dashboard

### Funciones
- **Iniciar servidor web**: Activa dashboard remoto
- **Detener servidor**: Desactiva el servicio
- **Estado**: Muestra si el servidor está activo

### Acceso Remoto
Una vez iniciado, accede desde el navegador a la URL mostrada.

---

**Nota:** A partir de v2.5.1, los agentes GEM fueron eliminados. El pipeline ahora es YouTube → Transcripción → Base de Conocimiento.

---

## 11. Menús

### Archivo
| Opción | Función |
|--------|---------|
| 📂 Abrir Carpeta Transcripciones | Abre directorio de entrada |
| 📂 Abrir Carpeta Procesados | Abre directorio de salida |
| 📂 Abrir Carpeta KB | Abre base de conocimiento |
| 📤 Exportar Configuración UI | Guarda configuración en ZIP |
| 📥 Importar Configuración UI | Restaura configuración desde ZIP |
| ❌ Salir | Cierra la aplicación |

### Ver
| Opción | Función |
|--------|---------|
| 🌙 Tema Oscuro | Cambia a tema dark |
| ☀️ Tema Claro | Cambia a tema light |
| 🔄 Refrescar | Actualiza listas y datos |
| 📋 Ver Log | Abre archivo de log |
| 🧹 Limpiar Consola | Limpia la consola inferior |

### Mantenimiento
| Opción | Función |
|--------|---------|
| 🧹 Limpiar Caché yt-dlp | Elimina caché de descargas |
| 🔄 Resetear Sesión | Restablece estado de la app |
| 🔧 Reparar Integridad | Verifica y repara KB |
| 🏥 Health Check | Diagnóstico completo del sistema |
| 📊 Reporte de Categorías | Genera reporte de categorías KB |

### Herramientas
| Opción | Función |
|--------|---------|
| 📺 Gestor de Canales | Diálogo avanzado de gestión |
| 🤖 Configurar IA | Configura proveedor y API key |
| 🚫 Editar Blacklist | Gestiona lista de exclusión |
| ⌨️ Atajos de Teclado | Editor de keybindings |
| 🚨 Backup de Pánico | Backup instantáneo manual |
| 📂 Restaurar Backup | Restaura desde archivo ZIP |
| 🕸️ Grafo de Roles | Genera gráfico de dependencias |
| 📄 Exportar Manual a PDF | Genera PDF del manual legal |

### Ayuda
| Opción | Función |
|--------|---------|
| 🌐 Buscar Actualizaciones | Abre página de releases |
| 📖 Documentación | Abre README.md |
| ℹ️ Acerca de | Información de la versión |

---

## 12. Configuración de IA

### Acceso
**Herramientas → Configurar IA**

### Proveedores Soportados
| Proveedor | Modelo | Costo |
|-----------|--------|-------|
| Gemini | gemini-pro | Gratis (15 RPM) |
| OpenAI | gpt-3.5-turbo | Pago por token |
| Ninguno | Clasificación local | Gratis |

### Configuración
1. Selecciona proveedor
2. Ingresa API key
3. (Opcional) Personaliza prompt del sistema
4. Guarda la configuración

### Seguridad
- Las API keys se encriptan con AES antes de guardar
- El archivo de configuración no es legible directamente
- Nunca se envían datos fuera del sistema

---

## 13. Gestión de Canales

### Añadir Canal
1. Ve a la pestaña **Monitor de Canales**
2. Arrastra la URL del canal a la zona de carga
3. O usa **Herramientas → Gestor de Canales**
4. Ingresa nombre y URL
5. Guarda

### Editar Canal
1. Selecciona el canal en la lista
2. Click derecho → **Editar**
3. Modifica nombre, URL o categoría
4. Guarda cambios

### Eliminar Canal
1. Selecciona el canal
2. Click en **Eliminar** o tecla `Supr`
3. Confirma la eliminación

### Exportar/Importar Canales
- **Exportar CSV**: Descarga lista de canales
- **Importar CSV**: Carga canales desde archivo

---

## 14. Backup y Restauración

### Backup Automático
- Se ejecuta al cerrar la aplicación
- Guarda `knowledge/` en `backups/` como ZIP
- Nombre: `knowledge_backup_YYYYMMDD_HHMMSS.zip`

### Backup Manual (Pánico)
- **Herramientas → Backup de Pánico**
- Crea backup instantáneo
- Nombre: `panic_backup_YYYYMMDD_HHMMSS.zip`

### Restaurar Backup
1. **Herramientas → Restaurar Backup**
2. Selecciona archivo ZIP de `backups/`
3. Confirma la restauración
4. Reinicia la aplicación

---

## 15. Solución de Problemas

### La aplicación no inicia
- Verifica que Python 3.11+ esté instalado
- Ejecuta `python gui_app.py` para ver errores
- Elimina el archivo `.app.lock` si existe

### Error de API Key
- Verifica que la key sea válida
- Ve a **Herramientas → Configurar IA**
- Prueba con `none` como proveedor para modo offline

### Error de rutas en ejecutable
- El ejecutable crea directorios automáticamente
- Si persiste, ejecuta desde código fuente

### Error "image.png" en IA
- Ya corregido en v2.5.0
- El sistema detecta y rechaza inputs no-texto
- Fallback automático a clasificación local

### La KB no se actualiza
- Verifica que haya archivos `.txt` en el directorio de salida
- Ejecuta **Mantenimiento → Reparar Integridad**
- Revisa el log para errores específicos

### Monitor no detecta videos
- Verifica conexión a internet
- Comprueba que las URLs de canales sean válidas
- Aumenta `MONITOR_INTERVAL_MINUTES` en `.env`

---

## 16. Atajos de Teclado

| Tecla | Función |
|-------|---------|
| `F1` | Abrir documentación |
| `F5` | Refrescar lista de archivos |
| `Ctrl+O` | Abrir carpeta |
| `Ctrl+S` | Guardar configuración |
| `Ctrl+Q` | Salir |
| `Ctrl+V` | Pegar URL desde portapapeles |
| `Ctrl+A` | Seleccionar todo |
| `Delete` | Eliminar selección |
| `Esc` | Cancelar operación |

---

**KDP Master Suite v2.5.0**  
**Editorial Zahlut**  
**Uso Privado**
