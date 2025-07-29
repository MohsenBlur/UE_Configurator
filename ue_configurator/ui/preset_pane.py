"""UI for importing and exporting config presets."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QFileDialog,
)


from ..config_db import ConfigDB


class PresetPane(QWidget):
    def __init__(self, presets_dir: Path, db: ConfigDB) -> None:
        super().__init__()
        self.presets_dir = presets_dir
        self.db = db
        self.setWindowTitle("Presets")

        self.list = QListWidget()
        self.import_btn = QPushButton("Import")
        self.export_btn = QPushButton("Export Current")

        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.export_btn)

        self.import_btn.clicked.connect(self.import_preset)
        self.export_btn.clicked.connect(self.export_preset)
        self.load_presets()

    def load_presets(self) -> None:
        self.list.clear()
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        for p in self.presets_dir.glob("*.ini"):
            self.list.addItem(p.name)

    def import_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select preset", str(self.presets_dir), "INI Files (*.ini)")
        if path:
            dest = self.presets_dir / Path(path).name
            Path(path).replace(dest)
            self.db.merge_preset(dest)
            self.load_presets()

    def export_preset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save preset", str(self.presets_dir / "preset.ini"), "INI Files (*.ini)")
        if path:
            self.db.export_preset(Path(path))

