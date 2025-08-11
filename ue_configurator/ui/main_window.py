"""Main window combining search and details panes."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import QSplitter, QMainWindow
from PySide6.QtGui import QAction

from ..config_db import ConfigDB
from .conflict_pane import ConflictPane
from .preset_pane import PresetPane
from ..settings import load_settings, save_settings

from .search_pane import SearchPane
from .details_pane import DetailsPane


class MainWindow(QMainWindow):
    def __init__(self, cache_file: Path, project_dir: Path) -> None:
        super().__init__()
        self.setWindowTitle("UE Config Assistant")
        self.project_dir = project_dir
        self.db = ConfigDB()
        self.conflict_pane: ConflictPane | None = None
        self.preset_pane: PresetPane | None = None
        config_dir = project_dir / "Config"
        if config_dir.exists():
            self.db.load(config_dir)

        self.search = SearchPane(cache_file, project_dir)
        self.details = DetailsPane(self.db)

        self.search.table.itemSelectionChanged.connect(self.show_details)

        splitter = QSplitter()
        splitter.addWidget(self.search)
        splitter.addWidget(self.details)

        self.setCentralWidget(splitter)

        # menu actions
        conflict_action = QAction("Show Duplicates", self)
        conflict_action.triggered.connect(self.show_conflicts)
        preset_action = QAction("Presets", self)
        preset_action.triggered.connect(self.show_presets)
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_config)
        self.menuBar().addAction(conflict_action)
        self.menuBar().addAction(preset_action)
        self.menuBar().addAction(save_action)

        settings = load_settings()
        if geo := settings.get("main_geometry"):
            self.restoreGeometry(bytes.fromhex(geo))

    def show_details(self) -> None:
        rows = self.search.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        item = self.search.data[row]
        self.details.show_details(item)

    def show_conflicts(self) -> None:
        try:
            self.conflict_pane = ConflictPane(self.db)
            self.conflict_pane.show()
        except Exception:
            logging.exception("Failed to open conflict pane")

    def save_config(self) -> None:
        ok, msg = self.db.validate()
        if not ok:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Validation Error", msg or "Invalid config")
            return
        config_dir = self.project_dir / "Config"
        self.db.save(config_dir)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        save_settings({"main_geometry": self.saveGeometry().data().hex()})
        super().closeEvent(event)

    def show_presets(self) -> None:
        try:
            presets = self.project_dir / "Presets"
            self.preset_pane = PresetPane(presets, self.db)
            self.preset_pane.show()
        except Exception:
            logging.exception("Failed to open presets pane")
