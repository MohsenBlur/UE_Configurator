"""Config database for merging and manipulating ini files."""

from __future__ import annotations

import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

from configupdater import ConfigUpdater


class IniFile:
    """Wrapper around ConfigUpdater preserving file path."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.updater = ConfigUpdater()
        if path.exists():
            self.updater.read(str(path))

    def comment_option(self, section: str, option: str) -> None:
        """Comment out an option if it exists."""
        if self.updater.has_section(section) and self.updater[section].has_option(option):
            self.updater[section][option].comment()

    def write(self, backup_dir: Path) -> None:
        """Write file to disk with backup."""
        if self.path.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.path, backup_dir / self.path.name)
        with self.path.open("w", encoding="utf-8") as f:
            self.updater.write(f)


class ConfigDB:
    """In-memory merged view of ini files."""

    PRIORITY = [
        "Default",  # lowest
        "Project",
        "Platform",
        "GameUserSettings",  # highest
    ]

    def __init__(self) -> None:
        self.files: List[IniFile] = []

    def load(self, config_dir: Path) -> None:
        patterns = [
            "Default*.ini",
            "Project*.ini",
            "Platform*.ini",
            "GameUserSettings.ini",
        ]
        for pat in patterns:
            for path in sorted(config_dir.glob(pat)):
                self.files.append(IniFile(path))

    def entries(self) -> Dict[Tuple[str, str], List[IniFile]]:
        result: Dict[Tuple[str, str], List[IniFile]] = {}
        for ini in self.files:
            for sec_name in ini.updater.sections():
                section = ini.updater[sec_name]
                for opt_name, option in section.items():
                    key = (sec_name, opt_name)
                    result.setdefault(key, []).append(ini)
        return result

    def find_duplicates(self) -> Dict[Tuple[str, str], List[IniFile]]:
        dups = {k: v for k, v in self.entries().items() if len(v) > 1}
        return dups

    def comment_lower_priority(self) -> None:
        dups = self.find_duplicates()
        for (section, option), files in dups.items():
            # sort files by priority
            files_sorted = sorted(
                files,
                key=lambda f: self._priority_of(f.path.name),
            )
            # keep highest priority (last) uncommented
            for ini in files_sorted[:-1]:
                ini.comment_option(section, option)

    def _priority_of(self, filename: str) -> int:
        for idx, prefix in enumerate(self.PRIORITY):
            if filename.startswith(prefix):
                return idx
        return -1

    def save(self, config_dir: Path) -> None:
        backup_dir = config_dir / "Backup" / datetime.now().strftime("%Y-%m-%d-%H%M%S")
        for ini in self.files:
            ini.write(backup_dir)
