"""SearchPane for browsing indexed CVars."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressDialog,
    QMessageBox,
)

from ..indexer import load_cache, build_cache, detect_engine_from_uproject


class _QtProgress:
    """Bridge ``build_cache`` progress callbacks to Qt signals."""

    def __init__(self, worker: "BuildCacheWorker") -> None:
        self.worker = worker
        self._value = 0
        self._maximum = 0

    def add_task(self, description: str, total: int) -> int:  # pragma: no cover - trivial
        self._maximum = total
        self.worker.progress.emit(0, total)
        return 0

    def advance(self, task_id: int) -> None:  # pragma: no cover - trivial
        self._value += 1
        self.worker.progress.emit(self._value, self._maximum)


class BuildCacheWorker(QObject):
    progress = Signal(int, int)
    finished = Signal(bool, str)

    def __init__(self, cache_file: Path, engine_root: Path | None, version: str) -> None:
        super().__init__()
        self.cache_file = cache_file
        self.engine_root = engine_root
        self.version = version

    def run(self) -> None:
        try:
            progress = _QtProgress(self)
            build_cache(
                cache_file=self.cache_file,
                engine_root=self.engine_root,
                version=self.version,
                progress=progress,
            )
            self.finished.emit(True, "")
        except Exception as exc:  # pragma: no cover - unexpected
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
        self._thread: QThread | None = None
        self._worker: BuildCacheWorker | None = None
        self._progress: QProgressDialog | None = None

        self.load_data()

    def load_data(self) -> None:
        if self.cache_file.exists():
            self.data = load_cache(self.cache_file)
            self._populate_categories()
            self.update_table()
            return

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        engine_root = None
        if self.use_local_engine:
            if self.project_dir:
                engine_root = detect_engine_from_uproject(self.project_dir)
            if not engine_root:
                engine_root = self.ask_engine_root()
            engine_root = Path(engine_root) if engine_root else None
        self._start_build_thread(engine_root)

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

    # --- Cache building -------------------------------------------------

    def _start_build_thread(self, engine_root: Path | None) -> None:
        self._worker = BuildCacheWorker(self.cache_file, engine_root, self.engine_version)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)

        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_build_finished)
        self._thread.started.connect(self._worker.run)

        self._progress = QProgressDialog("Building cache...", None, 0, 0, self)
        self._progress.setWindowTitle("Building Cache")
        self._progress.setWindowModality(Qt.ApplicationModal)
        self._progress.setCancelButton(None)
        self._progress.show()

        self._thread.start()

    def _on_progress(self, value: int, maximum: int) -> None:  # pragma: no cover - GUI update
        if maximum:
            self._progress.setMaximum(maximum)
            self._progress.setValue(value)
        else:
            self._progress.setRange(0, 0)

    def _on_build_finished(self, success: bool, message: str) -> None:
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        if self._progress:
            self._progress.close()
            self._progress = None
        if success:
            self.data = load_cache(self.cache_file)
            self._populate_categories()
            self.update_table()
        else:  # pragma: no cover - error path
            QMessageBox.critical(self, "Cache Error", message)
