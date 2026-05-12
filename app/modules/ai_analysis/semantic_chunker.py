"""
AI Analysis - Módulo 23: Chunker Inteligente para Ventanas de Contexto
====================================================================
Divide el texto en segmentos óptimos para prompts de Ollama (por ideas,
no por caracteres) respetando coherencia temática.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    chunks: List[str]
    chunk_count: int
    avg_chunk_size: int
    coherence_score: float
    boundaries: List[int]


class SemanticChunker:
    """
    Chunker Inteligente para Ventanas de Contexto
    Divide texto en segmentos óptimos por ideas, no caracteres.
    """

    IDEAL_CHUNK_SIZE = 500
    MIN_CHUNK_SIZE = 100
    MAX_CHUNK_SIZE = 1000

    BOUNDARY_PATTERNS = [
        r'\n\n+',
        r'\.\s+[A-Z]',
        r'\?\s+[A-Z]',
        r'!\s+[A-Z]',
        r';\s+[A-Z]',
    ]

    SECTION_PATTERNS = [
        r'^#{1,6}\s+',
        r'^\d+\.\s+',
        r'^\-\s+',
        r'^\*\s+',
        r'^•\s+',
    ]

    def __init__(self, ai_client=None):
        self._ai_client = ai_client
        self._stats = {
            'total_chunked': 0,
            'total_chunks': 0,
            'avg_coherence': 0.0
        }

    def chunk(
        self,
        text: str,
        max_tokens: int = 500,
        overlap: int = 50
    ) -> ChunkResult:
        """
        Divide texto en chunks semánticamente coherentes.

        Args:
            text: Texto a dividir
            max_tokens: Tamaño máximo por chunk (en palabras)
            overlap: Superposición entre chunks

        Returns:
            ChunkResult con chunks y metadatos
        """
        self._stats['total_chunked'] += 1

        ai_chunks = None
        if self._ai_client and self._ai_client.is_available():
            result = self._ai_client.analyze(text, "chunk")
            if result.success:
                ai_chunks = result.metadata.get('chunks', None)

        if ai_chunks:
            chunks = ai_chunks
        else:
            chunks = self._local_chunk(text, max_tokens)

        if overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks, overlap)

        boundaries = self._find_boundaries(chunks, text)
        coherence = self._calculate_coherence(chunks)

        self._stats['total_chunks'] += len(chunks)
        self._stats['avg_coherence'] = (
            (self._stats['avg_coherence'] * (self._stats['total_chunked'] - 1) + coherence) /
            self._stats['total_chunked']
        )

        avg_size = sum(len(c.split()) for c in chunks) / max(len(chunks), 1)

        return ChunkResult(
            chunks=chunks,
            chunk_count=len(chunks),
            avg_chunk_size=int(avg_size),
            coherence_score=coherence,
            boundaries=boundaries
        )

    def _local_chunk(self, text: str, max_tokens: int) -> List[str]:
        """Chunking local sin IA."""
        paragraphs = self._split_paragraphs(text)

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_words = len(para.split())

            if current_size + para_words > max_tokens and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            if para_words > max_tokens:
                sub_chunks = self._split_long_paragraph(para, max_tokens)
                chunks.extend(sub_chunks[:-1] if len(sub_chunks) > 1 else [])
                if sub_chunks:
                    current_chunk.append(sub_chunks[-1])
                    current_size = len(sub_chunks[-1].split())
            else:
                current_chunk.append(para)
                current_size += para_words

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [text]

    def _split_paragraphs(self, text: str) -> List[str]:
        """Separa párrafos."""
        parts = re.split(r'\n\s*\n', text)
        return [p.strip() for p in parts if p.strip()]

    def _split_long_paragraph(self, text: str, max_tokens: int) -> List[str]:
        """Divide párrafo largo en sub-chunks."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sub_chunks = []
        current = []
        current_size = 0

        for sent in sentences:
            sent_words = len(sent.split())
            if current_size + sent_words > max_tokens and current:
                sub_chunks.append(' '.join(current))
                current = []
                current_size = 0

            current.append(sent)
            current_size += sent_words

        if current:
            sub_chunks.append(' '.join(current))

        return sub_chunks if sub_chunks else [text]

    def _add_overlap(self, chunks: List[str], overlap: int) -> List[str]:
        """Añade superposición entre chunks."""
        if len(chunks) <= 1:
            return chunks

        overlapped = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_words = chunks[i - 1].split()[-overlap:]
            overlap_text = ' '.join(prev_words)
            chunks[i] = f"{overlap_text} {chunks[i]}"
            overlapped.append(chunks[i])

        return overlapped

    def _find_boundaries(self, chunks: List[str], original: str) -> List[int]:
        """Encuentra posiciones de límites en texto original."""
        boundaries = []
        pos = 0

        for chunk in chunks:
            found = original.find(chunk, pos)
            if found >= 0:
                boundaries.append(found)
                pos = found + len(chunk)
            else:
                boundaries.append(pos)
                pos += len(chunk)

        return boundaries

    def _calculate_coherence(self, chunks: List[str]) -> float:
        """Calcula score de coherencia entre chunks."""
        if len(chunks) <= 1:
            return 1.0

        coherence_scores = []
        for i in range(len(chunks) - 1):
            current_words = set(chunks[i].lower().split())
            next_words = set(chunks[i + 1].lower().split())

            intersection = current_words & next_words
            union = current_words | next_words

            if union:
                jaccard = len(intersection) / len(union)
                coherence_scores.append(jaccard)

        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.5

    def optimize_for_ollama(
        self,
        text: str,
        model_max_tokens: int = 4000
    ) -> List[str]:
        """
        Optimiza texto para modelo Ollama específico.

        Args:
            text: Texto a optimizar
            model_max_tokens: Límite de tokens del modelo

        Returns:
            Lista de chunks optimizados para el modelo
        """
        words_per_token = 0.75
        max_words = int(model_max_tokens * words_per_token)

        result = self.chunk(text, max_tokens=max_words)
        return result.chunks

    def batch_chunk(
        self,
        texts: List[str],
        max_tokens: int = 500
    ) -> List[ChunkResult]:
        """Procesa múltiples textos."""
        return [self.chunk(text, max_tokens) for text in texts]

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        stats = self._stats.copy()
        if stats['total_chunked'] > 0:
            stats['avg_chunks_per_text'] = stats['total_chunks'] / stats['total_chunked']
        else:
            stats['avg_chunks_per_text'] = 0.0
        return stats

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_chunked': 0,
            'total_chunks': 0,
            'avg_coherence': 0.0
        }


def create_chunker(ai_client=None) -> SemanticChunker:
    """
    Factory function para crear chunker.
    """
    return SemanticChunker(ai_client=ai_client)


def quick_chunk(text: str, max_tokens: int = 500) -> List[str]:
    """
    Función de conveniencia para chunking rápido.
    """
    chunker = SemanticChunker()
    result = chunker.chunk(text, max_tokens)
    return result.chunks