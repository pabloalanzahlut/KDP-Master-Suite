"""
KDP MASTER - Vector Search Module
===================================
Módulos 1-3: Embeddings, Búsqueda Vectorial, FAISS/HNSW
Búsqueda semántica usando Ollama para embeddings locales.
"""

import os
import json
import time
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768


@dataclass
class EmbeddedDocument:
    id: int
    content: str
    category: str
    source: str
    embedding: np.ndarray
    metadata: dict = None


class OllamaEmbedder:
    """
    MÓDULO 1: Embeddings de Consultas con Ollama
    Convierte texto a vector semántico usando modelo local.
    """
    
    def __init__(self, model: str = EMBEDDING_MODEL):
        self.model = model
        self._embedding_cache = {}
        logger.info(f"OllamaEmbedder inicializado con modelo: {model}")
    
    def embed_text(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Genera embedding para un texto.
        
        Args:
            text: Texto a convertir en embedding
            use_cache: Usar cache si está disponible
            
        Returns:
            Vector numpy de embeddings
        """
        if not text or not text.strip():
            return np.zeros(EMBEDDING_DIM)
        
        text = text.strip()
        
        if use_cache and text in self._embedding_cache:
            return self._embedding_cache[text]
        
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "embed", "-m", self.model, text],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                embedding_str = result.stdout.strip()
                embedding = np.array(json.loads(embedding_str))
                
                if len(embedding) > 0:
                    if use_cache and len(self._embedding_cache) < 100:
                        self._embedding_cache[text] = embedding
                    return embedding
            
            logger.warning(f"Falló embedding, usando hash simple: {result.stderr}")
            return self._simple_embedding(text)
            
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """Fallback: embedding simple basado en hash."""
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        return np.random.randn(EMBEDDING_DIM) * 0.1
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Genera embeddings para múltiples textos."""
        embeddings = []
        for text in texts:
            emb = self.embed_text(text)
            embeddings.append(emb)
        return np.array(embeddings)
    
    def clear_cache(self):
        """Limpia el cache de embeddings."""
        self._embedding_cache.clear()


class VectorIndex:
    """
    MÓDULO 3: Índice Vectorial FAISS/HNSW
    Indexa embeddings para búsqueda rápida.
    """
    
    def __init__(self, dimension: int = EMBEDDING_DIM, index_type: str = "hnsw"):
        self.dimension = dimension
        self.index_type = index_type
        self.documents: List[EmbeddedDocument] = []
        self.index = None
        self._initialized = False
        logger.info(f"VectorIndex inicializado: type={index_type}, dim={dimension}")
    
    def initialize_index(self):
        """Inicializa el índice vectorial."""
        try:
            import faiss
            if self.index_type == "hnsw":
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            elif self.index_type == "flat":
                self.index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "ivf":
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
            
            self._initialized = True
            logger.info(f"Índice FAISS inicializado: {self.index_type}")
        except ImportError:
            logger.warning("FAISS no disponible, usando implementación simple")
            self.index = SimpleVectorIndex(self.dimension)
            self._initialized = True
    
    def add_documents(self, documents: List[EmbeddedDocument]):
        """Añade documentos al índice."""
        if not self._initialized:
            self.initialize_index()
        
        if not documents:
            return
        
        for doc in documents:
            self.documents.append(doc)
        
        embeddings = np.array([d.embedding for d in documents])
        
        if hasattr(self.index, 'add'):
            self.index.add(embeddings)
        
        logger.info(f"Añadidos {len(documents)} documentos al índice vectorial")
    
    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[int, float]]:
        """
        Busca los k documentos más similares al query.
        
        Returns:
            Lista de tuplas (doc_id, similarity_score)
        """
        if not self._initialized or not self.documents:
            return []
        
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        try:
            if hasattr(self.index, 'search'):
                distances, indices = self.index.search(query_embedding, min(k, len(self.documents)))
                
                results = []
                for idx, dist in zip(indices[0], distances[0]):
                    if idx >= 0 and idx < len(self.documents):
                        score = 1.0 / (1.0 + dist)
                        results.append((self.documents[idx].id, score))
                
                return results
            else:
                return self.index.search(query_embedding, k)
                
        except Exception as e:
            logger.error(f"Error en búsqueda vectorial: {e}")
            return self._simple_search(query_embedding[0], k)
    
    def _simple_search(self, query: np.ndarray, k: int) -> List[Tuple[int, float]]:
        """Búsqueda simple sin FAISS."""
        scores = []
        for doc in self.documents:
            sim = self._cosine_similarity(query, doc.embedding)
            scores.append((doc.id, sim))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calcula similitud coseno."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    def save_index(self, filepath: str):
        """Guarda el índice a disco."""
        try:
            import faiss
            faiss.write_index(self.index, filepath)
            logger.info(f"Índice guardado: {filepath}")
        except Exception as e:
            logger.error(f"Error guardando índice: {e}")
    
    def load_index(self, filepath: str):
        """Carga el índice desde disco."""
        try:
            import faiss
            self.index = faiss.read_index(filepath)
            self._initialized = True
            logger.info(f"Índice cargado: {filepath}")
        except Exception as e:
            logger.error(f"Error cargando índice: {e}")


class SimpleVectorIndex:
    """Índice vectorial simple sin FAISS."""
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors = []
    
    def add(self, vectors: np.ndarray):
        self.vectors.extend(vectors)
    
    def search(self, query: np.ndarray, k: int) -> List[Tuple[int, float]]:
        scores = []
        for i, v in enumerate(self.vectors):
            sim = np.dot(query, v) / (np.linalg.norm(query) * np.linalg.norm(v) + 1e-8)
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


class VectorSearchEngine:
    """
    MÓDULO 2: Búsqueda Vectorial por Similitud Cosine
    Motor de búsqueda semántica combinando embeddings + DB.
    """
    
    def __init__(self, knowledge_db, embedder: OllamaEmbedder = None):
        self.db = knowledge_db
        self.embedder = embedder or OllamaEmbedder()
        self.vector_index = VectorIndex()
        self._index_built = False
        logger.info("VectorSearchEngine inicializado")
    
    def build_index(self, force_rebuild: bool = False) -> Dict:
        """
        Construye el índice vectorial desde la base de conocimiento.
        
        Returns:
            Diccionario con estado de la indexación
        """
        if self._index_built and not force_rebuild:
            return {'status': 'already_built', 'documents': len(self.vector_index.documents)}
        
        start_time = time.time()
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, content, category, source, tipo, timestamp
                FROM knowledge_entries
                WHERE content IS NOT NULL AND LENGTH(content) > 50
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            documents = []
            for row in rows:
                content = row[1]
                embedding = self.embedder.embed_text(content[:2000])
                
                doc = EmbeddedDocument(
                    id=row[0],
                    content=content,
                    category=row[2] or 'Sin categoría',
                    source=row[3] or '',
                    embedding=embedding,
                    metadata={'tipo': row[4], 'timestamp': str(row[5])}
                )
                documents.append(doc)
            
            self.vector_index.add_documents(documents)
            self._index_built = True
            
            elapsed = time.time() - start_time
            
            return {
                'status': 'SUCCESS',
                'documents_indexed': len(documents),
                'elapsed_seconds': round(elapsed, 2),
                'dimension': EMBEDDING_DIM,
                'model': self.embedder.model
            }
            
        except Exception as e:
            logger.error(f"Error construyendo índice vectorial: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def search_semantic(self, query: str, top_k: int = 20, 
                        filters: Dict = None, hybrid: bool = True) -> Dict:
        """
        MÓDULO 2: Búsqueda semántica principal.
        
        Args:
            query: Query de búsqueda en texto natural
            top_k: Número de resultados
            filters: Filtros (category, tipo, date_from, etc.)
            hybrid: Combinar con búsqueda FTS5
            
        Returns:
            Diccionario con resultados y scores
        """
        start_time = time.time()
        
        query_embedding = self.embedder.embed_text(query)
        
        vector_results = self.vector_index.search(query_embedding, top_k * 2)
        
        results = []
        seen_content = set()
        
        for doc_id, score in vector_results:
            for doc in self.vector_index.documents:
                if doc.id == doc_id:
                    if doc.content[:100] in seen_content:
                        continue
                    seen_content.add(doc.content[:100])
                    
                    if filters:
                        if filters.get('category') and filters['category'] != 'Todos':
                            if doc.category != filters['category']:
                                continue
                        if filters.get('type') and filters['type'] != 'Todos':
                            if doc.metadata.get('tipo') != filters['type']:
                                continue
                    
                    results.append({
                        'id': doc.id,
                        'source': doc.source,
                        'category': doc.category,
                        'type': doc.metadata.get('tipo', 'Artículo'),
                        'content_preview': doc.content[:300],
                        'semantic_score': round(score, 4),
                        'content': doc.content,
                        'timestamp': doc.metadata.get('timestamp', '')
                    })
                    break
        
        if hybrid and self.db:
            fts_results = self.db.search_fts(query, limit=top_k)
            fts_docs = fts_results.get('results', [])[:top_k]
            
            fts_by_id = {r['id']: r for r in fts_docs}
            
            hybrid_results = []
            for r in results:
                doc_id = r['id']
                if doc_id in fts_by_id:
                    fts_r = fts_by_id[doc_id]
                    r['fts_score'] = fts_r.get('rank', 0)
                    r['combined_score'] = (r['semantic_score'] * 0.6) + (1.0 / (fts_r.get('rank', 1) + 1) * 0.4)
                else:
                    r['combined_score'] = r['semantic_score'] * 0.8
                
                hybrid_results.append(r)
            
            hybrid_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            results = hybrid_results[:top_k]
        
        elapsed = time.time() - start_time
        
        return {
            'results': results[:top_k],
            'total': len(results),
            'elapsed_ms': round(elapsed * 1000, 2),
            'algorithm': 'Semantic-FTS Hybrid' if hybrid else 'Semantic Only',
            'query_embedding_dim': EMBEDDING_DIM,
            'indexed_docs': len(self.vector_index.documents)
        }


def get_vector_search_engine(knowledge_db) -> VectorSearchEngine:
    """Factory function para obtener el motor de búsqueda vectorial."""
    return VectorSearchEngine(knowledge_db)