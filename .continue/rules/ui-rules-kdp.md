---
name: frontend-ui-constraints
description: Restricciones de arquitectura y diseño para el frontend.
---

# ⚙️ FRONTEND CONSTRAINTS

### <pipeline_core>
- **Flujo Inalterable:** YouTube → Transcripción → KB → GEM.
- Cualquier propuesta de refactor debe respetar esta cadena de procesamiento.
</pipeline_core>

### <dependencias>
- No instalar librerías pesadas o externas sin auditoría previa.
- Priorizar soluciones nativas o ligeras para mantener el rendimiento local.
</dependencias>

### <filosofia_diseño>
- **Minimalismo:** Foco absoluto en la tarea.
- **Jerarquía:** Robustez + Claridad > Nuevas funcionalidades (Features).
</filosofia_diseño>

<validation_rule>
Si un cambio sugerido añade una librería externa o altera el flujo central, el agente debe emitir un aviso <ARCH_VIOLATION>.
</validation_rule>
