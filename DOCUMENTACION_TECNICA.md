# 📘 DOCUMENTACIÓN TÉCNICA - KDP MASTER SUITE

**Versión:** 2.5.1  
**Última actualización:** 2026-04-09

---

## 🏗️ Arquitectura SOMD (Service-Oriented Modular Desktop)

El sistema ha sido migrado de una arquitectura monolítica a una estructura modular orientada a servicios, optimizando el mantenimiento y la escalabilidad.

### Estructura de Directorios

```
KDP_MASTER/
├── app/                    # Directorio principal de la aplicación
│   ├── core/               # Lógica fundamental (Config, Seguridad, UI Framework)
│   ├── database/           # Persistencia y gestión de SQLite
│   ├── services/           # Lógica de negocio (Descargas, Procesamiento, Monitor)
│   └── ui/                 # Capa de presentación
│       ├── components/     # Widgets reutilizables (Toasts, Tooltips, Checkboxes)
│       └── tabs/           # Módulos individuales para cada pestaña del Notebook
├── data/                   # Datos brutos y transcripciones (Entrada)
├── outputs/                # Resultados procesados (Salida)
├── knowledge/              # Base de conocimiento y manuales maestros
├── main.py                 # Punto de entrada de la aplicación
└── dashboard_server.py     # Servidor web de monitoreo funcional
```

---

## 🔧 Componentes del Sistema

### 1. Capa Core (`app/core/`)
- **`config.py`**: Gestión centralizada de rutas, API Keys y variables de entorno.
- **`security.py`**: Motor de encriptación AES-256-GCM para llaves API.
- **`logger.py`**: Sistema de logs rotativos para aplicación y auditoría.
- **`ui_framework.py`**: Administrador de temas, animaciones y diseño responsive.
- **`utils.py`**: Utilidades de normalización de URLs y saneamiento de datos.

### 2. Servicios (`app/services/`)
- **`download_service.py`**: Integración con yt-dlp para extracción de contenido.
- **`processing_service.py`**: Algoritmos de limpieza y normalización de texto con deduplicación MD5.
- **`monitor_service.py`**: Motor de vigilancia automática con:
  - Normalización robusta de handles de YouTube (`@nombre` → URLs completas)
  - Acceso directo a `/videos` para evitar cache de la pestaña principal
  - Circuit breaker para protección contra rate limiting
  - Logs estructurados JSON para auditoría completa
- **`knowledge_integrator.py`**: Clasificación inteligente y sincronización de KB.
- **`watcher.py`**: Utilidad de productividad que implementa *Hot Reloading* y gestión del estado `app.lock` para sesiones de desarrollo intensivas.

### 3. Interfaz de Usuario (`app/ui/`)
- **`main_window.py`**: Orquestador central que aplica el patrón Mixin para cargar pestañas modulares.
- **Pestañas Modulares**: Cada pestaña (`download_tab`, `process_tab`, etc.) es un módulo independiente que encapsula su propia lógica y widgets.

---

## 🔐 Seguridad y Robustez

- **Cierre Seguro**: El sistema realiza backups automáticos, guarda el estado de la sesión y persiste la cola de descargas antes de salir.
- **Deduplicación Enterprise**: El sistema utiliza hashes MD5 de contenido real limpiado para evitar el procesamiento y análisis de contenidos idénticos, ahorrando recursos y espacio.
- **Firmas de Integridad**: La base de conocimiento utiliza checksums MD5 para detectar modificaciones no autorizadas en los manuales maestros.
- **Logs de Auditoría**: El sistema genera logs estructurados en `logs/audit.log` para seguir cada paso del pipeline de datos.
- **Normalización de URLs**: El sistema incluye migración automática de handles de YouTube a URLs completas para garantizar compatibilidad con `yt-dlp`.

---

## 🚀 Guía de Desarrollo

### Requisitos
- Python 3.10+
- yt-dlp
- cryptography

### Ejecución
```bash
python main.py
```

### Ejecutar Monitor (Modo CLI)
```bash
python app/services/monitor_service.py --cli
```

---
*Última actualización: 2026-01-25 - Versión Enterprise SOMD*