import os
import sys
import zipfile
import shutil
import urllib.request
from pathlib import Path

def install_ffmpeg():
    """
    Descarga e instala FFmpeg localmente en la carpeta 'bin' del proyecto.
    """
    base_dir = Path(os.getcwd())
    if base_dir.name == "dist":
        base_dir = base_dir.parent
    
    bin_dir = base_dir / "bin"
    if not bin_dir.exists():
        bin_dir.mkdir()

    ffmpeg_exe = bin_dir / "ffmpeg.exe"
    ffprobe_exe = bin_dir / "ffprobe.exe"

    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        print("✅ FFmpeg ya está instalado en la carpeta 'bin'.")
        return True, str(bin_dir)

    print("⬇️ Descargando FFmpeg (esto puede tardar unos minutos)...")
    
    # URL de una build estática de FFmpeg para Windows (gyan.dev es una fuente confiable)
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = bin_dir / "ffmpeg.zip"

    try:
        # Descargar
        with urllib.request.urlopen(url) as response, open(zip_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        
        print("📦 Descomprimiendo...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Encontrar la carpeta interna que contiene los binarios
            bin_folder_prefix = [n for n in zip_ref.namelist() if "bin/ffmpeg.exe" in n][0].split("bin/")[0]
            
            # Extraer solo los exes necesarios
            for file_name in ["ffmpeg.exe", "ffprobe.exe"]:
                source = f"{bin_folder_prefix}bin/{file_name}"
                target = bin_dir / file_name
                
                with zip_ref.open(source) as source_file, open(target, 'wb') as target_file:
                    shutil.copyfileobj(source_file, target_file)

        # Limpiar
        os.remove(zip_path)
        print(f"✅ FFmpeg instalado correctamente en: {bin_dir}")
        
        # Añadir al PATH temporalmente para esta sesión
        os.environ["PATH"] += os.pathsep + str(bin_dir)
        return True, str(bin_dir)

    except Exception as e:
        print(f"❌ Error instalando FFmpeg: {e}")
        if zip_path.exists():
            os.remove(zip_path)
        return False, str(e)

if __name__ == "__main__":
    install_ffmpeg()