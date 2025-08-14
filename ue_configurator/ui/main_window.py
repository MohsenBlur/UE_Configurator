"""Main window combining search and details panes."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import QSplitter, QMainWindow, QMessageBox
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtCore import QUrl

from ..config_db import ConfigDB
from .conflict_pane import ConflictPane
from .preset_pane import PresetPane
from .files_pane import FilesPane
from ..settings import load_settings, save_settings

from .search_pane import SearchPane
from .details_pane import DetailsPane


class MainWindow(QMainWindow):
    def __init__(self, cache_file: Path, project_dir: Path, use_local_engine: bool = False) -> None:
        super().__init__()
        self.setWindowTitle("UE Config Assistant")
        self.project_dir = project_dir
        self.db = ConfigDB()
        self.conflict_pane: ConflictPane | None = None
        self.preset_pane: PresetPane | None = None
        self.files_pane: FilesPane | None = None
        config_dir = project_dir / "Config"
        if config_dir.exists():
            self.db.load(config_dir)

        self.search = SearchPane(cache_file, project_dir, use_local_engine=use_local_engine)
        self.details = DetailsPane(self.db)

        self.search.table.itemSelectionChanged.connect(self.show_details)

        splitter = QSplitter()
        splitter.addWidget(self.search)
        splitter.addWidget(self.details)

        self.setCentralWidget(splitter)

        # menu actions
        conflict_action = QAction("Show Duplicates", self)
        conflict_action.setShortcut(QKeySequence("Ctrl+D"))
        conflict_action.setToolTip("Show duplicate entries (Ctrl+D)")
        conflict_action.triggered.connect(self.show_conflicts)

        preset_action = QAction("Presets", self)
        preset_action.setShortcut(QKeySequence("Ctrl+P"))
        preset_action.setToolTip("Manage presets (Ctrl+P)")
        preset_action.triggered.connect(self.show_presets)

        files_action = QAction("Config Files", self)
        files_action.setShortcut(QKeySequence("Ctrl+F"))
        files_action.setToolTip("Browse config files (Ctrl+F)")
        files_action.triggered.connect(self.show_files)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.setToolTip("Validate and save configuration (Ctrl+S)")
        save_action.triggered.connect(self.save_config)
        self.menuBar().addAction(conflict_action)
        self.menuBar().addAction(preset_action)
        self.menuBar().addAction(files_action)
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
            QMessageBox.warning(self, "Validation Error", msg or "Invalid config")
            return
        config_dir = self.project_dir / "Config"
        backup_dir = self.db.save(config_dir)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Save Successful")
        box.setText("Configuration saved successfully.")
        box.setInformativeText(f"Backups stored in:\n{backup_dir}")
        open_btn = box.addButton("Open Backup Folder", QMessageBox.ActionRole)
        box.addButton(QMessageBox.Ok)
        box.exec()
        if box.clickedButton() == open_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_dir)))

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

    def show_files(self) -> None:
        try:
            self.files_pane = FilesPane(self.db, self.details._populate_targets)
            self.files_pane.show()
        except Exception:
            logging.exception("Failed to open files pane")
