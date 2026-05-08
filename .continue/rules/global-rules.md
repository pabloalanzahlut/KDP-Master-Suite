---
name: global-rules
description: Restricciones críticas y principios fundamentales del sistema KDP_MASTER.
---

# 🚫 GLOBAL RULES

### <restricciones_estrictas>
- **No Feature Creep:** Queda terminantemente prohibido agregar nuevas funcionalidades (features) que no hayan sido aprobadas por el Orchestrator.
- **Flujo Inalterable:** El pipeline de datos `Transcripción → KB → GEM` es el núcleo del sistema. Cualquier modificación que altere este orden será rechazada.
- **Cero Sobre-Ingeniería:** No implementar soluciones complejas para problemas que pueden resolverse con lógica simple y directa.
- **Dependencias:** Bloqueo total a la introducción de librerías o dependencias pesadas que comprometan el rendimiento local.
</restricciones_estrictas>

### <principio_maestro>
> **Máxima robustez con mínima complejidad.**
- La estabilidad del sistema actual es la prioridad absoluta sobre la innovación.
</principio_maestro>

<enforcement>
Esta regla tiene prioridad sobre todas las demás. Si una instrucción del usuario entra en conflicto con estas reglas globales, el agente debe notificar la violación <GLOBAL_RULE_VIOLATION> y detener la ejecución.
</enforcement>

---

### <git_github_flujo>
**Auto-commit y Push a GitHub - Flujo Obligatorio**

Para cada cambio significativo en el código (programas, configuración, docs):

1. **Verificar repositorio existente**:
   ```bash
   git remote -v
   ```
   - Si NO hay repositorio remoto → **NOTIFICAR** al usuario y NO hacer push
   - Si SÍ hay repositorio → Proceder al paso 2

2. **Agregar archivos modificados**:
   ```bash
   git add <archivos>
   ```

3. **Crear commit con mensaje descriptivo**:
   ```bash
   git commit -m "tipo: descripción corta
   - Cambio 1
   - Cambio 2"
   ```
   - Prefijos válidos: `fix:`, `feat:`, `docs:`, `refactor:`, `chore:`

4. **Push a GitHub**:
   ```bash
   git push origin <branch>
   ```

**Reglas adicionales**:
- Siempre verificar que el repositorio existe antes de hacer push
- Si el proyecto tiene su propio repositorio, usarlo; si no, usar el principal del workspace
- Incluir descripción clara de qué cambió
- Commits pequeños y frecuentes > commits grandes
</git_github_flujo>
