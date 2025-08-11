"""UI pane for toggling active ini files."""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt

from ..config_db import ConfigDB


class FilesPane(QWidget):
    def __init__(self, db: ConfigDB, on_change: Callable[[], None] | None = None) -> None:
        super().__init__()
        self.db = db
        self.on_change = on_change
        self.setWindowTitle("Config Files")
        self.list = QListWidget()
        self.list.itemChanged.connect(self._toggle)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        self.populate()

    def populate(self) -> None:
        self.list.clear()
        for name, enabled in self.db.list_files():
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
            self.list.addItem(item)

    def _toggle(self, item: QListWidgetItem) -> None:
        name = item.text()
        enabled = item.checkState() == Qt.Checked
        self.db.set_file_enabled(name, enabled)
        if self.on_change:
            self.on_change()
