"""UI pane for resolving duplicate config entries."""

from __future__ import annotations

from typing import Dict, Tuple, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QRadioButton,
    QButtonGroup,
)

from ..config_db import ConfigDB, IniFile


class ConflictPane(QWidget):
    def __init__(self, db: ConfigDB) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("Resolve Duplicates")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Section", "Key", "File"])
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        self.populate()

    def populate(self) -> None:
        self.tree.clear()
        dups = self.db.find_duplicates()
        for (section, option), files in dups.items():
            parent = QTreeWidgetItem([section, option])
            self.tree.addTopLevelItem(parent)
            for ini in files:
                QTreeWidgetItem(parent, ["", ini.path.name])
        self.tree.expandAll()
