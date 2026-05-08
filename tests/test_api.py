#!/usr/bin/env python3
"""Debug GitHub API"""

import requests

TOKEN = "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"
OWNER = "pabloalanzahlut"
REPO = "KDP-Master-Suite"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# Test 1: GET contents
print("=== TEST 1: GET contents ===")
r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/", headers=HEADERS)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"Files: {[f['name'] for f in r.json()]}")

# Test 2: PUT (create new file)
print("\n=== TEST 2: PUT new file ===")
import base64
content = base64.b64encode(b"test").decode("ascii")
payload = {
    "message": "test commit",
    "content": content,
    "branch": "main"
}
r = requests.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/test.txt", headers=HEADERS, json=payload)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")