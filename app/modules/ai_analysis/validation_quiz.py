"""
AI Analysis - Validation Quiz Generator
=======================================
Módulo 38: Genera preguntas de validación para verificar comprensión.
Usa Ollama para crear quizzes de 3 preguntas.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correct_answer: int
    explanation: str
    difficulty: str
    topic: str


@dataclass
class QuizResult:
    questions: List[QuizQuestion]
    total_questions: int
    estimated_time_minutes: float
    topics_covered: List[str]


class ValidationQuizGenerator:
    """
    Generador de quizzes de validación.
    Crea 3 preguntas para verificar comprensión.
    """

    QUESTION_TEMPLATES = [
        {
            'pattern': r'¿Cu[áa]l\s+es',
            'type': 'multiple_choice',
            'difficulty': 'medium'
        },
        {
            'pattern': r'^El\s+principal',
            'type': 'true_false',
            'difficulty': 'easy'
        },
        {
            'pattern': r'¿Por\s+qu[ée]',
            'type': 'open',
            'difficulty': 'hard'
        },
        {
            'pattern': r'^Complete',
            'type': 'fill_blank',
            'difficulty': 'medium'
        }
    ]

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(self, text: str, num_questions: int = 3, difficulty: Optional[str] = None) -> QuizResult:
        """
        Genera quiz de validación.

        Args:
            text: Texto fuente para el quiz
            num_questions: Número de preguntas (default 3)
            difficulty: Dificultad (easy, medium, hard)

        Returns:
            QuizResult con preguntas generadas
        """
        if self.ai_client and self.ai_client.is_available():
            return self._generate_with_ai(text, num_questions, difficulty)
        return self._generate_fallback(text, num_questions, difficulty)

    def _generate_with_ai(self, text: str, num_questions: int, difficulty: Optional[str]) -> QuizResult:
        """Genera usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "quiz")
            if result.success:
                parsed = result.metadata
                questions = []

                for q_data in parsed.get('questions', []):
                    questions.append(QuizQuestion(
                        question=q_data.get('q', ''),
                        options=q_data.get('options', []),
                        correct_answer=q_data.get('correct', 0),
                        explanation=q_data.get('explanation', ''),
                        difficulty=q_data.get('difficulty', 'medium'),
                        topic=q_data.get('topic', 'general')
                    ))

                return QuizResult(
                    questions=questions,
                    total_questions=len(questions),
                    estimated_time_minutes=len(questions) * 1.5,
                    topics_covered=list(set(q.topic for q in questions))
                )
        except Exception as e:
            logger.warning(f"AI quiz generation failed: {e}")
        return self._generate_fallback(text, num_questions, difficulty)

    def _generate_fallback(self, text: str, num_questions: int, difficulty: Optional[str]) -> QuizResult:
        """Genera usando heurísticas."""
        key_concepts = self._extract_key_concepts(text)
        facts = self._extract_facts(text)

        questions = []

        if key_concepts:
            concept = random.choice(key_concepts)
            questions.append(QuizQuestion(
                question=f"¿Cuál es el concepto principal descrito en el texto?",
                options=self._create_options(concept, key_concepts[:3]),
                correct_answer=0,
                explanation=f"El concepto principal es: {concept}",
                difficulty='medium',
                topic='conceptual'
            ))

        if len(questions) < num_questions and facts:
            fact = random.choice(facts[:3])
            questions.append(QuizQuestion(
                question=f"Según el texto, ¿cuál de las siguientes afirmaciones es correcta?",
                options=self._create_options(fact, facts[:3]),
                correct_answer=0,
                explanation=f"Hecho extraído: {fact}",
                difficulty='easy',
                topic='factual'
            ))

        if len(questions) < num_questions:
            steps = self._extract_steps(text)
            if steps:
                questions.append(QuizQuestion(
                    question=f"¿Cuál es el primer paso mencionado para lograr el objetivo?",
                    options=[steps[0]] + [f"Paso {i+2}: {s[:50]}..." for i, s in enumerate(steps[1:3])],
                    correct_answer=0,
                    explanation=f"El primer paso es: {steps[0]}",
                    difficulty='medium',
                    topic='procedural'
                ))

        while len(questions) < num_questions:
            questions.append(QuizQuestion(
                question="¿El contenido proporciona información útil para el objetivo descrito?",
                options=["Sí, es muy relevante", "Parcialmente relevante", "Poco relevante", "No es relevante"],
                correct_answer=0,
                explanation="El quiz sirve para verificar comprensión general",
                difficulty='easy',
                topic='general'
            ))

        return QuizResult(
            questions=questions[:num_questions],
            total_questions=len(questions[:num_questions]),
            estimated_time_minutes=num_questions * 1.5,
            topics_covered=list(set(q.topic for q in questions))
        )

    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extrae conceptos clave."""
        patterns = [
            r'(?:concepto|principio|idea|estrategia|modelo|framework)\s+(?:de|principal|clave)\s+(.{10,40}?)(?:\.|,)',
            r'(?:el|la)\s+([A-Z][a-z]+(?:\s+[a-z]+)?)\s+(?:es|se\s+refiere\s+a|consiste\s+en)',
            r'^.*:\s*([A-Z][a-z]+(?:\s+[a-z]+){0,2})'
        ]

        concepts = []
        for p in patterns:
            matches = re.findall(p, text, re.MULTILINE)
            concepts.extend([m.strip() for m in matches if len(m) > 3])

        return list(dict.fromkeys(concepts))[:5]

    def _extract_facts(self, text: str) -> List[str]:
        """Extrae hechos del texto."""
        facts = []

        stat_patterns = [
            r'\d+(?:\.\d+)?\s*(?:%|mil|millones?|horas?|d[íi]as?|usuarios?|clientes?)',
            r'(?:aumento|reducc[íi]on|incremento|decrecimiento)\s+del\s+\d+%',
            r'(?:primero|segundo|tercero|final)\s+(?:paso|lugar|elemento|component)',
        ]

        for p in stat_patterns:
            matches = re.findall(p, text, re.IGNORECASE)
            facts.extend(matches)

        return facts[:5]

    def _extract_steps(self, text: str) -> List[str]:
        """Extrae pasos del texto."""
        steps = []

        step_patterns = [
            r'(?:pasos?|etapas?|fases?)\s+\d+:?\s*(.{20,80}?)(?:\.|$)',
            r'(?:primero|segundo|tercero|finalmente)\s*,?\s*(?:deber[íi]as?|hay\s+que|importante)\s+(.{20,60}?)(?:\.|$)',
            r'\d+\.\s*(.{20,80}?)(?:\.|$)'
        ]

        for p in step_patterns:
            matches = re.findall(p, text, re.IGNORECASE | re.MULTILINE)
            steps.extend([m.strip() for m in matches if len(m) > 10])

        return steps[:4]

    def _create_options(self, correct: str, alternatives: List[str]) -> List[str]:
        """Crea opciones de respuesta."""
        options = [correct]

        for alt in alternatives[:3]:
            if alt != correct and len(options) < 4:
                options.append(alt)

        while len(options) < 4:
            options.append("Otra afirmación no mencionada")

        random.shuffle(options)
        return options

    def batch_generate(self, texts: List[str]) -> List[QuizResult]:
        """Genera quizzes para múltiples textos."""
        return [self.generate(t) for t in texts]

    def export_quiz(self, quiz: QuizResult, format: str = 'markdown') -> str:
        """Exporta quiz a formato específico."""
        if format == 'markdown':
            lines = [f"# Quiz de Validación ({quiz.total_questions} preguntas)\n"]
            lines.append(f"Tiempo estimado: {quiz.estimated_time_minutes} minutos\n")
            lines.append(f"Temas: {', '.join(quiz.topics_covered)}\n\n")

            for i, q in enumerate(quiz.questions, 1):
                lines.append(f"## Pregunta {i} [{q.difficulty}]\n")
                lines.append(f"**{q.question}**\n\n")
                for j, opt in enumerate(q.options, 1):
                    marker = " ✅" if j == q.correct_answer + 1 else ""
                    lines.append(f"{j}. {opt}{marker}\n")
                lines.append(f"\n*Explicación: {q.explanation}*\n\n")

            return '\n'.join(lines)

        return str(quiz)