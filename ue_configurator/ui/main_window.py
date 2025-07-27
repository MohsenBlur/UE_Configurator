"""Main window combining search and details panes."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QSplitter, QMainWindow

from .search_pane import SearchPane
from .details_pane import DetailsPane


class MainWindow(QMainWindow):
    def __init__(self, cache_file: Path) -> None:
        super().__init__()
        self.setWindowTitle("UE Config Assistant")

        self.search = SearchPane(cache_file)
        self.details = DetailsPane()

        self.search.table.itemSelectionChanged.connect(self.show_details)

        splitter = QSplitter()
        splitter.addWidget(self.search)
        splitter.addWidget(self.details)

        self.setCentralWidget(splitter)

    def show_details(self) -> None:
        rows = self.search.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        item = {
            "name": self.search.table.item(row, 0).text(),
            "description": self.search.table.item(row, 1).text(),
            "file": self.search.table.item(row, 2).text(),
        }
        self.details.show_details(item)
