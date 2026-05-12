"""
CC Schema Monitor - Módulo 19: Generador de Manifest de Extracción
===================================================================
Crea JSON con metadatos técnicos: fuente, encoding, palabras, hash,
idioma, calidad y timestamp para trazabilidad.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExtractionMetadata:
    source_type: str
    source_url: str
    video_id: str
    title: str
    language: str
    encoding: str
    word_count: int
    char_count: int
    content_hash: str
    format: str
    quality_score: float
    extraction_timestamp: str
    duration_seconds: Optional[float] = None
    subtitle_count: Optional[int] = None
    auto_generated: Optional[bool] = None
    processing_time_ms: Optional[float] = None


class ManifestGenerator:
    """
    Generador de Manifest de Extracción
    Crea JSON con metadatos técnicos para trazabilidad.
    """

    CURRENT_VERSION = "1.0.0"

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or self._get_default_output_dir()

    def _get_default_output_dir(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "data", "extraction_manifests")

    def generate(
        self,
        source_url: str,
        video_id: str,
        title: str,
        content: str,
        source_type: str = "subtitle",
        language: str = "unknown",
        format: str = "vtt",
        quality_score: float = 0.0,
        duration_seconds: Optional[float] = None,
        subtitle_count: Optional[int] = None,
        auto_generated: Optional[bool] = None,
        processing_time_ms: Optional[float] = None,
        extra_metadata: Optional[Dict] = None
    ) -> ExtractionMetadata:
        """
        Genera metadatos de extracción.

        Args:
            source_url: URL de origen
            video_id: ID del video
            title: Título del video
            content: Contenido extraído
            source_type: Tipo de fuente (subtitle, ocr, etc.)
            language: Idioma detectado
            format: Formato del contenido
            quality_score: Score de calidad
            duration_seconds: Duración del video
            subtitle_count: Cantidad de subtítulos
            auto_generated: Si es auto-generado
            processing_time_ms: Tiempo de procesamiento
            extra_metadata: Metadatos adicionales

        Returns:
            ExtractionMetadata
        """
        encoding = self._detect_encoding(content)
        word_count = len(content.split())
        char_count = len(content)
        content_hash = self._compute_hash(content)

        metadata = ExtractionMetadata(
            source_type=source_type,
            source_url=source_url,
            video_id=video_id,
            title=title,
            language=language,
            encoding=encoding,
            word_count=word_count,
            char_count=char_count,
            content_hash=content_hash,
            format=format,
            quality_score=quality_score,
            extraction_timestamp=datetime.utcnow().isoformat(),
            duration_seconds=duration_seconds,
            subtitle_count=subtitle_count,
            auto_generated=auto_generated,
            processing_time_ms=processing_time_ms
        )

        if extra_metadata:
            for key, value in extra_metadata.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)

        return metadata

    def to_dict(self, metadata: ExtractionMetadata) -> Dict[str, Any]:
        """
        Convierte metadatos a diccionario.

        Args:
            metadata: ExtractionMetadata

        Returns:
            Diccionario serializable
        """
        return {
            "version": self.CURRENT_VERSION,
            "metadata": asdict(metadata),
            "checksum": self._compute_hash(json.dumps(asdict(metadata)))
        }

    def save(
        self,
        metadata: ExtractionMetadata,
        output_path: Optional[str] = None
    ) -> str:
        """
        Guarda manifest a archivo JSON.

        Args:
            metadata: ExtractionMetadata
            output_path: Ruta de salida (opcional)

        Returns:
            Ruta del archivo guardado
        """
        if output_path is None:
            os.makedirs(self.output_dir, exist_ok=True)
            filename = f"{metadata.video_id}_manifest.json"
            output_path = os.path.join(self.output_dir, filename)

        manifest_data = self.to_dict(metadata)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Manifest saved: {output_path}")
        return output_path

    def load(self, manifest_path: str) -> Optional[ExtractionMetadata]:
        """
        Carga manifest desde archivo.

        Args:
            manifest_path: Ruta al archivo

        Returns:
            ExtractionMetadata o None si falla
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)

            metadata_dict = manifest_data.get('metadata', {})
            return ExtractionMetadata(**metadata_dict)

        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return None

    def generate_batch(
        self,
        extractions: List[Dict]
    ) -> List[ExtractionMetadata]:
        """
        Genera manifests para múltiples extracciones.

        Args:
            extractions: Lista de diccionarios con datos de extracción

        Returns:
            Lista de ExtractionMetadata
        """
        manifests = []

        for ext in extractions:
            metadata = self.generate(
                source_url=ext.get('source_url', ''),
                video_id=ext.get('video_id', ''),
                title=ext.get('title', ''),
                content=ext.get('content', ''),
                source_type=ext.get('source_type', 'subtitle'),
                language=ext.get('language', 'unknown'),
                format=ext.get('format', 'vtt'),
                quality_score=ext.get('quality_score', 0.0),
                duration_seconds=ext.get('duration_seconds'),
                subtitle_count=ext.get('subtitle_count'),
                auto_generated=ext.get('auto_generated'),
                processing_time_ms=ext.get('processing_time_ms'),
                extra_metadata=ext.get('extra_metadata')
            )
            manifests.append(metadata)

        return manifests

    def save_batch(
        self,
        manifests: List[ExtractionMetadata],
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        Guarda múltiples manifests.

        Args:
            manifests: Lista de ExtractionMetadata
            output_dir: Directorio de salida

        Returns:
            Lista de rutas guardadas
        """
        if output_dir:
            self.output_dir = output_dir

        saved_paths = []
        for metadata in manifests:
            path = self.save(metadata)
            saved_paths.append(path)

        return saved_paths

    def _detect_encoding(self, content: str) -> str:
        """Detecta encoding del contenido."""
        try:
            content.encode('utf-8')
            return 'utf-8'
        except UnicodeEncodeError:
            pass

        for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                content.encode(enc)
                return enc
            except UnicodeEncodeError:
                continue

        return 'unknown'

    def _compute_hash(self, text: str) -> str:
        """Computa hash SHA-256."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


def create_generator(output_dir: Optional[str] = None) -> ManifestGenerator:
    """
    Factory function para crear el generador.
    """
    return ManifestGenerator(output_dir=output_dir)


def quick_manifest(
    video_id: str,
    content: str,
    source_url: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    Función de conveniencia para crear manifest rápido.
    """
    generator = ManifestGenerator()
    metadata = generator.generate(
        source_url=source_url,
        video_id=video_id,
        title=kwargs.get('title', video_id),
        content=content,
        **kwargs
    )
    return generator.to_dict(metadata)