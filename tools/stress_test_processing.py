import os
import time
import random
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.services.processing_service import ProcessingService

def run_stress_test(num_files=200):
    """Valida el motor de procesamiento con ráfagas de archivos y duplicados."""
    print(f"🚀 STRESS TEST: Procesamiento de {num_files} archivos...")
    
    in_dir = Path("data/stress_in")
    out_dir = Path("outputs/stress_out")
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    service = ProcessingService()
    filenames = []
    
    # 1. Crear ráfaga de archivos
    for i in range(num_files):
        fname = f"test_file_{i}.vtt"
        f_path = in_dir / fname
        # Alternar entre contenido único y duplicado para estresar el hash-lock
        content = f"WEBVTT\n\n00:01.000 --> 00:04.000\nData unique {i if i % 2 == 0 else 'DUPE'}"
        f_path.write_text(content)
        filenames.append(fname)
        
    # 2. Ejecutar procesamiento paralelo extremo
    print(f"  ⚡ Ejecutando procesamiento paralelo (8 workers)...")
    start = time.time()
    
    res = service.process_files(
        input_dir=str(in_dir),
        output_dir=str(out_dir),
        files_to_process=filenames,
        max_workers=8
    )
    
    duration = time.time() - start
    print(f"  ✅ Procesados: {res} archivos únicos en {duration:.2f}s")
    
    # 3. Test de colisión de hilos (Procesar exactamente lo mismo)
    print("  🧪 Verificando persistencia de Hash-Lock...")
    res_dupe = service.process_files(
        input_dir=str(in_dir),
        output_dir=str(out_dir),
        files_to_process=filenames
    )
    
    if res_dupe == 0:
        print("  ✅ Deduplicación Enterprise PASS (0 archivos duplicados permitidos)")
    else:
        print(f"  ❌ FAIL: Se permitieron {res_dupe} duplicados.")

    # Limpieza
    shutil.rmtree(in_dir)
    shutil.rmtree(out_dir)
    print("\n🏁 Stress Test de Procesamiento Finalizado.")

if __name__ == "__main__":
    run_stress_test()