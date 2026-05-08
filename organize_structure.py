import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STRUCTURE = {
    "docs": [
        "MANUAL_USUARIO.md",
        "Sugerencias y Trucos Finales.txt",
        "README.md"
    ],
    "modules": [
        "check_kb_health.py",
        "generate_role_graph.py",
        "integrate_knowledge.py",
        "convert_to_pdf.py",
        "generate_category_report.py",
        "generate_html_index.py",
        "validate_config.py",
        "install_ffmpeg.py",
        "security.py",
        "check_updates.py"
    ]
}

def organize():
    print(f"Organizando proyecto en: {BASE_DIR}")
    
    # Crear __init__.py en modules si no existe
    modules_dir = os.path.join(BASE_DIR, "modules")
    if not os.path.exists(modules_dir):
        os.makedirs(modules_dir)
    
    init_file = os.path.join(modules_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# KDP Master Modules\n")

    # Crear docs si no existe
    docs_dir = os.path.join(BASE_DIR, "docs")
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    # Mover archivos
    for folder, files in STRUCTURE.items():
        target_dir = os.path.join(BASE_DIR, folder)
        for file in files:
            src = os.path.join(BASE_DIR, file)
            dst = os.path.join(target_dir, file)
            
            if os.path.exists(src):
                try:
                    shutil.move(src, dst)
                    print(f"✅ Movido: {file} -> {folder}/")
                except Exception as e:
                    print(f"❌ Error moviendo {file}: {e}")
            else:
                print(f"⚠️ No encontrado: {file} (se omitió)")

if __name__ == "__main__":
    organize()