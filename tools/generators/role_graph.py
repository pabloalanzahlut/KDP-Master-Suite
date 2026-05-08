import os
import re
from pathlib import Path
from graphviz import Digraph

def generate_graph():
    """
    Genera un gráfico de dependencias de roles a partir de MATRIZ MAESTRA.md.
    """
    base_dir = Path(os.getcwd())
    if base_dir.name == "dist":
        base_dir = base_dir.parent
    
    matriz_file = base_dir / "knowledge" / "manuals" / "MATRIZ MAESTRA.md"
    output_path = base_dir / "outputs" / "reports"
    
    if not matriz_file.exists():
        return False, f"No se encontró el archivo: {matriz_file}"

    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    dot = Digraph('RoleInterdependencies', comment='Diagrama de Interdependencias de Roles SOE')
    dot.attr(rankdir='LR', size='15,15', splines='ortho', nodesep='0.8', label="Diagrama de Interdependencias de Roles SOE", labelloc="t", fontsize="20")
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue', fontname='Segoe UI')
    dot.attr('edge', fontname='Segoe UI', fontsize='10')

    content = matriz_file.read_text(encoding='utf-8')
    
    role_pattern = re.compile(r'\((\d+)\)\s*([^,\|]+)')
    table_row_pattern = re.compile(r'\|\s*F\d:.*?\|\s*(.*?)\s*\|.*?\|.*?\|.*?\|.*?\|\s*(.*?)\s*\|')
    
    nodes = set()
    edges = set()

    for row_match in table_row_pattern.finditer(content):
        involved_col, dependent_col = row_match.groups()
        
        involved_roles = [f"({num}) {name.strip()}" for num, name in role_pattern.findall(involved_col)]
        dependent_roles = [f"({num}) {name.strip()}" for num, name in role_pattern.findall(dependent_col)]
        
        for role in involved_roles + dependent_roles:
            nodes.add(role)
            
        for inv_role in involved_roles:
            for dep_role in dependent_roles:
                edges.add((dep_role, inv_role)) # Dependency: Dependent -> Involved

    for node in nodes:
        dot.node(node, node.replace('<br/>', '\\n'))
        
    for edge_from, edge_to in edges:
        dot.edge(edge_from, edge_to)

    try:
        output_file_path = output_path / "role_interdependencies_graph"
        dot.render(output_file_path, format='png', cleanup=True)
        return True, f"Gráfico guardado en: {output_file_path}.png"
    except Exception as e:
        return False, f"Error generando el gráfico. Asegúrate de que Graphviz está instalado en tu sistema y en el PATH.\nDetalle: {e}"

if __name__ == "__main__":
    success, msg = generate_graph()
    print(msg)