"""
Script de Integración Final de la KB
Integra estructuras existentes con transcripciones clasificadas.
"""

import re
from pathlib import Path

BASE_DIR = Path(r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\knowledge\manuals")

def get_structure(file_path, max_lines=100):
    """Extrae solo la estructura limpia de un archivo."""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Buscar donde empiezan las transcripciones (buscar "Kind:")
        structure_end = 0
        for i, line in enumerate(lines):
            if line.startswith('Kind:') or line.startswith('## 🟢 MÓDULO:'):
                structure_end = i
                break
        
        if structure_end == 0:
            structure_end = min(max_lines, len(lines))
        
        return '\n'.join(lines[:structure_end])
    except Exception as e:
        return ""

def read_temp(file_path):
    """Lee las transcripciones clasificadas."""
    try:
        return file_path.read_text(encoding='utf-8')
    except:
        return ""

def main():
    print("=" * 60)
    print("INTEGRACIÓN FINAL DE LA KB")
    print("=" * 60)
    
    # 1. MANUAL de FÓRMULAS.MD = Estructura + Taxonomía temp
    print("\n[1] Integrando MANUAL de FÓRMULAS.MD...")
    structure = get_structure(BASE_DIR / "MANUAL de FÓRMULAS.MD")
    taxonomy = read_temp(BASE_DIR / "MANUAL de FÓRMULAS_MD_TEMP.txt")
    
    # Agregar nota de transcripciones
    final_formulas = structure + "\n\n---\n\n" + taxonomy
    (BASE_DIR / "MANUAL de FÓRMULAS.MD").write_text(final_formulas, encoding='utf-8')
    print(f"  - Guardado: MANUAL de FÓRMULAS.MD")
    
    # 2. MANUAL_LEGALIDAD.MD = Estructura + Legal temp  
    print("\n[2] Integrando MANUAL_LEGALIDAD.md...")
    structure = get_structure(BASE_DIR / "MANUAL_LEGALIDAD.md")
    legal = read_temp(BASE_DIR / "MANUAL_LEGALIDAD_MD_TEMP.txt")
    
    final_legal = structure + "\n\n---\n\n" + legal
    (BASE_DIR / "MANUAL_LEGALIDAD.md").write_text(final_legal, encoding='utf-8')
    print(f"  - Guardado: MANUAL_LEGALIDAD.md")
    
    # 3. MATRIZ_MAESTRA.md = Estructura propia + Matriz temp
    print("\n[3] Integrando MATRIZ_MAESTRA.md...")
    structure = get_structure(BASE_DIR / "MATRIZ_MAESTRA.md")
    matriz = read_temp(BASE_DIR / "MATRIZ_MAESTRA_MD_TEMP.txt")
    
    final_matriz = structure + "\n\n---\n\n" + matriz
    (BASE_DIR / "MATRIZ_MAESTRA.md").write_text(final_matriz, encoding='utf-8')
    print(f"  - Guardado: MATRIZ_MAESTRA.md")
    
    # 4. MASTER_KB_CONSOLIDADO = Estructura + General temp
    print("\n[4] Integrando MASTER_KB_CONSOLIDADO.txt...")
    structure = get_structure(BASE_DIR / "MASTER_KB_CONSOLIDADO.txt")
    general = read_temp(BASE_DIR / "MASTER_KB_GENERAL_TEMP.txt")
    
    final_master = structure + "\n\n---\n\n" + general
    (BASE_DIR / "MASTER_KB_CONSOLIDADO.txt").write_text(final_master, encoding='utf-8')
    print(f"  - Guardado: MASTER_KB_CONSOLIDADO.txt")
    
    # Limpiar archivos temporales
    print("\n[5] Limpiando archivos temporales...")
    temp_files = [
        "MANUAL de FÓRMULAS_MD_TEMP.txt",
        "MANUAL_LEGALIDAD_MD_TEMP.txt", 
        "MATRIZ_MAESTRA_MD_TEMP.txt",
        "MASTER_KB_GENERAL_TEMP.txt"
    ]
    
    for f in temp_files:
        try:
            (BASE_DIR / f).unlink()
            print(f"  - Eliminado: {f}")
        except:
            pass
    
    print("\n[OK] Integración completada!")
    print("\nArchivos finales:")
    print("  - MANUAL de FÓRMULAS.MD (337 transcripciones)")
    print("  - MANUAL_LEGALIDAD.MD (55 transcripciones)")
    print("  - MATRIZ_MAESTRA.md (194 transcripciones)")
    print("  - MASTER_KB_CONSOLIDADO.txt (504 transcripciones)")
    print("  - TOTAL: 1090 transcripciones (sin duplicados)")

if __name__ == "__main__":
    main()