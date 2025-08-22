import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from pathlib import Path
import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
MainWindow = pytest.importorskip("ue_configurator.ui.main_window").MainWindow
QApplication = QtWidgets.QApplication


def test_row_selection_triggers_details(tmp_path):
    app = QApplication.instance() or QApplication([])
    project_dir = tmp_path / "Proj"
    project_dir.mkdir()
    (project_dir / "Config").mkdir()

    cache_file = tmp_path / "cache.json"
    data = [{
        "name": "r.Test",
        "description": "Test var",
        "default": "0",
        "category": "",
        "range": "",
        "file": ""
    }]
    cache_file.with_name("cache-5.4.json").write_text(json.dumps(data))

    window = MainWindow(cache_file, project_dir)
    captured = {}
    def fake_show_details(info):
        captured["item"] = info
    window.details.show_details = fake_show_details

    window.search.table.selectRow(0)
    QApplication.processEvents()
    assert captured["item"]["name"] == "r.Test"
