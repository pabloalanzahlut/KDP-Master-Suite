import os
import re
import hashlib
import threading
import time
import concurrent.futures
from pathlib import Path

class ProcessingService:
    """
    Encapsula la lógica de limpieza y procesamiento de archivos de transcripción.
    Optimizado con procesamiento paralelo usando ThreadPoolExecutor.
    """
    
    def __init__(self):
        self._hash_lock = threading.Lock()
        self._processed_hashes = set()
    
    def get_content_hash(self, text):
        """Calcula el hash MD5 del contenido para deduplicación."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def clean_content(self, text):
        """Limpia el contenido de un archivo de transcripción."""
        text = text.replace('\r\n', '\n')
        
        # Eliminar header WEBVTT completo (incluye líneas de metadata hasta línea en blanco)
        text = re.sub(r'WEBVTT([^\n]*\n)+?\n', '', text, count=1)
        
        # Eliminar timestamps SRT/VTT (con y sin horas, con coma o punto decimal)
        text = re.sub(r'\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[.,]\d{3}[^\n]*\n', '', text)
        text = re.sub(r'\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}[.,]\d{3}[^\n]*\n', '', text)
        
        # Eliminar números de secuencia SRT (solo líneas que son puramente numéricas)
        text = re.sub(r'^\d{1,4}\s*\n', '', text, flags=re.MULTILINE)
        
        # Eliminar tags HTML
        text = re.sub(r'<[^>]+>', '', text)
        
        # Eliminar líneas duplicadas consecutivas
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        unique = []
        if lines:
            unique.append(lines[0])
            for i in range(1, len(lines)):
                if lines[i] != lines[i-1]:
                    unique.append(lines[i])
        return "\n".join(unique)

    def process_files(self, input_dir, output_dir, files_to_process, progress_callback=None, log_callback=None, individual_progress_callback=None, max_workers=None):
        """
        Procesa una lista de archivos en paralelo, los limpia y los guarda en el directorio de salida.
        Retorna el número de archivos procesados exitosamente.
        
        Args:
            input_dir: Directorio de entrada con los archivos fuente
            output_dir: Directorio de salida para archivos procesados
            files_to_process: Lista de nombres de archivos a procesar
            progress_callback: Función Called con progreso global (0-100)
            log_callback: Función Called con mensajes de log (message, level='info')
            individual_progress_callback: Función Called con progreso por archivo (filename, percent, state, eta, speed)
            max_workers: Número máximo de hilos (default: min(32, cpu_count * 4))
        """
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                if log_callback: log_callback(f"Error creando directorio de salida: {e}", level='error')
                return 0
        
        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) * 4)
        
        total = len(files_to_process)
        if total == 0:
            return 0
            
        if log_callback: log_callback(f"=== Iniciando Procesamiento Paralelo ({max_workers} workers) ===")
        
        count = 0
        completed = 0
        
        file_start_times = {}
        file_sizes = {fname: os.path.getsize(os.path.join(input_dir, fname)) for fname in files_to_process if os.path.exists(os.path.join(input_dir, fname))}
        total_bytes = sum(file_sizes.values())
        
        def safe_individual_callback(filename, percent, state, eta=None, speed=None):
            if individual_progress_callback:
                try:
                    individual_progress_callback(filename, percent, state, eta, speed)
                except Exception:
                    pass
        
        def process_single(fname):
            nonlocal count, completed
            file_start_times[fname] = time.time()
            safe_individual_callback(fname, 0, 'processing')
            
            try:
                file_path = Path(input_dir) / fname
                
                raw = None
                for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            raw = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if raw is None:
                    safe_individual_callback(fname, 0, 'error')
                    return ('error', fname, "encoding desconocido")
                
                safe_individual_callback(fname, 50, 'processing')
                
                clean = self.clean_content(raw)
                content_hash = self.get_content_hash(clean)
                
                with self._hash_lock:
                    if content_hash in self._processed_hashes:
                        safe_individual_callback(fname, 100, 'duplicate')
                        return ('duplicate', fname, content_hash)
                    self._processed_hashes.add(content_hash)
                
                out_name = f"CLEAN_{Path(fname).stem}.txt"
                output_path = Path(output_dir) / out_name
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(clean)
                
                elapsed = time.time() - file_start_times[fname]
                file_size = file_sizes.get(fname, 1)
                speed = file_size / elapsed if elapsed > 0 else 0
                
                safe_individual_callback(fname, 100, 'completed', eta=0, speed=speed)
                return ('success', fname, output_path)
                
            except Exception as e:
                safe_individual_callback(fname, 0, 'error')
                return ('error', fname, str(e))
        
        def handle_result(future):
            nonlocal count, completed
            status, fname, data = future.result()
            completed += 1
            
            if status == 'success':
                count += 1
                if log_callback: log_callback(f"Procesado: {fname}")
            elif status == 'duplicate':
                if log_callback: log_callback(f"Saltado (Duplicado): {fname}", level='warning')
            else:
                if log_callback: log_callback(f"Error en {fname}: {data}", level='error')
            
            if progress_callback:
                self._safe_progress(progress_callback, (completed / total) * 100)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single, fname): fname for fname in files_to_process}
            for future in concurrent.futures.as_completed(futures):
                handle_result(future)
        
        if log_callback: log_callback(f"=== Finalizado. {count} archivos únicos procesados. ===")
        return count

    def _safe_progress(self, callback, value):
        """Wrapper seguro para callbacks de progreso desde hilos."""
        try:
            callback(value)
        except Exception:
            pass
