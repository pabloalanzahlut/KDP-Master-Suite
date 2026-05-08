---
name: documentation-consistency
description: Protocolo de sincronización obligatoria entre implementación y documentación.
---

# 📚 DOCUMENTATION CONSISTENCY

### <sincronización_obligatoria>
Toda modificación de lógica, flujo o interfaz **DEBE** reflejarse simultáneamente en:
1. **Código:** Comentarios técnicos y limpieza según `@clean-code`.
2. **Documentación Técnica:** Actualización de esquemas, APIs y lógica en la carpeta `/docs`.
3. **Manual de Usuario:** Ajuste de pasos operativos si la funcionalidad cambia para el usuario final.
</sincronización_obligatoria>

### <criterio_de_aceptación>
- Si un cambio en el código no tiene su contraparte en la documentación:
  → **STATUS: INCOMPLETO**
  → **ACTION: Bloquear Deploy/Merge**
</criterio_de_aceptación>

<audit_instruction>
Antes de finalizar cualquier comando `/refine` o `/build`, el agente debe verificar si los archivos en `D:/ANEXOS KDP Y DIGITALES/KDP_MASTER/docs` requieren una actualización basada en los cambios del `@diff`.
</audit_instruction>
