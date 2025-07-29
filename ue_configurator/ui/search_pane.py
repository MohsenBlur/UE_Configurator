"""SearchPane for browsing indexed CVars."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from ..indexer import load_cache, build_cache


class SearchPane(QWidget):
    def __init__(self, cache_file: Path) -> None:
        super().__init__()
        self.cache_file = cache_file
        self.setWindowTitle("UE Config Assistant - Search")

        self.search_box = QLineEdit()
        self.category_box = QComboBox()
        self.category_box.addItem("All")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Description", "File"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_box)
        layout.addWidget(self.category_box)
        layout.addWidget(self.table)

        self.search_box.textChanged.connect(self.update_filter)
        self.category_box.currentTextChanged.connect(self.update_filter)

        self.data: List[Dict[str, str]] = []
        self.load_data()
        self._populate_categories()
        self.update_table()

    def load_data(self) -> None:
        if self.cache_file.exists():
            self.data = load_cache(self.cache_file)
        else:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            engine_root = self.ask_engine_root()
            if engine_root:
                build_cache(Path(engine_root), self.cache_file)
                self.data = load_cache(self.cache_file)

    def ask_engine_root(self) -> str | None:
        from PySide6.QtWidgets import QFileDialog

        path = QFileDialog.getExistingDirectory(self, "Select Engine Root")
        return path or None

    def _populate_categories(self) -> None:
        cats = sorted({d.get("category", "") for d in self.data if d.get("category")})
        for cat in cats:
            if self.category_box.findText(cat) == -1:
                self.category_box.addItem(cat)

    def update_filter(self, text: str) -> None:
        category = self.category_box.currentText()
        filtered = []
        for d in self.data:
            if text.lower() in d["name"].lower() or text.lower() in d["description"].lower():
                if category == "All" or d.get("category", "") == category:
                    filtered.append(d)
        self.update_table(filtered)

    def update_table(self, items: List[Dict[str, str]] | None = None) -> None:
        items = items if items is not None else self.data
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["description"]))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("file", "")))
        self.table.resizeRowsToContents()
