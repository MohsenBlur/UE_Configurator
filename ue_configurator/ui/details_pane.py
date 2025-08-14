"""DetailsPane shows full info for a selected CVar."""

from __future__ import annotations

from typing import Dict, List, cast
import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextBrowser,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
)

from ..config_db import ConfigDB
from .utils import infer_cvar_type


class DetailsPane(QWidget):
    def __init__(self, db: ConfigDB | None = None) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("CVar Details")
        self.text = QTextBrowser()
        self.value_edit: QWidget = QLineEdit()
        self.target_box = QComboBox()
        self.add_btn = QPushButton("Add to Config")
        self.add_btn.setEnabled(False)
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.text)
        self._layout.addWidget(self.value_edit)
        self._layout.addWidget(self.target_box)
        self._layout.addWidget(self.add_btn)

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
        dtype, min_val, max_val, options = infer_cvar_type(rng, default)
        self._setup_value_edit(dtype, min_val, max_val, options, default)
        self._populate_targets()
        self._update_add_enabled()

    def _setup_value_edit(
        self,
        dtype: str,
        min_val: float | None,
        max_val: float | None,
        options: List[str] | None,
        default: str,
    ) -> None:
        """Configure the input widget based on inferred type."""
        old = self.value_edit
        if dtype == "int":
            widget = QSpinBox()
            if min_val is not None:
                widget.setMinimum(int(min_val))
            if max_val is not None:
                widget.setMaximum(int(max_val))
            try:
                widget.setValue(int(float(default)))
            except Exception:
                pass
            widget.valueChanged.connect(lambda _=0: self._update_add_enabled())
        elif dtype == "float":
            widget = QDoubleSpinBox()
            if min_val is not None:
                widget.setMinimum(float(min_val))
            if max_val is not None:
                widget.setMaximum(float(max_val))
            try:
                widget.setValue(float(default))
            except Exception:
                pass
            widget.valueChanged.connect(lambda _=0: self._update_add_enabled())
        else:
            line = QLineEdit()
            if options:
                pattern = "|".join(map(re.escape, options))
                regex = QRegularExpression(f"^(?:{pattern})$")
                line.setValidator(QRegularExpressionValidator(regex, line))
            line.setText(default)
            line.textChanged.connect(lambda _=0: self._update_add_enabled())
            widget = line

        self._layout.replaceWidget(old, widget)
        old.deleteLater()
        self.value_edit = widget

    def _current_value(self) -> str:
        if isinstance(self.value_edit, (QSpinBox, QDoubleSpinBox)):
            return str(self.value_edit.value())
        return cast(QLineEdit, self.value_edit).text()

    def _update_add_enabled(self) -> None:
        valid = True
        if isinstance(self.value_edit, QLineEdit):
            valid = self.value_edit.hasAcceptableInput() and bool(self.value_edit.text())
        self.add_btn.setEnabled(valid)

    def _add(self) -> None:
        if not self.db or not self.current_item:
            return
        target = self.target_box.currentText()
        value = self._current_value()
        name = self.current_item.get("name", "")
        self.db.insert_setting("ConsoleVariables", name, value, target)
