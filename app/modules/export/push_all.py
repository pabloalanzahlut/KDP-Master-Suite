#!/usr/bin/env python3
"""Upload all folders"""

import os, base64, requests, sys

TOKEN = sys.argv[1]
OWNER = "pabloalanzahlut"
REPO = "KDP-Master-Suite"
BASE = r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER"

session = requests.Session()
session.headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

def upload_file(remotepath, localpath):
    if not os.path.exists(localpath):
        print(f"[SKIP] {localpath}")
        return
    content = base64.b64encode(open(localpath, "rb").read()).decode("ascii")
    r = session.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{remotepath}")
    sha = r.json()["sha"] if r.status_code == 200 else None
    payload = {"message": f"Add {remotepath}", "content": content, "branch": "main"}
    if sha: payload["sha"] = sha
    r = session.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{remotepath}", json=payload)
    print(f"[{r.status_code}] {remotepath}")

# .agent rules
agent_rules = [
    ".agent/agent.md",
    ".agent/rules/architecture-rules.md", ".agent/rules/backend-rules.md", ".agent/rules/coding-standards.md",
    ".agent/rules/documentation-rules.md", ".agent/rules/global-rules.md", ".agent/rules/Rule-ai-input-validation.md",
    ".agent/rules/Rule-backup-KB.md", ".agent/rules/Rule-check-transcription.md", ".agent/rules/Rule-GEM-feed.md",
    ".agent/rules/security-rules.md", ".agent/rules/ui-rules-kdp.md", ".agent/rules/ui-rules.md",
]
print("[*] Subiendo .agent/rules...")
for f in agent_rules:
    upload_file(f, os.path.join(BASE, f.replace("/", os.sep)))

# .agent workflows
agent_workflows = [
    ".agent/workflows/agent-algorithm.md", ".agent/workflows/agent-architect.md", ".agent/workflows/agent-backend.md",
    ".agent/workflows/agent-data.md", ".agent/workflows/agent-devops.md", ".agent/workflows/Agent-KB.md",
    ".agent/workflows/agent-performance.md", ".agent/workflows/Agent-Python-Pipeline.md", ".agent/workflows/agent-qa.md",
    ".agent/workflows/agent-scoring.md", ".agent/workflows/agent-security.md", ".agent/workflows/Agent-Transcription.md",
    ".agent/workflows/agent-ui-algorithm.md", ".agent/workflows/agent-uiux.md", ".agent/workflows/backend-audit.md",
    ".agent/workflows/full-audit.md", ".agent/workflows/orchestrator.md", ".agent/workflows/qa-validation.md",
    ".agent/workflows/release-gate.md", ".agent/workflows/ui-audit.md",
]
print("[*] Subiendo .agent/workflows...")
for f in agent_workflows:
    upload_file(f, os.path.join(BASE, f.replace("/", os.sep)))

# .agent-templates
print("[*] Subiendo .agent-templates...")
templates = [
    ".agent-templates/ADAPTACION_RUBROS.md", ".agent-templates/agent.md", ".agent-templates/industry-config.md",
    ".agent-templates/rules/architecture-rules.md", ".agent-templates/rules/backend-rules.md",
    ".agent-templates/rules/coding-standards.md", ".agent-templates/rules/documentation-rules.md",
    ".agent-templates/rules/global-rules.md", ".agent-templates/rules/security-rules.md", ".agent-templates/rules/ui-rules.md",
    ".agent-templates/templates/SOFTWARE_TEMPLATE.md",
    ".agent-templates/workflows/agent-algorithm.md", ".agent-templates/workflows/agent-architect.md",
    ".agent-templates/workflows/agent-backend.md", ".agent-templates/workflows/agent-data.md",
    ".agent-templates/workflows/agent-performance.md", ".agent-templates/workflows/agent-qa.md",
    ".agent-templates/workflows/agent-scoring.md", ".agent-templates/workflows/agent-security.md",
    ".agent-templates/workflows/agent-uiux.md", ".agent-templates/workflows/full-audit.md",
    ".agent-templates/workflows/orchestrator.md", ".agent-templates/workflows/qa-validation.md",
    ".agent-templates/workflows/release-gate.md",
]
for f in templates:
    upload_file(f, os.path.join(BASE, f.replace("/", os.sep)))

# --- NUEVAS CARPETAS ARQUITECTURA ELITE ---
print("[*] Subiendo App Core y Tools...")
elite_files = [
    "app/services/backup_service.py",
    "app/services/monitor_service.py",
    "app/database/db_manager.py",
    "tools/ci_cd/run_tests.py",
    "tools/ci_cd/smoke_test.py",
    "tools/packaging/portable_check.py"
]
for f in elite_files:
    upload_file(f, os.path.join(BASE, f.replace("/", os.sep)))

print("[OK] Completado!")