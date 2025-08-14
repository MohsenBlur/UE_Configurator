"""UI pane for toggling active ini files."""

from __future__ import annotations

from typing import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import Qt, QPoint, QUrl

from ..config_db import ConfigDB


class FilesPane(QWidget):
    def __init__(self, db: ConfigDB, on_change: Callable[[], None] | None = None) -> None:
        super().__init__()
        self.db = db
        self.on_change = on_change
        self.setWindowTitle("Config Files")
        self.list = QListWidget()
        self.list.itemChanged.connect(self._toggle)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._context_menu)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        self.populate()

    def populate(self) -> None:
        self.list.clear()
        for name, enabled in self.db.list_files():
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
            if self.db.config_dir:
                path = self.db.config_dir / name
            else:
                path = Path(name)
            item.setData(Qt.UserRole, path)
            item.setToolTip(str(path))
            self.list.addItem(item)

    def _toggle(self, item: QListWidgetItem) -> None:
        name = item.text()
        enabled = item.checkState() == Qt.Checked
        self.db.set_file_enabled(name, enabled)
        if self.on_change:
            self.on_change()

    def _context_menu(self, pos: QPoint) -> None:
        item = self.list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        open_action = menu.addAction("Open in Editor")
        action = menu.exec(self.list.mapToGlobal(pos))
        if action == open_action:
            self._open_item(item)

    def _open_item(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
