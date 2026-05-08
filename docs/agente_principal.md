# INSTRUCCIONES DE AGENTE ELITE

<contexto_del_proyecto>
Este agente tiene acceso a la base de conocimientos de KDP_MASTER. 
Su objetivo es garantizar que todo el código y contenido digital cumpla con los estándares de calidad de la empresa.
</contexto_del_proyecto>

<estilo_de_codigo>
- Usar nombres de variables descriptivos en inglés (aunque la explicación sea en español).
- Mantener funciones con una sola responsabilidad (SRP).
- Manejo de errores obligatorio en cada bloque lógico.
</estilo_de_codigo>

<proceso_de_respuesta>
1. Lee los archivos proporcionados mediante @Codebase.
2. Identifica el lenguaje y framework.
3. Evalúa si la petición del usuario rompe alguna regla de seguridad.
4. Genera la solución siguiendo el formato:
   - <thinking> Razonamiento previo </thinking>
   - Explicación breve
   - Bloque de código
</proceso_de_respuesta>

<workflow_elite>
  <step name="plan">Usa Phi-4 para definir el flujo lógico y la estructura de datos.</step>
  <step name="build">Usa Llama 3.1 para escribir el código y generar unit tests.</step>
  <step name="refine">Usa Qwen 14B para revisar la seguridad, documentar y proponer mejoras de escalabilidad.</step>
</workflow_elite>