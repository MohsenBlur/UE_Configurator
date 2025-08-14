"""SearchPane for browsing indexed CVars."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
    QThread,
    QObject,
    Signal,
    QEventLoop,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QTableView,
    QHeaderView,
    QProgressDialog,
    QMessageBox,
)

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


class _ProgressAdapter(QObject):
    """Adapter to translate indexer progress callbacks into Qt signals."""

    changed = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self._total = 0
        self._value = 0

    def add_task(self, _desc: str, total: int = 0) -> int:
        self._total = total
        self._value = 0
        self.changed.emit(self._value, self._total)
        return 0

    def advance(self, _task_id: int) -> None:
        self._value += 1
        self.changed.emit(self._value, self._total)


class BuildCacheWorker(QObject):
    """Worker object running ``build_cache`` in a separate thread."""

    progress = Signal(int, int)
    finished = Signal(bool, str)

    def __init__(
        self,
        cache_file: Path,
        engine_root: Path | None,
        version: str,
    ) -> None:
        super().__init__()
        self.cache_file = cache_file
        self.engine_root = engine_root
        self.version = version

    def run(self) -> None:
        adapter = _ProgressAdapter()
        adapter.changed.connect(self.progress.emit)
        try:
            build_cache(
                cache_file=self.cache_file,
                engine_root=self.engine_root,
                version=self.version,
                progress=adapter,
            )
            self.finished.emit(True, "")
        except Exception as exc:  # pragma: no cover - network/IO failures
            self.finished.emit(False, str(exc))


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

    def load_data(self) -> None:
        if self.cache_file.exists():
            self.data = load_cache(self.cache_file)
            self._populate_categories()
            self.update_table()
            return

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        engine_root: Path | None = None
        if self.use_local_engine:
            if self.project_dir:
                root = detect_engine_from_uproject(self.project_dir)
                if root:
                    engine_root = Path(root)
            if engine_root is None:
                chosen = self.ask_engine_root()
                if chosen:
                    engine_root = Path(chosen)

        self._build_cache(engine_root)

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

    # ------------------------------------------------------------------
    # Cache building helpers
    # ------------------------------------------------------------------

    def _build_cache(self, engine_root: Path | None) -> None:
        """Run ``build_cache`` in a background thread with progress dialog."""

        self.progress_dialog = QProgressDialog("Building cache...", "", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        self._thread = QThread(self)
        worker = BuildCacheWorker(self.cache_file, engine_root, self.engine_version)
        worker.moveToThread(self._thread)
        worker.progress.connect(self._update_progress)
        worker.finished.connect(self.progress_dialog.close)
        worker.finished.connect(self._thread.quit)

        result: dict[str, str | bool] = {}

        def _finished(success: bool, msg: str) -> None:
            result["success"] = success
            result["msg"] = msg

        worker.finished.connect(_finished)

        self._thread.started.connect(worker.run)
        self._thread.start()

        loop = QEventLoop()
        worker.finished.connect(loop.quit)
        loop.exec()

        self._thread.wait()
        worker.deleteLater()
        self._thread.deleteLater()

        if result.get("success"):
            self.data = load_cache(self.cache_file)
            self._populate_categories()
            self.update_table()
        else:
            QMessageBox.critical(
                self,
                "Cache Error",
                f"Failed to build cache: {result.get('msg', '')}",
            )

    def _update_progress(self, value: int, total: int) -> None:
        if total:
            self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(value)
        else:
            self.progress_dialog.setRange(0, 0)
