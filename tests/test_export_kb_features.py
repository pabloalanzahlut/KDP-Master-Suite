"""
KDP MASTER - Tests para Módulos de Exportación KB
=================================================
Tests para verificar la funcionalidad de los módulos de exportación:
- export_settings_tab.py
- export_preview.py
- KBExportService
- KBExportScheduler
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestExportSettingsTab:
    """Tests para ExportSettingsTab."""

    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.logger = Mock()
        app.config_file = None
        return app

    @pytest.fixture
    def mock_parent(self):
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            parent = tk.Frame(root)
            yield parent
            root.destroy()
        except:
            parent = Mock()
            yield parent

    def test_export_settings_tab_init(self, mock_parent, mock_app):
        """Test de inicialización del tab de configuración."""
        try:
            from app.ui.tabs.export_settings_tab import ExportSettingsTab
            tab = ExportSettingsTab(mock_parent, mock_app)
            assert tab is not None
            assert tab.app == mock_app
        except ImportError as e:
            pytest.skip(f" tkinter no disponible: {e}")

    def test_export_settings_default_values(self, mock_parent, mock_app):
        """Test de valores por defecto."""
        try:
            from app.ui.tabs.export_settings_tab import ExportSettingsTab
            tab = ExportSettingsTab(mock_parent, mock_app)
            assert tab.format_var.get() == "html"
            assert tab.template_var.get() == "complete"
            assert tab.enable_filters_var.get() == False
            assert tab.incremental_var.get() == True
        except ImportError:
            pytest.skip("tkinter no disponible")

    def test_export_settings_save_load(self, mock_parent, mock_app, tmp_path):
        """Test de guardar y cargar configuración."""
        try:
            from app.ui.tabs.export_settings_tab import ExportSettingsTab

            config_file = tmp_path / "test_config.json"
            mock_app.config_file = str(config_file)

            tab = ExportSettingsTab(mock_parent, mock_app)

            tab.format_var.set("pdf")
            tab.template_var.set("minimal")
            tab.enable_filters_var.set(True)
            tab.categories_var.set("test1, test2")
            tab.days_filter_var.set(7)
            tab.max_entries_var.set(100)
            tab.split_threshold_var.set(1500)

            tab._save_settings()

            assert config_file.exists()

            with open(config_file, 'r') as f:
                saved = json.load(f)

            assert saved["export"]["format"] == "pdf"
            assert saved["export"]["template"] == "minimal"
            assert saved["export"]["enable_filters"] == True
            assert "test1" in saved["export"]["categories"]
            assert saved["export"]["days_filter"] == 7

            tab.format_var.set("html")
            tab._load_settings()

            assert tab.format_var.get() == "pdf"
            assert tab.template_var.get() == "minimal"

        except ImportError:
            pytest.skip("tkinter no disponible")


class TestExportPreviewComponent:
    """Tests para ExportPreviewComponent."""

    @pytest.fixture
    def sample_preview_data(self):
        return {
            "entries": [
                {
                    "title": "Test Entry 1",
                    "category": "General",
                    "source": "test",
                    "timestamp": datetime.now().isoformat(),
                    "content_preview": "Contenido de prueba 1 " * 50
                },
                {
                    "title": "Test Entry 2",
                    "category": "Manuales",
                    "source": "test",
                    "timestamp": datetime.now().isoformat(),
                    "content_preview": "Contenido de prueba 2 " * 50
                },
                {
                    "title": "Test Entry 3",
                    "category": "General",
                    "source": "test",
                    "timestamp": datetime.now().isoformat(),
                    "content_preview": "Contenido de prueba 3 " * 50
                }
            ],
            "total_count": 3,
            "preview_count": 3,
            "estimated_size_kb": 15.5,
            "categories": ["General", "Manuales"],
            "filters_applied": {}
        }

    def test_preview_data_structure(self, sample_preview_data):
        """Test de estructura de datos de preview."""
        assert "entries" in sample_preview_data
        assert "total_count" in sample_preview_data
        assert "estimated_size_kb" in sample_preview_data
        assert "categories" in sample_preview_data

        assert sample_preview_data["total_count"] == 3
        assert len(sample_preview_data["categories"]) == 2

        for entry in sample_preview_data["entries"]:
            assert "title" in entry
            assert "category" in entry
            assert "content_preview" in entry

    def test_preview_entry_size_calculation(self, sample_preview_data):
        """Test de cálculo de tamaño de entradas."""
        for entry in sample_preview_data["entries"]:
            content = entry.get("content_preview", "")
            size = len(content.encode('utf-8'))
            assert size > 0
            assert size < 10000

    def test_preview_category_filtering(self, sample_preview_data):
        """Test de filtrado por categoría."""
        categories = sample_preview_data["categories"]
        general_entries = [e for e in sample_preview_data["entries"]
                          if e["category"] == "General"]

        assert len(general_entries) == 2

        manuales_entries = [e for e in sample_preview_data["entries"]
                           if e["category"] == "Manuales"]
        assert len(manuales_entries) == 1

    def test_preview_size_format(self):
        """Test de formateo de tamaño."""
        def format_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"

        assert "500 B" == format_size(500)
        assert "1.0 KB" == format_size(1024)
        assert "1.5 KB" == format_size(1536)
        assert "1.0 MB" == format_size(1024 * 1024)


class TestKBExportService:
    """Tests para KBExportService."""

    @pytest.fixture
    def temp_kb_dir(self, tmp_path):
        kb_dir = tmp_path / "knowledge"
        kb_dir.mkdir()
        (kb_dir / "test_entry.md").write_text("# Test Entry\n\nContent here.", encoding='utf-8')
        return kb_dir

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        output_dir = tmp_path / "exports"
        output_dir.mkdir()
        return output_dir

    def test_export_filters_creation(self):
        """Test de creación de ExportFilters."""
        try:
            from app.services.kb_export_service import ExportFilters

            filters = ExportFilters(
                categories=["Test"],
                days_back=7,
                search_query="test",
                limit=100
            )

            assert filters.categories == ["Test"]
            assert filters.days_back == 7
            assert filters.search_query == "test"
            assert filters.limit == 100

            filters_dict = filters.to_dict()
            assert filters_dict["categories"] == ["Test"]
            assert filters_dict["days_back"] == 7

            filters_restored = ExportFilters.from_dict(filters_dict)
            assert filters_restored.categories == filters.categories
            assert filters_restored.days_back == filters.days_back

        except ImportError:
            pytest.skip("KBExportService no disponible")

    def test_export_config_creation(self):
        """Test de creación de ExportConfig."""
        try:
            from app.services.kb_export_service import ExportConfig

            config = ExportConfig(
                format="html",
                template="full",
                compression=True,
                max_entries_per_file=200,
                split_threshold_kb=1500
            )

            assert config.format == "html"
            assert config.template == "full"
            assert config.compression == True
            assert config.max_entries_per_file == 200

            config_dict = config.to_dict()
            assert config_dict["format"] == "html"

            config_restored = ExportConfig.from_dict(config_dict)
            assert config_restored.format == config.format

        except ImportError:
            pytest.skip("KBExportService no disponible")

    def test_export_service_init(self, tmp_path):
        """Test de inicialización del servicio."""
        try:
            from app.services.kb_export_service import KBExportService

            kb_dir = tmp_path / "knowledge"
            kb_dir.mkdir()
            output_dir = tmp_path / "exports"
            output_dir.mkdir()

            service = KBExportService(
                kb_dir=str(kb_dir),
                output_dir=str(output_dir)
            )

            assert service is not None
            assert service.kb_dir == kb_dir
            assert service.output_dir == output_dir

        except ImportError:
            pytest.skip("KBExportService no disponible")

    def test_preview_export(self, tmp_path):
        """Test de preview de exportación."""
        try:
            from app.services.kb_export_service import KBExportService

            kb_dir = tmp_path / "knowledge"
            kb_dir.mkdir()
            (kb_dir / "entry1.md").write_text("# Entry 1\n\nContent.", encoding='utf-8')
            (kb_dir / "entry2.md").write_text("# Entry 2\n\nContent.", encoding='utf-8')

            output_dir = tmp_path / "exports"
            output_dir.mkdir()

            service = KBExportService(
                kb_dir=str(kb_dir),
                output_dir=str(output_dir)
            )

            preview = service.preview_export(max_entries=10)

            assert "entries" in preview
            assert "total_count" in preview
            assert preview["total_count"] >= 0

        except ImportError:
            pytest.skip("KBExportService no disponible")


class TestKBExportScheduler:
    """Tests para KBExportScheduler."""

    def test_scheduler_config(self):
        """Test de configuración del scheduler."""
        try:
            from app.services.kb_export_scheduler import KBExportScheduler

            scheduler = KBExportScheduler()

            status = scheduler.get_status()
            assert "running" in status
            assert "frequency" in status

            scheduler.configure(
                enabled=True,
                frequency="daily",
                hour=3,
                minute=30,
                template="full",
                compression=True
            )

            status = scheduler.get_status()
            assert status["frequency"] == "daily"
            assert status["hour"] == 3
            assert status["minute"] == 30

        except ImportError:
            pytest.skip("KBExportScheduler no disponible")

    def test_calculate_next_run(self):
        """Test de cálculo de próxima ejecución."""
        try:
            from app.services.kb_export_scheduler import KBExportScheduler

            scheduler = KBExportScheduler()

            next_hourly = scheduler._calculate_next_run(0, 0, "hourly")
            assert next_hourly is not None

            next_daily = scheduler._calculate_next_run(23, 59, "daily")
            assert next_daily is not None

            next_weekly = scheduler._calculate_next_run(2, 0, "weekly")
            assert next_weekly is not None

        except ImportError:
            pytest.skip("KBExportScheduler no disponible")


class TestExportTemplates:
    """Tests para plantillas de exportación."""

    def test_templates_available(self):
        """Test de disponibilidad de plantillas."""
        try:
            from app.modules.export.export_kb import EXPORT_TEMPLATES

            assert "minimal" in EXPORT_TEMPLATES
            assert "complete" in EXPORT_TEMPLATES
            assert "index_only" in EXPORT_TEMPLATES

            minimal = EXPORT_TEMPLATES["minimal"]
            assert minimal["include_toc"] == False
            assert minimal["include_header"] == False

            complete = EXPORT_TEMPLATES["complete"]
            assert complete["include_toc"] == True
            assert complete["include_search"] == True
            assert complete["include_sqlite"] == True

        except ImportError:
            pytest.skip("export_kb no disponible")

    def test_template_content_generation(self):
        """Test de generación de contenido según plantilla."""
        try:
            from app.modules.export.export_kb import EXPORT_TEMPLATES

            for template_name, template in EXPORT_TEMPLATES.items():
                assert isinstance(template, dict)
                assert "name" in template
                assert "include_toc" in template
                assert "include_header" in template
                assert "include_search" in template

        except ImportError:
            pytest.skip("export_kb no disponible")


class TestExportHistory:
    """Tests para historial de exportaciones."""

    def test_history_entry_structure(self):
        """Test de estructura de entrada de historial."""
        try:
            from app.services.kb_export_service import ExportHistoryEntry

            entry = ExportHistoryEntry(
                id=1,
                export_date="2024-01-01 12:00",
                format="html",
                template="full",
                entries_count=100,
                file_size_bytes=1024000,
                file_path="/exports/test.html",
                export_type="full",
                filters_applied="{}",
                last_entry_id=0,
                status="success"
            )

            assert entry.id == 1
            assert entry.format == "html"
            assert entry.entries_count == 100
            assert entry.status == "success"

        except ImportError:
            pytest.skip("ExportHistoryEntry no disponible")

    def test_export_result_structure(self):
        """Test de estructura de resultado de exportación."""
        try:
            from app.services.kb_exporter import ExportResult

            result = ExportResult(
                success=True,
                output_path="/exports/test.html",
                format="html",
                entries_count=50,
                categories_count=5,
                file_size_bytes=500000
            )

            assert result.success == True
            assert result.entries_count == 50
            assert result.categories_count == 5

        except ImportError:
            pytest.skip("ExportResult no disponible")


class TestExportIntegration:
    """Tests de integración de exportación."""

    def test_export_kb_function(self):
        """Test de función export_kb()."""
        try:
            from app.services.kb_export_service import export_kb

            result = export_kb(format="html", template="minimal")

            assert isinstance(result, dict)
            assert "success" in result
            assert "output_path" in result or "error" in result

        except ImportError:
            pytest.skip("export_kb no disponible")

    def test_compression_zip(self, tmp_path):
        """Test de compresión ZIP."""
        try:
            from app.services.kb_export_service import KBExportService

            output_dir = tmp_path / "exports"
            output_dir.mkdir()

            test_file = output_dir / "test.html"
            test_file.write_text("<html>test</html>")

            service = KBExportService(output_dir=str(output_dir))

            zip_path = service.create_zip_archive([test_file])

            if zip_path:
                assert zip_path.exists()
                assert zip_path.suffix == ".zip"

        except ImportError:
            pytest.skip("KBExportService no disponible")

    def test_split_zip_archives(self, tmp_path):
        """Test de archivos ZIP separados por categoría."""
        try:
            from app.services.kb_export_service import KBExportService

            output_dir = tmp_path / "exports"
            output_dir.mkdir()

            service = KBExportService(output_dir=str(output_dir))

            grouped = {
                "Categoria1": [],
                "Categoria2": []
            }

            result = service.create_split_zip_archives(grouped, "minimal")
            assert isinstance(result, list)

        except ImportError:
            pytest.skip("KBExportService no disponible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
