from __future__ import annotations

"""Minimal fallback implementation of ConfigUpdater.

This stub provides a tiny subset of the ``configupdater`` package used in the
project.  It supports only the features exercised in the tests: reading simple
INI files, manipulating options, commenting lines and writing the result back to
 disk.  It intentionally keeps the implementation lightweight and is **not** a
full replacement for the external library.
"""

from collections import OrderedDict
from typing import Dict, Iterator, Tuple

__all__ = ["ConfigUpdater"]


class Option:
    """Represents a single option within a section."""

    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value
        # store original representation so that commenting can simply prefix it
        self.lines = [f"{key}={value}\n"]


class Section:
    """Container holding options for a section."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._options: Dict[str, Option] = OrderedDict()

    # Mapping style helpers -------------------------------------------------
    def items(self) -> Iterator[Tuple[str, Option]]:
        return iter(self._options.items())

    def has_option(self, option: str) -> bool:
        return option in self._options

    def __getitem__(self, option: str) -> Option:
        return self._options[option]

    def __setitem__(self, option: str, value: str) -> None:
        opt = self._options.get(option)
        if opt is None:
            opt = Option(option, value)
            self._options[option] = opt
        else:
            opt.value = value
            opt.lines[0] = f"{option}={value}\n"

    def __delitem__(self, option: str) -> None:
        del self._options[option]


class ConfigUpdater:
    """Very small subset of :mod:`configupdater.ConfigUpdater`."""

    def __init__(self) -> None:
        self._sections: Dict[str, Section] = OrderedDict()

    # Section handling ------------------------------------------------------
    def sections(self) -> Iterator[str]:
        return iter(self._sections.keys())

    def has_section(self, name: str) -> bool:
        return name in self._sections

    def add_section(self, name: str) -> None:
        self._sections[name] = Section(name)

    def __getitem__(self, section: str) -> Section:
        return self._sections[section]

    # Reading / writing -----------------------------------------------------
    def read(self, path: str) -> None:
        current: Section | None = None
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    name = stripped[1:-1]
                    current = Section(name)
                    self._sections[name] = current
                elif current is not None and "=" in line:
                    key, val = line.split("=", 1)
                    key_l = key.strip().lower()
                    opt = Option(key_l, val.strip())
                    opt.lines[0] = raw  # preserve original including newline
                    current._options[key_l] = opt
                # ignore blank lines and comments

    def write(self, fp) -> None:
        first = True
        for name, section in self._sections.items():
            if not first:
                fp.write("\n")
            first = False
            fp.write(f"[{name}]\n")
            for opt in section._options.values():
                fp.write(opt.lines[0])
