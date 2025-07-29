"""ProjectChooser widget."""

from pathlib import Path
import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QFileDialog,
)

from .main_window import MainWindow

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

        self.layout = QVBoxLayout(self)
        self.recent = QListWidget()
        self.browse_btn = QPushButton("Browse for .uproject")

        self.layout.addWidget(self.recent)
        self.layout.addWidget(self.browse_btn)

        self.browse_btn.clicked.connect(self.browse)
        self.recent.itemDoubleClicked.connect(self.open_recent)

        self._load()

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
        self.main_window = MainWindow(cache)  # type: ignore[attr-defined]
        self.main_window.show()
        self.close()

