"""CVar Indexer CLI."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Iterable, List, Dict, Tuple

import rich.progress
import json as jsonlib

REGISTER = re.compile(
    r'IConsoleVariable::Register\s*\(\s*"(?P<name>[A-Za-z0-9_.]+)"\s*,\s*(?P<default>[^,]+),\s*"(?P<desc>[^"]+)"',
)
UE_CVAR = re.compile(
    r'UE_CVAR_(?:INTEGER|FLOAT|STRING)\s*\(\s*"(?P<name>[^"]+)"\s*,\s*(?P<default>[^,]+),\s*"(?P<desc>[^"]+)"',
)

COMMENT_CATEGORY = re.compile(r"Category:\s*(?P<val>.+)")
COMMENT_RANGE = re.compile(r"Range:\s*(?P<val>.+)")


def iter_headers(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.h"):
        yield path


def _parse_comment_metadata(lines: List[str], idx: int) -> Tuple[str | None, str | None]:
    """Parse category and range from comment lines above ``idx``."""
    category: str | None = None
    valid_range: str | None = None
    for j in range(idx - 1, max(-1, idx - 4), -1):
        line = lines[j].strip()
        if not line.startswith("//"):
            break
        comment = line[2:].strip()
        m = COMMENT_CATEGORY.search(comment)
        if m:
            category = m.group("val").strip()
        m = COMMENT_RANGE.search(comment)
        if m:
            valid_range = m.group("val").strip()
    return category, valid_range


def index_headers(root: Path, progress: rich.progress.Progress | None = None) -> list[dict[str, str]]:
    results = []
    headers = list(iter_headers(root)) if progress else iter_headers(root)
    task_id = None
    if progress:
        task_id = progress.add_task("Headers", total=len(headers))
    for header in headers:
        text = header.read_text(errors="ignore")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            match = REGISTER.search(line) or UE_CVAR.search(line)
            if match:
                category, rng = _parse_comment_metadata(lines, idx)
                results.append(
                    {
                        "name": match.group("name"),
                        "description": match.group("desc"),
                        "default": match.group("default").strip(),
                        "category": category or "",
                        "range": rng or "",
                        "file": str(header),
                    }
                )
        if progress and task_id is not None:
            progress.advance(task_id)
    return results


def build_cache(engine_root: Path, cache_file: Path, progress: rich.progress.Progress | None = None) -> None:
    data = index_headers(engine_root, progress)
    cache_file.write_text(json.dumps(data, indent=2))


def load_cache(cache_file: Path) -> List[Dict[str, str]]:
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            pass
    return []


def detect_engine_from_uproject(project_dir: Path) -> Path | None:
    """Return engine root defined in a project's .uproject."""
    for up in project_dir.glob("*.uproject"):
        try:
            data = jsonlib.loads(up.read_text())
            assoc = data.get("EngineAssociation")
            if assoc and Path(assoc).exists():
                return Path(assoc)
        except Exception:
            continue
    return None


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Index UE headers for CVars")
    parser.add_argument("engine_root", type=Path)
    parser.add_argument("--cache", type=Path, default=Path.home() / ".ue5_config_assistant" / "cvar_cache.json")
    args = parser.parse_args()

    progress = rich.progress.Progress()
    with progress:
        build_cache(args.engine_root, args.cache, progress)

    print(f"Cache written to {args.cache}")


if __name__ == "__main__":
    main()
