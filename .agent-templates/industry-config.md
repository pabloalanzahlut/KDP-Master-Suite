# 📋 INDUSTRY CONFIGURATION TEMPLATE

## INSTRUCCIONES DE USO

Este archivo define las variables que deben personalizarse para adaptar las directivas
a cualquier rubro o industria. Reemplaza cada `{{VARIABLE}}` con el valor correspondiente
antes de copiar los templates al directorio `.agent/` del nuevo proyecto.

---

## VARIABLES OBLIGATORIAS

| Variable | Descripción | Ejemplo KDP | Ejemplo Legal | Ejemplo E-commerce |
|----------|-------------|-------------|---------------|---------------------|
| `{{PROJECT_NAME}}` | Nombre del proyecto | KDP_MASTER | LegalDocAnalyzer | StoreOptimizer |
| `{{INDUSTRY}}` | Rubro/industria | KDP Publishing | Legal Technology | E-Commerce |
| `{{PIPELINE_DESCRIPTION}}` | Pipeline central de datos | YouTube → Transcripción → KB → GEM | Contrato → Extracción → KB → Dictamen | Producto → Análisis → KB → Optimización |
| `{{PIPELINE_NAME}}` | Nombre corto del pipeline | Transcription Pipeline | Contract Pipeline | Product Pipeline |
| `{{DOMAIN_RULES}}` | Reglas específicas del dominio | No modificar flujo de transcripción a publicación | No alterar texto de contratos | No modificar precios sin validación |
| `{{COMPLIANCE_FRAMEWORK}}` | Marco regulatorio | KDP Content Guidelines, Amazon TOS | GDPR, Ley Protección de Datos | PCI-DSS, Ley Comercio Electrónico |
| `{{UI_FRAMEWORK}}` | Tecnología de UI | Tkinter + ttk | React + Tailwind | Next.js + TailwindCSS |
| `{{EXTERNAL_SERVICES}}` | Servicios externos | YouTube API, Gemini AI | DocuSign API, LexisNexis | Shopify API, Stripe |
| `{{HEAVY_DEPS_POLICY}}` | Política de dependencias | Prohibido dependencias pesadas | Solo librerías auditadas | Permitidas librerías populares |
| `{{OPERATION_MODE}}` | Modo de operación | Desktop Offline-First | Cloud SaaS | Cloud CDN + Edge |
| `{{DATA_SENSITIVITY}}` | Nivel sensibilidad datos | Público | Confidencial | Público |
| `{{TARGET_USERS}}` | Perfil de usuarios | Editores KDP | Abogados | Vendedores online |

---

## EJEMPLOS COMPLETOS POR INDUSTRIA

### Ejemplo 1: KDP Publishing (proyecto actual)

```
PROJECT_NAME: KDP Master Suite
INDUSTRY: Amazon KDP Publishing
PIPELINE_DESCRIPTION: YouTube → Transcripción → KB → GEM
PIPELINE_NAME: Transcription Pipeline
DOMAIN_RULES: No modificar flujo de transcripción a publicación KDP
COMPLIANCE_FRAMEWORK: KDP Content Guidelines, Amazon TOS
UI_FRAMEWORK: Tkinter + ttk
EXTERNAL_SERVICES: YouTube Data API, Google Gemini AI
HEAVY_DEPS_POLICY: Prohibido dependencias pesadas en pipeline core
OPERATION_MODE: Desktop Offline-First
DATA_SENSITIVITY: Público
TARGET_USERS: Editores y publishers de Amazon KDP
```

### Ejemplo 2: Legal Technology

```
PROJECT_NAME: LegalDoc Analyzer
INDUSTRY: Legal Technology
PIPELINE_DESCRIPTION: Contrato → Extracción de cláusulas → KB → Dictamen legal
PIPELINE_NAME: Contract Analysis Pipeline
DOMAIN_RULES: No alterar texto original de contratos; mantener trazabilidad de cambios
COMPLIANCE_FRAMEWORK: GDPR, Ley Protección de Datos, Confidencialidad abogado-cliente
UI_FRAMEWORK: React + TailwindCSS
EXTERNAL_SERVICES: DocuSign API, LexisNexis API, Notary API
HEAVY_DEPS_POLICY: Solo librerías auditadas con licencia comercial
OPERATION_MODE: Cloud SaaS
DATA_SENSITIVITY: Confidencial
TARGET_USERS: Abogados y profesionales del derecho
```

### Ejemplo 3: E-Commerce

```
PROJECT_NAME: Store Optimizer
INDUSTRY: E-Commerce / Retail Digital
PIPELINE_DESCRIPTION: Catálogo → Indexación → KB → Recomendación de productos
PIPELINE_NAME: Product Recommendation Pipeline
DOMAIN_RULES: Precios exactos; stock en tiempo real; no mostrar productos agotados
COMPLIANCE_FRAMEWORK: PCI-DSS, GDPR, Ley Protección al Consumidor
UI_FRAMEWORK: Next.js + TailwindCSS
EXTERNAL_SERVICES: Shopify API, Stripe, FedEx API, TaxJar
HEAVY_DEPS_POLICY: Permitidas librerías populares con >10k stars
OPERATION_MODE: Cloud CDN + Edge Computing
DATA_SENSITIVITY: Público
TARGET_USERS: Vendedores online, managers de e-commerce
```

### Ejemplo 4: Healthcare

```
PROJECT_NAME: Health Record Analyzer
INDUSTRY: Healthcare Technology
PIPELINE_DESCRIPTION: Historial clínico → Normalización → KB → Diagnóstico asistido
PIPELINE_NAME: Clinical Data Pipeline
DOMAIN_RULES: No exponer PHI; mantener consentimiento del paciente; audit trail obligatorio
COMPLIANCE_FRAMEWORK: HIPAA, FDA 21 CFR Part 11, GDPR
UI_FRAMEWORK: React + FHIR-compliant components
EXTERNAL_SERVICES: Epic API, HL7 FHIR Server, Pharmacy API
HEAVY_DEPS_POLICY: Solo librerías con certificación médica, sin telemetría
OPERATION_MODE: On-Premise + Cloud backup
DATA_SENSITIVITY: Restringido
TARGET_USERS: Médicos, personal clínico
```

### Ejemplo 5: Finanzas

```
PROJECT_NAME: FinRisk Engine
INDUSTRY: Finance / Banking
PIPELINE_DESCRIPTION: Transacción → Validación → KB → Reporte de riesgo
PIPELINE_NAME: Transaction Risk Pipeline
DOMAIN_RULES: Cumplir límites regulatorios; no modificar datos de transacciones
COMPLIANCE_FRAMEWORK: SOX, PCI-DSS, Basel III, AML/KYC
UI_FRAMEWORK: Angular + Material Design
EXTERNAL_SERVICES: Stripe API, Bloomberg Terminal, SWIFT Network
HEAVY_DEPS_POLICY: Solo paquetes con CVE review y aprobación de seguridad
OPERATION_MODE: Hybrid Cloud
DATA_SENSITIVITY: Restringido
TARGET_USERS: Analistas financieros, risk managers
```

### Ejemplo 6: Educación / EdTech

```
PROJECT_NAME: Course Analyzer
INDUSTRY: Education Technology
PIPELINE_DESCRIPTION: Contenido educativo → Transcripción → KB → Evaluación generada
PIPELINE_NAME: Learning Content Pipeline
DOMAIN_RULES: Contenido pedagógicamente válido; no generar evaluaciones sin validación
COMPLIANCE_FRAMEWORK: FERPA, COPPA, WCAG 2.1 AA
UI_FRAMEWORK: Vue.js + Vuetify
EXTERNAL_SERVICES: LTI API, Turnitin API, Zoom API, LMS Integration
HEAVY_DEPS_POLICY: Sin restricciones especiales, priorizar accesibilidad
OPERATION_MODE: Cloud SaaS
DATA_SENSITIVITY: Confidencial
TARGET_USERS: Educadores, estudiantes, administradores académicos
```
