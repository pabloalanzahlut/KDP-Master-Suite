---
name: architecture-rules
description: Estándares de diseño estructural, desacoplamiento y jerarquía de componentes.
---

# 🏗️ ARCHITECTURE RULES

### <separación_de_responsabilidades>
- **SoC (Separation of Concerns):** La lógica de negocio, el acceso a datos (KB) y la interfaz deben residir en capas independientes.
- **Validación:** Prohibido mezclar lógica de transcripción con lógica de renderizado UI.
</separación_de_responsabilidades>

### <desacoplamiento>
- **Loose Coupling:** Evitar el acoplamiento fuerte entre módulos. Usar interfaces o funciones de puente para la comunicación entre el Pipeline y el GEM.
- **Dependencias:** Los módulos de bajo nivel no deben conocer los detalles de implementación de los módulos de alto nivel.
</desacoplamiento>

### <mantenibilidad_vs_complejidad>
- **KISS (Keep It Simple, Stupid):** Priorizar siempre el código mantenible y legible sobre soluciones "astutas" o innecesariamente complejas.
- **Escalabilidad:** Diseñar pensando en que el flujo YouTube → GEM pueda recibir nuevos nodos sin reconstruir el sistema completo.
</mantenibilidad_vs_complejidad>

<audit_gate>
Cualquier propuesta que genere una dependencia circular o fusione capas de responsabilidad activará un bloqueo <ARCH_COUPLE_ERROR>.
</audit_gate>
