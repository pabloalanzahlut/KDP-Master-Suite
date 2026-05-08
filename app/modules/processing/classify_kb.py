"""
Script de Clasificación de Transcripciones por Tema
Clasifica transcripciones de MASTER_KB_CONSOLIDADO en archivos correspondientes.
"""

import re
from pathlib import Path

BASE_DIR = Path(r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\knowledge\manuals")
MASTER_KB = BASE_DIR / "MASTER_KB_CONSOLIDADO.txt"
OUTPUT_DIR = BASE_DIR

# Palabras clave por categoría
TAXONOMY_KEYWORDS = [
    "taxonomy", "categor", "keyword", "search term", "A9", "listing", "metadata",
    "title", "subtitle", "backend", "search terms", "index", "find", "discover",
    "organize", "structure", "tag", "label", "facet", "niche", "BSR"
]

LEGAL_KEYWORDS = [
    "legal", "compliance", "TOS", "W-8BEN", "fiscal", "tax", "copyright",
    "DRM", "2FA", "security", "account", "suspended", "policy", "violation",
    "infring", "trademark", "brand", "rights", "royalty", "payment"
]

MATRIZ_KEYWORDS = [
    "workflow", "fase", "phase", "publish", "launch", "launching", "release",
    "process", "rol", "role", "gate", "milestone", "strategy", "system",
    "automate", "automation", "template", "checklist", "roadmap"
]

def load_modules(content):
    """Extrae módulos del contenido."""
    lines = content.split('\n')
    modules = []
    current_module = []
    
    for line in lines:
        if line.startswith('## 🟢 MÓDULO:'):
            if current_module:
                modules.append(current_module)
            current_module = [line]
        elif current_module:
            current_module.append(line)
    
    if current_module:
        modules.append(current_module)
    
    return modules

def classify_module(module_lines):
    """Clasifica un módulo según su contenido."""
    full_text = '\n'.join(module_lines).lower()
    
    # Extraer título
    title = ""
    for line in module_lines[:5]:
        match = re.search(r'## 🟢 MÓDULO: (.+)', line)
        if match:
            title = match.group(1).lower()
            break
    
    # Verificar keywords
    tax_score = sum(1 for kw in TAXONOMY_KEYWORDS if kw in full_text)
    legal_score = sum(1 for kw in LEGAL_KEYWORDS if kw in full_text)
    matriz_score = sum(1 for kw in MATRIZ_KEYWORDS if kw in full_text)
    
    # Clasificar por puntuación
    scores = {
        "taxonomy": tax_score,
        "legal": legal_score,
        "matriz": matriz_score
    }
    
    max_score = max(scores.values())
    
    if max_score == 0:
        return "general"  # No coincide con ninguna categoría específica
    elif scores["taxonomy"] == max_score:
        return "taxonomy"
    elif scores["legal"] == max_score:
        return "legal"
    elif scores["matriz"] == max_score:
        return "matriz"
    else:
        return "general"

def main():
    print("=" * 60)
    print("CLASIFICACIÓN DE TRANSCRIPCIONES POR TEMA")
    print("=" * 60)
    
    # Cargar contenido
    print("\n[1] Cargando MASTER_KB_CONSOLIDADO...")
    content = MASTER_KB.read_text(encoding='utf-8')
    
    # Extraer estructura (header hasta primer módulo)
    header_end = 0
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('## 🟢 MÓDULO:'):
            header_end = i
            break
    
    header = '\n'.join(lines[:header_end])
    
    # Extraer módulos
    print("[2] Extrayendo módulos...")
    modules = load_modules(content)
    print(f"  - Total módulos: {len(modules)}")
    
    # Clasificar
    print("[3] Clasificando módulos...")
    classified = {
        "taxonomy": [],
        "legal": [],
        "matriz": [],
        "general": []
    }
    
    for module in modules:
        category = classify_module(module)
        classified[category].append(module)
    
    print(f"  - Taxonomía: {len(classified['taxonomy'])}")
    print(f"  - Legal: {len(classified['legal'])}")
    print(f"  - Matriz/Fases: {len(classified['matriz'])}")
    print(f"  - General/Otras: {len(classified['general'])}")
    
    # Generar archivos
    print("\n[4] Generando archivos...")
    
    # MANUAL de FÓRMULAS.MD = Taxonomía
    formulas_content = header + "\n\n---\n\n"
    formulas_content += "## 📚 MÓDULOS DE TAXONOMÍA Y MÉTRICAS\n\n"
    formulas_content += "*Transcripciones clasificadas del tema*\n\n---\n\n"
    for module in classified["taxonomy"]:
        formulas_content += '\n'.join(module) + "\n\n---\n\n"
    
    (OUTPUT_DIR / "MANUAL de FÓRMULAS_MD_TEMP.txt").write_text(formulas_content, encoding='utf-8')
    
    # MANUAL_LEGALIDAD = Legal
    legal_content = header + "\n\n---\n\n"
    legal_content += "## 📚 MÓDULOS DE LEGALIDAD Y COMPLIANCE\n\n"
    legal_content += "*Transcripciones clasificadas del tema*\n\n---\n\n"
    for module in classified["legal"]:
        legal_content += '\n'.join(module) + "\n\n---\n\n"
    
    (OUTPUT_DIR / "MANUAL_LEGALIDAD_MD_TEMP.txt").write_text(legal_content, encoding='utf-8')
    
    # MATRIZ_MAESTRA = Matriz/Fases
    matriz_content = header + "\n\n---\n\n"
    matriz_content += "## 📚 MÓDULOS DE PROCESOS Y FASES SOE\n\n"
    matriz_content += "*Transcripciones clasificadas del tema*\n\n---\n\n"
    for module in classified["matriz"]:
        matriz_content += '\n'.join(module) + "\n\n---\n\n"
    
    (OUTPUT_DIR / "MATRIZ_MAESTRA_MD_TEMP.txt").write_text(matriz_content, encoding='utf-8')
    
    # MASTER_KB = General + остальное
    general_content = header + "\n\n---\n\n"
    general_content += "## 📚 DEMÁS TRANSCRIPCIONES\n\n"
    general_content += "*Transcripciones no clasificadas en categorías específicas*\n\n---\n\n"
    for module in classified["general"]:
        general_content += '\n'.join(module) + "\n\n---\n\n"
    
    (OUTPUT_DIR / "MASTER_KB_GENERAL_TEMP.txt").write_text(general_content, encoding='utf-8')
    
    print(f"\n[OK] Archivos temporales generados")
    print(f"  - MANUAL de FÓRMULAS_MD_TEMP.txt")
    print(f"  - MANUAL_LEGALIDAD_MD_TEMP.txt")
    print(f"  - MATRIZ_MAESTRA_MD_TEMP.txt")
    print(f"  - MASTER_KB_GENERAL_TEMP.txt")

if __name__ == "__main__":
    main()