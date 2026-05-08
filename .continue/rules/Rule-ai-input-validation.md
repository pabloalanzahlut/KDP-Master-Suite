---
name: ai-input-validation
description: Regla para validar inputs de IA y compatibilidad de visión (Multimodal).
---

# 🤖 AI INPUT VALIDATION

### <condiciones>
1. **Gemini Pro (Non-Vision):** NO enviar imágenes.
2. **GPT-3.5 Turbo:** NO enviar imágenes.
3. **Soporte Multimodal:** Solo los modelos `gemini-pro-vision`, `gpt-4-vision-preview` o `gpt-4o` procesan imágenes.
</condiciones>

### <acciones_obligatorias>
- **Pre-check:** Validar el MIME type (`image/png`, `image/jpg`) antes de la invocación.
- **Error Handling:** Si el modelo no soporta Vision, retornar: `ERROR_MODEL_INCOMPATIBILITY: Vision not supported`.
- **Logic:** No intentar conversiones de texto a imagen ni viceversa de forma automática.
</acciones_obligatorias>

### <whitelist_vision>
- gemini-pro-vision
- gpt-4-vision-preview
- gpt-4o
- gemma3:12b (si aplica localmente)
</whitelist_vision>
