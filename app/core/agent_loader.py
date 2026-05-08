# -*- coding: utf-8 -*-
"""
Agente de Carga de Reglas y Workflows
Carga y parsea archivos .md desde .agent/rules/ y .agent/workflows/
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any

class AgentLoader:
    """
    Carga y parsea archivos de reglas y workflows desde la carpeta .agent/
    """
    def __init__(self, app_root=None):
        if app_root is None:
            import sys
            if getattr(sys, 'frozen', False):
                self.base_dir = Path(sys.executable).parent
            else:
                self.base_dir = Path(__file__).parent.parent.parent
        else:
            self.base_dir = Path(app_root)
        
        self.agent_dir = self.base_dir / ".agent"
        self.rules_dir = self.agent_dir / "rules"
        self.workflows_dir = self.agent_dir / "workflows"
        
        self.rules: Dict[str, Any] = {}
        self.workflows: Dict[str, Any] = {}
    
    def load_all(self) -> Dict[str, Any]:
        """Carga todas las reglas y workflows."""
        self.rules = self._load_directory(self.rules_dir, "rule")
        self.workflows = self._load_directory(self.workflows_dir, "workflow")
        return {
            "rules": self.rules,
            "workflows": self.workflows,
            "summary": {
                "rules_count": len(self.rules),
                "workflows_count": len(self.workflows)
            }
        }
    
    def _load_directory(self, directory: Path, kind: str) -> Dict[str, Any]:
        """Carga todos los archivos .md de un directorio."""
        result = {}
        if not directory.exists():
            return result
        
        for md_file in directory.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                parsed = self._parse_md(content, md_file.name)
                key = md_file.stem.lower().replace("-", "_")
                result[key] = parsed
            except Exception as e:
                print(f"Error cargando {md_file.name}: {e}")
        
        return result
    
    def _parse_md(self, content: str, filename: str) -> Dict[str, Any]:
        """Parsea un archivo .md de regla/workflow."""
        result = {
            "filename": filename,
            "description": "",
            "raw": content
        }
        
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            fm_content = frontmatter_match.group(1)
            desc_match = re.search(r'description:\s*(.+)', fm_content)
            if desc_match:
                result["description"] = desc_match.group(1).strip()
        
        lines = content.split('\n')
        in_section = None
        section_content = []
        
        for line in lines:
            if line.startswith('### '):
                if in_section and section_content:
                    result[in_section] = '\n'.join(section_content).strip()
                in_section = line.replace('### ', '').strip().lower()
                section_content = []
            elif line.startswith('## ') and not line.startswith('###'):
                if in_section and section_content:
                    result[in_section] = '\n'.join(section_content).strip()
                in_section = line.replace('## ', '').strip().lower()
                section_content = []
            elif in_section:
                section_content.append(line)
        
        if in_section and section_content:
            result[in_section] = '\n'.join(section_content).strip()
        
        return result
    
    def get_rule(self, name: str) -> Dict[str, Any]:
        """Obtiene una regla específica por nombre."""
        key = name.lower().replace("-", "_")
        return self.rules.get(key, {})
    
    def get_workflow(self, name: str) -> Dict[str, Any]:
        """Obtiene un workflow específico por nombre."""
        key = name.lower().replace("-", "_")
        return self.workflows.get(key, {})
    
    def validate_rules(self) -> List[str]:
        """Valida que las reglas tengan los campos requeridos."""
        issues = []
        required_fields = ["description"]
        
        for name, rule in self.rules.items():
            for field in required_fields:
                if field not in rule or not rule[field]:
                    issues.append(f"Rule '{name}': falta campo '{field}'")
        
        return issues
    
    def get_active_config(self) -> Dict[str, Any]:
        """Retorna configuración activa para la app basadas en reglas/workflows."""
        config = {
            "enabled_agents": [],
            "rules_summary": []
        }
        
        for wf_name, wf in self.workflows.items():
            if "responsabilidades" in wf or "salida esperada" in wf:
                config["enabled_agents"].append({
                    "name": wf_name,
                    "description": wf.get("description", "")
                })
        
        for rule_name, rule in self.rules.items():
            config["rules_summary"].append({
                "name": rule_name,
                "description": rule.get("description", "")
            })
        
        return config


def load_agents_config(app_root=None) -> Dict[str, Any]:
    """Función de conveniencia para cargar la configuración."""
    loader = AgentLoader(app_root)
    return loader.load_all()


if __name__ == "__main__":
    loader = AgentLoader()
    data = loader.load_all()
    print(f"Rules cargados: {data['summary']['rules_count']}")
    print(f"Workflows cargados: {data['summary']['workflows_count']}")
    print("\nRules:")
    for k, v in data["rules"].items():
        print(f"  - {k}: {v.get('description', 'Sin descripción')}")
    print("\nWorkflows:")
    for k, v in data["workflows"].items():
        print(f"  - {k}: {v.get('description', 'Sin descripción')}")