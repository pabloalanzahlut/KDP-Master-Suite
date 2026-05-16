"""
Metadata Enricher
================
Enriquece metadatos de archivos con info adicional.
"""

from typing import Dict
import os
from pathlib import Path


class MetadataEnricher:
    def enrich(self, file_path: str, metadata: Dict) -> Dict:
        path = Path(file_path)
        metadata["extension"] = path.suffix
        metadata["name"] = path.name
        metadata["parent"] = str(path.parent)
        if os.path.exists(file_path):
            metadata["exists"] = True
            metadata["size"] = os.path.getsize(file_path)
        return metadata


_global_enricher = None


def get_metadata_enricher() -> MetadataEnricher:
    global _global_enricher
    if _global_enricher is None:
        _global_enricher = MetadataEnricher()
    return _global_enricher