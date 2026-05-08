# -*- coding: utf-8 -*-
"""
Safe AI Wrapper - Previene errores de input incorrecto a modelos de IA
======================================================================
"""

import os
import logging

logger = logging.getLogger(__name__)

# Modelos que SOLO aceptan texto
TEXT_ONLY_MODELS = [
    'gemini-pro',
    'gpt-3.5-turbo',
    'gpt-4',
    'gpt-4-turbo',
    'text-davinci-003',
]

# Modelos que aceptan imágenes/visión
VISION_MODELS = [
    'gemini-pro-vision',
    'gpt-4-vision-preview',
    'gpt-4o',
    'gpt-4o-mini',
    'claude-3-opus',
    'claude-3-sonnet',
]


def is_text_input(input_data):
    """Verifica si el input es texto válido."""
    if input_data is None:
        return False
    if isinstance(input_data, str):
        return len(input_data.strip()) > 0
    if isinstance(input_data, (bytes, bytearray)):
        return False
    if hasattr(input_data, 'read'):
        return False
    return True


def validate_ai_input(input_data, model_name=None):
    """
    Valida que el input sea compatible con el modelo.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if input_data is None:
        return False, "Input es None"
    
    if isinstance(input_data, (bytes, bytearray)):
        return False, "Input binario no soportado - solo texto"
    
    if hasattr(input_data, 'read'):
        return False, "Input de archivo no soportado - solo texto"
    
    if isinstance(input_data, str):
        if len(input_data.strip()) == 0:
            return False, "Input vacío"
        
        # Verificar si parece ser datos binarios en string
        if input_data.startswith(('\x89PNG', '\xff\xd8', 'GIF8', 'RIFF')):
            return False, "Datos de imagen detectados en input de texto"
        
        return True, None
    
    return False, f"Tipo de input no reconocido: {type(input_data)}"


def safe_generate_content(model, prompt, model_name=None):
    """
    Wrapper seguro para generate_content de Gemini.
    Previene el error 'this model does not support image input'
    """
    # Validar el prompt
    is_valid, error_msg = validate_ai_input(prompt, model_name)
    if not is_valid:
        logger.error(f"AI Input validation failed: {error_msg}")
        raise ValueError(f"Input inválido para IA: {error_msg}")
    
    # Si el modelo es text-only, asegurar que no haya imágenes
    if model_name and model_name in TEXT_ONLY_MODELS:
        if isinstance(prompt, str):
            # Verificar patrones comunes de imágenes
            if any(prompt.startswith(prefix) for prefix in ['\x89PNG', '\xff\xd8', 'GIF8']):
                raise ValueError("No se puede enviar imagen a modelo de texto. Use un modelo de visión como gemini-pro-vision")
    
    # Ejecutar la llamada
    return model.generate_content(prompt)


def classify_with_validation(integrator, text):
    """
    Wrapper para classify_with_ai con validación previa.
    """
    if not text or not text.strip():
        return None
    
    is_valid, error_msg = validate_ai_input(text)
    if not is_valid:
        logger.warning(f"Input validation failed in classify: {error_msg}")
        return None
    
    return integrator._classify_with_ai(text)