#!/usr/bin/env python3
"""GitHub Push - gui_app.py"""

import os, base64, requests, sys

TOKEN = sys.argv[1]
OWNER = "pabloalanzahlut"
REPO = "KDP-Master-Suite"
BASE_DIR = r"D:\ANEXOS KDP Y DIGITALES\KDP_MASTER"

session = requests.Session()
session.headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

f = "gui_app.py"
path = os.path.join(BASE_DIR, f)
print(f"[*] Subiendo {f}...")
content = base64.b64encode(open(path, "rb").read()).decode("ascii")

resp = session.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{f}")
sha = resp.json()["sha"] if resp.status_code == 200 else None
r = session.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{f}", 
    json={"message": f"Update {f}", "content": content, "branch": "main", "sha": sha})
print(f"[{r.status_code}] {f}")