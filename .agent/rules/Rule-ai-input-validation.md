---
description: Regla para validar inputs de IA antes de enviar a la API.
---

### Condiciones:

1. Si el proveedor es "gemini" con modelo "gemini-pro" → NO enviar imágenes.
2. Si el proveedor es "openai" con modelo "gpt-3.5-turbo" → NO enviar imágenes.
3. Solo modelos gemini-pro-vision o gpt-4-vision soportan imágenes.

### Acciones:

- Validar tipo de contenido antes de llamar a la API.
- Si es imagen/png/jpg y modelo no soporta vision → retornar error claro.
- No intentar convertir texto a imagen.

### Modelos con soporte vision:

- gemini-pro-vision
- gpt-4-vision-preview
- gpt-4o