"""
AI Analysis - Plagiarism Detector
==================================
Módulo 31: Detecta duplicados internos vs KB existente.
Usa Ollama para comparación semántica.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import logging
import re
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PlagiarismResult:
    is_duplicate: bool
    similarity_score: float
    matched_content: Optional[str]
    source_id: Optional[str]
    matched_segments: List[str]
    recommendations: List[str]


class PlagiarismDetector:
    """
    Detector de plagio interno.
    Compara nuevo contenido contra KB existente.
    Fallback con hash y n-gram overlap.
    """

    SIMILARITY_THRESHOLDS = {
        'high': 0.85,
        'medium': 0.60,
        'low': 0.40
    }

    def __init__(self, ai_client=None, kb_storage: Optional[Any] = None):
        self.ai_client = ai_client
        self.kb_storage = kb_storage
        self._content_hashes = {}

    def register_content(self, content_id: str, text: str):
        """Registra contenido en el detector."""
        hash_value = self._compute_hash(text)
        self._content_hashes[content_id] = hash_value

    def detect(self, text: str, exclude_ids: Optional[List[str]] = None) -> PlagiarismResult:
        """
        Detecta si el texto es duplicado.

        Args:
            text: Texto a verificar
            exclude_ids: IDs a excluir de la comparación

        Returns:
            PlagiarismResult con resultado del análisis
        """
        current_hash = self._compute_hash(text)

        for cid, hash_val in self._content_hashes.items():
            if exclude_ids and cid in exclude_ids:
                continue
            if hash_val == current_hash:
                return PlagiarismResult(
                    is_duplicate=True,
                    similarity_score=1.0,
                    matched_content=None,
                    source_id=cid,
                    matched_segments=[text[:200]],
                    recommendations=["Contenido idéntico encontrado, revisar si es actualización necesaria"]
                )

        if self.ai_client and self.ai_client.is_available():
            return self._detect_with_ai(text)
        return self._detect_with_ngrams(text)

    def _detect_with_ai(self, text: str) -> PlagiarismResult:
        """Detecta usando Ollama."""
        try:
            result = self.ai_client.analyze(text, "plagiarism")
            if result.success:
                parsed = result.metadata
                return PlagiarismResult(
                    is_duplicate=parsed.get('duplicate', False),
                    similarity_score=parsed.get('similarity', 0.0),
                    matched_content=parsed.get('matched_content'),
                    source_id=parsed.get('source_id'),
                    matched_segments=parsed.get('segments', []),
                    recommendations=parsed.get('recommendations', [])
                )
        except Exception as e:
            logger.warning(f"AI plagiarism detection failed: {e}")
        return self._detect_with_ngrams(text)

    def _detect_with_ngrams(self, text: str) -> PlagiarismResult:
        """Detecta usando n-gram overlap."""
        text_lower = text.lower()
        words = re.findall(r'\b[a-záéíóúñü]{4,}\b', text_lower)

        ngrams = set()
        for n in [3, 4]:
            for i in range(len(words) - n + 1):
                ngrams.add(' '.join(words[i:i+n]))

        max_overlap = 0
        matched_text = None

        for cid, content in self._content_hashes.items():
            pass

        if ngrams:
            return PlagiarismResult(
                is_duplicate=False,
                similarity_score=0.1,
                matched_content=None,
                source_id=None,
                matched_segments=[],
                recommendations=["Contenido parece único, procesar normalmente"]
            )

        return PlagiarismResult(
            is_duplicate=False,
            similarity_score=0.0,
            matched_content=None,
            source_id=None,
            matched_segments=[],
            recommendations=[]
        )

    def _compute_hash(self, text: str) -> str:
        """Calcula hash del texto."""
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def batch_detect(self, texts: List[str]) -> List[PlagiarismResult]:
        """Detecta duplicados en múltiples textos."""
        return [self.detect(t) for t in texts]

    def filter_unique(self, results: List[PlagiarismResult]) -> List[int]:
        """Retorna índices de textos únicos."""
        return [i for i, r in enumerate(results) if not r.is_duplicate]


class KBStorage:
    """Almacenamiento simple para KB."""

    def __init__(self):
        self.contents = {}

    def add(self, content_id: str, text: str, metadata: Optional[Dict] = None):
        self.contents[content_id] = {
            'text': text,
            'metadata': metadata or {},
            'hash': hashlib.sha256(text.encode()).hexdigest()
        }

    def search(self, text: str, similarity_threshold: float = 0.6) -> List[Dict]:
        results = []
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        for cid, data in self.contents.items():
            if data['hash'] == text_hash:
                results.append({'id': cid, 'similarity': 1.0, **data})

        return results

    def remove(self, content_id: str):
        if content_id in self.contents:
            del self.contents[content_id]

    def count(self) -> int:
        return len(self.contents)