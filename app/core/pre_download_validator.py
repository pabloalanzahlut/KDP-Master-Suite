"""
Módulos P2: Validación Pre-Descarga
- P2-15: Comparador de Timestamps
- P2-16: Validación de Disponibilidad (404)
- P2-18: Validación de Región (Geo-Block)
- P2-19: Check de Licencia (Creative Commons)
"""
import logging
import re
import urllib.request
import json
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Resultado de validación pre-descarga."""
    is_valid: bool
    validation_type: str
    message: str
    details: Optional[Dict] = None


class PreDownloadValidator:
    """Validador de videos antes de descargar."""

    GEO_BLOCK_REGIONS = {
        'CN': 'China',
        'RU': 'Rusia',
        'KP': 'Corea del Norte',
        'IR': 'Iran',
        'SY': 'Siria',
        'CU': 'Cuba'
    }

    CC_LICENSES = [
        'creative commons',
        'cc by',
        'cc-by',
        'cc0',
        'public domain'
    ]

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    def compare_timestamps(
        self,
        video_data: Dict,
        local_data: Optional[Dict] = None
    ) -> ValidationResult:
        """
        P2-15: Compara timestamps de publicación vs última modificación local.
        Args:
            video_data: Datos del video de YouTube
            local_data: Datos locales si existen
        Returns:
            ValidationResult con el análisis
        """
        upload_date_str = video_data.get('upload_date') or video_data.get('published_at')
        if not upload_date_str:
            return ValidationResult(
                is_valid=True,
                validation_type="timestamp_comparison",
                message="No hay fecha de publicación disponible"
            )

        try:
            if isinstance(upload_date_str, str):
                upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00'))
            else:
                upload_date = upload_date_str

            now = datetime.now()
            days_since_upload = (now - upload_date).days

            if local_data:
                local_modified = local_data.get('modified_at') or local_data.get('updated_at')
                if local_modified:
                    if isinstance(local_modified, str):
                        local_date = datetime.fromisoformat(local_modified.replace('Z', '+00:00'))
                    else:
                        local_date = local_modified

                    if upload_date > local_date:
                        return ValidationResult(
                            is_valid=True,
                            validation_type="timestamp_comparison",
                            message=f"Video actualizado en YouTube (publicado: {upload_date.date()}, local: {local_date.date()})",
                            details={
                                "upload_date": upload_date.isoformat(),
                                "local_date": local_date.isoformat(),
                                "is_updated": True
                            }
                        )
                    elif abs((upload_date - local_date).days) <= 1:
                        return ValidationResult(
                            is_valid=True,
                            validation_type="timestamp_comparison",
                            message="Video sin cambios",
                            details={"is_updated": False, "days_diff": 0}
                        )

            message = f"Video de hace {days_since_upload} días"
            if days_since_upload > 365:
                message += " (contenido antiguo)"
            elif days_since_upload > 30:
                message += " (contenido reciente)"

            return ValidationResult(
                is_valid=True,
                validation_type="timestamp_comparison",
                message=message,
                details={
                    "upload_date": upload_date.isoformat(),
                    "days_since_upload": days_since_upload,
                    "is_updated": False
                }
            )

        except Exception as e:
            return ValidationResult(
                is_valid=True,
                validation_type="timestamp_comparison",
                message=f"Error comparando timestamps: {e}",
                details={"error": str(e)}
            )

    def check_availability(self, video_url: str) -> ValidationResult:
        """
        P2-16: Verifica si el video está disponible (no 404, no privado).
        Args:
            video_url: URL del video de YouTube
        Returns:
            ValidationResult con disponibilidad
        """
        try:
            request = urllib.request.Request(
                video_url,
                headers={'User-Agent': self._user_agent}
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = response.getcode()
                if status == 200:
                    return ValidationResult(
                        is_valid=True,
                        validation_type="availability",
                        message="Video disponible",
                        details={"status_code": status}
                    )
                elif status == 404:
                    return ValidationResult(
                        is_valid=False,
                        validation_type="availability",
                        message="Video no encontrado (404)",
                        details={"status_code": 404, "reason": "not_found"}
                    )
                elif status == 403:
                    return ValidationResult(
                        is_valid=False,
                        validation_type="availability",
                        message="Video es privado o restringido (403)",
                        details={"status_code": 403, "reason": "private"}
                    )

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ValidationResult(
                    is_valid=False,
                    validation_type="availability",
                    message="Video no encontrado",
                    details={"status_code": 404, "reason": "not_found"}
                )
            elif e.code == 403:
                return ValidationResult(
                    is_valid=False,
                    validation_type="availability",
                    message="Video privado o restringido",
                    details={"status_code": 403, "reason": "private"}
                )
            elif e.code == 429:
                return ValidationResult(
                    is_valid=False,
                    validation_type="availability",
                    message="Demasiadas peticiones (429) - intentar más tarde",
                    details={"status_code": 429, "reason": "rate_limited"}
                )
            return ValidationResult(
                is_valid=False,
                validation_type="availability",
                message=f"Error HTTP: {e.code}",
                details={"status_code": e.code, "reason": "http_error"}
            )

        except Exception as e:
            return ValidationResult(
                is_valid=True,
                validation_type="availability",
                message=f"No se pudo verificar disponibilidad: {str(e)[:50]}",
                details={"error": str(e), "assume_available": True}
            )

    def check_geo_restriction(
        self,
        video_data: Dict,
        user_country: str = "unknown"
    ) -> ValidationResult:
        """
        P2-18: Verifica restricciones geográficas del video.
        Args:
            video_data: Datos del video (incluye region_restriction)
            user_country: Código de país del usuario (ISO 3166-1 alpha-2)
        Returns:
            ValidationResult con análisis de región
        """
        region_restrictions = video_data.get('region_restriction') or video_data.get('available_regions')

        if not region_restrictions:
            return ValidationResult(
                is_valid=True,
                validation_type="geo_restriction",
                message="Sin restricciones regionales - disponible globalmente"
            )

        allowed = region_restrictions.get('allowed', [])
        blocked = region_restrictions.get('blocked', [])

        if allowed:
            if user_country.upper() in [c.upper() for c in allowed]:
                return ValidationResult(
                    is_valid=True,
                    validation_type="geo_restriction",
                    message=f"Usuario en región permitida: {user_country}",
                    details={"allowed_regions": allowed, "user_country": user_country}
                )
            else:
                blocked_region = next((self.GEO_BLOCK_REGIONS.get(c.upper(), c) for c in allowed if c.upper() in [x.upper() for x in self.GEO_BLOCK_REGIONS]), allowed[0])
                return ValidationResult(
                    is_valid=False,
                    validation_type="geo_restriction",
                    message=f"Video no disponible en tu región: {user_country}",
                    details={
                        "allowed_regions": allowed,
                        "user_country": user_country,
                        "reason": "not_in_allowed_list"
                    }
                )

        if blocked:
            if user_country.upper() in [c.upper() for c in blocked]:
                return ValidationResult(
                    is_valid=False,
                    validation_type="geo_restriction",
                    message=f"Video bloqueado en tu región: {user_country}",
                    details={
                        "blocked_regions": blocked,
                        "user_country": user_country,
                        "reason": "in_blocked_list"
                    }
                )

        return ValidationResult(
            is_valid=True,
            validation_type="geo_restriction",
            message="Disponible en tu región",
            details={"blocked_regions": blocked, "user_country": user_country}
        )

    def check_license(self, video_data: Dict) -> ValidationResult:
        """
        P2-19: Verifica la licencia del video (Creative Commons).
        Args:
            video_data: Datos del video (incluye license, rights_owner)
        Returns:
            ValidationResult con análisis de licencia
        """
        license_type = video_data.get('license') or video_data.get('rights_metadata', {}).get('license')
        rights_owner = video_data.get('rights_owner') or video_data.get('rights_metadata', {}).get('owner')

        if not license_type:
            return ValidationResult(
                is_valid=True,
                validation_type="license",
                message="Licencia estándar de YouTube",
                details={"license": "youtube_standard"}
            )

        license_lower = str(license_type).lower()

        if any(cc in license_lower for cc in self.CC_LICENSES):
            return ValidationResult(
                is_valid=True,
                validation_type="license",
                message=f"Licencia Creative Commons: {license_type}",
                details={
                    "license": license_type,
                    "is_cc": True,
                    "rights_owner": rights_owner
                }
            )

        if 'creative' in license_lower:
            return ValidationResult(
                is_valid=True,
                validation_type="license",
                message=f"Licencia: {license_type}",
                details={"license": license_type, "is_cc": True}
            )

        return ValidationResult(
            is_valid=True,
            validation_type="license",
            message=f"Licencia: {license_type}",
            details={"license": license_type, "is_cc": False}
        )

    def validate_all(
        self,
        video_data: Dict,
        local_data: Optional[Dict] = None,
        check_availability: bool = False,
        user_country: str = "unknown"
    ) -> List[ValidationResult]:
        """Ejecuta todas las validaciones pre-descarga."""
        results = []

        results.append(self.compare_timestamps(video_data, local_data))

        if check_availability:
            video_url = video_data.get('url') or video_data.get('webpage_url')
            if video_url:
                results.append(self.check_availability(video_url))

        results.append(self.check_geo_restriction(video_data, user_country))
        results.append(self.check_license(video_data))

        return results


_global_validator: Optional[PreDownloadValidator] = None


def get_pre_download_validator(timeout: int = 10) -> PreDownloadValidator:
    """Obtiene la instancia global del validador."""
    global _global_validator
    if _global_validator is None:
        _global_validator = PreDownloadValidator(timeout)
    return _global_validator