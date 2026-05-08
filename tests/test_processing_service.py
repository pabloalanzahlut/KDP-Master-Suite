import pytest
from app.services.processing_service import ProcessingService

def test_clean_content_removes_vtt_header():
    """clean_content elimina header WEBVTT"""
    raw = "WEBVTT\nKind: captions\n\n00:00:01 --> 00:00:05\nTexto"
    svc = ProcessingService()
    result = svc.clean_content(raw)
    assert "WEBVTT" not in result
    assert "Texto" in result

def test_clean_content_removes_timestamps():
    """clean_content elimina timestamps VTT"""
    raw = "00:00:01.000 --> 00:00:05.000\nHola mundo"
    svc = ProcessingService()
    result = svc.clean_content(raw)
    assert "-->" not in result

def test_clean_content_removes_duplicates():
    """clean_content elimina líneas duplicadas consecutivas"""
    raw = "Línea 1\nLínea 1\nLínea 2\nLínea 2\nLínea 3"
    svc = ProcessingService()
    result = svc.clean_content(raw)
    lines = [l for l in result.split("\n") if l]
    assert len(lines) == 3

def test_clean_content_removes_html_tags():
    """clean_content elimina tags HTML"""
    raw = "<b>Negrita</b> y <i>cursiva</i>"
    svc = ProcessingService()
    result = svc.clean_content(raw)
    assert "<" not in result
    assert "Negrita" in result

def test_get_content_hash_is_md5():
    """get_content_hash retorna MD5 de 32 caracteres"""
    svc = ProcessingService()
    h = svc.get_content_hash("test content")
    assert len(h) == 32

def test_get_content_hash_consistency():
    """Hash consistente para mismo contenido"""
    svc = ProcessingService()
    h1 = svc.get_content_hash("texto")
    h2 = svc.get_content_hash("texto")
    assert h1 == h2

def test_get_content_hash_different_for_different_content():
    """Hash diferente para contenido diferente"""
    svc = ProcessingService()
    h1 = svc.get_content_hash("texto A")
    h2 = svc.get_content_hash("texto B")
    assert h1 != h2