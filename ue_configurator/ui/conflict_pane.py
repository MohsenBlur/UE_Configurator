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
    QPushButton,
)

from ..config_db import ConfigDB, IniFile


class ConflictPane(QWidget):
    def __init__(self, db: ConfigDB) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("Resolve Duplicates")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Section", "Key", "File"])
        self.fix_btn = QPushButton("Comment Lower Priority")
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addWidget(self.fix_btn)
        self.populate()

        self.fix_btn.clicked.connect(self.fix)

    def populate(self) -> None:
        self.tree.clear()
        dups = self.db.find_duplicates()
        for (section, option), files in dups.items():
            parent = QTreeWidgetItem([section, option])
            self.tree.addTopLevelItem(parent)
            for ini in files:
                QTreeWidgetItem(parent, ["", ini.path.name])
        self.tree.expandAll()

    def fix(self) -> None:
        self.db.comment_lower_priority()
        if self.db.config_dir:
            self.db.save(self.db.config_dir)
        self.populate()
