---
description: Regla para validar transcripciones antes de insertarlas en la KB.
---

### Condiciones:

1. Transcripción no vacía.
2. Hash de transcripción único.
3. Texto normalizado UTF-8.
4. No contener caracteres inválidos.

### Acciones:

- Si cumple todas: marcar como "válida".
- Si falla alguna: marcar como "fallida" y generar alerta.
- Registrar timestamp de verificación.
