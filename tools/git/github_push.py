#!/usr/bin/env python3
"""GitHub Push"""

import os, base64, requests, sys

# Token como argumento o variable
TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_TOKEN", "")
OWNER = "pabloalanzahlut"
REPO = "KDP-Master-Suite"
BASE_DIR = r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER"

if not TOKEN:
    print("[!] Error: Proporciona token como argumento")
    print("     python github_push.py ghp_TOKEN")
    sys.exit(1)

session = requests.Session()
session.headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "KDP-Push/1.0"
}

def get_sha(path):
    r = session.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}")
    return r.json()["sha"] if r.status_code == 200 else None

def upload(f):
    if not os.path.exists(os.path.join(BASE_DIR, f)):
        return print(f"[SKIP] {f}")
    content = base64.b64encode(open(os.path.join(BASE_DIR, f), "rb").read()).decode("ascii")
    sha = get_sha(f)
    payload = {"message": f"Update {f}", "content": content, "branch": "main"}
    if sha: payload["sha"] = sha
    r = session.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{f}", json=payload)
    print(f"[{r.status_code}] {f}")

if __name__ == "__main__":
    # Lista extendida para incluir Arquitectura Elite v2.9.0
    files_to_sync = [
        "main.py", 
        "gui_app.py",
        "requirements.txt", 
        "README.md", 
        "app/services/backup_service.py",
        "app/services/monitor_service.py",
        "app/database/db_manager.py",
        "tools/ci_cd/run_tests.py",
        "tools/ci_cd/smoke_test.py"
    ]
    for f in files_to_sync:
        upload(f)