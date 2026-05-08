"""
Script de Merge para MASTER_KB.txt y MASTER_KB_TRANSCRIPCIONES.txt
Elimina duplicados, contenido banal, y consolida el conocimiento.
"""

import re
import hashlib
from pathlib import Path

BASE_DIR = Path(r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\knowledge\manuals")
MASTER_KB = BASE_DIR / "MASTER_KB.txt"
TRANSCRIPCIONES = BASE_DIR / "MASTER_KB_TRANSCRIPCIONES.txt"
OUTPUT_FILE = BASE_DIR / "MASTER_KB_CONSOLIDADO.txt"

BANAL_KEYWORDS = [
    "blooper", "outtake", "behind the scenes", "bts", "vlog", "day in my life",
    "q&a random", "subscribe", "like this video", "hit the bell", "notification",
    "easter egg", "trailer", "teaser", "coming soon", "music video", "lyrics",
    "prank", "challenge", "tag", "collab", "shoutout", "sponsored", "paid partnership",
    "affiliate link", "disclaimer", "not financial advice", "my cat", "my dog", "my kids",
    "travel vlog", "food vlog", "storytime", "rant", "confession", "drama", "gossip"
]

def extract_video_id(fuente_line):
    match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', fuente_line)
    return match.group(1) if match else None

def extract_module_content(lines, start_idx):
    content_lines = []
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if re.match(r'^## 🟢 MÓDULO:', line) and i != start_idx:
            break
        content_lines.append(line.rstrip('\n'))
    return content_lines

def is_content_banal(lines):
    content_text = ' '.join(lines).lower()
    for keyword in BANAL_KEYWORDS:
        if keyword in content_text:
            return True
    return False

def normalize_title(title_line):
    match = re.search(r'## 🟢 MÓDULO: (.+)', title_line)
    return match.group(1).strip() if match else title_line

def compute_content_hash(lines):
    content = '\n'.join(lines)
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def extract_all_modules(lines):
    modules = []
    for i, line in enumerate(lines):
        if re.match(r'^## 🟢 MÓDULO:', line):
            module_lines = extract_module_content(lines, i)
            modules.append(module_lines)
    return modules

def main():
    print("=" * 60)
    print("MERGE MASTER_KB + TRANSCRIPCIONES")
    print("=" * 60)
    
    # Cargar archivos
    print("\n[1] Cargando archivos...")
    master_content = MASTER_KB.read_text(encoding='utf-8')
    master_lines = master_content.split('\n')
    transcripciones_content = TRANSCRIPCIONES.read_text(encoding='utf-8')
    transcripciones_lines = transcripciones_content.split('\n')
    
    # Extraer header de MASTER_KB (hasta el primer módulo)
    header_end = 0
    for i, line in enumerate(master_lines):
        if line.startswith('## 🟢 MÓDULO:'):
            header_end = i
            break
    header_part = master_lines[:header_end]
    print(f"  - Headerextraido: {header_end} lineas")
    
    # Extraer módulos
    print("\n[2] Extrayendo modulos...")
    master_modules = extract_all_modules(master_lines)
    transcripciones_modules = extract_all_modules(transcripciones_lines)
    print(f"  - Modulos en MASTER_KB: {len(master_modules)}")
    print(f"  - Modulos en TRANSCRIPCIONES: {len(transcripciones_modules)}")
    
    # Deduplicación
    print("\n[3] Deduplicando por ID de video...")
    seen_video_ids = set()
    unique_modules = []
    banal_count = 0
    
    for module in master_modules + transcripciones_modules:
        if len(module) < 3:
            continue
        fuente_line = [l for l in module if 'FUENTE:' in l]
        if not fuente_line:
            continue
        video_id = extract_video_id(fuente_line[0])
        
        if is_content_banal(module):
            banal_count += 1
            continue
            
        if video_id and video_id not in seen_video_ids:
            seen_video_ids.add(video_id)
            unique_modules.append(module)
        elif not video_id:
            content_hash = compute_content_hash(module)
            if content_hash not in seen_video_ids:
                seen_video_ids.add(content_hash)
                unique_modules.append(module)
    
    print(f"  - Modulos unicos retenidos: {len(unique_modules)}")
    print(f"  - Modulos banales eliminados: {banal_count}")
    
    # Ordenar
    print("\n[4] Ordenando modulos...")
    unique_modules.sort(key=lambda m: normalize_title(m[0]) if m else '')
    
    # Construir header
    print("\n[5] Actualizando header...")
    n_modules = len(unique_modules)
    n_videos = len(seen_video_ids)
    n_banal = banal_count
    
    new_header = f"""# 📚 MASTER_KB - ÍNDICE DE CONOCIMIENTO KDP v4.0
**Versión:** 4.0  
**Fecha:** 2026-04-11  
**Modelo IA:** qwen3:8b (Ollama local)

---

## 📁 Archivos de la Base de Conocimiento

| Archivo | Contenido | Estado |
|---------|------------|--------|
| MASTER_KB.txt | Estructura+Transcripciones | OBSOLETO |
| MASTER_KB_TRANSCRIPCIONES.txt | Transcripciones | OBSOLETO |
| MASTER_KB_CONSOLIDADO.txt | Conocimiento unificado | ACTIVO |
| MANUAL_LEGALIDAD.md | Compliance, TOS, fiscalidad, 2FA | Completo v2.6 |
| MANUAL de FÓRMULAS.MD | Métricas, KPIs, Taxonomía (Rol #14) | Completo |
| MATRIZ_MAESTRA.md | Fases SOE, roles, KPIs, Gates | En desarrollo |
| SYNTHLEARN_PROMPTS.md | Prompt maestro oficial | Activo |

---

## 🔑 18 CATEGORÍAS KDP (INVARIABLES)

| # | Categoría | Palabras Clave |
|---|-----------|----------------|
| 1 | Investigación de Nichos | nicho, demanda, BSR, competencia, validación, tendencia, oportunidad, mercado, palabras clave, bestseller |
| 2 | Diseño de Portada | cover, thumbnail, Canva, diseño, conversión, CTR, color, tipografía |
| 3 | Publicación KDP | upload, ISBN, categorías, metadatos, KDP Console, paperback, ebook, kindle unlimited |
| 4 | Amazon Ads (PPC) | ACOS, Sponsored Products, pujas, campañas, keywords, targeting, presupuesto |
| 5 | Legalidad y Compliance | TOS, W-8BEN, 2FA, copyright, DRM, fiscalidad, IVA, regalías |
| 6 | Pricing y Monetización | precio, royalties, margen, costo de impresión, estrategia de precios, bundle |
| 7 | Reviews y Gestión de Reseñas | reseñas, reviews, feedback, estrellas, gestión de reseñas |
| 8 | SEO Amazon (A9) | keywords, búsqueda, posicionamiento, backend keywords, categorización |
| 9 | Optimización de Listados | bullet points, descripción, título, A+ content, rich media |
| 10 | Marketing y Tráfico Externo | redes sociales, tráfico, Facebook ads, Instagram, TikTok, Pinterest |
| 11 | Low-Content | coloring book, workbook, journal, planner, notebook, activity book, dot marker |
| 12 | Medium-Content | guide, handbook, manual, course, educational |
| 13 | High-Content | novels, non-fiction, fiction, children's books |
| 14 | Análisis de Datos | métricas, dashboard, ventas, reportes, analytics |
| 15 | Herramientas y Software | Canva, ChatGPT, Publisher Rocket, KDP Rocket, Kindle Create |
| 16 | Scaling y Automatización | automatización, procesos, sistemas, eficiencia, workflow |
| 17 | Internacionalización | traducción, localization, idiomas, mercado internacional |
| 18 | Brand Building | marca, branding, identidad, series |

---

## 👥 37+1 ROLES GEM (FIJOS)

| # | Rol | Descripción |
|---|-----|-------------|
| 1 | Analista de Mercado Educativo | Identificación y validación de nichos rentables |
| 2 | Copywriter de Conversión | Copy para listings, descripciones persuasivas |
| 3 | Diseñador Gráfico UI/UX | Portadas, interiores, diseño visual de alta conversión |
| 4 | Especialista en Accesibilidad e Inclusión | Contenido accesible para todas las audiencias |
| 5 | Product Manager de Plataforma | Gestión de producto y roadmap editorial |
| 6 | Especialista SEO Amazon (A9) | Optimización para el algoritmo de búsqueda de Amazon |
| 7 | Especialista PPC Amazon | Campañas de publicidad pagada en Amazon |
| 8 | User Researcher | Investigación de usuario y feedback |
| 9 | Community Manager | Gestión de comunidad, redes sociales, engagement |
| 10 | Gestor de Calidad y Satisfacción | Control de calidad, satisfacción del cliente |
| 11 | Consultor de PI para Contenido Educativo | Protección de propiedad intelectual educativa |
| 12 | Productor de Audiolibros | Producción de audiolibros para ACX/Audible |
| 13 | Traductor Profesional | Traducción y adaptación de contenido |
| 14 | Especialista en Print-on-Demand | Especificaciones técnicas de impresión |
| 15 | Video Marketing Specialist | Creación de videos promocionales |
| 16 | Especialista Cross-Platform | Distribución multi-plataforma |
| 17 | Affiliate Marketing Manager | Programa de afiliados y comisiones |
| 18 | Analista Financiero | Análisis de rentabilidad, pricing, ROI |
| 19 | Consultor en Propiedad Intelectual | Registro de marcas y protección legal |
| 20 | Especialista en Compliance KDP | Cumplimiento de políticas de Amazon |
| 21 | Especialista en IA para Automatización | Automatización con herramientas de IA |
| 22 | Especialista en Gamificación | Elementos gamificados para engagement |
| 23 | Desarrollador de Apps/Complementos | Desarrollo de apps companions |
| 24 | PR Manager | Relaciones públicas y marketing |
| 25 | Analista de Regalías y Fiscalidad | Gestión fiscal internacional |
| 26 | Gestor de Credenciales y Seguridad | Seguridad de cuentas y gestión de accesos |
| 27 | IA para Automatización Editorial | Automatización de procesos editoriales |
| 28 | Diseñador Instruccional | Diseño de experiencias de aprendizaje |
| 29 | Ilustrador Conceptual | Creación de ilustraciones y assets |
| 30 | Editor Técnico de Interiores | Formateo técnico de interiores |
| 31 | Gestor de Credenciales | Gestión de credenciales de cuenta |
| 32 | Editor de Estilo | Revisión de estilo y tono |
| 33 | Coordinador de Red | Coordinación de equipos y recursos |
| 34 | Portfolio Manager | Gestión de portfolio editorial |
| 35 | Scaling Specialist | Especialista en escalabilidad |
| 36 | Inovação Scout | Investigación de tendencias emergentes |
| 37 | Taxonomía y Arquitectura de Información | Organización y estructura del conocimiento |
| +1 | Branding | Identidad de marca y posicionamiento |

---

## 📊 Estadísticas del Sistema (MERGE v4.0)

| Métrica | Valor |
|--------|-------|
| Total entradas de conocimiento | {n_modules} |
| Videos procesados | {n_videos} |
| Contenido banal/fuera de scope | {n_banal} |
| Entradas analizadas profundamente | [A CALCULAR] |

---

## 🔄 Historial de Procesamiento

| Fecha | Videos | Entradas | Score Avg | Modelo | Notas |
|-------|--------|----------|-----------|--------|-------|
| 2026-04-09 | - | - | - | qwen3:8b | Inicio sistema v3.0 |
| 2026-04-11 | {n_videos} | {n_modules} | - | qwen3:8b | Merge KB + Transcripciones |

---

## ⚙️ Configuración Ollama

```env
OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_KEEP_ALIVE=2m
BATCH_THRESHOLD=10
MAX_TOKENS_INPUT=4000
```

---

*Archivo consolidado el 2026-04-11*
*Eliminar duplicados por video_id*
*Contenido banal eliminado: {n_banal}*
"""
    
    # Generar output
    print("\n[6] Generando archivo consolidado...")
    output_lines = [new_header]
    output_lines.append('')
    output_lines.append('---')
    output_lines.append('')
    
    for module in unique_modules:
        output_lines.extend(module)
        output_lines.append('')
        output_lines.append('---')
        output_lines.append('')
    
    output_content = '\n'.join(output_lines)
    OUTPUT_FILE.write_text(output_content, encoding='utf-8')
    
    print(f"\n[OK] Archivo consolidado guardado: {OUTPUT_FILE}")
    print(f"   - Total lineas: {len(output_content.split(chr(10)))}")
    print(f"   - Total modulos: {n_modules}")
    print(f"   - Videos unicos: {n_videos}")
    print(f"   - Contenido banal eliminado: {n_banal}")

if __name__ == "__main__":
    main()