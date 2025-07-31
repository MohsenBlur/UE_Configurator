"""DetailsPane shows full info for a selected CVar."""

from __future__ import annotations

from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextBrowser,
    QLineEdit,
    QComboBox,
    QPushButton,
)

from ..config_db import ConfigDB


class DetailsPane(QWidget):
    def __init__(self, db: ConfigDB | None = None) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("CVar Details")
        self.text = QTextBrowser()
        self.value_edit = QLineEdit()
        self.target_box = QComboBox()
        self.add_btn = QPushButton("Add to Config")
        layout = QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.value_edit)
        layout.addWidget(self.target_box)
        layout.addWidget(self.add_btn)

        self.current_item: Dict[str, str] | None = None
        self.add_btn.clicked.connect(self._add)

    def set_db(self, db: ConfigDB) -> None:
        self.db = db
        self._populate_targets()

    def _populate_targets(self) -> None:
        if not self.db:
            return
        self.target_box.clear()
        for name in self.db.available_targets():
            self.target_box.addItem(name)

    def show_details(self, info: Dict[str, str]) -> None:
        self.current_item = info
        desc = info.get("description", "")
        file = info.get("file", "")
        rng = info.get("range", "")
        default = info.get("default", "")
        content = f"<b>{info.get('name')}</b><br>{desc}<br><i>{file}</i>"
        if rng:
            content += f"<br>Range: {rng}"
        if default:
            content += f"<br>Default: {default}"
        self.text.setHtml(content)
        self.value_edit.setText(default)
        self._populate_targets()

    def _add(self) -> None:
        if not self.db or not self.current_item:
            return
        target = self.target_box.currentText()
        value = self.value_edit.text()
        name = self.current_item.get("name", "")
        self.db.insert_setting("ConsoleVariables", name, value, target)
