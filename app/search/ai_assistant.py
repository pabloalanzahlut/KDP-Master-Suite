"""
KDP MASTER - AI Assistant Module
==================================
Módulos 37-48: Asistencia Inteligente y Automatización
Chat RAG, reporte, sugerencias, FAQs, best practices.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str
    sources: List[Dict] = field(default_factory=list)


class RAGAssistant:
    """
    MÓDULO 37: Chat sobre Resultados (RAG)
    Permite hacer preguntas sobre los resultados encontrados.
    """
    
    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self.conversation_history: List[ChatMessage] = []
        self.current_context: List[Dict] = []
        logger.info("RAGAssistant inicializado")
    
    def set_context(self, results: List[Dict]):
        """
        Establece el contexto de resultados para el chat.
        
        Args:
            results: Lista de resultados de búsqueda
        """
        self.current_context = results[:10]
    
    def ask(self, question: str) -> Dict:
        """
        Responde una pregunta sobre el contexto actual.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            Diccionario con respuesta y fuentes
        """
        if not self.current_context:
            return {
                'answer': 'No hay resultados disponibles para analizar. Realiza una búsqueda primero.',
                'sources': [],
                'error': 'no_context'
            }
        
        context = self._build_context()
        
        history_text = ""
        if len(self.conversation_history) > 0:
            last_msgs = self.conversation_history[-3:]
            history_text = "\n".join([f"{m.role}: {m.content}" for m in last_msgs])
        
        try:
            prompt = f"""Eres un asistente de conocimiento experto en KDP/Amazon Publishing.
Responde preguntas basándote ÚNICAMENTE en el contexto proporcionado.

Contexto de documentos:
{context}

Historial de conversación:
{history_text}

Pregunta actual: {question}

Responde de forma clara y concisa. Si no tienes información suficiente, dilo honestamente.
CITA las fuentes cuando menciones información de los documentos."""

            import subprocess
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=90
            )
            
            if result.returncode == 0:
                answer = result.stdout.strip()
                
                self.conversation_history.append(ChatMessage(
                    role="user",
                    content=question,
                    timestamp=datetime.now().isoformat()
                ))
                
                self.conversation_history.append(ChatMessage(
                    role="assistant",
                    content=answer,
                    timestamp=datetime.now().isoformat(),
                    sources=self.current_context[:3]
                ))
                
                return {
                    'answer': answer,
                    'sources': self.current_context[:3],
                    'question': question
                }
        
        except Exception as e:
            logger.error(f"RAG chat falló: {e}")
        
        return self._simple_answer(question)
    
    def _build_context(self) -> str:
        """Construye contexto desde resultados."""
        context_parts = []
        
        for i, r in enumerate(self.current_context, 1):
            title = r.get('source', r.get('title', f'Doc {i}'))
            category = r.get('category', '')
            tipo = r.get('type', r.get('tipo', ''))
            content = r.get('content', r.get('content_preview', ''))[:500]
            
            context_parts.append(f"[{i}] {title} ({category} - {tipo}):\n{content}...\n")
        
        return "\n---\n".join(context_parts)
    
    def _simple_answer(self, question: str) -> Dict:
        """Respuesta simple sin LLM."""
        question_lower = question.lower()
        
        for r in self.current_context:
            content = r.get('content', r.get('content_preview', ''))
            
            if any(kw in content.lower() for kw in question_lower.split()[:2]):
                return {
                    'answer': f"Según el documento: {content[:300]}...",
                    'sources': [r],
                    'question': question
                }
        
        return {
            'answer': 'No encontré información específica en los resultados. ¿Puedes ser más específico?',
            'sources': [],
            'question': question
        }
    
    def clear_history(self):
        """Limpia el historial de conversación."""
        self.conversation_history.clear()
    
    def get_history(self) -> List[ChatMessage]:
        """Retorna historial de conversación."""
        return self.conversation_history.copy()


class SearchReportGenerator:
    """
    MÓDULO 38: Generación de Reporte de Búsqueda
    Crea documento sintetizando resultados.
    """
    
    def __init__(self):
        self.output_dir = os.path.expanduser("~/Documents/KDP_Master/search_reports")
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("SearchReportGenerator inicializado")
    
    def generate_report(self, query: str, results: List[Dict], 
                        analysis: Dict = None) -> str:
        """
        Genera reporte de búsqueda en Markdown.
        
        Args:
            query: Query original
            results: Resultados de búsqueda
            analysis: Análisis opcional (de ResultAnalyzer)
            
        Returns:
            Ruta del archivo generado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_busqueda_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Reporte de Búsqueda - KDP Master\n\n")
                f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Query:** {query}\n")
                f.write(f"**Total de resultados:** {len(results)}\n\n")
                f.write("---\n\n")
                
                if analysis and analysis.get('summary'):
                    f.write(f"## Resumen\n\n{analysis['summary']}\n\n")
                
                if analysis and analysis.get('key_points'):
                    f.write("## Puntos Clave\n\n")
                    for i, point in enumerate(analysis['key_points'][:5], 1):
                        f.write(f"{i}. {point}\n")
                    f.write("\n")
                
                f.write("## Resultados\n\n")
                for i, r in enumerate(results[:20], 1):
                    title = r.get('source', r.get('title', f'Resultado {i}'))
                    category = r.get('category', 'Sin categoría')
                    tipo = r.get('type', r.get('tipo', 'Artículo'))
                    content = r.get('content_preview', r.get('content', ''))[:300]
                    
                    f.write(f"### {i}. {title}\n\n")
                    f.write(f"- **Categoría:** {category}\n")
                    f.write(f"- **Tipo:** {tipo}\n")
                    f.write(f"\n{content}...\n\n")
                    f.write("---\n\n")
                
                if analysis and analysis.get('tools_mentioned'):
                    f.write("## Herramientas Mentionadas\n\n")
                    for tool in analysis['tools_mentioned']:
                        f.write(f"- {tool}\n")
                    f.write("\n")
                
                if analysis and analysis.get('metrics'):
                    f.write("## Métricas Encontradas\n\n")
                    for metric in analysis['metrics']:
                        f.write(f"- {metric}\n")
                    f.write("\n")
                
                f.write(f"\n*Reporte generado automáticamente por KDP Master Search*\n")
            
            logger.info(f"Reporte generado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return None


class SearchSuggester:
    """
    MÓDULO 39: Sugerencia de Búsquedas Relacionadas
    Sugiere queries alternativas basadas en resultados.
    """
    
    def __init__(self):
        self.suggestions_cache = {}
    
    def suggest(self, query: str, results: List[Dict]) -> List[str]:
        """
        Sugiere búsquedas relacionadas.
        
        Returns:
            Lista de queries sugeridas
        """
        if not results:
            return []
        
        suggestions = set()
        
        categories = [r.get('category', '') for r in results]
        category_counter = Counter(categories)
        
        if category_counter:
            top_cat = category_counter.most_common(1)[0][0]
            suggestions.add(f"{query} {top_cat}")
        
        keywords = self._extract_keywords(results)
        for kw in keywords[:3]:
            suggestions.add(f"{query} {kw}")
        
        tipo = results[0].get('type', results[0].get('tipo', ''))
        if tipo:
            suggestions.add(f"{tipo.lower()} {query}")
        
        return list(suggestions)[:5]
    
    def _extract_keywords(self, results: List[Dict]) -> List[str]:
        """Extrae keywords de resultados."""
        all_words = []
        
        for r in results[:5]:
            content = r.get('content', r.get('content_preview', ''))
            words = content.split()
            
            for w in words:
                if 4 <= len(w) <= 20 and w.isalpha():
                    all_words.append(w.lower())
        
        word_counts = Counter(all_words)
        
        stopwords = {'que', 'del', 'para', 'con', 'los', 'las', 'una', 'este', 'esta', 
                     'por', 'como', 'más', 'pero', 'sus', 'ya', 'o', 'se', 'lo', 'más'}
        
        keywords = [w for w, c in word_counts.most_common(20) if w not in stopwords and c > 2]
        
        return keywords[:10]


class KnowledgeGapDetector:
    """
    MÓDULO 40: Alerta de Conocimiento Faltante
    Detecta lagunas en los resultados.
    """
    
    def __init__(self):
        self.known_gaps = []
    
    def detect_gaps(self, query: str, results: List[Dict]) -> List[str]:
        """
        Detecta qué información falta en los resultados.
        
        Returns:
            Lista de temas que no tienen cobertura
        """
        gaps = []
        
        expected_topics = {
            'ads': ['estrategia', 'presupuesto', 'bid', 'campaña'],
            'marketing': ['promoción', 'publicidad', 'canal'],
            'seo': ['palabras clave', 'ranking', 'optimización'],
            'pricing': ['precio', 'royalty', 'estrategia']
        }
        
        query_lower = query.lower()
        
        for topic, keywords in expected_topics.items():
            if topic in query_lower:
                for kw in keywords:
                    found = False
                    for r in results:
                        if kw in r.get('content', '').lower():
                            found = True
                            break
                    if not found:
                        gaps.append(f"{topic}_{kw}")
        
        return gaps
    
    def suggest_creation(self, gaps: List[str]) -> List[str]:
        """Sugiere crear contenido para llenar gaps."""
        suggestions = []
        
        gap_keywords = {
            'ads_estrategia': 'Crear nota sobre estrategias de Amazon Ads',
            'ads_presupuesto': 'Crear guía de presupuestos para campañas',
            'marketing_promoción': 'Crear manual de promociones para libros',
            'seo_palabras': 'Crear guía de selección de palabras clave',
        }
        
        for gap in gaps:
            if gap in gap_keywords:
                suggestions.append(gap_keywords[gap])
        
        return suggestions


class FAQGenerator:
    """
    MÓDULO 45: Generación de FAQs desde Resultados
    Crea preguntas frecuentes basadas en resultados.
    """
    
    def generate_faqs(self, results: List[Dict]) -> List[Dict]:
        """
        Genera FAQs desde resultados de búsqueda.
        
        Returns:
            Lista de preguntas y respuestas
        """
        faqs = []
        
        questions_patterns = [
            (r'qué es\s+([^\?]+)', r'¿Qué es \1?'),
            (r'cómo\s+([^\?]+)', r'¿Cómo \1?'),
            (r'cuál es\s+([^\?]+)', r'¿Cuál es \1?'),
        ]
        
        for r in results[:10]:
            content = r.get('content', '')
            
            for pattern, question_template in questions_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    subject = match.group(1).strip()[:50]
                    question = question_template.replace(r'\1', subject)
                    
                    answer_start = match.end()
                    answer = content[answer_start:answer_start + 200].strip()
                    
                    if answer:
                        faqs.append({
                            'question': question,
                            'answer': answer + '...',
                            'source': r.get('source', r.get('id', ''))
                        })
            
            if len(faqs) >= 10:
                break
        
        return faqs[:10]


class BestPracticeExtractor:
    """
    MÓDULO 46: Extracción de Best Practices
    Sintetiza mejores prácticas de resultados.
    """
    
    def extract(self, results: List[Dict]) -> List[str]:
        """
        Extrae mejores prácticas de los resultados.
        
        Returns:
            Lista de mejores prácticas
        """
        best_practices = []
        
        bp_keywords = [
            'recomiendo', 'mejor práctica', 'importante', 'clave', 'fundamental',
            'estrategia', 'optimizar', 'mejorar', 'incrementar', 'aumentar'
        ]
        
        for r in results[:10]:
            content = r.get('content', '')
            sentences = content.split('.')
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(kw in sentence.lower() for kw in bp_keywords):
                    if 30 < len(sentence) < 150:
                        best_practices.append(sentence)
        
        return best_practices[:10]


def get_ai_assistant(model: str = "llama3.1:8b") -> Dict:
    """Factory para obtener todos los asistentes."""
    return {
        'rag': RAGAssistant(model),
        'reporter': SearchReportGenerator(),
        'suggester': SearchSuggester(),
        'gap_detector': KnowledgeGapDetector(),
        'faq_generator': FAQGenerator(),
        'best_practice': BestPracticeExtractor()
    }