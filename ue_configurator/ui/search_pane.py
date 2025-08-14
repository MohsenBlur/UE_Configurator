"""SearchPane for browsing indexed CVars."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QTableView,
    QHeaderView,
)

import rich.progress
from ..indexer import load_cache, build_cache, detect_engine_from_uproject


class SearchFilterProxyModel(QSortFilterProxyModel):
    """Proxy model handling text and category filtering."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text: str = ""
        self._category: str = "All"

    def set_text_filter(self, text: str) -> None:
        self._text = text.lower()
        self.invalidateFilter()

    def set_category_filter(self, category: str) -> None:
        self._category = category
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:  # type: ignore[override]
        model = self.sourceModel()
        name_index = model.index(source_row, 0, source_parent)
        desc_index = model.index(source_row, 1, source_parent)
        name = (name_index.data() or "").lower()
        desc = (desc_index.data() or "").lower()
        category = name_index.data(Qt.UserRole) or ""
        text_match = self._text in name or self._text in desc
        category_match = self._category == "All" or category == self._category
        return text_match and category_match


class SearchPane(QWidget):
    def __init__(
        self,
        cache_file: Path,
        project_dir: Path | None = None,
        engine_version: str = "5.4",
        use_local_engine: bool = False,
    ) -> None:
        super().__init__()
        self.cache_file = cache_file
        self.project_dir = project_dir
        self.engine_version = engine_version
        self.use_local_engine = use_local_engine
        self.setWindowTitle("UE Config Assistant - Search")

        self.search_box = QLineEdit()
        self.category_box = QComboBox()
        self.category_box.addItem("All")

        self.model = QStandardItemModel(0, 3, self)
        self.model.setHorizontalHeaderLabels(["Name", "Description", "File"])

        self.proxy_model = SearchFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)
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
            if self.use_local_engine:
                engine_root = None
                if self.project_dir:
                    engine_root = detect_engine_from_uproject(self.project_dir)
                if not engine_root:
                    engine_root = self.ask_engine_root()
                if engine_root:
                    progress = rich.progress.Progress()
                    with progress:
                        build_cache(
                            cache_file=self.cache_file,
                            engine_root=Path(engine_root),
                            progress=progress,
                        )
                else:
                    build_cache(self.cache_file, version=self.engine_version)
            else:
                build_cache(self.cache_file, version=self.engine_version)
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

    def update_filter(self, _text: str = "") -> None:
        """Update proxy model filters based on search text and category."""
        self.proxy_model.set_text_filter(self.search_box.text())
        self.proxy_model.set_category_filter(self.category_box.currentText())

    def update_table(self, items: List[Dict[str, str]] | None = None) -> None:
        items = items if items is not None else self.data
        self.model.setRowCount(0)
        for item in items:
            name = QStandardItem(item["name"])
            # Store category in the first column for filtering
            name.setData(item.get("category", ""), Qt.UserRole)
            desc = QStandardItem(item["description"])
            file_item = QStandardItem(item.get("file", ""))
            self.model.appendRow([name, desc, file_item])
        self.table.resizeRowsToContents()
