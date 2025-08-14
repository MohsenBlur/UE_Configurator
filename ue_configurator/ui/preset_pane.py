"""UI for importing and exporting config presets."""

from __future__ import annotations

import logging
from pathlib import Path
import shutil

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QMenu,
)
from PySide6.QtCore import Qt


from ..config_db import ConfigDB


class PresetPane(QWidget):
    def __init__(self, presets_dir: Path, db: ConfigDB) -> None:
        super().__init__()
        self.presets_dir = presets_dir
        self.db = db
        self.setWindowTitle("Presets")

        self.list = QListWidget()
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
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
        try:
            self.list.clear()
            self.presets_dir.mkdir(parents=True, exist_ok=True)
            for p in self.presets_dir.glob("*.ini"):
                self.list.addItem(p.name)
        except Exception:
            logging.exception("Failed to load presets")

    def import_preset(self) -> None:
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select preset", str(self.presets_dir), "INI Files (*.ini)"
            )
            if path:
                dest = self.presets_dir / Path(path).name
                shutil.copy2(path, dest)
                self.db.merge_preset(dest)
                QMessageBox.information(
                    self, "Preset Imported", f"Imported {dest.name}"
                )
                self.load_presets()
        except Exception:
            logging.exception("Failed to import preset")

    def export_preset(self) -> None:
        try:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save preset",
                str(self.presets_dir / "preset.ini"),
                "INI Files (*.ini)",
            )
            if path:
                self.db.export_preset(Path(path))
        except Exception:
            logging.exception("Failed to export preset")

    def _show_context_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        rename_act = menu.addAction("Rename")
        delete_act = menu.addAction("Delete")
        action = menu.exec(self.list.mapToGlobal(pos))
        if action == rename_act:
            self._rename_preset(item)
        elif action == delete_act:
            self._delete_preset(item)

    def _delete_preset(self, item) -> None:
        name = item.text()
        path = self.presets_dir / name
        confirm = QMessageBox.question(
            self,
            "Delete Preset",
            f"Delete {name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                path.unlink()
                self.load_presets()
            except Exception:
                logging.exception("Failed to delete preset")
                QMessageBox.warning(
                    self, "Delete Failed", f"Could not delete {name}"
                )

    def _rename_preset(self, item) -> None:
        old_name = item.text()
        old_path = self.presets_dir / old_name
        new_name, ok = QInputDialog.getText(
            self, "Rename Preset", "New name:", text=old_name
        )
        if ok and new_name and new_name != old_name:
            new_path = self.presets_dir / new_name
            try:
                old_path.rename(new_path)
                self.load_presets()
            except Exception:
                logging.exception("Failed to rename preset")
                QMessageBox.warning(
                    self, "Rename Failed", f"Could not rename {old_name}"
                )

