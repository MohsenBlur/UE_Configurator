"""CVar Indexer CLI."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Iterable, List, Dict, Tuple

import contextlib
import rich.progress
import json as jsonlib
import requests
import cloudscraper
from bs4 import BeautifulSoup

REGISTER = re.compile(
    r'IConsoleVariable::Register\s*\(\s*"(?P<name>[A-Za-z0-9_.]+)"\s*,\s*(?P<default>[^,]+),\s*"(?P<desc>[^"]+)"',
)
UE_CVAR = re.compile(
    r'UE_CVAR_(?:INTEGER|FLOAT|STRING)\s*\(\s*"(?P<name>[^"]+)"\s*,\s*(?P<default>[^,]+),\s*"(?P<desc>[^"]+)"',
)

COMMENT_CATEGORY = re.compile(r"Category:\s*(?P<val>.+)")
COMMENT_RANGE = re.compile(r"Range:\s*(?P<val>.+)")

DOCS_URL = (
    "https://dev.epicgames.com/documentation/en-us/unreal-engine/"
    "unreal-engine-console-variables-reference"
)


def parse_console_variable_page(html: str) -> List[Dict[str, str]]:
    """Parse console variables from a reference HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, str]] = []
    for table in soup.find_all("table", class_="table"):
        rows = table.find_all("tr")
        # Skip the header row that contains column titles.
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            name = cols[0].get_text(strip=True)
            default = cols[1].get_text(strip=True)
            desc = cols[2].get_text(strip=True)
            results.append(
                {
                    "name": name,
                    "description": desc,
                    "default": default,
                    "category": "",
                    "range": "",
                    "file": "",
                }
            )
    return results


def scrape_console_variables(version: str) -> List[Dict[str, str]]:
    """Fetch console variables from Epic's online documentation for ``version``.

    Parameters
    ----------
    version:
        Engine version string, e.g. "5.4".
    """

    url = f"{DOCS_URL}?application_version={version}"
    # Some locations block generic user agents or requests without language
    # headers and respond with HTTP 403.  Pretend to be a real browser so that
    # the request succeeds more reliably for end users.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        # Some regions appear to require a referer header for the request to
        # succeed.  Provide one to further mimic a real browser request.
        "Referer": "https://dev.epicgames.com/documentation/",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 403:
        # Some environments sit behind Cloudflare protection which rejects
        # generic requests.  Retry using cloudscraper which simulates a real
        # browser more effectively.
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, headers=headers, timeout=10)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(
            f"Failed to fetch console variable reference for UE {version}: {exc}"
        ) from exc
    return parse_console_variable_page(resp.text)


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


def build_cache(
    cache_file: Path,
    engine_root: Path | None = None,
    version: str = "5.4",
    progress: rich.progress.Progress | None = None,
) -> None:
    """Build a cache of console variables.

    Parameters
    ----------
    cache_file:
        Where to write the JSON cache.
    engine_root:
        If provided, index local engine headers; otherwise fetch from the
        online documentation.
    version:
        Engine version to scrape when ``engine_root`` is ``None``.
    """

    if engine_root:
        data = index_headers(engine_root, progress)
    else:
        try:
            data = scrape_console_variables(version)
        except Exception as exc:  # pragma: no cover - network dependent
            # Network errors should not abort application startup; create an
            # empty cache instead and allow the caller to continue.
            print(f"Warning: unable to build online cache: {exc}")
            data = []
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

    parser = argparse.ArgumentParser(description="Build CVar cache")
    parser.add_argument(
        "--engine-root",
        type=Path,
        help="Optional path to a local Unreal Engine source tree",
    )
    parser.add_argument(
        "--version",
        default="5.4",
        help="Engine version to scrape from online docs (ignored if --engine-root is provided)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path.home() / ".ue5_config_assistant" / "cvar_cache.json",
    )
    args = parser.parse_args()

    progress = rich.progress.Progress() if args.engine_root else None
    with progress or contextlib.nullcontext():
        build_cache(
            cache_file=args.cache,
            engine_root=args.engine_root,
            version=args.version,
            progress=progress,
        )

    print(f"Cache written to {args.cache}")


if __name__ == "__main__":
    main()
