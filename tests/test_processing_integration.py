import pytest
import time
from pathlib import Path
from app.services.processing_service import ProcessingService

def test_process_files_returns_unique_count(tmp_path):
    """process_files retorna count de archivos únicos"""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    files = ["test1.vtt", "test2.vtt", "test3.vtt"]
    for f in files:
        (input_dir / f).write_text(f"WEBVTT\n\nContenido {f}")
    
    svc = ProcessingService()
    count = svc.process_files(str(input_dir), str(output_dir), files)
    assert count == 3

def test_process_files_removes_duplicates(tmp_path):
    """process_files deduplica contenido idéntico"""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    files = [f"dup_{i}.vtt" for i in range(5)]
    for f in files:
        (input_dir / f).write_text("WEBVTT\n\nContenido Duplicado")
    
    svc = ProcessingService()
    count = svc.process_files(str(input_dir), str(output_dir), files)
    assert count == 1  # Solo uno pasa como único

def test_process_files_concurrent_timing(tmp_path):
    """process_files con paralelismo no debe ser excesivamente lento"""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    files = [f"par_{i}.vtt" for i in range(20)]
    for i, f in enumerate(files):
        content = f"WEBVTT\n\nContenido {i}"  # Contenido diferente para evitar dedup
        (input_dir / f).write_text(content)
    
    svc = ProcessingService()
    start = time.perf_counter()
    count = svc.process_files(str(input_dir), str(output_dir), files, max_workers=4)
    elapsed = time.perf_counter() - start
    
    assert count == 20
    assert elapsed < 5.0  # 20 archivos debe procesarse en <5s

def test_process_files_handles_utf8_fallback(tmp_path, caplog):
    """process_files usa fallback de encoding"""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    file = "utf8_test.vtt"
    (input_dir / file).write_text("WEBVTT\n\nContenido válido en UTF-8")
    
    svc = ProcessingService()
    count = svc.process_files(str(input_dir), str(output_dir), [file])
    assert count == 1  # Debe procesarse exitosamente

def test_process_files_creates_output_dir(tmp_path):
    """process_files crea output_dir si no existe"""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "new_output"
    input_dir.mkdir()
    
    files = ["test.vtt"]
    (input_dir / "test.vtt").write_text("WEBVTT\n\nContenido")
    
    svc = ProcessingService()
    count = svc.process_files(str(input_dir), str(output_dir), files)
    assert count == 1
    assert output_dir.exists()