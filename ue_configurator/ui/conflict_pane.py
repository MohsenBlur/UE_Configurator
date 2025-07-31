"""UI pane for resolving duplicate config entries."""

from __future__ import annotations

from typing import Dict, Tuple, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
    QPushButton,
)

from ..config_db import ConfigDB, IniFile


class ConflictPane(QWidget):
    def __init__(self, db: ConfigDB) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("Resolve Duplicates")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Section", "Key", "Action"])
        self.apply_btn = QPushButton("Apply")
        self.actions: Dict[Tuple[str, str], QComboBox] = {}
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addWidget(self.apply_btn)
        self.populate()

        self.apply_btn.clicked.connect(self.apply)

    def populate(self) -> None:
        self.tree.clear()
        dups = self.db.find_duplicates()
        for (section, option), files in dups.items():
            parent = QTreeWidgetItem([section, option])
            self.tree.addTopLevelItem(parent)
            combo = QComboBox()
            combo.addItems(["Comment", "Delete", "Ignore"])
            self.tree.setItemWidget(parent, 2, combo)
            self.actions[(section, option)] = combo
            for ini in files:
                QTreeWidgetItem(parent, ["", "", ini.path.name])
        self.tree.expandAll()

    def apply(self) -> None:
        for (section, option), combo in self.actions.items():
            action = combo.currentText().lower()
            self.db.resolve_duplicate(section, option, action)
        if self.db.config_dir:
            self.db.save(self.db.config_dir)
        self.populate()
