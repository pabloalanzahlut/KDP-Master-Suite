"""
KDP MASTER - Result Analyzer Module
====================================
Módulos 25-36: Análisis Cognitivo de Resultados
Resumen, key points, contradicciones, clasificación, scoring.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    summary: str
    key_points: List[str]
    contradictions: List[Dict]
    content_type: str
    is_current: bool
    duplicate_group: Optional[int]
    metrics: List[str]
    tools_mentioned: List[str]
    sentiment: str
    expertise_level: str
    actionable_steps: List[str]


class ResultAnalyzer:
    """
    Analizador cognitivo de resultados de búsqueda.
    """
    
    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        logger.info("ResultAnalyzer inicializado")
    
    def analyze_results(self, results: List[Dict], query: str = None) -> Dict:
        """
        MÓDULOS 25-36: Análisis completo de resultados.
        
        Returns:
            Diccionario con análisis detallado
        """
        if not results:
            return self._empty_analysis()
        
        summary = self._generate_summary(results, query)
        
        key_points = self._extract_key_points(results)
        
        contradictions = self._detect_contradictions(results)
        
        content_types = self._classify_content_types(results)
        
        is_current = self._check_actuality(results)
        
        duplicates = self._detect_duplicates(results)
        
        metrics = self._extract_metrics(results)
        
        tools = self._identify_tools(results)
        
        sentiment = self._analyze_sentiment(results)
        
        expertise = self._detect_expertise_level(results)
        
        actions = self._extract_actionable_steps(results)
        
        return {
            'summary': summary,
            'key_points': key_points,
            'contradictions': contradictions,
            'content_types': content_types,
            'is_current': is_current,
            'duplicates': duplicates,
            'metrics': metrics,
            'tools_mentioned': tools,
            'sentiment': sentiment,
            'expertise_level': expertise,
            'actionable_steps': actions,
            'total_analyzed': len(results)
        }
    
    def _empty_analysis(self) -> Dict:
        return {
            'summary': 'Sin resultados para analizar.',
            'key_points': [],
            'contradictions': [],
            'content_types': {},
            'is_current': True,
            'duplicates': [],
            'metrics': [],
            'tools_mentioned': [],
            'sentiment': 'neutral',
            'expertise_level': 'unknown',
            'actionable_steps': []
        }
    
    def _generate_summary(self, results: List[Dict], query: str = None) -> str:
        """
        MÓDULO 25: Resumen Automático de Resultados
        Genera resumen de los top resultados.
        """
        if not results:
            return "Sin resultados."
        
        type_counts = Counter()
        category_counts = Counter()
        
        for r in results:
            tipo = r.get('type', r.get('tipo', 'Artículo'))
            type_counts[tipo] += 1
            
            cat = r.get('category', 'Sin categoría')
            category_counts[cat] += 1
        
        total = len(results)
        summary_parts = []
        
        if type_counts:
            top_type = type_counts.most_common(1)[0]
            summary_parts.append(f"{top_type[0]} ({top_type[1]})")
        
        if category_counts:
            top_cat = category_counts.most_common(1)[0]
            summary_parts.append(f"en {top_cat[0]} ({top_cat[1]})")
        
        return f"Encontrados {total} resultados: {', '.join(summary_parts)}. Los resultados cubren principalmente: " + \
               ", ".join([f"{c[0]} ({c[1]})" for c in category_counts.most_common(3)])
    
    def _extract_key_points(self, results: List[Dict]) -> List[str]:
        """
        MÓDULO 26: Extracción de Puntos Clave
        Extrae puntos clave de cada resultado.
        """
        key_points = []
        
        patterns = [
            r'^\d+\.\s+(.+)',
            r'•\s+(.+)',
            r'-\s+(.+)',
            r'[:;]\s*([A-Z][^.!?]+)',
        ]
        
        for r in results[:5]:
            content = r.get('content', r.get('content_preview', ''))
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches[:2]:
                    point = match.strip() if isinstance(match, str) else match[0].strip()
                    if 20 < len(point) < 150:
                        key_points.append(point)
                        
                        if len(key_points) >= 10:
                            return key_points
        
        return key_points[:10]
    
    def _detect_contradictions(self, results: List[Dict]) -> List[Dict]:
        """
        MÓDULO 27: Detección de Contradicciones
        Identifica resultados que se contradicen.
        """
        contradictions = []
        
        keywords_neg = ['no', 'nunca', 'nada', 'ninguno', 'negativo', 'malo', 'error', 'problema']
        keywords_pos = ['sí', 'siempre', 'todo', 'positivo', 'bueno', 'éxito', 'recomiendo']
        
        for i, r1 in enumerate(results[:5]):
            for j, r2 in enumerate(results[i+1:5], i+1):
                content1 = r1.get('content', '')[:500].lower()
                content2 = r2.get('content', '')[:500].lower()
                
                neg1 = sum(1 for k in keywords_neg if k in content1)
                pos1 = sum(1 for k in keywords_pos if k in content1)
                
                neg2 = sum(1 for k in keywords_neg if k in content2)
                pos2 = sum(1 for k in keywords_pos if k in content2)
                
                if (neg1 > pos1 and pos2 > neg2) or (pos1 > neg1 and neg2 > pos2):
                    contradictions.append({
                        'result_1': r1.get('source', r1.get('id', 'Doc 1')),
                        'result_2': r2.get('source', r2.get('id', 'Doc 2')),
                        'type': 'opposing_views'
                    })
        
        return contradictions
    
    def _classify_content_types(self, results: List[Dict]) -> Dict:
        """
        MÓDULO 28: Clasificación de Tipo de Contenido
        Etiqueta resultados como tutorial, teoría, caso, herramienta.
        """
        type_counts = {
            'tutorial': 0,
            'theory': 0,
            'case_study': 0,
            'tool': 0,
            'news': 0,
            'opinion': 0
        }
        
        for r in results:
            content = r.get('content', r.get('content_preview', '')).lower()
            
            if any(k in content for k in ['cómo', 'tutorial', 'guía paso', 'instrucciones']):
                type_counts['tutorial'] += 1
            elif any(k in content for k in ['investigación', 'estudio', 'datos', 'estadística']):
                type_counts['theory'] += 1
            elif any(k in content for k in ['caso de', 'ejemplo real', 'experiencia']):
                type_counts['case_study'] += 1
            elif any(k in content for k in ['herramienta', 'software', 'app', 'servicio']):
                type_counts['tool'] += 1
            elif any(k in content for k in ['noticia', 'actualización', 'nuevo']):
                type_counts['news'] += 1
            elif any(k in content for k in ['opinión', 'considero', 'creo que']):
                type_counts['opinion'] += 1
        
        return type_counts
    
    def _check_actuality(self, results: List[Dict]) -> bool:
        """
        MÓDULO 29: Score de Actualidad
        Evalúa si el contenido está actualizado.
        """
        current_year = 2026
        
        outdated = 0
        for r in results:
            date_str = str(r.get('timestamp', ''))
            
            if date_str:
                try:
                    if '2020' in date_str or '2019' in date_str:
                        outdated += 1
                    elif '2021' in date_str or '2022' in date_str:
                        outdated += 0.5
                except:
                    pass
        
        return outdated < len(results) * 0.3
    
    def _detect_duplicates(self, results: List[Dict]) -> List[Dict]:
        """
        MÓDULO 30: Detección de Duplicados Conceptuales
        Encuentra resultados con >90% similitud.
        """
        duplicates = []
        
        for i, r1 in enumerate(results[:10]):
            for j, r2 in enumerate(results[i+1:10], i+1):
                content1 = r1.get('content', '')[:200].lower()
                content2 = r2.get('content', '')[:200].lower()
                
                words1 = set(content1.split())
                words2 = set(content2.split())
                
                if words1 and words2:
                    similarity = len(words1 & words2) / len(words1 | words2)
                    
                    if similarity > 0.7:
                        duplicates.append({
                            'group': i,
                            'docs': [r1.get('id'), r2.get('id')],
                            'similarity': round(similarity, 2)
                        })
        
        return duplicates
    
    def _extract_metrics(self, results: List[Dict]) -> List[str]:
        """
        MÓDULO 31: Extracción de Métricas/KPIs
        Extrae números, porcentajes, fechas mencionadas.
        """
        metrics = []
        
        patterns = [
            r'\d+%', r'\d+\.\d+%',
            r'\$\d+', r'\$\d+\.\d+',
            r'\d+k\b', r'\d+m\b',
            r'CTR\s*\d+%', r'ACoS\s*\d+%',
            r'BSR\s*#?\d+',
        ]
        
        for r in results[:5]:
            content = r.get('content', '')
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match not in metrics:
                        metrics.append(match)
        
        return list(set(metrics))[:10]
    
    def _identify_tools(self, results: List[Dict]) -> List[str]:
        """
        MÓDULO 32: Identificación de Herramientas Mencionadas
        Lista software/plataformas citadas.
        """
        tools = []
        
        tool_names = [
            'Helium 10', 'Jungle Scout', 'KDP', 'Kindle', 'Amazon',
            'Canva', 'ChatGPT', 'Python', 'Excel', 'Google',
            'Publisher Rocket', 'KeywordSpy', 'MerchantWords'
        ]
        
        for r in results:
            content = r.get('content', '').lower()
            
            for tool in tool_names:
                if tool.lower() in content and tool not in tools:
                    tools.append(tool)
        
        return tools[:10]
    
    def _analyze_sentiment(self, results: List[Dict]) -> str:
        """
        MÓDULO 33: Análisis de Sentimiento
        Evalúa tono general del contenido.
        """
        positive_words = ['excelente', 'recomiendo', 'éxito', 'mejor', 'positivo', 'útil', 'importante']
        negative_words = ['error', 'problema', 'mal', 'peor', 'negativo', 'cuidado', 'precaución']
        neutral_words = ['información', 'datos', 'resultados', 'método', 'proceso']
        
        pos_count = neg_count = neu_count = 0
        
        for r in results:
            content = r.get('content', '').lower()
            pos_count += sum(1 for w in positive_words if w in content)
            neg_count += sum(1 for w in negative_words if w in content)
            neu_count += sum(1 for w in neutral_words if w in content)
        
        if pos_count > neg_count and pos_count > neu_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _detect_expertise_level(self, results: List[Dict]) -> str:
        """
        MÓDULO 34: Detección de Nivel de Expertiz
        Clasifica como básico/intermedio/avanzado.
        """
        basic_keywords = ['introducción', 'básico', 'para principiantes', 'qué es', 'conceptos']
        advanced_keywords = ['avanzado', 'experto', 'optimización', 'estrategia avanzada', 'implementación']
        
        basic_score = advanced_score = 0
        
        for r in results:
            content = r.get('content', '').lower()
            
            basic_score += sum(1 for k in basic_keywords if k in content)
            advanced_score += sum(1 for k in advanced_keywords if k in content)
        
        if advanced_score > basic_score:
            return 'advanced'
        elif basic_score > advanced_score:
            return 'basic'
        else:
            return 'intermediate'
    
    def _extract_actionable_steps(self, results: List[Dict]) -> List[str]:
        """
        MÓDULO 35: Extracción de Acciones Accionables
        Identifica pasos concretos en resultados.
        """
        steps = []
        
        step_patterns = [
            r'(\d+)\.\s*([A-Z][^.!?]{20,80})',
            r'primer[oa]\s+([A-Z][^.!?]{20,60})',
            r'paso\s+(\d+)\s*[:\-]?\s*([A-Z][^.!?]{20,60})',
            r'configura[r]?\s+([A-Z][^.!?]{20,60})',
            r'crea[r]?\s+([A-Z][^.!?]{20,60})',
        ]
        
        for r in results[:3]:
            content = r.get('content', '')
            
            for pattern in step_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    step = match[-1] if isinstance(match, tuple) else match
                    step = step.strip()
                    if 20 < len(step) < 80:
                        steps.append(step)
        
        return steps[:5]


def get_result_analyzer(model: str = "llama3.1:8b") -> ResultAnalyzer:
    """Factory para obtener el analizador de resultados."""
    return ResultAnalyzer(model)