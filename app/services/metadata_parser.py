import json
import re
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime


class MetadataParser:
    """Parser para metadatos de archivos JSON de yt-dlp."""
    
    REQUIRED_FIELDS = ['title', 'description', 'tags', 'duration', 'upload_date']
    
    @staticmethod
    def parse_json_file(json_path: Path) -> Dict[str, Any]:
        """
        Extrae y normaliza metadatos de un archivo JSON de yt-dlp.
        
        Args:
            json_path: Ruta al archivo .info.json de yt-dlp
            
        Returns:
            Dict con campos normalizados de metadatos
        """
        if not json_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        
        return MetadataParser._normalize_metadata(raw)
    
    @staticmethod
    def _normalize_metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza los metadatos crudos de yt-dlp."""
        
        duration_seconds = raw.get('duration')
        
        derived = MetadataParser._compute_derived_fields(raw)
        
        return {
            'video_id': raw.get('id'),
            'title': raw.get('title', 'Sin titulo'),
            'description': (raw.get('description') or '')[:2000],
            'description_full': raw.get('description', ''),
            'tags': raw.get('tags') or [],
            'duration_seconds': duration_seconds,
            'duration_formatted': MetadataParser._format_duration(duration_seconds),
            'upload_date': raw.get('upload_date'),
            'upload_datetime': MetadataParser._parse_upload_date(raw.get('upload_date')),
            'channel': raw.get('channel'),
            'channel_id': raw.get('channel_id'),
            'channel_url': raw.get('channel_url'),
            'view_count': raw.get('view_count'),
            'like_count': raw.get('like_count'),
            'comment_count': raw.get('comment_count'),
            'thumbnail': raw.get('thumbnail'),
            'categories': raw.get('categories') or [],
            'availability': raw.get('availability', 'unknown'),
            'webpage_url': raw.get('webpage_url'),
            'uploader': raw.get('uploader'),
            'uploader_id': raw.get('uploader_id'),
            'age_limit': raw.get('age_limit'),
            'media_type': raw.get('media_type'),
            'timestamp': raw.get('timestamp'),
            **derived
        }
    
    @staticmethod
    def _compute_derived_fields(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula campos derivados."""
        duration = raw.get('duration') or 0
        
        return {
            'has_tags': bool(raw.get('tags')),
            'has_description': bool(raw.get('description')),
            'description_length': len(raw.get('description') or ''),
            'is_short': duration <= 60,
            'is_medium': 60 < duration <= 600,
            'is_long': duration > 600,
            'tags_count': len(raw.get('tags') or []),
            'engagement_ratio': MetadataParser._calculate_engagement(
                raw.get('like_count', 0),
                raw.get('view_count', 0)
            )
        }
    
    @staticmethod
    def _format_duration(seconds: Optional[int]) -> str:
        """Convierte segundos a formato HH:MM:SS o MM:SS."""
        if not seconds:
            return "00:00"
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    
    @staticmethod
    def _parse_upload_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parsea fecha YYYYMMDD a datetime."""
        if not date_str or len(date_str) != 8:
            return None
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            return None
    
    @staticmethod
    def _calculate_engagement(likes: int, views: int) -> Optional[float]:
        """Calcula ratio de engagement (likes/views * 100)."""
        if not views or views == 0:
            return None
        return round((likes / views) * 100, 2)
    
    @staticmethod
    def extract_keywords(description: str, tags: List[str], max_keywords: int = 20) -> List[str]:
        """
        Extrae keywords combinando tags + analisis de descripcion.
        
        Args:
            description: Descripcion del video
            tags: Tags extraidos por yt-dlp
            max_keywords: Numero maximo de keywords a retornar
            
        Returns:
            Lista de keywords unicas
        """
        keywords = []
        
        if tags:
            keywords = [t.lower().strip() for t in tags if t][:max_keywords]
        
        if len(keywords) < max_keywords and description:
            extra_keywords = MetadataParser._extract_keywords_from_text(
                description, 
                max_keywords - len(keywords)
            )
            for kw in extra_keywords:
                if kw.lower() not in [k.lower() for k in keywords]:
                    keywords.append(kw)
        
        return keywords[:max_keywords]
    
    @staticmethod
    def _extract_keywords_from_text(text: str, max_count: int) -> List[str]:
        """Extrae keywords de texto usando patron simple (palabras de 4+ letras)."""
        if not text:
            return []
        
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'will', 'your', 'they',
            'about', 'more', 'some', 'than', 'very', 'just', 'also', 'only',
            'been', 'would', 'could', 'should', 'into', 'what', 'when',
            'there', 'which', 'their', 'these', 'those', 'other', 'such'
        }
        
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        filtered = [w for w in words if w not in stop_words and len(w) > 3]
        
        word_freq = {}
        for w in filtered:
            word_freq[w] = word_freq.get(w, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_count]]
    
    @staticmethod
    def find_json_for_vtt(vtt_path: Path) -> Optional[Path]:
        """
        Encuentra el archivo JSON counterpart para un archivo VTT.
        
        Args:
            vtt_path: Ruta al archivo .vtt
            
        Returns:
            Ruta al archivo .info.json equivalente o None
        """
        base_name = vtt_path.stem
        json_name = f"{base_name}.info.json"
        json_path = vtt_path.parent / json_name
        
        if json_path.exists():
            return json_path
        
        json_path_alt = vtt_path.parent / f"{base_name}.info.json"
        if json_path_alt.exists():
            return json_path_alt
        
        return None
    
    @staticmethod
    def get_video_metadata(vtt_path: Path) -> Optional[Dict[str, Any]]:
        """
        Obtiene metadatos completos para un archivo VTT.
        Busca automaticamente el JSON counterpart.
        
        Args:
            vtt_path: Ruta al archivo .vtt
            
        Returns:
            Dict de metadatos o None si no se encuentra JSON
        """
        json_path = MetadataParser.find_json_for_vtt(vtt_path)
        if not json_path:
            return None
        
        try:
            return MetadataParser.parse_json_file(json_path)
        except Exception:
            return None
    
    @staticmethod
    def to_json_string(metadata: Dict[str, Any]) -> str:
        """Convierte metadatos a string JSON para almacenamiento en DB."""
        return json.dumps(metadata, ensure_ascii=False, indent=2)
    
    @staticmethod
    def from_json_string(json_str: str) -> Dict[str, Any]:
        """Convierte string JSON a dict de metadatos."""
        return json.loads(json_str)


def test_parser():
    """Test basico del parser."""
    test_json = Path(__file__).parent.parent / "data" / "transcriptions" / "Zachary_Donovan_-_Official" / "20251206_How_to_Make_360_Day_Selling_AI_Puzzle_Books_on_Amazon_KDP_Full_Guide [Cj2X8Aak2cM].info.json"
    
    if test_json.exists():
        metadata = MetadataParser.parse_json_file(test_json)
        print(f"Title: {metadata['title']}")
        print(f"Duration: {metadata['duration_formatted']}")
        print(f"Tags: {metadata['tags'][:5]}...")
        print(f"Keywords: {MetadataParser.extract_keywords(metadata['description'], metadata['tags'], 10)}")
        
        keywords_json = MetadataParser.to_json_string(metadata)
        print(f"\nJSON length: {len(keywords_json)} chars")
    else:
        print(f"Test file not found: {test_json}")


if __name__ == "__main__":
    test_parser()