# 📋 Product Backlog - KDP Master Suite

**Versión:** 2.6.0  
**Última actualización:** 2026-04-09  
**Cambios desde v2.5.1:** Detección de contenido duplicado entre canales con estrategia híbrida

---

Este documento rastrea las historias de usuario, mejoras técnicas y bugs conocidos, priorizados por valor de negocio para el ecosistema KDP.

## 🟢 Sprint Actual (En Progreso)

| ID | Tipo | Título | Prioridad | Estimación | Estado |
|----|------|--------|-----------|------------|--------|
| US-008 | Feature | Detección de Contenido Duplicado entre Canales | Alta | 5 pts | ✅ Completed |
| US-007 | Feature | Exportación de KB a formato legible (PDF/HTML) | Media | 3 pts | ✅ Completed |

## 🟡 Next Up (Próximo Sprint)

| ID | Tipo | Título | Historia de Usuario | Prioridad |
|----|------|--------|---------------------|-----------|
| US-004 | Feature | Clasificación automática mejorada con IA multi-categoría | *Como usuario, quiero que mis transcripciones se clasifiquen con mayor precisión para organizar mejor mi KB.* | Alta |
| US-005 | Feature | Mejora del sistema de búsqueda en KB | *Como usuario, quiero buscar rápidamente en mi base de conocimiento para找到 contenido específico.* | Alta |
| US-006 | Tech | Refactorización de UI framework a componentes reutilizables | *Como desarrollador, quiero componentes modulares para facilitar mantenimiento.* | Media |

## 📦 Cambios en v2.6.0 (Completados)

| ID | Cambio | Descripción | Estado |
|----|-------|-------------|--------|
| C-005 | Sistema de Detección de Duplicados | Motor híbrido: Hash MD5 → Duration Window → Title Similarity → Tags → IA (opcional) | ✅ |
| C-006 | UI de Decisión de Duplicados | Diálogo modal para que el usuario decida qué hacer con contenido duplicado | ✅ |
| C-007 | Estadísticas de Duplicados | Panel en Monitor tab mostrando total duplicados y tasa | ✅ |
| C-008 | Extensión de Base de Datos | Nuevas columnas (duration_seconds, tags), tabla video_relations | ✅ |
| C-009 | Exportación KB a PDF/HTML | Motor híbrido DB+MD, HTML con TOC/búsqueda, auditoría | ✅ |

## 🔵 Backlog General (Futuro)

### Épica: Pipeline de Contenido

- [ ] **Procesamiento Batch con Progreso Individual**: Procesar cientos de transcripciones con barras de progreso por archivo sin bloquear la UI.
- [ ] **Extracción de Metadata Enriquecida**: Título, descripción, tags, duración, fecha del video en la KB.
- [ ] **Validación de Integridad Post-Descarga**: Verificar checksum MD5 después de cada descarga.

### Épica: Monitor Inteligente

- [ ] **Filtros por Palabras Clave**: Solo descargar videos que contengan términos específicos.
- [ ] **Programación Horaria**: Configurar ventanas de monitoreo (ej: solo de noche).
- [ ] **Notificaciones Windows Toast**: Alertas visuales cuando se detecte contenido nuevo.

### Épica: Base de Datos y Búsqueda

- [ ] **Indexación de Archivos en DB**: Reemplazar os.walk() con búsqueda indexada para velocidad instantánea.
- [ ] **Transacciones Batch**: Usar ejecutemany() para inserciones masivas de videos.
- [x] **Exportación de KB a PDF/HTML**: Generar documentos profesionales de la base de conocimiento.

## 🔴 Deuda Técnica y Bugs

- [ ] **Tech**: Actualizar dependencias de Python a versiones más recientes.
- [ ] **Tech**: Implementar pruebas unitarias para servicios core (`processing_service`, `knowledge_integrator`).
- [ ] **Bug**: Mejorar manejo de errores cuando yt-dlp cambia su API interna.
- [ ] **Tech**: Migrar configuración de `.env` a sistema de gestión centralizada con validación.
- [ ] **Tech**: Eliminar código de AgentLoader no usado (app/core/agent_loader.py).

---

**Criterios de Priorización (MoSCoW):**

- **Must Have**: Pipeline estable, monitor funcional, clasificación precisa, seguridad de API keys.
- **Should Have**: Exportación de KB.
- **Could Have**: Notificaciones Windows Toast, programación horaria del monitor.
- **Won't Have**: Nube pública, suscripciones, integración con servicios de terceros no autorizados, API REST local, sincronización entre dispositivos, agentes GEM internos.
