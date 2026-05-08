import os

def generate_context(paths, output_file):
    with open(output_file, 'w', encoding='utf-8') as out:
        for path in paths:
            out.write(f"# DIRECTORIO: {path}\n\n")
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith('.md'):
                        file_path = os.path.join(root, f)
                        out.write(f"## ARCHIVO: {f}\n")
                        with open(file_path, 'r', encoding='utf-8') as content:
                            out.write(content.read() + "\n\n---\n\n")

# Ejecútalo apuntando a tus carpetas
rutas = [
    r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\.agent\rules",
    r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\.agent\workflows"
]
generate_context(rutas, "CONTEXTO_MAESTRO.md")
