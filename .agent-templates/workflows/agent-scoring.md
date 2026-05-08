# 📊 SCORING AGENT

## INPUT
Todos los reports de agentes

## MODELO DE SCORING

Calidad = 100 - (errores ponderados)

Ponderación:
- CRITICAL: -30
- HIGH: -15
- MEDIUM: -5
- LOW: -1

Riesgo:
- HIGH si existe CRITICAL
- MEDIUM si existe HIGH
- LOW si no

Deuda técnica:
- % basado en issues totales / complejidad

## OUTPUT

## 📡 AGENT MESSAGE

FROM: agent-scoring
TYPE: SCORE_REPORT

DATA:
- calidad: X
- riesgo: LOW/MED/HIGH
- deuda: %
