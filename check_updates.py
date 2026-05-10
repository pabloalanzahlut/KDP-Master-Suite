# === INICIO MODULO: GitHub Update Checker ===
# Responsabilidad: Consultar GitHub API y verificar actualizaciones
# Dependencias: requests (ya en requirements.txt)
# Testing: python check_updates.py

import requests
from datetime import datetime

try:
    from app.core.version import get_version, save_update_check, get_update_settings
    CURRENT_VERSION = get_version()
except ImportError:
    CURRENT_VERSION = "2.4.4"

REPO_OWNER = "pabloalanzahlut"
REPO_NAME = "KDP-Master-Suite"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

def check_for_updates(channel: str = "stable"):
    """
    Verifica actualizaciones desde GitHub API.
    Args:
        channel: "stable" o "beta" para elegir tipo de release
    Retorna: (has_update, latest_version, changelog, download_url, release_info)
    """
    settings = get_update_settings()
    print(f"[*] Verificando actualizaciones... (Local: v{CURRENT_VERSION}, Canal: {channel})")
    
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'KDP-Master-Suite-Updater'
        }
        
        if channel == "beta":
            api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
        else:
            api_url = API_URL
        
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if channel == "beta" and isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            latest_version = data.get('tag_name', '').lstrip('v')
            
            current_parts = [int(x) for x in CURRENT_VERSION.split('.')]
            latest_parts = [int(x) for x in latest_version.split('.')]
            
            save_update_check(datetime.now().isoformat(), latest_version)
            
            if latest_parts > current_parts:
                print(f"[!] Actualizacion disponible: v{latest_version}")
                
                assets = data.get('assets', [])
                exe_download_url = None
                for asset in assets:
                    if asset.get('name', '').endswith('.exe'):
                        exe_download_url = asset.get('browser_download_url')
                        break
                
                release_info = {
                    'version': latest_version,
                    'name': data.get('name', ''),
                    'body': data.get('body', ''),
                    'html_url': data.get('html_url', ''),
                    'exe_url': exe_download_url,
                    'published': data.get('published_at', ''),
                    'tag': data.get('tag_name', '')
                }
                
                changelog = data.get('body', 'Sin notas de lanzamiento disponibles')
                download_url = exe_download_url or data.get('html_url', f'https://github.com/{REPO_OWNER}/{REPO_NAME}/releases')
                
                return True, latest_version, changelog, download_url, release_info
            else:
                print("[+] Tienes la version mas reciente.")
                return False, CURRENT_VERSION, None, None, None
                
        elif response.status_code == 404:
            print("[-] Repo no encontrado o sin releases")
            return False, CURRENT_VERSION, "Repo sin releases", None, None
        else:
            print(f"[-] Error API: {response.status_code}")
            return False, CURRENT_VERSION, f"Error: {response.status_code}", None, None
            
    except requests.exceptions.Timeout:
        print("[-] Error: Timeout de conexion")
        return False, CURRENT_VERSION, "Timeout", None, None
    except requests.exceptions.ConnectionError:
        print("[-] Error: Sin conexion a internet")
        return False, CURRENT_VERSION, "Sin conexion", None, None
    except Exception as e:
        print(f"[-] Error inesperado: {e}")
        return False, CURRENT_VERSION, str(e), None, None


def get_release_info(version=None):
    """
    Obtiene informacion de un release especifico o el ultimo.
    """
    if version:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/v{version}"
    else:
        url = API_URL
        
    try:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'version': data.get('tag_name', '').lstrip('v'),
                'name': data.get('name', ''),
                'body': data.get('body', ''),
                'url': data.get('html_url', ''),
                'published': data.get('published_at', '')
            }
    except:
        pass
    return None


if __name__ == "__main__":
    check_for_updates()
# === FIN MODULO ===