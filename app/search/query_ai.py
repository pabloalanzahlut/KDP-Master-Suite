"""
KDP MASTER - Query AI Processing Module
=========================================
Módulos 5-8: Expansión, Reformulación, Intención, Q&A con IA
Procesamiento inteligente de queries usando Ollama.
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryIntent:
    intent_type: str
    confidence: float
    entities: List[str]
    metadata: Dict


class QueryExpander:
    """
    MÓDULO 5: Expansión de Consulta con IA
    Añade sinónimos y términos relacionados usando el diccionario de sinónimos.
    """
    
    def __init__(self):
        self._load_synonyms()
    
    def _load_synonyms(self):
        """Carga diccionario de sinónimos."""
        synonyms_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'synonyms.json'
        )
        
        self.synonyms = {}
        
        if os.path.exists(synonyms_path):
            try:
                with open(synonyms_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.synonyms = data.get('synonym_groups', {})
            except Exception as e:
                logger.warning(f"Error cargando sinónimos: {e}")
    
    def expand_query(self, query: str) -> str:
        """
        Expande query con sinónimos y términos relacionados.
        
        Args:
            query: Query original
            
        Returns:
            Query expandida
        """
        query_lower = query.lower()
        expanded_terms = []
        
        for main_term, synonyms in self.synonyms.items():
            if main_term in query_lower:
                expanded_terms.extend(synonyms[:3])
            for syn in synonyms:
                if syn in query_lower:
                    expanded_terms.append(main_term)
        
        if expanded_terms:
            return query + " " + " ".join(expanded_terms)
        
        return query
    
    def expand_with_ai(self, query: str, model: str = "llama3.1:8b") -> str:
        """
        Expansión de query usando LLM para términos más inteligentes.
        """
        try:
            prompt = f"""Given the search query: "{query}"

Generate 5-10 related search terms that would help find more relevant results. 
Include synonyms, related concepts, and common variations.

Output ONLY the expanded query terms separated by spaces, nothing else."""

            import subprocess
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                expanded = result.stdout.strip()
                return query + " " + expanded
            
        except Exception as e:
            logger.warning(f"Expansión IA falló: {e}")
        
        return self.expand_query(query)


class QueryReformulator:
    """
    MÓDULO 6: Reformulación de Consulta Natural
    Reescribe queries ambiguas a forma precisa.
    """
    
    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self.reformulation_cache = {}
    
    def reformulate(self, query: str, context: str = None) -> str:
        """
        Reformula query ambigua/vaga a forma precisa.
        
        Args:
            query: Query original
            context: Contexto opcional (categoría activa, etc.)
            
        Returns:
            Query reformulada
        """
        if not query or len(query.strip()) < 2:
            return query
        
        cache_key = f"{query}_{context or 'none'}"
        if cache_key in self.reformulation_cache:
            return self.reformulation_cache[cache_key]
        
        try:
            context_hint = f"Context: {context}" if context else ""
            
            prompt = f"""Rewrite this search query to be more precise and specific for finding relevant content in a KDP/Amazon publishing knowledge base.

Original query: "{query}"
{context_hint}

If the query is already specific, return it as-is.
If it's vague (like "Amazon" or "marketing"), suggest more specific terms.
If it's ambiguous, disambiguate based on KDP context.

Output ONLY the reformulated query, nothing else."""

            import subprocess
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                reformulated = result.stdout.strip().strip('"').strip()
                self.reformulation_cache[cache_key] = reformulated
                return reformulated
            
        except Exception as e:
            logger.warning(f"Reformulación falló: {e}")
        
        return self._simple_reformulate(query)
    
    def _simple_reformulate(self, query: str) -> str:
        """Reformulación simple sin LLM."""
        query_lower = query.lower()
        
        reformulations = {
            'amazon': 'Amazon KDP publishing',
            'ads': 'Amazon Ads advertising',
            'marketing': 'book marketing promotion',
            'seo': 'Amazon SEO optimization',
            'price': 'pricing strategy royalty',
            'category': 'KDP category selection',
            'launch': 'book launch strategy',
        }
        
        for key, reformulated in reformulations.items():
            if key == query_lower:
                return reformulated
        
        return query


class IntentDetector:
    """
    MÓDULO 7: Detección de Intención de Búsqueda
    Clasifica si el usuario busca definición, tutorial, ejemplo, etc.
    """
    
    INTENT_PATTERNS = {
        'tutorial': ['cómo', 'como', 'tutorial', 'guía', 'pasos', 'aprender', 'hacer', 'configurar', 'crear'],
        'definition': ['qué es', 'que es', 'definición', 'significado', 'explicar', 'qué significa'],
        'example': ['ejemplo', 'caso', 'ejemplos', 'sample', 'template', 'plantilla'],
        'comparison': ['vs', 'versus', 'comparar', 'diferencia', 'mejor', 'comparación'],
        'research': ['investigación', 'estudio', 'datos', 'estadística', 'métricas', 'porcentaje'],
        'tool': ['herramienta', 'software', 'app', 'aplicación', 'servicio'],
        'legal': ['legal', 'términos', 'condiciones', 'política', 'compliance', 'derecho'],
        'troubleshooting': ['error', 'problema', 'solución', 'arreglar', 'fix', 'error'],
    }
    
    def detect_intent(self, query: str) -> QueryIntent:
        """
        Detecta la intención de búsqueda.
        
        Returns:
            QueryIntent con tipo, confianza y entidades
        """
        query_lower = query.lower()
        
        intent_scores = {}
        
        for intent, keywords in self.INTENT_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return QueryIntent(
                intent_type='general',
                confidence=0.5,
                entities=[],
                metadata={}
            )
        
        intent_type = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[intent_type] / len(query.split()), 1.0)
        
        entities = self._extract_entities(query)
        
        return QueryIntent(
            intent_type=intent_type,
            confidence=confidence,
            entities=entities,
            metadata={'intent_scores': intent_scores}
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extrae entidades de la query (fechas, marcas, herramientas)."""
        entities = []
        
        year_match = re.search(r'(20\d{2}|19\d{2})', query)
        if year_match:
            entities.append(year_match.group(1))
        
        tools = ['Helium 10', 'Jungle Scout', 'KDP', 'Amazon', 'Canva', 'ChatGPT', 'Python']
        for tool in tools:
            if tool.lower() in query.lower():
                entities.append(tool)
        
        return entities
    
    def adjust_results_by_intent(self, results: List[Dict], intent: QueryIntent) -> List[Dict]:
        """Ajusta resultados según intención detectada."""
        if intent.intent_type == 'tutorial':
            for r in results:
                content_lower = r.get('content', '').lower()
                if any(kw in content_lower for kw in [' paso ', ' cómo ', ' tutorial ', ' guía ']):
                    r['intent_boost'] = r.get('intent_boost', 0) + 0.2
        
        elif intent.intent_type == 'definition':
            for r in results:
                content_lower = r.get('content', '').lower()
                if 'definición' in content_lower or 'qué es' in content_lower:
                    r['intent_boost'] = r.get('intent_boost', 0) + 0.2
        
        return sorted(results, key=lambda x: x.get('intent_boost', 0), reverse=True)


class NaturalQA:
    """
    MÓDULO 8: Búsqueda por Pregunta Natural (Q&A)
    Permite preguntar en lenguaje natural y obtener respuestas.
    """
    
    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self.qa_history = []
    
    def answer_question(self, question: str, context_results: List[Dict]) -> Dict:
        """
        Responde una pregunta basándose en los resultados de búsqueda.
        
        Args:
            question: Pregunta en lenguaje natural
            context_results: Resultados de búsqueda como contexto
            
        Returns:
            Diccionario con respuesta y fuentes
        """
        if not context_results:
            return {
                'answer': 'No hay suficiente contexto para responder.',
                'sources': [],
                'confidence': 0.0
            }
        
        context = self._build_context(context_results[:5])
        
        try:
            prompt = f"""Based on the following knowledge base excerpts, answer the question.

Question: {question}

Context:
{context}

If the answer is in the context, provide it clearly and cite which source it came from.
If not enough information, say so honestly.
Be concise but informative."""

            import subprocess
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                answer = result.stdout.strip()
                
                self.qa_history.append({
                    'question': question,
                    'answer': answer,
                    'sources': [r.get('id') for r in context_results[:3]]
                })
                
                return {
                    'answer': answer,
                    'sources': context_results[:3],
                    'confidence': 0.8,
                    'question': question
                }
        
        except Exception as e:
            logger.error(f"Q&A falló: {e}")
        
        return self._simple_answer(question, context_results)
    
    def _build_context(self, results: List[Dict]) -> str:
        """Construye contexto desde resultados de búsqueda."""
        context_parts = []
        
        for i, r in enumerate(results, 1):
            title = r.get('source', f'Document {i}')
            content = r.get('content_preview', r.get('content', ''))[:300]
            context_parts.append(f"[{i}] {title}: {content}...")
        
        return "\n\n".join(context_parts)
    
    def _simple_answer(self, question: str, results: List[Dict]) -> Dict:
        """Respuesta simple sin LLM."""
        if not results:
            return {'answer': 'No encontré información relevante.', 'sources': [], 'confidence': 0.0}
        
        first_result = results[0]
        content = first_result.get('content_preview', first_result.get('content', ''))[:500]
        
        return {
            'answer': f"Basado en la información encontrada: {content}...",
            'sources': [first_result],
            'confidence': 0.5,
            'question': question
        }
    
    def get_history(self) -> List[Dict]:
        """Retorna historial de Q&A."""
        return self.qa_history.copy()


class EntityExtractor:
    """
    MÓDULO 9: Extracción de Entidades de la Consulta
    Identifica personas, herramientas, fechas en la query.
    """
    
    def extract(self, query: str) -> Dict:
        """
        Extrae entidades de la query.
        
        Returns:
            Diccionario con entidades categorizadas
        """
        entities = {
            'dates': [],
            'tools': [],
            'brands': [],
            'numbers': [],
            'categories': []
        }
        
        year_match = re.search(r'(20\d{2}|19\d{2})', query)
        if year_match:
            entities['dates'].append(year_match.group(1))
        
        month_match = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|january|february|march|april|may|june|july|august|september|october|november|december)', query, re.IGNORECASE)
        if month_match:
            entities['dates'].append(month_match.group(1))
        
        tools = ['Helium 10', 'Jungle Scout', 'Canva', 'KDP', 'Kindle', 'Amazon', 'ChatGPT', 'Python', 'Excel']
        for tool in tools:
            if tool.lower() in query.lower():
                entities['tools'].append(tool)
        
        numbers = re.findall(r'\d+%|\d+px|\$\d+|\d+.\d+', query)
        entities['numbers'].extend(numbers)
        
        kdp_categories = ['Ads', 'SEO', 'KDP', 'Kindle Unlimited', 'Pricing', 'Marketing', 'Legal']
        for cat in kdp_categories:
            if cat.lower() in query.lower():
                entities['categories'].append(cat)
        
        return entities


def get_query_processor(model: str = "llama3.1:8b") -> Dict:
    """Factory para obtener todos los procesadores de query."""
    return {
        'expander': QueryExpander(),
        'reformulator': QueryReformulator(model),
        'intent_detector': IntentDetector(),
        'qa': NaturalQA(model),
        'entity_extractor': EntityExtractor()
    }