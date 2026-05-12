"""
CC Schema Monitor - Módulo 12: Fallback OCR de Miniatura
========================================================
Extrae texto de frames clave vía OCR ligero si no hay subtítulos
disponibles, con umbral de confianza >70%.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import io
import time
import logging
import tempfile
import hashlib
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

MIN_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_FRAMES = 5
DEFAULT_MIN_DURATION = 60


@dataclass
class OCRFrameResult:
    frame_index: int
    timestamp: float
    text: str
    confidence: float
    language_hint: Optional[str] = None


@dataclass
class OCRExtractionResult:
    success: bool
    frames_processed: int
    frames_with_text: int
    total_words: int
    combined_text: str
    average_confidence: float
    error: Optional[str] = None
    frames: List[OCRFrameResult] = None


class ThumbnailOCRExtractor:
    """
    Fallback OCR de Miniatura
    Extrae texto de frames clave cuando no hay subtítulos disponibles.
    """

    def __init__(self, min_confidence: float = MIN_CONFIDENCE_THRESHOLD):
        self.min_confidence = min_confidence
        self._available = self._check_ocr_availability()
        self._stats = {
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'total_frames': 0,
            'total_words': 0
        }

    def _check_ocr_availability(self) -> bool:
        """Verifica si hay OCR disponible."""
        try:
            import pytesseract
            return True
        except ImportError:
            logger.warning("pytesseract not available - OCR fallback disabled")
            return False

    def extract_from_video(self, video_url: str, frames: int = DEFAULT_FRAMES) -> OCRExtractionResult:
        """
        Extrae texto OCR de frames del video.

        Args:
            video_url: URL del video
            frames: Número de frames a procesar

        Returns:
            OCRExtractionResult con texto extraído
        """
        self._stats['total_attempts'] += 1

        if not self._available:
            return OCRExtractionResult(
                success=False,
                frames_processed=0,
                frames_with_text=0,
                total_words=0,
                combined_text="",
                average_confidence=0.0,
                error="OCR not available - pytesseract not installed"
            )

        try:
            import cv2
            import pytesseract
            import numpy as np

            temp_dir = tempfile.mkdtemp()
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(temp_dir, 'video.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }

            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            if not info or 'duration' not in info:
                return OCRExtractionResult(
                    success=False,
                    frames_processed=0,
                    frames_with_text=0,
                    total_words=0,
                    combined_text="",
                    average_confidence=0.0,
                    error="Could not get video info"
                )

            duration = info.get('duration', 0)
            if duration < DEFAULT_MIN_DURATION:
                return OCRExtractionResult(
                    success=False,
                    frames_processed=0,
                    frames_with_text=0,
                    total_words=0,
                    combined_text="",
                    average_confidence=0.0,
                    error=f"Video too short: {duration}s < {DEFAULT_MIN_DURATION}s minimum"
                )

            video_path = os.path.join(temp_dir, f"video.{info.get('ext', 'mp4')}")
            if not os.path.exists(video_path):
                return OCRExtractionResult(
                    success=False,
                    frames_processed=0,
                    frames_with_text=0,
                    total_words=0,
                    combined_text="",
                    average_confidence=0.0,
                    error="Video file not found after download"
                )

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            frame_indices = self._select_frame_indices(total_frames, frames)
            results = []
            total_words = 0

            for idx, frame_pos in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()

                if not ret:
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                enhanced = cv2.equalizeHist(gray)

                text, confidence = self._extract_text_from_frame(enhanced)

                if confidence >= self.min_confidence and text.strip():
                    timestamp = frame_pos / fps if fps > 0 else 0
                    results.append(OCRFrameResult(
                        frame_index=idx,
                        timestamp=timestamp,
                        text=text,
                        confidence=confidence
                    ))
                    total_words += len(text.split())

            cap.release()

            combined = '\n'.join([r.text for r in results])
            avg_conf = sum(r.confidence for r in results) / len(results) if results else 0.0

            os.remove(video_path)
            os.rmdir(temp_dir)

            success = len(results) > 0
            if success:
                self._stats['successful'] += 1
            else:
                self._stats['failed'] += 1

            self._stats['total_frames'] += len(results)
            self._stats['total_words'] += total_words

            return OCRExtractionResult(
                success=success,
                frames_processed=len(frame_indices),
                frames_with_text=len(results),
                total_words=total_words,
                combined_text=combined,
                average_confidence=avg_conf,
                frames=results
            )

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            self._stats['failed'] += 1
            return OCRExtractionResult(
                success=False,
                frames_processed=0,
                frames_with_text=0,
                total_words=0,
                combined_text="",
                average_confidence=0.0,
                error=str(e)
            )

    def extract_from_thumbnail(self, thumbnail_path: str) -> Tuple[str, float]:
        """
        Extrae texto de una miniatura específica.

        Args:
            thumbnail_path: Ruta a la imagen

        Returns:
            (text, confidence)
        """
        if not self._available:
            return "", 0.0

        try:
            import cv2
            import pytesseract
            import numpy as np

            img = cv2.imread(thumbnail_path)
            if img is None:
                return "", 0.0

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            enhanced = cv2.equalizeHist(gray)

            text, confidence = self._extract_text_from_frame(enhanced)
            return text, confidence

        except Exception as e:
            logger.error(f"Thumbnail OCR failed: {e}")
            return "", 0.0

    def _select_frame_indices(self, total_frames: int, num_frames: int) -> List[int]:
        """Selecciona índices de frames equitativamente distribuidos."""
        if total_frames <= num_frames:
            return list(range(total_frames))

        step = total_frames / num_frames
        return [int(i * step) for i in range(num_frames)]

    def _extract_text_from_frame(self, frame) -> Tuple[str, float]:
        """Extrae texto de un frame con pytesseract."""
        try:
            import pytesseract

            config = '--psm 6 -c preserve_interword_spaces=1'
            data = pytesseract.image_to_data(frame, config=config, output_type=pytesseract.Output.DICT)

            text_parts = []
            confidences = []
            n_boxes = len(data['text'])

            for i in range(n_boxes):
                conf = float(data['conf'][i])
                if conf > 0:
                    text = data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(conf)

            combined_text = ' '.join(text_parts)
            avg_conf = sum(confidences) / len(confidences) / 100 if confidences else 0.0

            return combined_text, avg_conf

        except Exception as e:
            logger.error(f"Frame text extraction failed: {e}")
            return "", 0.0

    def is_available(self) -> bool:
        """Retorna si OCR está disponible."""
        return self._available

    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        return self._stats.copy()

    def reset_stats(self):
        """Resetea estadísticas."""
        self._stats = {
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'total_frames': 0,
            'total_words': 0
        }


class LightweightOCRExtractor:
    """
    Versión ligera que solo extrae de thumbnails sin descargar video.
    Útil para pre-visualización rápida.
    """

    def __init__(self, min_confidence: float = MIN_CONFIDENCE_THRESHOLD):
        self.min_confidence = min_confidence
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Verifica disponibilidad de PIL para OCR simple."""
        try:
            from PIL import Image
            import pytesseract
            return True
        except ImportError:
            return False

    def extract_from_url(self, thumbnail_url: str) -> Tuple[str, float]:
        """
        Extrae texto de thumbnail via URL.

        Args:
            thumbnail_url: URL de la miniatura

        Returns:
            (text, confidence)
        """
        if not self._available:
            return "", 0.0

        try:
            import urllib.request
            from PIL import Image
            import pytesseract
            import io

            req = urllib.request.Request(
                thumbnail_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                img_data = response.read()

            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img, lang='eng')

            words = len(text.split())
            confidence = min(words / 100, 1.0) if words > 0 else 0.0

            return text.strip(), confidence

        except Exception as e:
            logger.error(f"URL thumbnail OCR failed: {e}")
            return "", 0.0


def create_ocr_extractor(min_confidence: float = MIN_CONFIDENCE_THRESHOLD) -> ThumbnailOCRExtractor:
    """
    Factory function para crear el extractor OCR.
    """
    return ThumbnailOCRExtractor(min_confidence=min_confidence)


def quick_ocr_check(video_url: str) -> OCRExtractionResult:
    """
    Función de conveniencia para OCR rápido.
    """
    extractor = ThumbnailOCRExtractor()
    return extractor.extract_from_video(video_url)