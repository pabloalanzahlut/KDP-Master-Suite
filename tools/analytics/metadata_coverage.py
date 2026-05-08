#!/usr/bin/env python3
"""
Script de diagnóstico: Analiza la cobertura de metadatos en archivos JSON de yt-dlp.
Ejecutar: python check_metadata_coverage.py
"""
import json
import os
from pathlib import Path
from collections import defaultdict

def analyze_metadata_coverage(data_dir: str = None):
    """Analiza qué campos están presentes en los JSON existentes"""
    if data_dir is None:
        data_dir = Path(__file__).parent / "data" / "transcriptions"
    else:
        data_dir = Path(data_dir)
    
    if not data_dir.exists():
        print(f"❌ Directorio no encontrado: {data_dir}")
        return
    
    json_files = list(data_dir.glob("**/*.info.json"))
    
    if not json_files:
        print(f"❌ No se encontraron archivos .info.json en {data_dir}")
        return
    
    print(f"[ANALIZANDO] {len(json_files)} archivos JSON...")
    print("=" * 60)
    
    fields_found = defaultdict(int)
    fields_empty = defaultdict(int)
    sample_values = {}
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for field in ['title', 'description', 'tags', 'duration', 'upload_date', 
                          'channel', 'channel_id', 'view_count', 'like_count', 
                          'comment_count', 'categories', 'thumbnail', 'availability']:
                if field in data and data[field]:
                    fields_found[field] += 1
                    if field not in sample_values:
                        sample_values[field] = str(data[field])[:80]
                elif field in data:
                    fields_empty[field] += 1
                else:
                    fields_empty[field] += 1
                    
        except Exception as e:
            print(f"[WARN] Error procesando {json_file.name}: {e}")
    
    print(f"\n[REPORTE] COBERTURA DE METADATOS ({len(json_files)} archivos):")
    print("-" * 60)
    
    priority_fields = ['title', 'description', 'tags', 'duration', 'upload_date', 
                       'channel', 'channel_id', 'view_count', 'like_count']
    
    for field in priority_fields:
        count = fields_found.get(field, 0)
        pct = count / len(json_files) * 100
        status = "[OK]" if pct >= 90 else ("[WARN]" if pct >= 50 else "[FAIL]")
        print(f"  {status} {field:20s}: {pct:5.1f}% ({count}/{len(json_files)})")
    
    print("\n[CAMPOS SECUNDARIOS]:")
    print("-" * 60)
    secondary_fields = ['comment_count', 'categories', 'thumbnail', 'availability']
    for field in secondary_fields:
        count = fields_found.get(field, 0)
        pct = count / len(json_files) * 100
        print(f"  [--] {field:20s}: {pct:5.1f}% ({count}/{len(json_files)})")
    
    print("\n[EJEMPLOS DE VALORES]:")
    print("-" * 60)
    for field, value in sample_values.items():
        print(f"  {field}: {value}...")
    
    print("\n[CONCLUSIONES]:")
    print("-" * 60)
    high_coverage = sum(1 for f in priority_fields if fields_found.get(f, 0) / len(json_files) >= 0.9)
    print(f"  - Campos con >90% cobertura: {high_coverage}/{len(priority_fields)}")
    
    if high_coverage >= 7:
        print("  - VEREDICTO: Enriquecimiento PASIVO es suficiente")
        print("  - Los datos de yt-dlp ya cubren la mayoria de necesidades")
    else:
        print("  - VEREDICTO: Considerar enriquecimiento ACTIVO para campos faltantes")
    
    return {
        'total_files': len(json_files),
        'fields_found': dict(fields_found),
        'fields_empty': dict(fields_empty),
        'coverage': {f: fields_found.get(f, 0) / len(json_files) * 100 for f in priority_fields}
    }

if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else None
    analyze_metadata_coverage(data_dir)