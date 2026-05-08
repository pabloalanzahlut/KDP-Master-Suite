---
name: gem-data-insertion
description: Regla para alimentar el GEM con transcripciones validadas y consistencia de KB.
---

# 📥 GEM DATA INSERTION PROTOCOL

### <pre_condiciones_obligatorias>
1. **Validación de Origen:** La transcripción debe estar marcada como "válida" según `@rule-check-transcription`.
2. **Sincronización:** La Base de Conocimientos (KB) debe estar actualizada y confirmada como consistente antes de proceder.
</pre_condiciones_obligatorias>

### <acciones_de_ejecucion>
- **Integridad:** Insertar transcripción en el GEM sin alteraciones al contenido original (Raw Data).
- **Trazabilidad:** Registrar obligatoriamente el `timestamp` de envío.
- **Fail-Safe:** Emitir una alerta inmediata en caso de fallo en cualquier nodo de inserción.
</acciones_de_ejecucion>

<constraint>
PROHIBIDO modificar, resumir o editar la transcripción durante el proceso de inserción al GEM.
</constraint>
