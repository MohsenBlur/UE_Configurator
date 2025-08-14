import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
FilesPane = pytest.importorskip("ue_configurator.ui.files_pane").FilesPane
ConfigDB = pytest.importorskip("ue_configurator.config_db").ConfigDB
QUrl = pytest.importorskip("PySide6.QtCore").QUrl


def _make_db(tmp_path: Path) -> ConfigDB:
    config_dir = tmp_path / "Config"
    config_dir.mkdir()
    (config_dir / "DefaultGame.ini").write_text("[/Script/Engine.Engine]\n")
    db = ConfigDB()
    db.load(config_dir)
    return db


def test_files_pane_tooltip_shows_full_path(tmp_path):
    app = QApplication.instance() or QApplication([])
    db = _make_db(tmp_path)
    pane = FilesPane(db)
    item = pane.list.item(0)
    assert item.toolTip() == str(db.config_dir / item.text())


def test_open_item_uses_desktop_services(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    db = _make_db(tmp_path)
    pane = FilesPane(db)
    item = pane.list.item(0)
    captured = {}
    def fake_open(url):
        captured["url"] = url
        return True
    monkeypatch.setattr("PySide6.QtGui.QDesktopServices.openUrl", fake_open)
    pane._open_item(item)
    assert captured["url"].toLocalFile() == str(db.config_dir / item.text())
