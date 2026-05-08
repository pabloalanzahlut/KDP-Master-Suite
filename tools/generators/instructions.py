#!/usr/bin/env python3
"""Generar script de instrucciones para el usuario"""

INSTRUCTIONS = """
================================================================================
INSTRUCCIONES PARA GENERAR TOKEN CON PERMISOS DE ESCRITURA
================================================================================

El token actual TIENE PERMISOS DE LECTURA (puede leer repos publicos) pero 
NO tiene permisos de ESCRITURA (no puede hacer push).

Pasos para generar nuevo token:

1. Ve a: https://github.com/settings/tokens/new

2. Configura:
   - Note: "KDP Master Suite Push"
   - Expiration: 90 days (o 1 year)
   
3. En "Select scopes", marca:
   [X] repo          (Full control of private repositories)
   [X] repo:status  (Access commit statuses)
   
   <<< IMPORTANTE: "repo" es el scope principal >>>

4. Clic en "Generate token"

5. COPIA el nuevo token (empieza con ghp_ o gho_)

6. Reemplaza el token en github_push.py linea 7:
   TOKEN = "ghp_AQUI_TU_NUEVO_TOKEN"

7. Ejecuta: python github_push.py

================================================================================
NOTA: El token "classic" (empieza con ghp_) tiene todos los permisos
      El token "fine-grained" (empieza con gho_) necesita permisos especificos
================================================================================
"""

print(INSTRUCTIONS)

# Tambien crear un script para facilitar el cambio
with open(r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\github_push.py", "r") as f:
    content = f.read()

new_content = content.replace(
    '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', 
    'ghp_TU_NUEVO_TOKEN_AQUI'
)

with open(r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\github_push.py", "w") as f:
    f.write(new_content)

print("\n[!] Actualizado github_push.py con marcador de token")
print("[*] Reemplaza 'ghp_TU_NUEVO_TOKEN_AQUI' con tu token real")