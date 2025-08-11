"""ProjectChooser widget."""

from pathlib import Path
import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QFileDialog,
    QCheckBox,
)

from .main_window import MainWindow
from ..settings import load_settings, save_settings

RECENT_FILE = Path.home() / ".ue5_config_assistant" / "recent.json"


def load_recent() -> list[str]:
    if RECENT_FILE.exists():
        try:
            return json.loads(RECENT_FILE.read_text())
        except Exception:
            pass
    return []


def save_recent(projects: list[str]) -> None:
    RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECENT_FILE.write_text(json.dumps(projects, indent=2))


class ProjectChooser(QWidget):
    """Simple UI for choosing a .uproject file."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("UE Config Assistant - Choose Project")

        settings = load_settings()

        self.layout = QVBoxLayout(self)
        self.recent = QListWidget()
        self.browse_btn = QPushButton("Browse for .uproject")
        self.local_engine_chk = QCheckBox("Use local engine headers")

        self.layout.addWidget(self.recent)
        self.layout.addWidget(self.browse_btn)
        self.layout.addWidget(self.local_engine_chk)

        self.browse_btn.clicked.connect(self.browse)
        self.recent.itemDoubleClicked.connect(self.open_recent)

        self._load()

        if geo := settings.get("chooser_geometry"):
            self.restoreGeometry(bytes.fromhex(geo))

    def _load(self) -> None:
        for proj in load_recent():
            self.recent.addItem(proj)

    def browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select .uproject", "", "Unreal Project (*.uproject)")
        if path:
            self._select(path)

    def open_recent(self, item) -> None:  # type: ignore[override]
        self._select(item.text())

    def _select(self, path: str) -> None:
        projects = [path] + [self.recent.item(i).text() for i in range(self.recent.count()) if self.recent.item(i).text() != path]
        save_recent(projects[:10])

        cache = Path.home() / ".ue5_config_assistant" / "cvar_cache.json"
        project_dir = Path(path).parent
        self.main_window = MainWindow(
            cache,
            project_dir,
            use_local_engine=self.local_engine_chk.isChecked(),
        )  # type: ignore[attr-defined]
        self.main_window.show()
        save_settings({"chooser_geometry": self.saveGeometry().data().hex()})
        self.close()

