# === INICIO MODULO: GitHub Update Checker ===
# Responsabilidad: Consultar GitHub API y verificar actualizaciones
# Dependencias: requests (ya en requirements.txt)
# Testing: python check_updates.py

import requests

CURRENT_VERSION = "2.4.4"
REPO_OWNER = "pabloalanzahlut"
REPO_NAME = "KDP-Master-Suite"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

def check_for_updates():
    """
    Verifica actualizaciones desde GitHub API.
    Retorna: (has_update, latest_version, changelog, download_url)
    """
    print(f"[*] Verificando actualizaciones... (Local: v{CURRENT_VERSION})")
    
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'KDP-Master-Suite-Updater'
        }
        response = requests.get(API_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get('tag_name', '').lstrip('v')
            
            # Comparar versiones semanticas
            current_parts = [int(x) for x in CURRENT_VERSION.split('.')]
            latest_parts = [int(x) for x in latest_version.split('.')]
            
            if latest_parts > current_parts:
                print(f"[!] Actualizacion disponible: v{latest_version}")
                
                changelog = data.get('body', 'Sin notas de lanzamiento disponibles')
                download_url = data.get('html_url', f'https://github.com/{REPO_OWNER}/{REPO_NAME}/releases')
                
                return True, latest_version, changelog, download_url
            else:
                print("[+] Tienes la version mas reciente.")
                return False, CURRENT_VERSION, None, None
                
        elif response.status_code == 404:
            print("[-] Repo no encontrado o sin releases")
            return False, CURRENT_VERSION, "Repo sin releases", None
        else:
            print(f"[-] Error API: {response.status_code}")
            return False, CURRENT_VERSION, f"Error: {response.status_code}", None
            
    except requests.exceptions.Timeout:
        print("[-] Error: Timeout de conexion")
        return False, CURRENT_VERSION, "Timeout", None
    except requests.exceptions.ConnectionError:
        print("[-] Error: Sin conexion a internet")
        return False, CURRENT_VERSION, "Sin conexion", None
    except Exception as e:
        print(f"[-] Error inesperado: {e}")
        return False, CURRENT_VERSION, str(e), None


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