"""
KDP MASTER - AI Assistant Module
=================================
Módulos 37-48: Asistencia Inteligente y Automatización
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChatRAG:
    """
    MÓDULO 37: Chat sobre Resultados (RAG)
    Permite hacer preguntas sobre resultados encontrados.
    """
    
    def __init__(self, ollama_client=None):
        self.client = ollama_client
        
    def chat_about_results(self, question: str, results: List[Dict]) -> str:
        """Responde preguntas sobre los resultados de búsqueda."""
        if not self.client:
            return "Chat RAG no disponible (Ollama no conectado)"
        
        context = ""
        for i, r in enumerate(results[:5], 1):
            title = r.get('title', r.get('source', f'Result {i}'))
            content = r.get('content', '')[:500]
            context += f"\n--- Resultado {i}: {title} ---\n{content}\n"
        
        prompt = f"""Basándote en los siguientes resultados de búsqueda, responde la pregunta.
Si la respuesta no está en los resultados, indica que no tienes esa información.

RESULTADOS:
{context}

PREGUNTA: {question}

RESPUESTA:"""
        
        return self.client.generate_completion(prompt, max_tokens=400) or \
               "No puedo responder basada en los resultados actuales."


class SearchReportGenerator:
    """
    MÓDULO 38: Generación de Reporte de Búsqueda
    IA crea documento sintetizando resultados.
    """
    
    def generate_report(self, query: str, results: List[Dict], format: str = "md") -> str:
        """Genera reporte de búsqueda."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if format == "md":
            return self._generate_markdown_report(query, results, timestamp)
        elif format == "txt":
            return self._generate_text_report(query, results, timestamp)
        else:
            return self._generate_markdown_report(query, results, timestamp)
    
    def _generate_markdown_report(self, query: str, results: List[Dict], timestamp: str) -> str:
        """Genera reporte en formato Markdown."""
        report = f"""# Reporte de Búsqueda - KDP Master

**Fecha:** {timestamp}
**Query:** {query}
**Total de resultados:** {len(results)}

---

## Resumen

"""
        
        categories = {}
        for r in results:
            cat = r.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        report += "### Distribución por Categoría\n\n"
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{cat}**: {count} resultados\n"
        
        report += "\n## Resultados\n\n"
        
        for i, r in enumerate(results[:15], 1):
            title = r.get('title', r.get('source', f'Result {i}'))
            cat = r.get('category', 'Sin categoría')
            tipo = r.get('type', 'Artículo')
            date = r.get('date', 'N/A')
            content = r.get('content', '')[:300]
            
            report += f"""### {i}. {title}

- **Categoría:** {cat}
- **Tipo:** {tipo}
- **Fecha:** {date}

{content}...

---
"""
        
        return report
    
    def _generate_text_report(self, query: str, results: List[Dict], timestamp: str) -> str:
        """Genera reporte en formato texto."""
        report = f"""{'='*60}
REPORTE DE BÚSQUEDA - KDP MASTER
{'='*60}
Fecha: {timestamp}
Query: {query}
Total de resultados: {len(results)}
{'='*60}

RESUMEN
-------
"""
        
        categories = {}
        for r in results:
            cat = r.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            report += f"  {cat}: {count}\n"
        
        report += "\nRESULTADOS\n----------\n"
        
        for i, r in enumerate(results[:10], 1):
            title = r.get('title', r.get('source', f'Result {i}'))
            content = r.get('content', '')[:200]
            report += f"\n{i}. {title}\n{content}...\n"
        
        return report
    
    def save_report(self, query: str, results: List[Dict], filename: str = None) -> str:
        """Guarda reporte a archivo."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = query.replace(' ', '_')[:20]
            filename = f"reporte_busqueda_{safe_query}_{timestamp}.md"
        
        report = self.generate_report(query, results)
        
        base_path = os.path.expanduser("~/Documents/KDP_Master/reports")
        os.makedirs(base_path, exist_ok=True)
        
        filepath = os.path.join(base_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Reporte guardado: {filepath}")
        return filepath


class RelatedSearchSuggester:
    """
    MÓDULO 39: Sugerencia de Búsquedas Relacionadas
    IA sugiere queries alternativas.
    """
    
    def suggest_related(self, query: str, results: List[Dict]) -> List[str]:
        """Sugiere búsquedas relacionadas."""
        suggestions = []
        
        categories = set()
        for r in results:
            cat = r.get('category', '')
            if cat:
                categories.add(cat)
        
        query_lower = query.lower()
        
        if 'ads' in query_lower or 'publicidad' in query_lower:
            suggestions.extend(['Amazon Ads estrategia', 'Amazon Ads presupuesto', 'ACoS optimización'])
        
        if 'kdp' in query_lower or 'amazon' in query_lower:
            suggestions.extend(['KDP pricing', 'Kindle Unlimited', 'Amazon SEO keywords'])
        
        if 'marketing' in query_lower:
            suggestions.extend(['marketing digital libros', 'promoción KDP', 'estrategia lanzamiento'])
        
        if 'legal' in query_lower or 'compliance' in query_lower:
            suggestions.extend(['términos Amazon', 'derechos autor', 'ISBN requisito'])
        
        return suggestions[:6]


class KnowledgeGapDetector:
    """
    MÓDULO 40: Alerta de Conocimiento Faltante
    IA detecta lagunas en resultados.
    """
    
    EXPECTED_CATEGORIES = [
        'Amazon Ads', 'Amazon KDP', 'Amazon SEO', 'Legalidad y Compliance',
        'Marketing Digital', 'Kindle Unlimited', 'Pricing'
    ]
    
    def detect_gaps(self, results: List[Dict]) -> Dict:
        """Detecta categorías faltantes en resultados."""
        found_categories = set()
        for r in results:
            cat = r.get('category', '')
            if cat:
                found_categories.add(cat)
        
        missing = []
        for expected in self.EXPECTED_CATEGORIES:
            if expected not in found_categories:
                missing.append(expected)
        
        return {
            'has_gaps': len(missing) > 0,
            'missing_categories': missing,
            'message': f"Resultados no cubren: {', '.join(missing)}" if missing else "Resultados completos"
        }


class ReadingPrioritizer:
    """
    MÓDULO 41: Priorización de Lectura
    IA recomienda orden de lectura de resultados.
    """
    
    def prioritize(self, results: List[Dict]) -> List[Dict]:
        """Ordena resultados por prioridad de lectura."""
        prioritized = []
        
        for r in results:
            score = 0.0
            
            tipo = r.get('type', '').lower()
            if 'tutorial' in tipo:
                score += 0.3
            
            cat = r.get('category', '').lower()
            if 'ads' in cat or 'legal' in cat:
                score += 0.2
            
            words = r.get('words', 0)
            if 500 < words < 3000:
                score += 0.1
            
            date = r.get('date', '')
            if date:
                try:
                    if '2024' in date or '2025' in date:
                        score += 0.2
                except:
                    pass
            
            r['reading_priority_score'] = score
            prioritized.append(r)
        
        prioritized.sort(key=lambda x: x.get('reading_priority_score', 0), reverse=True)
        return prioritized


class CitationExtractor:
    """
    MÓDULO 42: Extracción de Citas para Referencia
    IA extrae fragmentos citables con fuente.
    """
    
    def extract_citations(self, results: List[Dict]) -> List[Dict]:
        """Extrae citas de los resultados."""
        citations = []
        
        for r in results:
            content = r.get('content', '')
            title = r.get('title', r.get('source', ''))
            category = r.get('category', '')
            
            sentences = content.split('.')
            for sentence in sentences[:3]:
                if 30 < len(sentence.strip()) < 150:
                    citations.append({
                        'text': sentence.strip(),
                        'source': title,
                        'category': category
                    })
        
        return citations[:20]


class VersionComparator:
    """
    MÓDULO 43: Comparación Automática de Versiones
    IA compara resultados de misma fuente diferente fecha.
    """
    
    def compare_versions(self, source: str, results: List[Dict]) -> Dict:
        """Compara versiones de contenido de la misma fuente."""
        source_results = [r for r in results if source.lower() in r.get('source', '').lower()]
        
        if len(source_results) < 2:
            return {'comparable': False, 'message': 'No hay suficientes versiones'}
        
        dates = []
        for r in source_results:
            date = r.get('date', '')
            if date:
                dates.append(date)
        
        dates.sort()
        
        if len(dates) >= 2:
            return {
                'comparable': True,
                'earliest': dates[0],
                'latest': dates[-1],
                'versions_found': len(dates),
                'note': f"Contenido actualizado desde {dates[0]} hasta {dates[-1]}"
            }
        
        return {'comparable': False, 'message': 'No se encontraron fechas'}


class TrendDetector:
    """
    MÓDULO 44: Detección de Tendencias en Resultados
    IA identifica patrones temporales.
    """
    
    def detect_trends(self, results: List[Dict]) -> Dict:
        """Detecta tendencias en los resultados."""
        years = {}
        
        for r in results:
            date = str(r.get('date', ''))
            year = date[:4] if len(date) >= 4 else 'Unknown'
            
            if year.isdigit():
                years[year] = years.get(year, 0) + 1
        
        if not years:
            return {'trend': 'unknown', 'message': 'Sin datos temporales'}
        
        sorted_years = sorted(years.items(), key=lambda x: x[0])
        
        if len(sorted_years) >= 2:
            recent = sorted_years[-1][0]
            older = sorted_years[0][0]
            
            if int(recent) - int(older) >= 2:
                return {
                    'trend': 'evolving',
                    'pattern': f"Evolución: {older} (teórico) → {recent} (práctico)",
                    'distribution': years
                }
        
        return {
            'trend': 'stable',
            'message': f"Distribución estable: {years}",
            'distribution': years
        }


class FAQGenerator:
    """
    MÓDULO 45: Generación de FAQs desde Resultados
    IA crea preguntas frecuentes basadas en resultados.
    """
    
    def generate_faqs(self, results: List[Dict]) -> List[Dict]:
        """Genera FAQs desde resultados."""
        faqs = []
        
        seen_questions = set()
        
        for r in results:
            content = r.get('content', '')
            title = r.get('title', '')
            
            questions = self._extract_potential_questions(content, title)
            
            for q in questions:
                if q not in seen_questions:
                    faqs.append({
                        'question': q,
                        'answer': r.get('content', '')[:200] + '...',
                        'source': title
                    })
                    seen_questions.add(q)
        
        return faqs[:10]
    
    def _extract_potential_questions(self, content: str, title: str) -> List[str]:
        """Extrae preguntas potenciales del contenido."""
        questions = []
        
        if 'cómo' in content.lower() or 'como' in content.lower():
            questions.append(f"¿Cómo {title.lower().replace('?', '')}?")
        
        if 'qué' in content.lower() or 'que es' in content.lower():
            questions.append(f"¿Qué es {title.lower().replace('?', '')}?")
        
        return questions


class BestPracticesExtractor:
    """
    MÓDULO 46: Extracción de Best Practices
    IA sintetiza mejores prácticas de resultados.
    """
    
    def extract_best_practices(self, results: List[Dict]) -> List[str]:
        """Extrae mejores prácticas de resultados."""
        practices = []
        
        keywords = ['mejor práctica', 'best practice', 'recomendación', 'sugieren', 'importante']
        
        for r in results:
            content = r.get('content', '')
            
            sentences = content.split('.')
            for sentence in sentences:
                if any(kw in sentence.lower() for kw in keywords):
                    if 30 < len(sentence.strip()) < 120:
                        practices.append(sentence.strip())
        
        return list(set(practices))[:10]


class InformationGapAnalyzer:
    """
    MÓDULO 47: Identificación de Gaps de Información
    IA detecta qué falta en resultados.
    """
    
    def analyze_gaps(self, query: str, results: List[Dict]) -> Dict:
        """Analiza gaps de información."""
        gaps = []
        
        content_lengths = [len(r.get('content', '')) for r in results]
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        if avg_length < 500:
            gaps.append("Contenido general sin profundidad")
        
        categories = set(r.get('category', '') for r in results)
        if len(categories) < 3:
            gaps.append("Poca diversidad de categorías")
        
        types = set(r.get('type', '') for r in results)
        if 'Tutorial' not in types and 'Caso' not in types:
            gaps.append("Faltan ejemplos prácticos")
        
        return {
            'has_gaps': len(gaps) > 0,
            'gaps': gaps,
            'summary': ' / '.join(gaps) if gaps else "Información completa"
        }


class PostSearchRecommender:
    """
    MÓDULO 48: Recomendación de Acciones Post-Búsqueda
    IA sugiere qué hacer con resultados.
    """
    
    def recommend_actions(self, results: List[Dict], query: str) -> List[Dict]:
        """Recomienda acciones después de la búsqueda."""
        actions = []
        
        if results:
            actions.append({
                'action': 'export',
                'label': 'Exportar a PDF',
                'description': 'Generar reporte profesional para compartir'
            })
            
            actions.append({
                'action': 'merge',
                'label': 'Fusionar en Manual',
                'description': 'Crear documento consolidado de conocimiento'
            })
        
        if len(results) > 5:
            actions.append({
                'action': 'deeper',
                'label': 'Profundizar en Tema',
                'description': f'Buscar más sobre: "{query} avanzado"'
            })
        
        categories = set(r.get('category', '') for r in results)
        if len(categories) > 1:
            actions.append({
                'action': 'explore',
                'label': 'Explorar Categorías',
                'description': f"Ver resultados en otras categorías: {', '.join(list(categories)[:2])}"
            })
        
        return actions