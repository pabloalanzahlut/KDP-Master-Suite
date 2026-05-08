import os
import sys
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from app.config import config
except ImportError:
    config = None

# Intentar importar librerías de IA
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    # ==================== MÓDULO 3: Google GenerativeAI - Nueva API ====================
    # Detectar versión de la librería para compatibilidad
    try:
        # Nueva API (v0.5+): usando Client
        _GEMINI_NEW_API = True
    except:
        _GEMINI_NEW_API = False
    # ==================== FIN MÓDULO 3 ====================
except ImportError:
    GEMINI_AVAILABLE = False
    _GEMINI_NEW_API = False

class KnowledgeIntegrator:
    """
    Módulo para integración de conocimiento y análisis avanzado de textos.
    Protocolo SYNTHLEARN v3.4.2 adaptado.
    """
    def __init__(self, custom_blacklist=None, db_manager=None):
        # This will be set by the GUI
        self.ai_provider = "none"
        self.api_key = None
        self.system_prompt = "Clasifica el siguiente texto en una de estas categorías: 'Legalidad y Compliance', 'Matriz de Roles y Fases SOE', 'Fórmulas y Métricas', 'Investigación de Nichos', 'Amazon Ads y Marketing', 'Conocimiento General KDP'. Responde SOLO con el nombre de la categoría."
        self.version = "3.4.2"
        self.custom_blacklist = custom_blacklist if custom_blacklist else []
        self.db_manager = db_manager
        # Base del proyecto
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).parent
            
        self.kb_dir = self.base_dir / "knowledge" / "manuals"
        
        # --- LÓGICA DE RECUPERACIÓN Y MIGRACIÓN ---
        # Si existe la carpeta antigua 'knowledge_base', movemos los archivos a la nueva ubicación
        old_kb_dir = self.base_dir / "knowledge_base"
        if old_kb_dir.exists():
            if not self.kb_dir.exists():
                self.kb_dir.mkdir(parents=True)
            
            print(f"Detectada carpeta antigua: {old_kb_dir}. Migrando archivos...")
            for item in old_kb_dir.glob("*"):
                if item.is_file():
                    target = self.kb_dir / item.name
                    # Si ya existe en destino, lo renombramos para no perder nada
                    if target.exists():
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        target = target.with_name(f"{target.stem}_CONFLICT_{ts}{target.suffix}")
                    
                    try:
                        shutil.move(str(item), str(target))
                        print(f"Recuperado: {item.name} -> {target.name}")
                    except Exception as e:
                        print(f"Error moviendo {item.name}: {e}")
            
            # Renombrar carpeta vieja para evitar confusión futura
            try:
                old_kb_dir.rename(self.base_dir / "knowledge_base_OLD_MIGRATED")
            except:
                pass
        # -------------------------------------------

        # Crear directorio de conocimiento si no existe
        if not self.kb_dir.exists():
            self.kb_dir.mkdir(parents=True)

        # Definir Archivos Maestros Locales
        self.files = {
            "LEGALIDAD": self.kb_dir / "MANUAL_LEGALIDAD.md",
            "MATRIZ": self.kb_dir / "MATRIZ_MAESTRA.md",
            "FORMULAS": self.kb_dir / "MANUAL de FÓRMULAS.MD",
            "MASTER": self.kb_dir / "MASTER_KB.txt"
        }
        self.checksum_file = self.kb_dir / "checksums.json"
        
        # Locks para acceso concurrente a archivos (Garantiza atomicidad Enterprise)
        self.file_locks = {key: threading.Lock() for key in self.files.keys()}
        self.checksum_lock = threading.Lock()
        
        # Configuración de IA
        if config:
            self.ai_provider = config.general.ai_provider
            self.api_key = config.general.ai_api_key
        else:
            self.ai_provider = os.getenv("AI_PROVIDER", "ollama").lower()
            self.api_key = os.getenv("AI_API_KEY")

    def _classify_with_ai(self, text):
        """Clasifica el texto usando una API de IA (OpenAI o Gemini)."""
        if not text or not text.strip():
            return None
        
        if self.ai_provider == "openai" and OPENAI_AVAILABLE and self.api_key:
            try:
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text[:1000]}
                    ]
                )
                category = response.choices[0].message.content.strip()
                return self._map_ai_category(category)
            except Exception as e:
                print(f"Error OpenAI: {e}")
                return None
        
        elif self.ai_provider == "gemini" and GEMINI_AVAILABLE and self.api_key:
            # ==================== MÓDULO 3: Google GenerativeAI - Compatibilidad API ====================
            try:
                # Intentar nueva API (v0.5+) primero
                try:
                    client = genai.Client(api_key=self.api_key)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[f"{self.system_prompt}\n\nTexto: {text[:1000]}"]
                    )
                    return self._map_ai_category(response.text.strip())
                except (AttributeError, TypeError):
                    # Fallback a API antigua (v0.3.x)
                    genai.configure(api_key=self.api_key)
                    model = genai.GenerativeModel('gemini-pro')
                    response = model.generate_content(f"{self.system_prompt}\n\nTexto: {text[:1000]}")
                    return self._map_ai_category(response.text.strip())
            except Exception as e:
                error_str = str(e).lower()
                if "image" in error_str and ("does not support" in error_str or "vision" in error_str):
                    print(f"⚠️ Modelo no soporta imágenes, usando clasificación local")
                    return self._classify_block(text[:500])
                print(f"Error Gemini: {e}")
                return None
            # ==================== FIN MÓDULO 3 ====================
                
        return None

    def _validate_ai_input(self, text):
        """Valida que el input sea texto válido para modelos de texto."""
        if not text:
            return False, "Input vacío"
        if isinstance(text, (bytes, bytearray)):
            return False, "Input binario no soportado - solo texto"
        if hasattr(text, 'read'):
            return False, "Input de archivo no soportado"
        if isinstance(text, str):
            text_lower = text[:100] if len(text) > 100 else text
            if any(text.startswith(prefix) for prefix in ['\x89PNG', '\xff\xd8', 'GIF8', 'RIFF', 'PK\x03\x04', 'BMP']):
                return False, "Datos de imagen detectados (PNG/JPG/GIF/BMP)"
            if any(binary_marker in text_lower for binary_marker in ['image/png', 'image/jpeg', 'data:image', '\\x89\\x50']):
                return False, "Referencia a imagen detectada"
        return True, None

    def _map_ai_category(self, category):
        """Mapea la respuesta de la IA a las claves internas."""
        cat_map = {
            "Legalidad y Compliance": ("Legalidad y Compliance", "LEGALIDAD"),
            "Matriz de Roles y Fases SOE": ("Matriz de Roles y Fases SOE", "MATRIZ"),
            "Fórmulas y Métricas": ("Fórmulas y Métricas", "FORMULAS"),
            "Investigación de Nichos": ("Investigación de Nichos", "MASTER"),
            "Amazon Ads y Marketing": ("Amazon Ads y Marketing", "MASTER"),
            "Conocimiento General KDP": ("Conocimiento General KDP", "MASTER")
        }
        return cat_map.get(category, ("Conocimiento General KDP", "MASTER"))

    def update_blacklist(self, new_list):
        self.custom_blacklist = new_list

    def analyze_text(self, text, source_filename="Desconocido"):
        """
        Analiza el texto, lo clasifica y lo integra en la base de conocimiento usando multi-threading.
        """
        if not text:
            return {"error": "Texto vacío"}
        
        # Validar que el input es texto, no binario/imagen
        if not self._validate_ai_input(text)[0]:
            return {"error": "Input no válido: solo se acepta texto, no imágenes o binarios"}

        # 1. Extraer bloques (simulado por párrafos dobles)
        blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
        if not blocks:
            blocks = [text]

        results = {"integrated": [], "duplicates": []}
        
        # 2. Procesamiento paralelo de bloques (Optimización Enterprise)
        # Esto es especialmente útil si se usa IA (I/O bound)
        def process_single_block(block):
            if self._is_banal(block):
                return None

            ai_result = self._classify_with_ai(block)
            if ai_result:
                category, key = ai_result
            else:
                category, key = self._classify_block(block)
            
            target_file = self.files.get(key, self.files["MASTER"])
            
            # El lock se maneja dentro de _append_to_file para máxima granularidad
            success = self._append_to_file(target_file, block, source_filename, category, lock_key=key)
            return (category, target_file.name, success)

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_block = {executor.submit(process_single_block, b): b for b in blocks}
            for future in as_completed(future_to_block):
                res = future.result()
                if res:
                    category, filename, success = res
                    if success:
                        results["integrated"].append(f"[{category}] -> {filename}")
                    else:
                        results["duplicates"].append(f"[{category}] Duplicado omitido")

        return results

    def _is_banal(self, block):
        """Filtra contenido irrelevante, corto o repetitivo común."""
        b = block.strip().lower()
        if len(b) < 50: return True # Descarta frases muy cortas sin sustancia
        defaults = ["suscríbete", "dale like", "activa la campanita", "video anterior", "mis redes sociales", "bienvenidos a un nuevo video"]
        check_list = defaults + [x.lower() for x in self.custom_blacklist]
        if any(x in b for x in check_list):
            return True
        return False

    def _classify_block(self, block):
        """Clasifica el contenido según palabras clave del protocolo."""
        b_lower = block.lower()
        
        # 1. Compliance y Legalidad (Categoría 15)
        if any(w in b_lower for w in ["términos", "legal", "copyright", "licencia", "marca", "tos", "suspensión", "bloqueo", "infracción", "política"]):
            return "Legalidad y Compliance", "LEGALIDAD"
            
        # 2. Matriz de Roles y Fases SOE
        if any(w in b_lower for w in ["taxonomía", "arquitectura de información", "fase soe", "kpi", "checklist", "matriz", "roles dependientes", "gates de decisión"]):
            return "Matriz de Roles y Fases SOE", "MATRIZ"

        # 3. Fórmulas y Métricas (Categoría 13)
        if any(w in b_lower for w in ["fórmula", "calculo", "roi", "precio", "acos", "tacos", "bsr", "kpi", "margen", "royalty", "beneficio", "ganancia", "taxonomía"]):
            return "Fórmulas y Métricas", "FORMULAS"
            
        # 4. Investigación de Nichos (Categoría 1)
        if any(w in b_lower for w in ["nicho", "investigación", "demanda", "competencia", "validación", "oportunidad", "tendencia"]):
            return "Investigación de Nichos", "MASTER"

        # 5. Amazon Ads (Categoría 11)
        if any(w in b_lower for w in ["ads", "publicidad", "campaña", "pujas", "targeting", "ppc", "impresiones", "clics"]):
            return "Amazon Ads y Marketing", "MASTER"

        return "Conocimiento General KDP", "MASTER"

    def _calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except FileNotFoundError:
            return None

    def update_file_checksum(self, file_path):
        current_hash = self._calculate_md5(file_path)
        if current_hash:
            with self.checksum_lock:
                checksums = {}
                if self.checksum_file.exists():
                    try:
                        with open(self.checksum_file, 'r') as f:
                            checksums = json.load(f)
                    except:
                        pass
                
                checksums[file_path.name] = current_hash
                with open(self.checksum_file, 'w') as f:
                    json.dump(checksums, f, indent=4)

    def verify_integrity(self):
        issues = []
        if not self.checksum_file.exists():
            return issues
        try:
            with open(self.checksum_file, 'r') as f:
                checksums = json.load(f)
        except:
            return ["Error leyendo archivo de checksums."]
        for filename, saved_hash in checksums.items():
            file_path = self.kb_dir / filename
            current_hash = self._calculate_md5(file_path)
            if not file_path.exists():
                issues.append(f"Archivo faltante: {filename}")
            elif current_hash != saved_hash:
                issues.append(f"Integridad comprometida: {filename} (Hash no coincide)")
        return issues

    def recalculate_all_checksums(self):
        """Recalcula y sobrescribe todos los checksums para los archivos existentes."""
        checksums = {}
        for file_path in self.kb_dir.glob("*"):
            if file_path.is_file() and file_path.name != self.checksum_file.name:
                current_hash = self._calculate_md5(file_path)
                if current_hash:
                    checksums[file_path.name] = current_hash
        
        with open(self.checksum_file, 'w') as f:
            json.dump(checksums, f, indent=4)
        return len(checksums)

    def _append_to_file(self, file_path, content, source, category, lock_key=None):
        """Escribe en el archivo maestro si no es duplicado. Con soporte de Locking.
        También escribe en la base de datos si db_manager está disponible (dual-write)."""
        lock = self.file_locks.get(lock_key, threading.Lock()) # Fallback a lock temporal si no hay key
        
        with lock:
            if not file_path.exists():
                file_path.write_text(f"# {category.upper()} - BASE DE CONOCIMIENTO (KDP MASTER)\n\n", encoding="utf-8")

            current_content = file_path.read_text(encoding="utf-8")
            
            # Detección simple de duplicados
            if content.strip() in current_content:
                return False

            # Formato de entrada
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n\n## 🟢 MÓDULO: {category}\n- **FUENTE:** {source}\n- **FECHA:** {timestamp}\n\n{content.strip()}\n\n---"
            
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(entry)
            self.update_file_checksum(file_path)
            
            # Dual-write: también escribir en la base de datos
            if self.db_manager:
                try:
                    self.db_manager.insert_entry(category, source, content.strip(), timestamp)
                except Exception as e:
                    print(f"⚠️ Error escribiendo en DB de conocimiento: {e}")
            
            return True
