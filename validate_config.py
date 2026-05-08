import json
import os
import sys

def validate_settings(config_path="settings.json"):
    """
    Valida la estructura y tipos de datos del archivo de configuración.
    Retorna (True, "OK") si es válido, o (False, "Error") si no lo es.
    """
    if not os.path.exists(config_path):
        return True, "El archivo de configuración no existe (se usarán valores por defecto)."

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Error de sintaxis JSON: {e}"

    # Esquema esperado (clave: tipo)
    expected_schema = {
        "input_dir": str,
        "output_dir": str,
        "blacklist": list,
        "channels": list,
        "ai_provider": str,
        "ai_api_key": str,
        "ai_system_prompt": str
    }

    errors = []

    for key, expected_type in expected_schema.items():
        if key in config:
            if not isinstance(config[key], expected_type):
                errors.append(f"Tipo incorrecto para '{key}': Se esperaba {expected_type.__name__}, se obtuvo {type(config[key]).__name__}")
        # No marcamos error si falta la clave, ya que se usarán defaults, 
        # pero podríamos hacerlo si fuera crítico.

    # Validaciones específicas adicionales
    if "channels" in config:
        for i, channel in enumerate(config["channels"]):
            if not isinstance(channel, dict) or "name" not in channel or "url" not in channel:
                errors.append(f"Formato inválido en canal #{i+1}: Debe ser un objeto con 'name' y 'url'")

    if errors:
        return False, "\n".join(errors)

    return True, "Configuración válida."

if __name__ == "__main__":
    valid, msg = validate_settings()
    if valid:
        print(f"✅ {msg}")
        sys.exit(0)
    else:
        print(f"❌ Errores de configuración encontrados:\n{msg}")
        sys.exit(1)