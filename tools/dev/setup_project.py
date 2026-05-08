import os
import sys
import subprocess
import pkg_resources

def check_python_version():
    print("[*] Verificando versión de Python...")
    if sys.version_info < (3, 8):
        print("[-] Error: Se requiere Python 3.8 o superior.")
        sys.exit(1)
    print(f"[+] Python {sys.version_info.major}.{sys.version_info.minor} detectado.")

def create_directories():
    print("\n[*] Verificando estructura de directorios...")
    directories = [
        "data/transcriptions",
        "outputs/transcriptions_processed",
        "logs"
    ]
    
    for d in directories:
        path = os.path.join(os.getcwd(), d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"[+] Directorio creado: {d}")
        else:
            print(f"[v] Directorio existente: {d}")

def install_requirements():
    print("\n[*] Verificando dependencias...")
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print("[-] Error: No se encontró requirements.txt")
        sys.exit(1)

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("[+] Dependencias instaladas/verificadas correctamente.")
    except subprocess.CalledProcessError:
        print("[-] Error instalando dependencias.")
        sys.exit(1)

def create_env_file():
    print("\n[*] Verificando archivo .env...")
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("DOWNLOAD_DIR=data/transcriptions\n")
            f.write("PROCESSED_DIR=outputs/transcriptions_processed\n")
            f.write("DEFAULT_LANGUAGES=es,en\n")
            f.write("LOG_LEVEL=INFO\n")
        print("[+] Archivo .env creado con valores por defecto.")
    else:
        print("[v] Archivo .env ya existe.")

def main():
    print("=== KDP MASTER SETUP ===")
    check_python_version()
    create_env_file()
    create_directories()
    install_requirements()
    print("\n=== CONFIGURACIÓN COMPLETADA CON ÉXITO ===")
    print("Ahora puedes ejecutar: python run_transcriptions.py")

if __name__ == "__main__":
    main()