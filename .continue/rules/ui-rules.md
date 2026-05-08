---
name: frontend-arch-constraints
description: Restricciones de diseño, arquitectura y dependencias del frontend.
---

# ⚙️ FRONTEND CONSTRAINTS

### <arquitectura_central>
- **Pipeline Intocable:** YouTube → Transcripción → KB → GEM.
- **Regla:** Cualquier sugerencia que altere este orden o elimine un nodo será rechazada automáticamente.
</arquitectura_central>

### <gestion_de_dependencias>
- **Bloqueo de Librerías:** Prohibido instalar librerías pesadas (ej. frameworks de UI masivos) o externas sin justificación crítica.
- **Whitelist:** `ttkbootstrap` (Recomendado para Design System Bootstrap).
- **Enfoque:** Uso prioritario de componentes de `ttkbootstrap` para consistencia y rendimiento.
</gestion_de_dependencias>

### <filosofia_del_producto>
- **Estética:** Mantener el minimalismo absoluto y el foco funcional.
- **Prioridad Técnica:** Robustez + Claridad > Acumulación de funcionalidades (Features).
</filosofia_del_producto>

<compliance_check>
Si una tarea de desarrollo implica añadir una dependencia de terceros, el agente debe disparar una alerta <EXTERNAL_DEP_WARNING> antes de proceder.
</compliance_check>
