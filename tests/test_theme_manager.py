# -*- coding: utf-8 -*-
"""
Test Suite para ThemeManager y ThemeEditor
Ejecuta pruebas automatizadas del sistema de temas.
"""

import sys
import os
import json
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.ui_framework import ThemeManager


class ThemeManagerTest:
    """Suite de pruebas para ThemeManager."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.passed = 0
        self.failed = 0
        self.tests = []
        
    def run_all(self):
        """Ejecuta todas las pruebas."""
        print("=" * 60)
        print("[TEST] ThemeManager Test Suite")
        print("=" * 60)
        
        self.test_validate_hex_colors()
        self.test_validate_invalid_colors()
        self.test_validate_missing_fields()
        self.test_merge_with_base_dark()
        self.test_merge_with_base_light()
        self.test_save_theme()
        self.test_load_theme()
        self.test_list_themes()
        self.test_custom_theme_with_override()
        
        print("\n" + "=" * 60)
        print(f"[RESULT] {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        return self.failed == 0
    
    def assert_test(self, name, condition, error_msg=""):
        """Registra resultado de prueba."""
        self.tests.append(name)
        if condition:
            print(f"  [PASS] {name}")
            self.passed += 1
        else:
            print(f"  [FAIL] {name}: {error_msg}")
            self.failed += 1
    
    def test_validate_hex_colors(self):
        """Prueba: Validación de colores hex válidos."""
        tm = ThemeManager(None, self.temp_dir)
        
        valid_theme = {
            "name": "test",
            "base": "dark",
            "colors": {
                "bg_primary": "#0a0e1a",
                "fg_primary": "#ffffff",
                "accent": "#3b82f6"
            }
        }
        
        is_valid, error = tm.validate_theme_strict(valid_theme)
        self.assert_test("validate_hex_colors", is_valid, str(error))
    
    def test_validate_invalid_colors(self):
        """Prueba: Validación rechaza colores inválidos (sin base = todos requeridos)."""
        tm = ThemeManager(None, self.temp_dir)
        
        invalid_theme = {
            "name": "test",
            "base": None,
            "colors": {
                "bg_primary": "#GGGGGG",
                "bg_secondary": "#1e293b",
                "bg_tertiary": "#334155",
                "fg_primary": "#f1f5f9",
                "fg_secondary": "#cbd5e1",
                "accent": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "info": "#06b6d4"
            }
        }
        
        is_valid, error = tm.validate_theme_strict(invalid_theme)
        self.assert_test("validate_invalid_colors", not is_valid, str(error))
    
    def test_validate_missing_fields(self):
        """Prueba: Validación detecta campos faltantes."""
        tm = ThemeManager(None, self.temp_dir)
        
        incomplete_theme = {
            "name": "test",
            "colors": {
                "bg_primary": "#000000"
            }
        }
        
        is_valid, error = tm.validate_theme_strict(incomplete_theme)
        self.assert_test("validate_missing_fields", not is_valid, str(error))
    
    def test_merge_with_base_dark(self):
        """Prueba: Fusionar tema con base dark."""
        tm = ThemeManager(None, self.temp_dir)
        
        custom = {
            "name": "custom",
            "base": "dark",
            "colors": {"accent": "#ff0000"}
        }
        
        merged = tm.merge_with_base(custom)
        
        success = (merged["colors"]["bg_primary"] == "#0a0e1a" and 
                  merged["colors"]["accent"] == "#ff0000")
        
        self.assert_test("merge_with_base_dark", success, "Merge failed")
    
    def test_merge_with_base_light(self):
        """Prueba: Fusionar tema con base light."""
        tm = ThemeManager(None, self.temp_dir)
        
        custom = {
            "name": "custom",
            "base": "light",
            "colors": {"accent": "#00ff00"}
        }
        
        merged = tm.merge_with_base(custom)
        
        success = (merged["colors"]["bg_primary"] == "#f8fafc" and 
                  merged["colors"]["accent"] == "#00ff00")
        
        self.assert_test("merge_with_base_light", success, "Merge failed")
    
    def test_save_theme(self):
        """Prueba: Guardar tema en archivo."""
        tm = ThemeManager(None, self.temp_dir)
        
        theme = {
            "name": "test_theme",
            "base": "dark",
            "colors": {
                "accent": "#a855f7",
                "bg_secondary": "#1e1b4b"
            }
        }
        
        success, msg, path = tm.save_theme(theme)
        
        self.assert_test("save_theme", success and os.path.exists(path), msg)
    
    def test_load_theme(self):
        """Prueba: Cargar tema desde archivo."""
        tm = ThemeManager(None, self.temp_dir)
        
        theme = {
            "name": "load_test",
            "base": "dark",
            "colors": {"accent": "#10b981"}
        }
        
        tm.save_theme(theme)
        success, colors, fonts, msg = tm.load_custom_theme("load_test")
        
        self.assert_test("load_theme", success and colors["accent"] == "#10b981", msg)
    
    def test_list_themes(self):
        """Prueba: Listar temas disponibles."""
        tm = ThemeManager(None, self.temp_dir)
        
        themes = tm.list_available_themes()
        
        has_builtins = "dark" in themes and "light" in themes
        has_custom = any(t["type"] == "custom" for t in themes.values())
        
        self.assert_test("list_themes", has_builtins, "Missing built-in themes")
    
    def test_custom_theme_with_override(self):
        """Prueba: Tema custom sobrescribe solo override."""
        tm = ThemeManager(None, self.temp_dir)
        
        theme = {
            "name": "override_test",
            "base": "dark",
            "colors": {"accent": "#f59e0b"}
        }
        
        merged = tm.merge_with_base(theme)
        
        success = (merged["colors"]["bg_primary"] == "#0a0e1a" and
                  merged["colors"]["accent"] == "#f59e0b" and
                  merged["colors"]["fg_primary"] == "#f1f5f9")
        
        self.assert_test("custom_theme_with_override", success, "Override failed")


def run_tests():
    """Punto de entrada principal."""
    test_suite = ThemeManagerTest()
    success = test_suite.run_all()
    return success


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)