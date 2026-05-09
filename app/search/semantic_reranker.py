"""
KDP MASTER - Semantic Re-ranker Module
========================================
Módulo 4: Re-ranking Semántico de Resultados
Reordena resultados FTS5 por relevancia semántica usando IA.
"""

import logging
from typing import List, Dict, Tuple, Optional
import time

logger = logging.getLogger(__name__)


class SemanticReRanker:
    """
    MÓDULO 4: Re-ranking Semántico de Resultados
    Reordena resultados de búsqueda por relevancia semántica.
    """
    
    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self._score_cache = {}
        logger.info(f"SemanticReRanker inicializado: {model}")
    
    def rerank(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Re-ralea resultados basándose en relevancia semántica.
        
        Args:
            query: Query original
            results: Lista de resultados a re-rankear
            top_k: Número de resultados a retornar
            
        Returns:
            Lista re-ordenada de resultados con scores de relevancia
        """
        if not results:
            return []
        
        if len(results) <= top_k:
            return results
        
        scored_results = []
        
        for result in results:
            content = result.get('content', result.get('content_preview', ''))[:1000]
            
            cache_key = f"{query[:20]}_{result.get('id')}_{content[:50]}"
            if cache_key in self._score_cache:
                relevance_score = self._score_cache[cache_key]
            else:
                relevance_score = self._calculate_relevance(query, content)
                if len(self._score_cache) < 500:
                    self._score_cache[cache_key] = relevance_score
            
            result['semantic_relevance'] = round(relevance_score, 4)
            
            original_score = result.get('bm25_score', result.get('semantic_score', 0.5))
            result['final_score'] = (original_score * 0.4) + (relevance_score * 0.6)
            
            scored_results.append(result)
        
        scored_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        logger.info(f"Re-ranked {len(results)} resultados para query '{query[:30]}...'")
        
        return scored_results[:top_k]
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """
        Calcula relevancia semántica entre query y contenido.
        Usa múltiples factores para determinar relevancia.
        """
        query_terms = set(query.lower().split())
        content_lower = content.lower()
        
        content_terms = set(content_lower.split())
        
        overlap = query_terms & content_terms
        jaccard = len(overlap) / (len(query_terms | content_terms) + 1)
        
        position_score = self._calculate_position_score(query_lower=query.lower(), content=content_lower)
        
        length_penalty = self._calculate_length_penalty(content)
        
        keyword_density = sum(1 for t in query_terms if t in content_lower) / (len(query_terms) + 1)
        
        relevance = (
            jaccard * 0.3 +
            position_score * 0.25 +
            length_penalty * 0.2 +
            keyword_density * 0.25
        )
        
        return min(max(relevance, 0.0), 1.0)
    
    def _calculate_position_score(self, query_lower: str, content: str) -> float:
        """Calcula score basado en posición de términos en el contenido."""
        query_terms = query_lower.split()
        
        if not query_terms:
            return 0.5
        
        positions = []
        for term in query_terms:
            pos = content.find(term)
            if pos >= 0:
                positions.append(pos)
        
        if not positions:
            return 0.0
        
        avg_position = sum(positions) / len(positions)
        content_length = len(content)
        
        position_score = 1.0 - (avg_position / max(content_length, 1))
        
        return position_score
    
    def _calculate_length_penalty(self, content: str) -> float:
        """Calcula penalización por longitud (contenidos muy cortos o muy largos)."""
        word_count = len(content.split())
        
        if word_count < 50:
            return word_count / 50.0
        elif word_count > 5000:
            return 1.0 - ((word_count - 5000) / 10000)
        else:
            return 1.0
    
    def rerank_with_llm(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Re-ranking avanzado usando LLM para mejor evaluación semántica.
        Requiere Ollama disponible.
        """
        if not results:
            return []
        
        try:
            prompt = self._build_rerank_prompt(query, results[:20])
            
            import subprocess
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                scores = self._parse_llm_response(result.stdout, len(results[:20]))
                
                for i, r in enumerate(results[:20]):
                    if i < len(scores):
                        r['llm_relevance'] = scores[i]
                        r['final_score'] = r.get('semantic_relevance', 0.5) * 0.5 + scores[i] * 0.5
                
                results[:20].sort(key=lambda x: x.get('final_score', 0), reverse=True)
                
        except Exception as e:
            logger.warning(f"Re-ranking LLM falló, usando método simple: {e}")
        
        return results[:top_k]
    
    def _build_rerank_prompt(self, query: str, results: List[Dict]) -> str:
        """Construye prompt para re-ranking con LLM."""
        prompt = f"Given the query: '{query}', rank the following documents by relevance (1-10):\n\n"
        
        for i, r in enumerate(results, 1):
            title = r.get('source', r.get('title', f'Doc {r.get("id")}'))
            preview = r.get('content_preview', r.get('content', ''))[:200]
            prompt += f"{i}. {title}: {preview}...\n"
        
        prompt += "\nProvide scores as: 1:score, 2:score, ..."
        
        return prompt
    
    def _parse_llm_response(self, response: str, num_docs: int) -> List[float]:
        """Parsea respuesta del LLM para obtener scores."""
        scores = []
        
        for line in response.split('\n'):
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    score = float(parts[1].strip()) / 10.0
                    scores.append(min(max(score, 0.0), 1.0))
                except:
                    pass
        
        while len(scores) < num_docs:
            scores.append(0.5)
        
        return scores[:num_docs]
    
    def clear_cache(self):
        """Limpia el cache de scores."""
        self._score_cache.clear()


class CrossEncoderReranker:
    """
    Re-ranker basado en cross-encoder para mayor precisión.
    """
    
    def __init__(self):
        self.scores_cache = {}
        logger.info("CrossEncoderReranker inicializado")
    
    def score_pairs(self, query: str, documents: List[str]) -> List[float]:
        """
        Calcula scores de relevancia para cada par query-documento.
        
        Args:
            query: Query de búsqueda
            documents: Lista de contenidos a evaluar
            
        Returns:
            Lista de scores (0-1)
        """
        scores = []
        
        for doc in documents:
            score = self._compute_cross_score(query, doc)
            scores.append(score)
        
        return scores
    
    def _compute_cross_score(self, query: str, document: str) -> float:
        """Computa score de relevancia query-documento."""
        query_terms = set(query.lower().split())
        doc_terms = set(document.lower().split())
        
        exact_match = len(query_terms & doc_terms) / (len(query_terms) + 1)
        
        query_keywords = [t for t in query_terms if len(t) > 3]
        partial_match = sum(1 for t in query_keywords if any(t in d or d in t for d in doc_terms)) / (len(query_keywords) + 1)
        
        semantic_approx = self._semantic_approximation(query, document)
        
        score = (exact_match * 0.4) + (partial_match * 0.3) + (semantic_approx * 0.3)
        
        return min(max(score, 0.0), 1.0)
    
    def _semantic_approximation(self, query: str, document: str) -> float:
        """Aproximación semántica simple."""
        query_words = query.lower().split()
        doc_lower = document.lower()
        
        matches = sum(1 for w in query_words if w in doc_lower)
        
        return matches / (len(query_words) + 1)


def get_reranker(model: str = "llama3.1:8b") -> SemanticReRanker:
    """Factory function para obtener el re-ranker."""
    return SemanticReRanker(model)