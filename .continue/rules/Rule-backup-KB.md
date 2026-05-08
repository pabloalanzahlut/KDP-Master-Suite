---
name: kb-backup-protocol
description: Sistema de respaldo preventivo de la Base de Conocimientos (KB) ante mutaciones de datos.
---

# 💾 KB BACKUP PROTOCOL

### <condiciones_de_activación>
1. **Existencia:** Confirmar presencia de la KB local en la ruta definida.
2. **Mutación Detectada:** Cambios confirmados mediante verificación de `hash` o incremento en el conteo de registros.
</condiciones_de_activación>

### <procedimiento_operativo>
- **Ejecución:** Generar copia íntegra en la ruta `.kb_backups/` utilizando el formato de nombre `YYYY-MM-DD_HHMMSS_kb_backup.db` (o extensión correspondiente).
- **Logging:** Registrar resultado (SUCCESS/FAIL) en el log de operaciones global.
- **System Check:** Validar espacio en disco. **CRÍTICO:** Alertar y detener proceso si el espacio disponible es menor a 500MB.
</procedimiento_operativo>

<safety_gate>
Si el backup falla o el espacio en disco es insuficiente, se debe abortar la secuencia de inserción en el GEM para evitar corrupción de datos.
</safety_gate>
