---
name: global-rules
description: Restricciones críticas y principios fundamentales del sistema KDP_MASTER.
---

# 🚫 GLOBAL RULES

### <restricciones_estrictas>
- **No Feature Creep:** Queda terminantemente prohibido agregar nuevas funcionalidades (features) que no hayan sido aprobadas por el Orchestrator.
- **Flujo Inalterable:** El pipeline de datos `Transcripción → KB → GEM` es el núcleo del sistema. Cualquier modificación que altere este orden será rechazada.
- **Cero Sobre-Ingeniería:** No implementar soluciones complejas para problemas que pueden resolverse con lógica simple y directa.
- **Dependencias:** Bloqueo total a la introducción de librerías o dependencias pesadas que comprometan el rendimiento local.
</restricciones_estrictas>

### <principio_maestro>
> **Máxima robustez con mínima complejidad.**
- La estabilidad del sistema actual es la prioridad absoluta sobre la innovación.
</principio_maestro>

<enforcement>
Esta regla tiene prioridad sobre todas las demás. Si una instrucción del usuario entra en conflicto con estas reglas globales, el agente debe notificar la violación <GLOBAL_RULE_VIOLATION> y detener la ejecución.
</enforcement>
