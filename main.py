"""Launcher for UE Configurator with dependency management."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import venv
from pathlib import Path


REQUIRED_MODULES = {
    "PySide6": "PySide6",
    "configupdater": "configupdater",
    "rich": "rich",
    "requests": "requests",
    "beautifulsoup4": "bs4",
}


def _missing_modules() -> list[str]:
    missing = []
    for pkg, mod in REQUIRED_MODULES.items():
        if importlib.util.find_spec(mod) is None:
            missing.append(pkg)
    return missing


def _pip_install(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def _create_venv(venv_dir: Path) -> tuple[Path, Path]:
    """Create a virtual environment and return paths to python and pip."""
    venv.create(venv_dir, with_pip=True)
    bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bin_dir / ("python.exe" if os.name == "nt" else "python")
    pip = bin_dir / ("pip.exe" if os.name == "nt" else "pip")
    return python, pip


def ensure_dependencies() -> None:
    missing = _missing_modules()
    if not missing:
        return
    print("Missing dependencies:", ", ".join(missing))
    choice = input("Install missing packages now? [y/N] ").strip().lower()
    if not choice.startswith("y"):
        print("Continuing without installing; functionality may be limited.")
        return

    in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ
    root = Path(__file__).resolve().parent
    if not in_venv:
        venv_dir = root / ".venv"
        print(f"Creating virtual environment at {venv_dir}...")
        python, pip = _create_venv(venv_dir)
        _pip_install([str(pip), "install", *missing])
        print("Relaunching inside virtual environment...")
        os.execv(str(python), [str(python), __file__])
    else:
        _pip_install([sys.executable, "-m", "pip", "install", *missing])


def launch() -> None:
    ensure_dependencies()
    from ue_configurator.app import main as app_main  # type: ignore

    app_main()


if __name__ == "__main__":
    launch()

