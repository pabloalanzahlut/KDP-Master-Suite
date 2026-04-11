# 🔄 GUÍA DE ADAPTACIÓN A NUEVOS RUBROS

## Cómo usar este sistema de templates

Este sistema permite reutilizar la estructura de agentes y reglas del proyecto KDP_MASTER
para CUALQUIER industria, manteniendo la arquitectura intacta y solo cambiando las
variables de dominio.

---

## 📋 PASO 1: Definir variables del rubro

Abre industry-config.md y completa la tabla de configuración con los valores de tu industria.

### Variables obligatorias:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| {{PROJECT_NAME}} | Nombre del proyecto | MiProyecto |
| {{INDUSTRY}} | Industria/rubro | Legal, Finance, Healthcare |
| {{PIPELINE_DESCRIPTION}} | Pipeline central de datos | Fuente → Proceso → Almacén → Salida |
| {{PIPELINE_NAME}} | Nombre corto del pipeline | Data Pipeline |
| {{DOMAIN_RULES}} | Reglas específicas del dominio | No alterar datos sensibles |
| {{COMPLIANCE_FRAMEWORK}} | Marco regulatorio aplicable | GDPR, HIPAA, SOX |
| {{UI_FRAMEWORK}} | Tecnología de interfaz | React, CustomTkinter, Flutter |
| {{EXTERNAL_SERVICES}} | Servicios externos | APIs, webhooks, integraciones |
| {{HEAVY_DEPS_POLICY}} | Política de dependencias | Sin dependencias pesadas |
| {{OPERATION_MODE}} | Modo de operación | Desktop, Cloud, Hybrid |

---

## 📋 PASO 2: Copiar templates al proyecto

Copiar toda la estructura .agent-templates/ al nuevo proyecto y renombrar como .agent/.

---

## 📋 PASO 3: Reemplazar variables

Reemplaza TODAS las variables {{VARIABLE}} en cada archivo con los valores definidos en el Paso 1.

### PowerShell (Windows):

Usa un script de reemplazo que itere sobre todos los archivos .md en .agent/ y reemplace
cada variable por su valor correspondiente.

### Bash (Linux/Mac):

Usa sed para reemplazos en masa sobre todos los archivos del directorio.

---

## 📋 PASO 4: Validar consistencia

1. Verificar que ningún {{VARIABLE}} quede sin reemplazar
2. Confirmar que el pipeline descrito coincide con la arquitectura real
3. Revisar que las reglas de dominio sean aplicables
4. Validar que el framework de compliance sea correcto para la industria

---

## 📋 PASO 5: Crear estado inicial

Crear el archivo .agent/state/system-state.md con el estado inicial del sistema.

---

## 🏭 EJEMPLOS POR INDUSTRIA

### Legal / Derecho

`
PROJECT_NAME: LegalDocAnalyzer
INDUSTRY: Legal Technology
PIPELINE_DESCRIPTION: Contrato → Extracción de cláusulas → KB → Dictamen legal
PIPELINE_NAME: Contract Analysis Pipeline
DOMAIN_RULES: No alterar texto original de contratos; mantener trazabilidad de cambios
COMPLIANCE_FRAMEWORK: GDPR + Ley de Protección de Datos + Confidencialidad abogado-cliente
UI_FRAMEWORK: React + TailwindCSS
EXTERNAL_SERVICES: DocuSign API, LexisNexis API, Notary API
HEAVY_DEPS_POLICY: Solo librerías auditadas con licencia comercial
OPERATION_MODE: Cloud SaaS
DATA_SENSITIVITY: Confidencial
TARGET_USERS: Abogados y profesionales del derecho
`

### Finanzas / Banca

`
PROJECT_NAME: FinRiskEngine
INDUSTRY: Finance / Banking
PIPELINE_DESCRIPTION: Transacción → Validación → KB → Reporte de riesgo
PIPELINE_NAME: Transaction Risk Pipeline
DOMAIN_RULES: Cumplir límites regulatorios; no modificar datos de transacciones
COMPLIANCE_FRAMEWORK: SOX + PCI-DSS + Basel III + AML/KYC
UI_FRAMEWORK: Angular + Material Design
EXTERNAL_SERVICES: Stripe API, Bloomberg Terminal, SWIFT Network
HEAVY_DEPS_POLICY: Solo paquetes con CVE review y aprobación de seguridad
OPERATION_MODE: Hybrid Cloud
DATA_SENSITIVITY: Restringido
TARGET_USERS: Analistas financieros, risk managers
`

### Healthcare / Salud

`
PROJECT_NAME: HealthRecordAnalyzer
INDUSTRY: Healthcare Technology
PIPELINE_DESCRIPTION: Historial clínico → Normalización → KB → Diagnóstico asistido
PIPELINE_NAME: Clinical Data Pipeline
DOMAIN_RULES: No exponer PHI; mantener consentimiento del paciente; audit trail obligatorio
COMPLIANCE_FRAMEWORK: HIPAA + FDA 21 CFR Part 11 + GDPR
UI_FRAMEWORK: React + FHIR-compliant components
EXTERNAL_SERVICES: Epic API, HL7 FHIR Server, Pharmacy API
HEAVY_DEPS_POLICY: Solo librerías con certificación médica, sin telemetría
OPERATION_MODE: On-Premise + Cloud backup
DATA_SENSITIVITY: Restringido
TARGET_USERS: Médicos, personal clínico
`

### E-Commerce

`
PROJECT_NAME: StoreOptimizer
INDUSTRY: E-Commerce / Retail Digital
PIPELINE_DESCRIPTION: Catálogo → Indexación → KB → Recomendación de productos
PIPELINE_NAME: Product Recommendation Pipeline
DOMAIN_RULES: Precios exactos; stock en tiempo real; no mostrar productos agotados
COMPLIANCE_FRAMEWORK: PCI-DSS + GDPR + Ley Protección al Consumidor
UI_FRAMEWORK: Next.js + TailwindCSS
EXTERNAL_SERVICES: Shopify API, Stripe, FedEx API, TaxJar
HEAVY_DEPS_POLICY: Permitidas librerías populares con >10k stars
OPERATION_MODE: Cloud CDN + Edge Computing
DATA_SENSITIVITY: Público
TARGET_USERS: Vendedores online, managers de e-commerce
`

### Educación / EdTech

`
PROJECT_NAME: CourseAnalyzer
INDUSTRY: Education Technology
PIPELINE_DESCRIPTION: Contenido educativo → Transcripción → KB → Evaluación generada
PIPELINE_NAME: Learning Content Pipeline
DOMAIN_RULES: Contenido pedagógicamente válido; no generar evaluaciones sin validación
COMPLIANCE_FRAMEWORK: FERPA + COPPA + WCAG 2.1 AA
UI_FRAMEWORK: Vue.js + Vuetify
EXTERNAL_SERVICES: LTI API, Turnitin API, Zoom API, LMS Integration
HEAVY_DEPS_POLICY: Sin restricciones especiales, priorizar accesibilidad
OPERATION_MODE: Cloud SaaS
DATA_SENSITIVITY: Confidencial
TARGET_USERS: Educadores, estudiantes, administradores académicos
`

### Real Estate / Inmobiliaria

`
PROJECT_NAME: PropertyAnalyzer
INDUSTRY: Real Estate Technology
PIPELINE_DESCRIPTION: Propiedad → Valuación → KB → Recomendación de inversión
PIPELINE_NAME: Property Analysis Pipeline
DOMAIN_RULES: Datos de valuación verificados; no mostrar propiedades sin documentación
COMPLIANCE_FRAMEWORK: Ley de Bienes Raíces, Protección al Consumidor, GDPR
UI_FRAMEWORK: React + Mapbox GL
EXTERNAL_SERVICES: MLS API, Zillow API, Google Maps, Mortgage Calculator API
HEAVY_DEPS_POLICY: Permitidas librerías de mapeo y visualización
OPERATION_MODE: Cloud SaaS + Mobile
DATA_SENSITIVITY: Público
TARGET_USERS: Agentes inmobiliarios, inversores
`

---

## ⚠️ REGLAS DE ADAPTACIÓN

1. NO modificar la estructura de agentes — solo cambiar variables
2. NO agregar o quitar agentes sin justificación arquitectónica
3. Mantener el formato de output ## AGENT MESSAGE en todos los agentes
4. Preservar el orden de ejecución en el orchestrator
5. Actualizar state/system-state.md con las variables del nuevo rubro
6. Documentar cambios en un archivo CHANGELOG_RUBRO.md

---

## ✅ CHECKLIST DE ADAPTACIÓN

- [ ] Variables definidas en industry-config.md
- [ ] Templates copiados al proyecto como .agent/
- [ ] Todas las variables {{VARIABLE}} reemplazadas
- [ ] Pipeline description coincide con arquitectura real
- [ ] Reglas de dominio son aplicables
- [ ] Framework de compliance es correcto
- [ ] UI framework corresponde a la tecnología usada
- [ ] Servicios externos están documentados
- [ ] Política de dependencias es clara
- [ ] Modo de operación está definido
- [ ] No quedan {{VARIABLE}} sin reemplazar
- [ ] .agent/state/system-state.md creado
- [ ] CHANGELOG_RUBRO.md creado

---

## 🔧 ARCHIVOS ADICIONALES PARA .agents/

Si el proyecto usa el directorio .agents/ con frontmatter YAML:

`yaml
---
trigger: always_on
---

# ⚙️ FRONTEND CONSTRAINTS

- No modificar flujo central: {{PIPELINE_DESCRIPTION}}
- {{HEAVY_DEPS_POLICY}}
- Mantener minimalismo y foco
- Prioridad: robustez + claridad > features
`

---

## 📂 ESTRUCTURA FINAL ESPERADA

`
NUEVO_PROYECTO/
├── .agent/
│   ├── agent.md                          ← Orquestador maestro
│   ├── rules/
│   │   ├── global-rules.md               ← Reglas globales
│   │   ├── architecture-rules.md         ← Reglas de arquitectura
│   │   ├── coding-standards.md           ← Estándares de código
│   │   ├── security-rules.md             ← Reglas de seguridad
│   │   ├── backend-rules.md              ← Restricciones backend
│   │   ├── ui-rules.md                   ← Restricciones frontend
│   │   └── documentation-rules.md        ← Reglas de documentación
│   ├── workflows/
│   │   ├── orchestrator.md               ← Workflow coordinador
│   │   ├── full-audit.md                 ← Auditoría completa
│   │   ├── qa-validation.md              ← Validación QA
│   │   ├── release-gate.md               ← Gate de despliegue
│   │   ├── agent-scoring.md              ← Modelo de scoring
│   │   ├── agent-algorithm.md            ← Agente de algoritmos
│   │   ├── agent-backend.md              ← Agente backend
│   │   ├── agent-data.md                 ← Agente de datos
│   │   ├── agent-performance.md          ← Agente de performance
│   │   ├── agent-security.md             ← Agente de seguridad
│   │   ├── agent-qa.md                   ← Agente QA
│   │   ├── agent-architect.md            ← Agente arquitecto
│   │   └── agent-uiux.md                 ← Agente UI/UX
│   └── state/
│       └── system-state.md               ← Estado del sistema
└── .agents/ (opcional)
    └── rules/
        └── ui-rules-{{INDUSTRY}}.md      ← Reglas UI específicas
`
