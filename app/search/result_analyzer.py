"""
KDP MASTER - Result Analyzer Module
====================================
Módulos 25-36: Análisis Cognitivo de Resultados
"""

import re
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResultSummarizer:
    """
    MÓDULO 25: Resumen Automático de Resultados
    IA genera resumen de top 10 resultados.
    """
    
    def summarize_results(self, results: List[Dict], top_n: int = 10) -> Dict:
        """Genera resumen de los primeros N resultados."""
        if not results:
            return {'summary': 'Sin resultados', 'topics': []}
        
        categories = Counter()
        types = Counter()
        content_samples = []
        
        for result in results[:top_n]:
            cat = result.get('category', 'Unknown')
            tipo = result.get('type', 'Artículo')
            content = result.get('content', '')[:200]
            
            categories[cat] += 1
            types[tipo] += 1
            content_samples.append(content)
        
        total = len(results[:top_n])
        
        topic_summary = []
        for cat, count in categories.most_common(3):
            percentage = (count / total * 100) if total > 0 else 0
            topic_summary.append(f"{cat} ({percentage:.0f}%)")
        
        return {
            'summary': f"Los {total} resultados cubren: {', '.join(topic_summary)}",
            'topics': list(categories.keys())[:5],
            'types_distribution': dict(types),
            'total_analyzed': total
        }


class KeyPointExtractor:
    """
    MÓDULO 26: Extracción de Key Points
    IA extrae puntos clave de cada resultado.
    """
    
    def extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """Extrae puntos clave del contenido."""
        if not content:
            return []
        
        sentences = re.split(r'[.!?\n]+', content)
        
        key_points = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                keywords = ['importante', 'clave', 'fundamental', 'recordar', 'nota',
                          'recuerda', 'atención', 'mejor', 'recomendado', 'tips']
                
                if any(kw in sentence.lower() for kw in keywords):
                    key_points.append(sentence)
        
        if not key_points and sentences:
            key_points = [s.strip() for s in sentences[:3] if len(s.strip()) > 30]
        
        return key_points[:max_points]


class ContradictionDetector:
    """
    MÓDULO 27: Detección de Contradicciones
    IA identifica resultados que se contradicen.
    """
    
    CONTRADICTION_PATTERNS = [
        ('sí', 'no'),
        ('recomiendo', 'no recomiendo'),
        ('funciona', 'no funciona'),
        ('mejor', 'peor'),
        ('importante', 'no importante'),
        ('obligatorio', 'opcional')
    ]
    
    def detect_contradictions(self, results: List[Dict]) -> List[Dict]:
        """Detecta contradicciones entre resultados."""
        contradictions = []
        
        content_by_category = defaultdict(list)
        for r in results:
            cat = r.get('category', 'Unknown')
            content_by_category[cat].append(r)
        
        for cat, cat_results in content_by_category.items():
            if len(cat_results) < 2:
                continue
            
            for i, r1 in enumerate(cat_results):
                for r2 in cat_results[i+1:]:
                    if self._has_contradiction(r1.get('content', ''), r2.get('content', '')):
                        contradictions.append({
                            'result_1': r1.get('title', r1.get('source', '')),
                            'result_2': r2.get('title', r2.get('source', '')),
                            'category': cat,
                            'severity': 'medium'
                        })
        
        return contradictions[:5]
    
    def _has_contradiction(self, text1: str, text2: str) -> bool:
        """Detecta si dos textos tienen contradicción."""
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for pos, neg in self.CONTRADICTION_PATTERNS:
            if (pos in text1_lower and neg in text2_lower) or \
               (pos in text2_lower and neg in text1_lower):
                return True
        
        return False


class ContentTypeClassifier:
    """
    MÓDULO 28: Clasificación de Tipo de Contenido
    IA etiqueta resultados como tutorial, teoría, caso, herramienta.
    """
    
    TYPE_PATTERNS = {
        'tutorial': ['cómo', 'tutorial', 'guía paso', 'instrucciones', 'aprender', 'enseñar'],
        'teoria': ['concepto', 'teoría', 'explicación', 'porque', 'razón', 'fundamento'],
        'caso': ['caso de estudio', 'ejemplo', 'ejemplo real', 'experiencia', 'resultado'],
        'herramienta': ['herramienta', 'software', 'app', 'plataforma', 'recurso'],
        'opinion': ['opinión', 'considero', 'pienso', 'recomiendo', 'mejor opción']
    }
    
    def classify(self, content: str, title: str = "") -> str:
        """Clasifica tipo de contenido."""
        text = f"{title} {content}".lower()
        
        scores = {}
        for content_type, patterns in self.TYPE_PATTERNS.items():
            score = sum(1 for p in patterns if p in text)
            scores[content_type] = score
        
        if max(scores.values()) == 0:
            return 'general'
        
        return max(scores.items(), key=lambda x: x[1])[0]


class FreshnessScorer:
    """
    MÓDULO 29: Score de Actualidad
    IA evalúa si contenido está actualizado u obsoleto.
    """
    
    def calculate_freshness(self, content: str, date_str: str) -> Dict:
        """Calcula score de actualidad del contenido."""
        score = 0.5
        status = "actualizado"
        issues = []
        
        try:
            if len(date_str) == 10:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                days_ago = (datetime.now() - date).days
                
                if days_ago <= 90:
                    score = 1.0
                elif days_ago <= 180:
                    score = 0.8
                elif days_ago <= 365:
                    score = 0.6
                else:
                    score = 0.4
                    status = "puede estar obsoleto"
                    issues.append(f"Contenido de hace {days_ago//30} meses")
        except:
            pass
        
        old_keywords = ['2020', '2021', '2022', 'antiguo', 'obsoleto', 'deprecated']
        if any(kw in content.lower() for kw in old_keywords):
            score *= 0.7
            issues.append("Menciona fechas antiguas")
        
        return {
            'freshness_score': score,
            'status': status,
            'issues': issues,
            'date': date_str
        }


class DuplicateDetector:
    """
    MÓDULO 30: Detección de Duplicados Conceptuales
    IA encuentra resultados que dicen lo mismo.
    """
    
    def find_duplicates(self, results: List[Dict], threshold: float = 0.9) -> List[Dict]:
        """Encuentra resultados duplicados conceptualmente."""
        duplicates = []
        
        for i, r1 in enumerate(results):
            for r2 in results[i+1:]:
                similarity = self._calculate_similarity(
                    r1.get('content', ''),
                    r2.get('content', '')
                )
                
                if similarity >= threshold:
                    duplicates.append({
                        'result_1': r1.get('title', r1.get('source', '')),
                        'result_2': r2.get('title', r2.get('source', '')),
                        'similarity': similarity
                    })
        
        return duplicates[:10]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre textos."""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0


class MetricsExtractor:
    """
    MÓDULO 31: Extracción de Métricas/KPIs Mencionados
    IA extrae números, porcentajes, fechas de resultados.
    """
    
    def extract_metrics(self, content: str) -> List[Dict]:
        """Extrae métricas mencionadas en el contenido."""
        metrics = []
        
        percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
        for match in re.finditer(percentage_pattern, content):
            metrics.append({
                'type': 'percentage',
                'value': match.group(1),
                'context': content[max(0, match.start()-20):match.end()+20]
            })
        
        number_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:dólares|usd|€|euros|unidades|ventas|clics|impresiones)'
        for match in re.finditer(number_pattern, content, re.IGNORECASE):
            metrics.append({
                'type': 'currency' if 'dól' in match.group().lower() or 'usd' in match.group().lower() or '€' in match.group() else 'number',
                'value': match.group(1),
                'context': content[max(0, match.start()-20):match.end()+20]
            })
        
        return metrics[:10]


class ToolsMentionExtractor:
    """
    MÓDULO 32: Identificación de Herramientas Mencionadas
    IA lista software/plataformas citadas.
    """
    
    KNOWN_TOOLS = [
        'helium 10', 'jungle scout', 'publisher rocket', 'kindle inspector',
        'kobo', 'draft2digital', 'calibre', 'canva', 'adobe', 'word',
        'excel', 'google docs', 'grammarly', 'chatgpt', 'ollama',
        'youtube', 'vimeo', 'OBS', 'ffmpeg'
    ]
    
    def extract_tools(self, content: str) -> List[str]:
        """Extrae herramientas mencionadas."""
        content_lower = content.lower()
        
        found_tools = []
        for tool in self.KNOWN_TOOLS:
            if tool in content_lower:
                found_tools.append(tool.title())
        
        return list(set(found_tools))


class SentimentAnalyzer:
    """
    MÓDULO 33: Análisis de Sentimiento de Resultados
    IA evalúa si contenido es positivo/negativo/neutral.
    """
    
    POSITIVE_WORDS = ['excelente', 'bueno', 'recomiendo', 'mejor', 'efectivo', 'útil', 'funciona']
    NEGATIVE_WORDS = ['malo', 'no funciona', 'problema', 'error', 'fallo', 'cuidado', 'evitar']
    
    def analyze_sentiment(self, content: str) -> Dict:
        """Analiza sentimiento del contenido."""
        content_lower = content.lower()
        
        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in content_lower)
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in content_lower)
        
        if pos_count > neg_count:
            sentiment = 'positive'
        elif neg_count > pos_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'positive_score': pos_count,
            'negative_score': neg_count,
            'neutral': pos_count == neg_count
        }


class ExpertiseLevelDetector:
    """
    MÓDULO 34: Detección de Nivel de Expertiz
    IA clasifica como básico/intermedio/avanzado.
    """
    
    def detect_level(self, content: str, title: str = "") -> str:
        """Detecta nivel de expertise del contenido."""
        text = f"{title} {content}".lower()
        
        basic_keywords = ['qué es', 'introducción', 'básico', 'para principiantes', 'empezar']
        intermediate_keywords = ['cómo', 'tutorial', 'estrategia', 'optimizar', 'mejorar']
        advanced_keywords = ['avanzado', 'experto', 'optimización', 'automatización', 'inteligencia']
        
        basic_count = sum(1 for k in basic_keywords if k in text)
        intermediate_count = sum(1 for k in intermediate_keywords if k in text)
        advanced_count = sum(1 for k in advanced_keywords if k in text)
        
        if advanced_count > 0:
            return 'avanzado'
        elif basic_count > 0:
            return 'básico'
        elif intermediate_count > 0:
            return 'intermedio'
        
        return 'general'


class ActionableExtractor:
    """
    MÓDULO 35: Extracción de Acciones Accionables
    IA identifica pasos concretos en resultados.
    """
    
    def extract_actions(self, content: str) -> List[str]:
        """Extrae acciones concreteas del contenido."""
        actions = []
        
        steps = re.findall(r'(?:^\d+[.)\])|(?:^[-•]\s))(.+)', content, re.MULTILINE)
        
        for step in steps:
            if len(step.strip()) > 10 and len(step.strip()) < 150:
                actions.append(step.strip())
        
        if not actions:
            action_verbs = ['crear', 'configurar', 'optimizar', 'implementar', 'usar', 'establecer']
            sentences = content.split('.')
            
            for sentence in sentences:
                if any(verb in sentence.lower() for verb in action_verbs):
                    if 20 < len(sentence.strip()) < 120:
                        actions.append(sentence.strip())
        
        return actions[:7]


class ConceptMapGenerator:
    """
    MÓDULO 36: Mapa Conceptual de Resultados
    IA genera gráfico de relaciones entre resultados.
    """
    
    def generate_map(self, results: List[Dict]) -> Dict:
        """Genera mapa conceptual de resultados."""
        nodes = []
        links = []
        
        for i, result in enumerate(results[:15]):
            nodes.append({
                'id': i,
                'label': result.get('title', result.get('source', f'Result {i}'))[:30],
                'category': result.get('category', 'Unknown'),
                'type': result.get('type', 'Artículo')
            })
        
        categories = defaultdict(list)
        for i, node in enumerate(nodes):
            categories[node['category']].append(i)
        
        for cat, indices in categories.items():
            if len(indices) > 1:
                for j in range(len(indices) - 1):
                    links.append({
                        'source': indices[j],
                        'target': indices[j+1],
                        'type': 'same_category'
                    })
        
        return {
            'nodes': nodes,
            'links': links,
            'categories': list(categories.keys())
        }