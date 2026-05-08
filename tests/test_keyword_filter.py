import pytest
from app.core.keyword_filter import KeywordFilter

def test_disabled_filter_returns_true():
    """Filtro deshabilitado debe permitir todo"""
    f = KeywordFilter()
    assert f.should_process("Cualquier título")[0] is True

def test_or_mode_one_match():
    """OR: cualquier keyword matchea"""
    f = KeywordFilter(include_keywords=["kdp", "amazon"], mode="OR")
    f.enabled = True
    assert f.should_process("Guía KDP 2024")[0] is True

def test_or_mode_no_match():
    """OR: sin match retorna False"""
    f = KeywordFilter(include_keywords=["kdp", "amazon"], mode="OR")
    f.enabled = True
    assert f.should_process("Tutorial Photoshop")[0] is False

def test_and_mode_all_match():
    """AND: todas las keywords deben matchear"""
    f = KeywordFilter(include_keywords=["kdp", "low"], mode="AND")
    f.enabled = True
    assert f.should_process("KDP Low Content")[0] is True

def test_and_mode_partial():
    """AND: parcial retorna False"""
    f = KeywordFilter(include_keywords=["kdp", "low"], mode="AND")
    f.enabled = True
    assert f.should_process("Solo KDP")[0] is False

def test_blacklist_blocks_always():
    """Blacklist tiene prioridad"""
    f = KeywordFilter(include_keywords=["kdp"], exclude_keywords=["gratis"], mode="OR")
    f.enabled = True
    assert f.should_process("KDP Gratis")[0] is False

def test_serialization_roundtrip():
    """JSON serialization debe mantener estado"""
    f = KeywordFilter(include_keywords=["kdp"], exclude_keywords=["spam"], mode="AND")
    f.enabled = True
    restored = KeywordFilter.from_json(f.to_json())
    assert restored.include_keywords == ["kdp"]
    assert restored.exclude_keywords == ["spam"]
    assert restored.mode == "AND"