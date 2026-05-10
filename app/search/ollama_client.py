"""
KDP MASTER - Ollama Client Module
===================================
Cliente para conexión con Ollama local (_embeddings, completion, rerank).
"""

import json
import os
import logging
from typing import List, Dict, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Cliente para Ollama local - Módulos 1-12: Búsqueda Semántica y Vectorial
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url
        self.model = model
        self._available_models = None
        self._connection_tested = False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Verifica conexión con Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self._available_models = response.json().get('models', [])
                self._connection_tested = True
                return True, "Conectado a Ollama"
            return False, f"Estado: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Ollama no encontrado (asegúrate de tener Ollama corriendo)"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """Lista modelos disponibles en Ollama."""
        if not self._connection_tested:
            self.test_connection()
        if self._available_models:
            return [m['name'] for m in self._available_models]
        return ["nomic-embed-text", "llama3", "mistral"]
    
    def set_embedding_model(self, model: str):
        """Cambia el modelo de embeddings."""
        self.model = model
        logger.info(f"Modelo de embeddings cambiado a: {model}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        MÓDULO 1: Embeddings de Consultas con Ollama
        Convierte texto a vector semántico.
        """
        if not texts:
            return []
        
        embeddings = []
        
        for text in texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=30
                )
                
                if response.status_code == 200:
                    embedding = response.json().get('embedding', [])
                    embeddings.append(embedding)
                else:
                    logger.warning(f"Error generando embedding: {response.status_code}")
                    embeddings.append([0.0] * 768)
                    
            except Exception as e:
                logger.error(f"Error en embedding: {e}")
                embeddings.append([0.0] * 768)
        
        return embeddings
    
    def generate_completion(self, prompt: str, model: str = None, 
                           temperature: float = 0.3, max_tokens: int = 500) -> str:
        """
        Genera completion con Ollama para módulos de IA (expansión, reformulación, etc.)
        """
        model = model or "llama3"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            return ""
            
        except Exception as e:
            logger.error(f"Error en completion: {e}")
            return ""
    
    def expand_query(self, query: str) -> List[str]:
        """
        MÓDULO 5: Expansión de Consulta con IA
        Añade sinónimos y términos relacionados.
        """
        prompt = f"""E Expansiona esta consulta de búsqueda con sinónimos y términos relacionados para búsqueda en base de conocimiento KDP.
Consulta: {query}
Dame solo una lista de términos separados por comas, sin explicación:"""
        
        result = self.generate_completion(prompt, max_tokens=100)
        
        if result:
            terms = [query] + [t.strip() for t in result.split(',') if t.strip()]
            return terms[:10]
        
        return [query]
    
    def reformulate_query(self, query: str, context: str = "") -> str:
        """
        MÓDULO 6: Reformulación de Consulta Natural
        Reescribe query ambigua a forma precisa.
        """
        prompt = f"""Reformula esta consulta de búsqueda ambiguo a una forma precisa y clara.
Contexto adicional: {context}
Consulta original: {query}
Dame solo la consulta reformulada, sin explicación:"""
        
        return self.generate_completion(prompt, max_tokens=100) or query
    
    def detect_intent(self, query: str) -> str:
        """
        MÓDULO 7: Detección de Intención de Búsqueda
        Clasifica si busca definición, tutorial, ejemplo, etc.
        """
        prompt = f"""Clasifica esta consulta de búsqueda en una de estas categorías:
- definicion: quiere saber qué es algo
- tutorial: quiere aprender a hacer algo
- ejemplo: quiere ver casos prácticos
- comparacion: quiere comparar opciones
- herramienta: busca software/herramientas
- estrategia: quiere estrategias/plan
- general: búsqueda general

Consulta: {query}
Dame solo la categoría:"""
        
        result = self.generate_completion(prompt, max_tokens=20)
        
        intents = ['definicion', 'tutorial', 'ejemplo', 'comparacion', 'herramienta', 'estrategia', 'general']
        for intent in intents:
            if intent in result.lower():
                return intent
        
        return 'general'
    
    def answer_question(self, question: str, context: str) -> str:
        """
        MÓDULO 8: Búsqueda por Pregunta Natural (Q&A)
        Permite preguntar "¿Cómo configuro proxy?" y responde.
        """
        prompt = f"""Basándote en el siguiente contexto, responde la pregunta de forma precisa.
Si la respuesta no está en el contexto, indica que no tienes esa información.

CONTEXTO:
{context[:2000]}

PREGUNTA: {question}

RESPUESTA:"""
        
        return self.generate_completion(prompt, max_tokens=500)
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        MÓDULO 9: Extracción de Entidades de la Consulta
        Identifica personas, herramientas, fechas, marcas.
        """
        prompt = f"""Extrae las siguientes entidades de esta consulta:
- personas: nombres de personas mencionadas
- herramientas: software, apps, plataformas mencionadas
- fechas: años, meses, períodos mencionados
- marcas: empresas, productos mencionados
- conceptos: temas o conceptos principales

Consulta: {query}
Dame el resultado en formato JSON:"""
        
        result = self.generate_completion(prompt, max_tokens=200)
        
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {'personas': [], 'herramientas': [], 'fechas': [], 'marcas': [], 'conceptos': []}


class OllamaVectorStore:
    """
    MÓDULOS 2-3: Búsqueda Vectorial y Índice FAISS
    """
    
    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client
        self.embeddings = []
        self.metadata = []
        self._use_faiss = False
        self._index = None
        self._try_import_faiss()
    
    def _try_import_faiss(self):
        """Intenta importar FAISS para búsqueda vectorial optimizada."""
        try:
            import faiss
            self._use_faiss = True
            self._faiss = faiss
            logger.info("FAISS disponible para búsqueda vectorial")
        except ImportError:
            logger.warning("FAISS no disponible, usando búsqueda por similitud cosine manual")
            self._use_faiss = False
    
    def add_documents(self, texts: List[str], metadata: List[Dict]):
        """Añade documentos al índice vectorial."""
        self.embeddings = self.client.generate_embeddings(texts)
        self.metadata = metadata
        
        if self._use_faiss and self.embeddings:
            dim = len(self.embeddings[0])
            self._index = self._faiss.IndexFlatL2(dim)
            self._index.add(self.embeddings)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Búsqueda vectorial por similitud."""
        query_embedding = self.client.generate_embeddings([query])[0]
        
        if self._use_faiss and self._index:
            query_vec = [query_embedding]
            distances, indices = self._index.search(query_vec, top_k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.metadata):
                    results.append({
                        'index': int(idx),
                        'distance': float(distances[0][i]),
                        **self.metadata[idx]
                    })
            return results
        else:
            return self._cosine_search(query_embedding, top_k)
    
    def _cosine_search(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """Búsqueda por similitud cosine manual."""
        if not self.embeddings:
            return []
        
        similarities = []
        for i, emb in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_embedding, emb)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, sim in similarities[:top_k]:
            results.append({
                'index': idx,
                'similarity': sim,
                **self.metadata[idx]
            })
        
        return results
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similitud cosine entre dos vectores."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)


_ollama_client = None
_vector_store = None


def get_ollama_client() -> Optional[OllamaClient]:
    """Obtiene cliente singleton de Ollama."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


def get_vector_store() -> Optional[OllamaVectorStore]:
    """Obtiene store vectorial singleton."""
    global _vector_store
    if _vector_store is None:
        client = get_ollama_client()
        if client:
            _vector_store = OllamaVectorStore(client)
    return _vector_store