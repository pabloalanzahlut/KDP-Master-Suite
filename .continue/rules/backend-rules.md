---
name: backend-constraints
description: Restricciones de arquitectura de servidor, servicios y gestión de dependencias.
---

# ⚙️ BACKEND CONSTRAINTS

### <pipeline_seguro>
- **Flujo Obligatorio:** YouTube → Transcripción → KB → GEM.
- **Integridad:** Prohibido insertar pasos intermedios que no hayan sido validados por el Master Agent.
</pipeline_core>

### <infraestructura_local>
- **Zero External Services:** No se permite la integración de APIs o servicios de terceros que no estén declarados en la documentación técnica actual.
- **Lightweight Backend:** No instalar dependencias pesadas o frameworks redundantes.
</infraestructura_local>

### <prioridad_de_sistema>
- **Métrica Élite:** Robustez > Features. 
- Si una nueva funcionalidad compromete la estabilidad del flujo central, debe ser descartada.
</prioridad_de_sistema>

<compliance_alert>
Cualquier intento de modificar el flujo o añadir servicios externos activará una alerta de bloqueo <BACKEND_VIOLATION>.
</compliance_alert>
