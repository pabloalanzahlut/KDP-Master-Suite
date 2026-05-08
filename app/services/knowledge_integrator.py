import os
import sys
import shutil
import hashlib
import json
import time
import logging
import queue
import threading
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Tuple, Any

# Configuración local
try:
    from app.config import config
except ImportError:
    config = None

logger = logging.getLogger(__name__)

# ==================== IMPORTACIÓN DE LIBRERÍAS DE IA ====================

# OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google GenAI (NUEVA SDK - Reemplaza a google-generativeai)
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ google-genai no instalado. Ejecuta: pip install google-genai")

# Requests (para Ollama)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class KnowledgeIntegrator:
    """
    Módulo para integración de conocimiento y análisis avanzado de textos.
    Protocolo SYNTHLEARN v3.5.0 adaptado.
    Soporta: Ollama (Local), OpenAI, y Google Gemini (vía nueva SDK).
    """

    # 18 Categorías KDP (invariables)
    CATEGORIES = [
        "Investigación de Nichos", "Diseño de Portada", "Publicación KDP", 
        "Amazon Ads (PPC)", "Legalidad y Compliance", "Pricing y Monetización", 
        "Reviews y Gestión de Reseñas", "SEO Amazon (A9)", "Optimización de Listados", 
        "Marketing y Tráfico Externo", "Low-Content", "Medium-Content", 
        "High-Content", "Análisis de Datos", "Herramientas y Software", 
        "Scaling y Automatización", "Internacionalización", "Brand Building"
    ]

    # 37+1 Roles GEM
    ROLES_GEM = [
        (1, "Analista de Mercado Educativo"), (2, "Copywriter de Conversión"),
        (3, "Diseñador Gráfico UI/UX"), (4, "Especialista en Accesibilidad e Inclusión"),
        (5, "Product Manager de Plataforma"), (6, "Especialista SEO Amazon (A9)"),
        (7, "Especialista PPC Amazon"), (8, "User Researcher"),
        (9, "Community Manager"), (10, "Gestor de Calidad y Satisfacción"),
        (11, "Consultor de PI para Contenido Educativo"), (12, "Productor de Audiolibros"),
        (13, "Traductor Profesional"), (14, "Especialista en Print-on-Demand"),
        (15, "Video Marketing Specialist"), (16, "Especialista Cross-Platform"),
        (17, "Affiliate Marketing Manager"), (18, "Analista Financiero"),
        (19, "Consultor en Propiedad Intelectual"), (20, "Especialista en Compliance KDP"),
        (21, "Especialista en IA para Automatización"), (22, "Especialista en Gamificación"),
        (23, "Desarrollador de Apps/Complementos"), (24, "PR Manager"),
        (25, "Analista de Regalías y Fiscalidad"), (26, "Gestor de Credenciales y Seguridad"),
        (27, "IA para Automatización Editorial"), (28, "Diseñador Instruccional"),
        (29, "Ilustrador Conceptual"), (30, "Editor Técnico de Interiores"),
        (31, "Gestor de Credenciales"), (32, "Editor de Estilo"),
        (33, "Coordinador de Red"), (34, "Portfolio Manager"),
        (35, "Scaling Specialist"), (36, "Innovación Scout"),
        (37, "Taxonomía y Arquitectura de Información"), (38, "Branding")
    ]

    def __init__(self, custom_blacklist=None, db_manager=None):
        self.ai_provider = "none"
        self.api_key = None
        self.version = "3.5.0"
        self.custom_blacklist = custom_blacklist if custom_blacklist else []
        self.db_manager = db_manager
        
        # Base del proyecto
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).parent.parent.parent
            
        self.kb_dir = self.base_dir / "knowledge" / "manuals"
        
        # Configuración Ollama
        if config:
            self.ollama_model = config.ollama.model
            self.ollama_base_url = config.ollama.base_url
            self.ollama_timeout = config.ollama.timeout
            self.max_tokens_input = config.ollama.max_tokens_input
            self.batch_threshold = config.ollama.batch_threshold
            self.ai_provider = config.general.ai_provider
            self.api_key = config.general.ai_api_key
        else:
            self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))
            self.max_tokens_input = int(os.getenv("MAX_TOKENS_INPUT", "4000"))
            self.batch_threshold = int(os.getenv("BATCH_THRESHOLD", "10"))
            self.ai_provider = os.getenv("AI_PROVIDER", "ollama").lower()
            self.api_key = os.getenv("AI_API_KEY")
        
        self.ollama_available = self._check_ollama()
        
        # Cola de procesamiento batch
        self.batch_queue = queue.Queue()
        self.batch_in_progress = False
        self.progress_callback = None
        
        # Thread para procesamiento batch
        self.batch_thread = threading.Thread(target=self._batch_worker, daemon=True)
        self.batch_thread.start()
         
        # Mapeo de categorías para archivos
        self.category_to_file = {
            "Investigación de Nichos": "MASTER_NICHOS.md",
            "Diseño de Portada": "MASTER_PORTADA.md",
            "Publicación KDP": "MASTER_PUBLICACION.md",
            "Amazon Ads (PPC)": "MASTER_ADS.md",
            "Legalidad y Compliance": "MANUAL_LEGALIDAD.md",
            "Pricing y Monetización": "MASTER_PRICING.md",
            "Reviews y Gestión de Reseñas": "MASTER_REVIEWS.md",
            "SEO Amazon (A9)": "MASTER_SEO.md",
            "Optimización de Listados": "MASTER_LISTINGS.md",
            "Marketing y Tráfico Externo": "MASTER_MARKETING.md",
            "Low-Content": "MASTER_LOWCONTENT.md",
            "Medium-Content": "MASTER_MEDIUMCONTENT.md",
            "High-Content": "MASTER_HIGHCONTENT.md",
            "Análisis de Datos": "MASTER_ANALISIS.md",
            "Herramientas y Software": "MASTER_HERRAMIENTAS.md",
            "Scaling y Automatización": "MASTER_SCALING.md",
            "Internacionalización": "MASTER_INTERNACIONAL.md",
            "Brand Building": "MASTER_BRANDING.md"
        }
        
        # Archivos de salida
        self.files = {
            "LEGALIDAD": self.kb_dir / "MANUAL_LEGALIDAD.md",
            "MATRIZ": self.kb_dir / "MATRIZ_MAESTRA.md",
            "FORMULAS": self.kb_dir / "MANUAL de FÓRMULAS.MD",
            "MASTER": self.kb_dir / "MASTER_KB_TRANSCRIPCIONES.txt"
        }
        self.checksum_file = self.kb_dir / "checksums.json"
        
        # Locks para acceso concurrente
        self.file_locks = {key: threading.Lock() for key in self.files.keys()}
        self.checksum_lock = threading.Lock()

        logger.info(f"KnowledgeIntegrator v{self.version} inicializado")
        logger.info(f"Ollama disponible: {self.ollama_available} (modelo: {self.ollama_model})")
        if GEMINI_AVAILABLE:
            logger.info("✅ Google GenAI SDK disponible (Nueva versión)")
        else:
            logger.warning("⚠️ Google GenAI SDK no disponible")

    def _check_ollama(self) -> bool:
        """Verifica si Ollama está disponible."""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests no disponible - Ollama deshabilitado")
            return False
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama no disponible: {e}")
            return False

    def get_relevant_context(self, text: str, top_k: int = 5) -> str:
        """Extrae contexto relevante basado en keywords del texto."""
        text_lower = text.lower()
        
        category_keywords = {
            "Investigación de Nichos": ["nicho", "demanda", "bsr", "competencia", "validación", "mercado", "best seller"],
            "Diseño de Portada": ["cover", "portada", "thumbnail", "canva", "diseño", "conversión"],
            "Amazon Ads (PPC)": ["acos", "sponsored", "ppc", "pujas", "campaña", "keywords", "presupuesto"],
            "Legalidad y Compliance": ["tos", "w-8ben", "2fa", "copyright", "drám", "términos", "fiscalidad"],
            "Pricing y Monetización": ["precio", "royalty", "margen", "costo", "bundle", "descuento"],
            "Reviews y Gestión de Reseñas": ["reseñas", "reviews", "estrellas", "feedback", "auditoría"],
            "SEO Amazon (A9)": ["busqueda", "posicionamiento", "keywords", "backend", "categoría"],
            "Marketing y Tráfico Externo": ["tráfico", "redes sociales", "facebook", "instagram", "tiktok", "pinterest"],
            "Low-Content": ["coloring", "workbook", "journal", "planner", "notebook", "activity"],
            "Herramientas y Software": ["canva", "chatgpt", "publisher rocket", "kindle create"]
        }
        
        relevant = []
        for cat, keywords in category_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                relevant.append((cat, matches))
        
        relevant.sort(key=lambda x: x[1], reverse=True)
        
        if not relevant:
            return "General KDP"
        
        return ", ".join([r[0] for r in relevant[:top_k]])

    def get_categories_list(self) -> str:
        return ", ".join(self.CATEGORIES)

    def get_roles_gem_list(self) -> str:
        return ", ".join([f"#{num} {name}" for num, name in self.ROLES_GEM])

    def set_progress_callback(self, callback):
        self.progress_callback = callback

    # ==================== LÓGICA DE RECUPERACIÓN (MIGRACIÓN) ====================

    def _migrate_old_knowledge_base(self):
        old_kb_dir = self.base_dir / "knowledge_base"
        if old_kb_dir.exists():
            if not self.kb_dir.exists():
                self.kb_dir.mkdir(parents=True)
            
            logger.info(f"Detectada carpeta antigua: {old_kb_dir}. Migrando archivos...")
            for item in old_kb_dir.glob("*"):
                if item.is_file():
                    target = self.kb_dir / item.name
                    if target.exists():
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        target = target.with_name(f"{target.stem}_CONFLICT_{ts}{target.suffix}")
                    
                    try:
                        shutil.move(str(item), str(target))
                        logger.info(f"Recuperado: {item.name} -> {target.name}")
                    except Exception as e:
                        logger.error(f"Error moviendo {item.name}: {e}")
            
            try:
                old_kb_dir.rename(self.base_dir / "knowledge_base_OLD_MIGRATED")
            except:
                pass

    def _ensure_kb_directory(self):
        if not self.kb_dir.exists():
            self.kb_dir.mkdir(parents=True)

    # ==================== CLASIFICACIÓN IA ====================

    def _classify_with_ai(self, text):
        """Clasifica el texto usando una API de IA (OpenAI o Google Gemini)."""
        if not text or not text.strip():
            return None
        
        is_valid, error_msg = self._validate_ai_input(text)
        if not is_valid:
            logger.warning(f"⚠️ Input no válido para IA: {error_msg}, usando clasificación local")
            return self._classify_block(text[:500])
        
        # --- OPENAI ---
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
                error_str = str(e).lower()
                if "image" in error_str or "vision" in error_str or "does not support" in error_str:
                    logger.warning("⚠️ Modelo no soporta imágenes, usando clasificación local")
                    return self._classify_block(text[:500])
                logger.error(f"Error OpenAI: {e}")
                return None
        
        # --- GOOGLE GEMINI (NUEVA SDK) ---
        elif self.ai_provider == "gemini" and GEMINI_AVAILABLE and self.api_key:
            try:
                # Inicializar cliente con la nueva SDK
                client = genai.Client(api_key=self.api_key)
                
                # Preparar contenido (texto plano)
                prompt_content = f"{self.system_prompt}\n\nTexto a clasificar:\n{text[:2000]}"
                
                # Generar respuesta
                response = client.models.generate_content(
                    model='gemini-1.5-flash', # Modelo rápido y eficiente
                    contents=prompt_content
                )
                
                if response.text:
                    return self._map_ai_category(response.text.strip())
                return None
                
            except Exception as e:
                error_str = str(e).lower()
                # Manejo de errores específico
                if "image" in error_str or "vision" in error_str or "does not support" in error_str or "cannot read" in error_str:
                    logger.warning("⚠️ Modelo no soporta imágenes/binarios, usando clasificación local")
                    return self._classify_block(text[:500])
                logger.error(f"Error Google GenAI (SDK Nueva): {e}")
                return None
            
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
            # Headers de formatos de imagen comunes
            if any(text.startswith(prefix) for prefix in ['\x89PNG', '\xff\xd8', 'GIF8', 'RIFF', 'PK\x03\x04', 'BMP']):
                return False, "Datos de imagen detectados (PNG/JPG/GIF/BMP)"
            # Detectar strings que parecen contener datos binarios encoded
            if any(binary_marker in text_lower for binary_marker in ['image/png', 'image/jpeg', 'data:image', '\\x89\\x50', 'cannot read', 'image.png']):
                return False, "Referencia a imagen detectada o error de lectura"
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
        # Búsqueda flexible (case-insensitive y parcial)
        category_lower = category.lower()
        for key, value in cat_map.items():
            if key.lower() in category_lower:
                return value
        return ("Conocimiento General KDP", "MASTER")

    # ==================== OLLAMA INTEGRATION ====================

    def _classify_with_ollama(self, text: str) -> Optional[Dict]:
        """Clasifica texto usando Ollama local con retry."""
        if not self.ollama_available:
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                relevant_context = self.get_relevant_context(text, top_k=5)
                
                prompt = f"""Clasifica el siguiente texto sobre Amazon KDP.
Responde SOLO con JSON válido, sin texto adicional.
CATEGORÍAS: {', '.join(self.CATEGORIES)}
Si NO es sobre KDP: {{"scope": "FUERA_DE_SCOPE", "razon": "Contenido no relacionado"}}
Si es sobre KDP: {{"scope": "KDP", "categoria_principal": "...", "score_principal": 0.0-1.0, "tags": ["..."], "resumen": "...", "valor_score": 0-10}}
TEXTO: {text[:self.max_tokens_input]}"""
                
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=self.ollama_timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    raw_response = result.get("response", "")
                    
                    parsed = self.clean_json_response(raw_response)
                    if parsed:
                        if self.validate_classification(parsed):
                            parsed["raw_ai_response"] = raw_response
                            parsed["processed_by"] = self.ollama_model
                            return parsed
                        else:
                            logger.warning(f"Schema validation falló, usando fallback: {parsed}")
                
                logger.warning(f"Ollama respuesta inválida (intento {attempt + 1})")
                
            except requests.exceptions.Timeout:
                logger.warning(f"Ollama timeout (intento {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Error Ollama: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        logger.warning("Ollama falló después de todos los reintentos → activando fallback")
        return None

    def clean_json_response(self, response: str) -> Optional[Dict]:
        if not response:
            return None
        
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = response[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {e}, intentando reparar...")
                json_str = json_str.replace("'", '"').replace("\n", "  ")
                try:
                    return json.loads(json_str)
                except:
                    pass
        
        return None

    def validate_classification(self, data: Dict) -> bool:
        required_fields = ['scope', 'categoria_principal']
        
        if not all(k in data for k in required_fields):
            logger.warning(f"Campos faltantes: {required_fields}")
            return False
        
        if data.get('scope') not in ['KDP', 'FUERA_DE_SCOPE']:
            logger.warning(f"Scope inválido: {data.get('scope')}")
            return False
        
        if data.get('scope') == 'KDP':
            valid_cats = set(self.CATEGORIES)
            if data.get('categoria_principal') not in valid_cats:
                logger.warning(f"Categoría inválida: {data.get('categoria_principal')}")
                data['categoria_principal'] = "Investigación de Nichos"
        
        score = data.get('score_principal', 0)
        if not (0 <= score <= 1):
            data['score_principal'] = max(0, min(1, score))
        
        value = data.get('valor_score', 0)
        if not (0 <= value <= 10):
            data['valor_score'] = max(0, min(10, value))
        
        return True

    # ==================== BATCH PROCESSING ====================

    def queue_for_batch_analysis(self, text: str, source: str, source_url: str = None):
        self.batch_queue.put({
            'text': text,
            'source': source,
            'source_url': source_url,
            'timestamp': datetime.now().isoformat()
        })

    def _batch_worker(self):
        while True:
            try:
                items = []
                while len(items) < self.batch_threshold:
                    try:
                        item = self.batch_queue.get(timeout=30)
                        items.append(item)
                    except queue.Empty:
                        break
                
                if not items:
                    continue
                
                logger.info(f"Iniciando análisis batch de {len(items)} elementos")
                
                for i, item in enumerate(items):
                    try:
                        result = self._classify_with_ollama(item['text'])
                        
                        if result is None:
                            result = self._classify_with_local_rules(item['text'])
                        
                        if self.db_manager:
                            self._save_to_db(item, result)
                        
                        if self.progress_callback:
                            self.progress_callback(i + 1, len(items), item['source'])
                        
                    except Exception as e:
                        logger.error(f"Error procesando item batch: {e}")
                
                logger.info(f"Batch completado: {len(items)} elementos procesados")
                
            except Exception as e:
                logger.error(f"Error en batch worker: {e}")
                time.sleep(5)

    def _classify_with_local_rules(self, text: str) -> Dict:
        result = self._classify_block(text[:500])
        category, key = result
        
        return {
            "scope": "KDP",
            "categoria_principal": category,
            "score_principal": 0.5,
            "categorias_secundarias": [],
            "rol_gem": "#1 Analista de Mercado Educativo",
            "tags": ["clasificacion-local"],
            "resumen": text[:200] + "..." if len(text) > 200 else text,
            "metricas": {},
            "valor_score": 5,
            "contenido_banal": self._is_banal(text),
            "processed_by": "local-rules",
            "raw_ai_response": "Fallback a reglas locales"
        }

    def _save_to_db(self, item: Dict, result: Optional[Dict]):
        if not result or not self.db_manager:
            return
        
        try:
            category = result.get('categoria_principal', 'Investigación de Nichos')
            secondary = json.dumps(result.get('categorias_secundarias', []))
            tags = json.dumps(result.get('tags', []))
            metricas = json.dumps(result.get('metricas', {}))
            
            self.db_manager.insert_entry(
                category=category,
                secondary_categories=secondary,
                source=item.get('source', 'Unknown'),
                source_url=item.get('source_url'),
                content=item.get('text', ''),
                extract=result.get('resumen', '')[:200],
                tags=tags,
                confidence_score=result.get('score_principal', 0.0),
                value_score=result.get('valor_score', 0),
                is_banal=result.get('contenido_banal', False),
                is_analyzed=True,
                rol_gem=result.get('rol_gem'),
                metricas=metricas,
                raw_ai_response=result.get('raw_ai_response', ''),
                processed_by=result.get('processed_by', 'unknown')
            )
            logger.info(f"Entrada guardada en DB: {category}")
        except Exception as e:
            logger.error(f"Error guardando en DB: {e}")

    def update_blacklist(self, new_list):
        self.custom_blacklist = new_list

    def analyze_text(self, text, source_filename="Desconocido", source_url=None):
        if not text:
            return {"error": "Texto vacío"}
        
        if not self._validate_ai_input(text)[0]:
            return {"error": "Input no válido: solo se acepta texto, no imágenes o binarios"}
        
        # Intentar clasificación con Ollama (prioritaria)
        if self.ollama_available:
            ollama_result = self._classify_with_ollama(text)
            if ollama_result:
                if self.db_manager:
                    self._save_to_db({
                        'text': text,
                        'source': source_filename,
                        'source_url': source_url
                    }, ollama_result)
                
                return {
                    "integrated": [f"[{ollama_result.get('categoria_principal', 'KDP')}] Clasificación IA"],
                    "duplicates": [],
                    "classification": ollama_result,
                    "source": source_filename
                }
        
        # Fallback: usar reglas locales y método original
        blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
        if not blocks:
            blocks = [text]

        results = {"integrated": [], "duplicates": []}
        
        def process_single_block(block):
            if self._is_banal(block):
                return None

            ai_result = self._classify_with_ai(block)
            if ai_result:
                category, key = ai_result
            else:
                category, key = self._classify_block(block)
            
            target_file = self.files.get(key, self.files["MASTER"])
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
        b = block.strip().lower()
        if len(b) < 50: return True
        defaults = ["suscríbete", "dale like", "activa la campanita", "video anterior", "mis redes sociales", "bienvenidos a un nuevo video"]
        check_list = defaults + [x.lower() for x in self.custom_blacklist]
        if any(x in b for x in check_list):
            return True
        return False

    def _classify_block(self, block):
        b_lower = block.lower()
        
        if any(w in b_lower for w in ["términos", "legal", "copyright", "licencia", "marca", "tos", "suspensión", "bloqueo", "infracción", "política"]):
            return "Legalidad y Compliance", "LEGALIDAD"
            
        if any(w in b_lower for w in ["taxonomía", "arquitectura de información", "fase soe", "kpi", "checklist", "matriz", "roles dependientes", "gates de decisión"]):
            return "Matriz de Roles y Fases SOE", "MATRIZ"

        if any(w in b_lower for w in ["fórmula", "calculo", "roi", "precio", "acos", "tacos", "bsr", "kpi", "margen", "royalty", "beneficio", "ganancia", "taxonomía"]):
            return "Fórmulas y Métricas", "FORMULAS"
            
        if any(w in b_lower for w in ["nicho", "investigación", "demanda", "competencia", "validación", "oportunidad", "tendencia"]):
            return "Investigación de Nichos", "MASTER"

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
        self._ensure_master_kb_exists()
        
        if not self.checksum_file.exists():
            self.recalculate_all_checksums()
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

    def _ensure_master_kb_exists(self):
        master_kb_path = self.kb_dir / "MASTER_KB_TRANSCRIPCIONES.txt"
        
        if not master_kb_path.exists():
            self.kb_dir.mkdir(parents=True, exist_ok=True)
            
            template = f"""#  MASTER_KB - Base de Conocimiento KDP Master Suite
Versión: 1.0
Fecha de creación: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Modelo: qwen2.5:7b

📋 18 CATEGORÍAS KDP PRINCIPALES
{chr(10).join(self.CATEGORIES)}

👥 37+1 ROLES GEM (Generative Engine Marketing)
{chr(10).join([f"{num}. {name}" for num, name in self.ROLES_GEM])}

📊 Estadísticas
Videos procesados: 0
Entradas KB: 0
Última actualización: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
            master_kb_path.write_text(template, encoding="utf-8")
            logger.info(f"✅ MASTER_KB.txt creado automáticamente en {master_kb_path}")

            new_hash = self._calculate_md5(master_kb_path)
            if new_hash:
                try:
                    checksums = {}
                    if self.checksum_file.exists():
                        with open(self.checksum_file, 'r') as f:
                            checksums = json.load(f)
                    checksums[master_kb_path.name] = new_hash
                    with open(self.checksum_file, 'w') as f:
                        json.dump(checksums, f, indent=4)
                except Exception as e:
                    logger.warning(f"No se pudo actualizar checksum: {e}")

    def recalculate_all_checksums(self):
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
        lock = self.file_locks.get(lock_key, threading.Lock())
        with lock:
            if not file_path.exists():
                file_path.write_text(f"# {category.upper()} - BASE DE CONOCIMIENTO (KDP MASTER)\n\n", encoding="utf-8")

            current_content = file_path.read_text(encoding="utf-8")

            if content.strip() in current_content:
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n\n##  MÓDULO: {category}\n- **FUENTE:** {source}\n- **FECHA:** {timestamp}\n\n{content.strip()}\n\n---"

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(entry)
            self.update_file_checksum(file_path)

            if self.db_manager:
                try:
                    self.db_manager.insert_entry(category, source, content.strip(), timestamp)
                except Exception as e:
                    print(f"️ Error escribiendo en DB de conocimiento: {e}")

            return True