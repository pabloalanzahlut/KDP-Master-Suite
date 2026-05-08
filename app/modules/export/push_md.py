#!/usr/bin/env python3
"""Subir todos los MD"""

import os, base64, requests, sys

TOKEN = sys.argv[1]
OWNER = "pabloalanzahlut"
REPO = "KDP-Master-Suite"
BASE = r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER"

session = requests.Session()
session.headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

files = ["SPEC.md", "PRODUCT_BACKLOG.md", "PRODUCT_ROADMAP.md", "RELEASE_NOTES.md", 
        "MANUAL_USUARIO.md", "OPERATIONS_MANUAL.md", "VALUE_PROPOSITION.md",
        "DOCUMENTACION_TECNICA.md", "ANALISIS_EXPERTOS.md",
        "docs/DOCUMENTACION_TECNICA.md",
        "FUNCIONALIDADES ESPECIALES/PLAN FUNCIONALIDADES.txt"]

def upload(f):
    path = os.path.join(BASE, f)
    if not os.path.exists(path):
        return print(f"[SKIP] {f}")
    
    try:
        with open(path, "rb") as file_data:
            content = base64.b64encode(file_data.read()).decode("ascii")
            
        r = session.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{f}")
        sha = r.json().get("sha") if r.status_code == 200 else None
        
        payload = {"message": f"Add {f}", "content": content, "branch": "main"}
        if sha: payload["sha"] = sha
        r = session.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{f}", json=payload)
        print(f"[{r.status_code}] {f}")
    except Exception as e:
        print(f"[ERROR] No se pudo procesar {f}: {e}")

for f in files:
    upload(f)