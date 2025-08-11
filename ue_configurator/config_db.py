"""Config database for merging and manipulating ini files."""

from __future__ import annotations

import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

try:  # pragma: no cover - exercised when optional dependency missing
    from configupdater import ConfigUpdater
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    # ``configupdater`` is an optional dependency used for comment-preserving INI
    # edits.  Some environments (like the execution sandbox for this kata) do not
    # provide the external package.  To keep the project functional we ship a
    # very small subset implementation in ``_configupdater``.
    from ._configupdater import ConfigUpdater


class IniFile:
    """Wrapper around ConfigUpdater preserving file path."""

    def __init__(self, path: Path) -> None:
        self.path = path
        # ``configupdater`` raises ``DuplicateOptionError`` when the same option
        # appears multiple times within a section.  Some real world UE ini files
        # contain such duplicates, so read with ``strict=False`` to keep loading
        # resilient and let our own duplicate detection handle conflicts.
        self.updater = ConfigUpdater(strict=False)
        if path.exists():
            self.updater.read(str(path))

    def comment_option(self, section: str, option: str) -> None:
        """Comment out an option if it exists."""
        if self.updater.has_section(section) and self.updater[section].has_option(option):
            opt = self.updater[section][option]
            opt.lines[0] = f";{opt.lines[0]}"

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
        self.config_dir: Path | None = None

    def load(self, config_dir: Path) -> None:
        """Load all known ini files from ``config_dir``."""
        self.config_dir = config_dir
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
        """Comment out duplicate entries keeping the highest priority entry.

        This method no longer runs implicitly during :meth:`save`.  Call it
        explicitly if automatic duplicate commenting is desired; otherwise
        duplicates will remain untouched so the user can decide how to handle
        them.
        """
        dups = self.find_duplicates()
        for (section, option), files in dups.items():
            files_sorted = sorted(
                files,
                key=lambda f: self._priority_of(f.path.name),
            )
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

    def validate(self) -> Tuple[bool, str | None]:
        """Check for duplicates and basic syntax issues."""
        try:
            for ini in self.files:
                ini.updater.read(str(ini.path))
        except Exception as e:  # pragma: no cover - read should rarely fail
            return False, str(e)
        if self.find_duplicates():
            return False, "Duplicate entries detected"
        return True, None

    def available_targets(self) -> List[str]:
        return [ini.path.name for ini in self.files]

    def insert_setting(self, section: str, option: str, value: str, target_name: str | None = None) -> None:
        """Insert ``option`` into the specified ini file or best candidate."""
        option_l = option.lower()
        target: IniFile | None = None
        if target_name:
            for ini in self.files:
                if ini.path.name == target_name:
                    target = ini
                    break
        if target is None and self.files:
            for ini in reversed(self.files):
                if not (ini.updater.has_section(section) and ini.updater[section].has_option(option_l)):
                    target = ini
                    break
            if target is None:
                target = self.files[-1]
        if not target:
            return
        if not target.updater.has_section(section):
            target.updater.add_section(section)
        target.updater[section][option_l] = value

    def resolve_duplicate(self, section: str, option: str, action: str) -> None:
        option_l = option.lower()
        files = self.entries().get((section, option_l))
        if not files:
            return
        files_sorted = sorted(files, key=lambda f: self._priority_of(f.path.name))
        if action == "comment":
            for ini in files_sorted[:-1]:
                ini.comment_option(section, option_l)
        elif action == "delete":
            for ini in files_sorted[:-1]:
                if ini.updater.has_section(section) and ini.updater[section].has_option(option_l):
                    del ini.updater[section][option_l]

    def merge_preset(self, preset_path: Path) -> None:
        """Merge an external preset ``.ini`` file into the highest priority file."""
        if not self.files:
            return
        target = self.files[-1]
        updater = ConfigUpdater(strict=False)
        updater.read(str(preset_path))
        for sec in updater.sections():
            if not target.updater.has_section(sec):
                target.updater.add_section(sec)
            for opt, val in updater[sec].items():
                target.updater[sec][opt] = val.value

    def export_preset(self, path: Path) -> None:
        """Export current merged config to ``path``."""
        merged = ConfigUpdater(strict=False)
        for ini in self.files:
            for sec in ini.updater.sections():
                if not merged.has_section(sec):
                    merged.add_section(sec)
                for opt, val in ini.updater[sec].items():
                    if not merged[sec].has_option(opt):
                        merged[sec][opt] = val.value
        with path.open("w", encoding="utf-8") as f:
            merged.write(f)
