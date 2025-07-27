"""DetailsPane shows full info for a selected CVar."""

from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser


class DetailsPane(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CVar Details")
        self.text = QTextBrowser()
        layout = QVBoxLayout(self)
        layout.addWidget(self.text)

    def show_details(self, info: Dict[str, str]) -> None:
        desc = info.get("description", "")
        file = info.get("file", "")
        content = f"<b>{info.get('name')}</b><br>{desc}<br><i>{file}</i>"
        self.text.setHtml(content)
