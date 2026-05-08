import os
import sys
import logging
import argparse
from datetime import datetime
import yt_dlp
from colorama import init, Fore, Style
from tqdm import tqdm

try:
    from app.config import config
except ImportError:
    print("Advertencia: app.config no disponible, usando fallback")
    config = None

init(autoreset=True)

# Configuración
if config:
    DOWNLOAD_DIR = str(config.paths.transcriptions_dir)
    PROCESSED_DIR = str(config.paths.processed_dir)
    DEFAULT_LANGUAGES = config.general.default_languages
else:
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "data/transcriptions")
    PROCESSED_DIR = os.getenv("PROCESSED_DIR", "outputs/transcriptions_processed")
    DEFAULT_LANGUAGES = os.getenv("DEFAULT_LANGUAGES", "es,en").split(',')

LOG_DIR = "logs"

# Configuración de Logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "app.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TranscriptionManager:
    def __init__(self):
        self.ydl_opts = {
            'skip_download': True,  # No descargar video, solo metadatos/subs
            'writeautomaticsub': True,
            'writesub': True,
            'subtitleslangs': DEFAULT_LANGUAGES,
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s [%(id)s].%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

    def validate_url(self, url):
        if "youtube.com" not in url and "youtu.be" not in url:
            return False
        return True

    def process_url(self, url):
        if not self.validate_url(url):
            print(f"{Fore.RED}[!] URL inválida: {url}{Style.RESET_ALL}")
            logger.error(f"URL inválida proporcionada: {url}")
            return

        print(f"\n{Fore.CYAN}[i] Analizando URL: {url}...{Style.RESET_ALL}")
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Primero extraemos info para saber si es playlist o video
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    # Es una playlist
                    entries = list(info['entries'])
                    total_videos = len(entries)
                    print(f"{Fore.GREEN}[+] Playlist detectada con {total_videos} videos.{Style.RESET_ALL}")
                    
                    with tqdm(total=total_videos, desc="Procesando Playlist", unit="video") as pbar:
                        for entry in entries:
                            if entry:
                                self._download_entry(ydl, entry['webpage_url'])
                            pbar.update(1)
                else:
                    # Es un video único
                    print(f"{Fore.GREEN}[+] Video único detectado: {info.get('title', 'Desconocido')}{Style.RESET_ALL}")
                    self._download_entry(ydl, url)
                    
        except Exception as e:
            print(f"{Fore.RED}[X] Error crítico procesando URL: {e}{Style.RESET_ALL}")
            logger.error(f"Error crítico: {e}", exc_info=True)

    def _download_entry(self, ydl, url):
        try:
            ydl.download([url])
            logger.info(f"Descarga exitosa para: {url}")
        except Exception as e:
            logger.error(f"Error descargando {url}: {e}")
            print(f"{Fore.YELLOW}[!] Error en video individual, saltando...{Style.RESET_ALL}")

def print_banner():
    print(f"{Fore.MAGENTA}")
    print("="*50)
    print("   KDP MASTER - TRANSCRIPTION DOWNLOADER")
    print("="*50)
    print(f"{Style.RESET_ALL}")

def interactive_mode():
    manager = TranscriptionManager()
    
    while True:
        print("\nOpciones:")
        print("1. Descargar transcripciones (Video o Playlist)")
        print("2. Ver logs recientes")
        print("3. Salir")
        
        choice = input(f"\n{Fore.YELLOW}Selecciona una opción: {Style.RESET_ALL}")
        
        if choice == '1':
            url = input("Introduce la URL de YouTube: ").strip()
            if url:
                manager.process_url(url)
            else:
                print("URL vacía.")
        
        elif choice == '2':
            log_path = os.path.join(LOG_DIR, "app.log")
            if os.path.exists(log_path):
                print(f"\n{Fore.BLUE}--- Últimas 10 líneas del log ---{Style.RESET_ALL}")
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(line.strip())
            else:
                print("No hay logs todavía.")
                
        elif choice == '3':
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")

def main():
    print_banner()
    
    # Verificar directorios críticos antes de arrancar
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"{Fore.RED}[!] Directorio de descargas no encontrado. Ejecuta setup_project.py primero.{Style.RESET_ALL}")
        return

    parser = argparse.ArgumentParser(description="Descargador de transcripciones para KDP")
    parser.add_argument("--url", help="URL del video o playlist de YouTube")
    parser.add_argument("--batch", help="Archivo de texto con lista de URLs", type=str)
    
    args = parser.parse_args()
    
    manager = TranscriptionManager()

    if args.url:
        manager.process_url(args.url)
    elif args.batch:
        if os.path.exists(args.batch):
            with open(args.batch, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            print(f"Procesando {len(urls)} URLs desde archivo...")
            for url in urls:
                manager.process_url(url)
        else:
            print(f"Archivo batch no encontrado: {args.batch}")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()