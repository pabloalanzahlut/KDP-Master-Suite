# 📜 MASTER CONTEXT - KDP_MASTER

## 🧠 ORCHESTRATOR BEHAVIOR
name: master-agent-orchestrator
description: Directrices de operación, auditoría y toma de decisiones para el agente multi-sistema.
<modo_auditoria>ENABLED</modo_auditoria>
<control_versiones>Sync with @docs/last-update.log</control_versiones>
<misión>
Orquestar workflows especializados. Ante cada fix o update, auditar cambios contra la base técnica existente.
</misión>
<flujo_ejecucion>
1. Detección: Identificar archivos modificados usando `@diff`.
2. Contextualización: Cargar el corpus de reglas desde este documento.
3. Validación: Ejecutar lógica de auditoría estructural y de impacto.
4. QA: Ejecutar validación para evitar regresiones.
5. Decisión: Ejecutar `release-gate` para confirmar estabilidad.
6. Consolidar: Reportar estado final del enjambre de agentes.
</flujo_ejecucion>
<reglas_operativas>
- Lazy Audit: No analices lo que no cambió. Enfócate en el `diff`.
- Traceability: Cada decisión DEBE citar la regla específica (ej: `@security-rules`, `@clean-code`).
- Zero Noise: Si no hay errores críticos, reportar solo `PASS`.
- Delegación Obligatoria: No usar conocimiento general; aplicar estrictamente lo definido aquí.
- Deduplicación: Consolidar issues repetidos en un único hallazgo.
</reglas_operativas>
<formato_salida>
Estado global: PASS / FAIL
Riesgos críticos (Clasificados por severidad)
Decisión final: DEPLOY / NO DEPLOY
</formato_salida>



## 🧼 CLEAN CODE
name: clean-code
description: Estándares de legibilidad, estructura de funciones y eliminación de redundancia.
<legibilidad_y_semántica>
Nombres Claros: Variables, funciones y clases deben tener nombres descriptivos que expliquen su propósito sin necesidad de comentarios adicionales.
Idioma: Nombres de variables en inglés (convención técnica), explicaciones en español profesional.
</legibilidad_y_semántica>
<arquitectura_de_funciones>
Single Responsibility Principle (SRP): Cada función debe realizar una única tarea y hacerla bien.
Tamaño: Mantener funciones pequeñas y concisas. Si una función supera las 20 líneas, evaluar una subdivisión lógica.
</arquitectura_de_funciones>
DRY (Don't Repeat Yourself): Prohibida la lógica duplicada. Centralizar funciones comunes en utilidades o helpers.
Simplificación: Eliminar código muerto y refactorizar estructuras complejas por unas más legibles.
<audit_action>
Durante el proceso de `/refine`, cualquier bloque que viole el principio DRY o SRP será marcado para refactorización inmediata.
</audit_action>

---

## 📚 DOCUMENTATION CONSISTENCY
name: documentation-consistency
description: Protocolo de sincronización obligatoria entre implementación y documentación.
<sincronización_obligatoria>
Toda modificación de lógica, flujo o interfaz DEBE reflejarse simultáneamente en:
Código: Comentarios técnicos y limpieza según `@clean-code`.
Documentación Técnica: Actualización de esquemas, APIs y lógica en la carpeta `/docs`.
Manual de Usuario: Ajuste de pasos operativos si la funcionalidad cambia para el usuario final.
</sincronización_obligatoria>
<criterio_de_aceptación>
Si un cambio en el código no tiene su contraparte en la documentación:
→ STATUS: INCOMPLETO
→ ACTION: Bloquear Deploy/Merge</criterio_de_aceptación>
<audit_instruction>
Antes de finalizar cualquier comando `/refine` o `/build`, el agente debe verificar si los archivos en `D:/ANEXOS KDP Y DIGITALES/KDP_MASTER/docs` requieren una actualización basada en los cambios del `@diff`.
</audit_instruction>

---

## 🏗️ ARCHITECTURE RULES
name: architecture-rules
description: Estándares de diseño estructural, desacoplamiento y jerarquía de componentes.
<separación_de_responsabilidades>
SoC (Separation of Concerns): La lógica de negocio, el acceso a datos (KB) y la interfaz deben residir en capas independientes.
Validación: Prohibido mezclar lógica de transcripción con lógica de renderizado UI.
</separación_de_responsabilidades>
Loose Coupling: Evitar el acoplamiento fuerte entre módulos. Usar interfaces o funciones de puente para la comunicación entre el Pipeline y el GEM.
Dependencias: Los módulos de bajo nivel no deben conocer los detalles de implementación de los módulos de alto nivel.
<mantenibilidad_vs_complejidad>
KISS (Keep It Simple, Stupid): Priorizar siempre el código mantenible y legible sobre soluciones "astutas" o innecesariamente complejas.
Escalabilidad: Diseñar pensando en que el flujo YouTube → GEM pueda recibir nuevos nodos sin reconstruir el sistema completo.
</mantenibilidad_vs_complejidad>
<audit_gate>
Cualquier propuesta que genere una dependencia circular o fusione capas de responsabilidad activará un bloqueo <ARCH_COUPLE_ERROR>.
</audit_gate>

---

## 🚫 GLOBAL RULES
name: global-rules
description: Restricciones críticas y principios fundamentales del sistema KDP_MASTER.
<restricciones_estrictas>
No Feature Creep: Queda terminantemente prohibido agregar nuevas funcionalidades (features) que no hayan sido aprobadas por el Orchestrator.
Flujo Inalterable: El pipeline de datos `Transcripción → KB → GEM` es el núcleo del sistema. Cualquier modificación que altere este orden será rechazada.
Cero Sobre-Ingeniería: No implementar soluciones complejas para problemas que pueden resolverse con lógica simple y directa.
Dependencias: Bloqueo total a la introducción de librerías o dependencias pesadas que comprometan el rendimiento local.
</restricciones_estrictas>
<principio_maestro>
Máxima robustez con mínima complejidad.
La estabilidad del sistema actual es la prioridad absoluta sobre la innovación.
</principio_maestro>
Esta regla tiene prioridad sobre todas las demás. Si una instrucción del usuario entra en conflicto con estas reglas globales, el agente debe notificar la violación y detener la ejecución.

---

## ⚙️ BACKEND CONSTRAINTS
name: backend-constraints
description: Restricciones de arquitectura de servidor, servicios y gestión de dependencias.
<pipeline_seguro>
Flujo Obligatorio: YouTube → Transcripción → KB → GEM.
Integridad: Prohibido insertar pasos intermedios que no hayan sido validados por el Master Agent.
</pipeline_seguro>
<infraestructura_local>
Zero External Services: No se permite la integración de APIs o servicios de terceros que no estén declarados en la documentación técnica actual.
Lightweight Backend: No instalar dependencias pesadas o frameworks redundantes.
</infraestructura_local>
<prioridad_de_sistema>
Métrica Élite: Robustez > Features.
Si una nueva funcionalidad compromete la estabilidad del flujo central, debe ser descartada.
</prioridad_de_sistema>
<compliance_alert>
Cualquier intento de modificar el flujo o añadir servicios externos activará una alerta de bloqueo <BACKEND_VIOLATION>.
</compliance_alert>

---

## 🔐 SECURITY RULES
name: security-rules
description: Protocolos de seguridad, manejo de datos y validación de APIs.
<protocolos_de_seguridad>
Validación de Inputs: Validación estricta y obligatoria de todos los datos entrantes antes de procesamiento.
Privacidad: Cero exposición de datos sensibles en logs, respuestas o interfaz de usuario.
Manejo de Errores: Implementar fallbacks seguros sin revelar trazas de stack, paths internos o variables de entorno.
Sanitización: Verificar tipo de contenido (MIME/Headers) antes de cualquier llamada a API externa.
</protocolos_de_seguridad>

---

## 🤖 AI INPUT VALIDATION
name: ai-input-validation
description: Regla para validar inputs de IA y compatibilidad de visión (Multimodal).
<modelo_restricciones>
Gemini Pro (Non-Vision): NO enviar imágenes.
GPT-3.5 Turbo: NO enviar imágenes.
Soporte Multimodal: Solo los modelos explícitamente compatibles procesan archivos multimedia.
</modelo_restricciones>
<acciones_obligatorias>
Pre-check: Validar el MIME type (`image/png`, `image/jpg`, etc.) antes de la invocación.
Error Handling: Si el modelo no soporta Vision, retornar: `ERROR_MODEL_INCOMPATIBILITY: Vision not supported`.
Logic: Prohibido intentar conversiones automáticas de texto a imagen o viceversa sin intervención manual.
</acciones_obligatorias>
<whitelist_vision>
gemini-pro-vision
gpt-4-vision-preview
gpt-4o
gemma3:12b (si aplica localmente)
</whitelist_vision>

---

## 🔍 TRANSCRIPTION VALIDATION PROTOCOL
name: rule-check-transcription
description: Protocolo de validación técnica y normalización de transcripciones entrantes.
<condiciones_de_integridad>
Contenido: La transcripción debe contener texto (no vacía).
Unicidad: El `hash` de la transcripción no debe existir previamente en la base de datos (evitar duplicados).
Encoding: El texto debe estar estrictamente normalizado en UTF-8.
Sanitización: No debe contener caracteres nulos (`\0`) o secuencias de control inválidas que corrompan la base de datos.
</condiciones_de_integridad>
<acciones_de_clasificación>
PASS: Si cumple todos los criterios, etiquetar como `STATUS: VALIDA`.
FAIL: Si falla un solo criterio, etiquetar como `STATUS: FALLIDA` y emitir una alerta técnica detallando el error.
Log: Registrar obligatoriamente el `timestamp` del proceso de verificación.
</acciones_de_clasificación>
<connection_point>
Esta regla es el disparador obligatorio para `@gem-data-insertion`. Ningún dato llega al GEM sin el sello de `VALIDA` de este protocolo.
</connection_point>

---

## 📥 GEM DATA INSERTION PROTOCOL
name: gem-data-insertion
description: Regla para alimentar el GEM con transcripciones validadas y consistencia de KB.
<pre_condiciones_obligatorias>
Validación de Origen: La transcripción debe estar marcada como "válida" según `@rule-check-transcription`.
Sincronización: La Base de Conocimientos (KB) debe estar actualizada y confirmada como consistente antes de proceder.
</pre_condiciones_obligatorias>
<acciones_de_ejecucion>
Integridad: Insertar transcripción en el GEM sin alteraciones al contenido original (Raw Data).
Trazabilidad: Registrar obligatoriamente el `timestamp` de envío.
Fail-Safe: Emitir una alerta inmediata en caso de fallo en cualquier nodo de inserción.
</acciones_de_ejecucion>
PROHIBIDO modificar, resumir o editar la transcripción durante el proceso de inserción al GEM.

---

## 💾 KB BACKUP PROTOCOL
name: kb-backup-protocol
description: Sistema de respaldo preventivo de la Base de Conocimientos (KB) ante mutaciones de datos.
<condiciones_de_activación>
Existencia: Confirmar presencia de la KB local en la ruta definida.
Mutación Detectada: Cambios confirmados mediante verificación de `hash` o incremento en el conteo de registros.
</condiciones_de_activación>
<procedimiento_operativo>
Ejecución: Generar copia íntegra en la ruta `.kb_backups/` utilizando el formato de nombre `YYYY-MM-DD_HHMMSS_kb_backup.db` (o extensión correspondiente).
Logging: Registrar resultado (SUCCESS/FAIL) en el log de operaciones global.
System Check: Validar espacio en disco. CRÍTICO: Alertar y detener proceso si el espacio disponible es menor a 500MB.
</procedimiento_operativo>
<safety_gate>
Si el backup falla o el espacio en disco es insuficiente, se debe abortar la secuencia de inserción en el GEM para evitar corrupción de datos.
</safety_gate>

---

## ⚙️ FRONTEND CONSTRAINTS
name: frontend-constraints
description: Restricciones consolidadas de diseño, arquitectura y dependencias del frontend.
<arquitectura_central>
Pipeline Intocable: YouTube → Transcripción → KB → GEM.
Regla: Cualquier sugerencia que altere este orden o elimine un nodo será rechazada automáticamente.
Flujo Inalterable: Cualquier propuesta de refactor debe respetar estrictamente esta cadena de procesamiento.
</arquitectura_central>
<gestion_de_dependencias>
Bloqueo de Librerías: Prohibido instalar librerías pesadas (ej. frameworks de UI masivos) o externas sin justificación crítica y auditoría previa.
Enfoque: Uso de recursos nativos o utilidades de alto rendimiento ya existentes.
Priorizar soluciones nativas o ligeras para mantener el rendimiento local.
</gestion_de_dependencias>
<filosofia_del_producto>
Estética & Minimalismo: Mantener el minimalismo absoluto y el foco funcional.
Jerarquía: Prioridad Técnica: Robustez + Claridad > Acumulación de funcionalidades (Features).
</filosofia_del_producto>
<compliance_check>
Si una tarea de desarrollo implica añadir una dependencia de terceros o alterar el flujo central, el agente debe disparar una alerta <EXTERNAL_DEP_WARNING> / <ARCH_VIOLATION> antes de proceder.
</compliance_check>