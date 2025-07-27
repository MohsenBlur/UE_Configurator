"""CVar Indexer CLI."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Iterable, List, Dict

import rich.progress

REGISTER = re.compile(r'IConsoleVariable::Register[^\"]*\"(?P<name>[A-Za-z0-9_.]+)\".*?\"(?P<desc>[^\"]+)\"[^;]*;')
UE_CVAR = re.compile(r'UE_CVAR_(?:INTEGER|FLOAT|STRING)\s*\(\s*\"(?P<name>[^\"]+)\"\s*,.*?\"(?P<desc>[^\"]+)\"')


def iter_headers(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.h"):
        yield path


def index_headers(root: Path) -> list[dict[str, str]]:
    results = []
    for header in iter_headers(root):
        text = header.read_text(errors="ignore")
        for pattern in (REGISTER, UE_CVAR):
            for match in pattern.finditer(text):
                results.append({"name": match.group("name"), "description": match.group("desc"), "file": str(header)})
    return results


def build_cache(engine_root: Path, cache_file: Path) -> None:
    data = index_headers(engine_root)
    cache_file.write_text(json.dumps(data, indent=2))


def load_cache(cache_file: Path) -> List[Dict[str, str]]:
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            pass
    return []


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Index UE headers for CVars")
    parser.add_argument("engine_root", type=Path)
    parser.add_argument("--cache", type=Path, default=Path.home() / ".ue5_config_assistant" / "cvar_cache.json")
    args = parser.parse_args()

    progress = rich.progress.Progress()
    with progress:
        task = progress.add_task("Indexing", total=None)
        build_cache(args.engine_root, args.cache)
        progress.update(task, completed=1)

    print(f"Cache written to {args.cache}")


if __name__ == "__main__":
    main()
