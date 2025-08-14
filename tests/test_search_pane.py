import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from pathlib import Path
import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
SearchPane = pytest.importorskip("ue_configurator.ui.search_pane").SearchPane
QApplication = QtWidgets.QApplication


def test_search_pane_uses_local_engine(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    engine_root = tmp_path / "Engine"
    engine_root.mkdir()
    project_dir = tmp_path / "Proj"
    project_dir.mkdir()
    (project_dir / "Proj.uproject").write_text(json.dumps({"EngineAssociation": str(engine_root)}))
    captured = {}
    def fake_build_cache(cache_file, engine_root=None, version="5.4", progress=None):
        captured["engine_root"] = engine_root
        cache_file.write_text("[]")
    monkeypatch.setattr("ue_configurator.ui.search_pane.build_cache", fake_build_cache)
    cache_file = tmp_path / "cache.json"
    pane = SearchPane(cache_file, project_dir, use_local_engine=True)
    assert captured["engine_root"] == engine_root


def test_search_pane_appends_version(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    project_dir = tmp_path / "Proj"
    project_dir.mkdir()
    (project_dir / "Proj.uproject").write_text(json.dumps({"EngineAssociation": "5.1"}))

    def fake_build_cache(cache_file, engine_root=None, version="5.4", progress=None):
        cache_file.write_text("[]")

    monkeypatch.setattr("ue_configurator.ui.search_pane.build_cache", fake_build_cache)
    cache_file = tmp_path / "cache.json"
    pane = SearchPane(cache_file, project_dir)
    assert pane.cache_file.name == "cache-5.1.json"
