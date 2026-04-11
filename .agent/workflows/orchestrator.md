# 🧠 ORCHESTRATOR WORKFLOW (ENTERPRISE)

## 🎯 MISIÓN
Coordinar agentes especializados, consolidar resultados y producir una decisión técnica final basada en evidencia.

---

## 🔄 FLUJO DE EJECUCIÓN

### 1. Cargar estado actual
Leer:
→ .agents/state/system-state.md

---

### 2. Ejecutar agentes (orden obligatorio)

1. agent-algorithm
2. agent-backend
3. agent-data
4. agent-performance
5. agent-security
6. agent-qa
7. agent-architect

---

### 3. Recolectar mensajes

Todos los agentes deben responder en formato:

## 📡 AGENT MESSAGE

FROM: <agent-name>  
TYPE: <report-type>  

DATA:
- ...

---

### 4. Normalizar resultados

- Eliminar duplicados
- Agrupar por severidad:
  - CRITICAL
  - HIGH
  - MEDIUM
  - LOW

---

### 5. Enviar a scoring

Ejecutar:
→ agent-scoring

---

### 6. Actualizar estado

Escribir en:
→ .agents/state/system-state.md

Actualizar:
- Issues
- Score
- Riesgo
- Deuda técnica

---

### 7. Ejecutar release gate

Ejecutar:
→ release-gate.md

---

## 📊 OUTPUT FINAL

### Estado global
- PASS / FAIL

### Score
- Calidad: X/100
- Riesgo: LOW / MEDIUM / HIGH
- Deuda técnica: %

### Issues críticos
- Lista CRITICAL + HIGH

### Decisión final
- ✅ DEPLOY
- ❌ NO DEPLOY

---

## ⚙️ REGLAS CRÍTICAS

- Ningún agente puede salir de su dominio
- No duplicar información
- Priorizar impacto técnico sobre cantidad
- Si hay conflicto entre agentes:
  → gana el de mayor criticidad (Security > QA > Backend > UX)

---

## 🧠 PRINCIPIO

"Decisiones basadas en evidencia, no en opiniones"

## NUEVO FLUJO PARA UI

Si el análisis es frontend/UI:
→ Ejecutar ui-audit.md