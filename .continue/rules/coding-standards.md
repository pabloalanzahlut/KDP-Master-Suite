---
name: clean-code
description: Estándares de legibilidad, estructura de funciones y eliminación de redundancia.
---

# 🧼 CLEAN CODE

### <legibilidad_y_semántica>
- **Nombres Claros:** Variables, funciones y clases deben tener nombres descriptivos que expliquen su propósito sin necesidad de comentarios adicionales.
- **Idioma:** Nombres de variables en inglés (convención técnica), explicaciones en español profesional.
</legibilidad_y_semántica>

### <arquitectura_de_funciones>
- **Single Responsibility Principle (SRP):** Cada función debe realizar una única tarea y hacerla bien.
- **Tamaño:** Mantener funciones pequeñas y concisas. Si una función supera las 20 líneas, evaluar una subdivisión lógica.
</arquitectura_de_funciones>

### <mantenibilidad>
- **DRY (Don't Repeat Yourself):** Prohibida la lógica duplicada. Centralizar funciones comunes en utilidades o helpers.
- **Simplificación:** Eliminar código muerto y refactorizar estructuras complejas por unas más legibles.
</mantenibilidad>

<audit_action>
Durante el proceso de `/refine`, cualquier bloque que viole el principio DRY o SRP será marcado para refactorización inmediata.
</audit_action>
