# PRODUCT BACKLOG — KDP Master Suite

**Versión:** 2.5.1  
**Última actualización:** 2026-04-09  
**Cambios:** Eliminación de agentes GEM

---

## Sprint Actual (v2.5.1)

| ID | Historia de Usuario | Prioridad | Estado |
|---|---|---|---|
| US-001 | Como usuario, quiero que la cola de descargas reencole los fallidos automáticamente | MoSCoW: Must | ✅ Hecho |
| US-002 | Como usuario, quiero ver el progreso de búsqueda sin que la UI se congele | MoSCoW: Must | ✅ Hecho |
| US-003 | Como usuario, quiero que el botón Editar funcione correctamente en canales | MoSCoW: Must | ✅ Hecho |
| US-004 | Como usuario, quiero que "Buscar" abra la carpeta real y no knowledge | MoSCoW: Must | ✅ Hecho |
| US-005 | Como usuario, quiero importar CSV de formato "@handle - Nombre" sin errores | MoSCoW: Must | ✅ Hecho |

## Próximo Sprint (v2.6.0)

| ID | Historia de Usuario | Prioridad | Esfuerzo |
|---|---|---|---|
| US-006 | Como usuario, quiero validación de integridad post-descarga (MD5) | MoSCoW: Should | 2h |
| US-007 | Como usuario, quiero notificación Windows Toast al detectar videos nuevos | MoSCoW: Could | 4h |
| US-008 | Como usuario, quiero barra de progreso global siempre visible | MoSCoW: Should | 1h |
| US-009 | Como admin, quiero transacciones batch en DB para operaciones masivas | MoSCoW: Should | 3h |
| US-010 | Como usuario, quiero que el modo vigilancia cancele el timer anterior antes de crear uno nuevo | MoSCoW: Must | 1h |

## Backlog General

### Épica: Pipeline de Contenido
- Bulk processing de archivos con barra de progreso individual
- Detección de contenido duplicado entre canales
- Extracción de metadata enriquecida (título, descripción, tags, duración)
- Validación de integridad post-descarga (checksum MD5)
- Filtros por palabras clave en monitor

### Épica: Agentes GEM
- Ejecutar prompts de agentes directamente desde la UI
- Historial de ejecuciones de agentes
- Plantillas de agentes personalizables por el usuario

### Épica: Monitor Mejorado
- Programación horaria (configurar ventanas de monitoreo)
- Alertas configurables por canal
- Estadísticas de frecuencia de publicación

### Épica: Dashboard y Exportación
- Dashboard web responsive (móvil/tablet)
- Exportación de KB a PDF profesional
- Gráficos de tendencias de canales

## Deuda Técnica

| ID | Descripción | Impacto | Esfuerzo |
|---|---|---|---|
| DT-001 | Migrar gui_app.py (~4000 líneas) a main_window.py como entry point definitivo | Alto | 20h |
| DT-002 | Eliminar código duplicado residual en gui_app.py | Medio | 4h |
| DT-003 | Agregar tests automatizados para servicios core | Alto | 15h |
| DT-004 | Indexar archivos en DB para búsqueda instantánea | Medio | 6h |
| DT-005 | Migrar contenido de archivos MD a knowledge_entries DB | Bajo | 2h |
| DT-006 | Reemplazar after(86400000) recursivo con scheduler adecuado | Medio | 2h |
