---
description: Regla para respaldos locales de la KB antes de cada inserción de transcripción.
---

### Condiciones:

1. KB local existente.
2. Cambios detectados (hash o número de registros nuevos).

### Acciones:

- Crear backup en carpeta `.kb_backups/` con timestamp.
- Registrar éxito o fallo del backup en log de operaciones.
- Alertar si espacio en disco < 500MB.
